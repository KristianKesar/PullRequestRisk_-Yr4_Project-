# report.py - Kristian Kesar, C00296348
#
# builds the comment that gets posted on the PR (github markdown).
# for now it just shows the features + a few simple warnings.
# once the model's trained the risk score + reasons go in here too
#
# NEW - also makes the per-file warnings that show up as yellow boxes
# right next to the code in the PR's "Files changed" tab

import re

from .features import is_source_file, is_test_file
from .github_client import COMMENT_MARKER

# rough limits for the warnings, just placeholders til the model does it properly.
# from the apachejit data buggy commits were around 193 lines and 6 files
# (the middle value), so these only flag stuff well over that
LARGE_CHURN = 400
MANY_FILES = 10
MANY_SUBSYSTEMS = 3
BIG_FILE_CHURN = 200   # NEW - one single file changing this much is worth a look

# github only shows 10 warnings per step, so no point making more than that
MAX_FILE_WARNINGS = 10

# feature name -> what it says in the table, in this order
FEATURE_LABELS = [
    ("files_changed", "Files changed"),
    ("source_files", "Source files"),
    ("test_files", "Test files"),
    ("lines_added", "Lines added"),
    ("lines_deleted", "Lines deleted"),
    ("total_churn", "Total lines changed"),
    ("max_file_churn", "Largest single-file change"),
    ("directories_touched", "Directories touched"),
    ("subsystems_touched", "Top-level areas touched"),
    ("change_entropy", "Change spread (entropy)"),
    ("files_deleted", "Files deleted"),
]


def observations(f):
    # plain english warnings for stuff that usually goes with risky changes
    notes = []
    if f.total_churn >= LARGE_CHURN:
        notes.append(f"Large change: {f.total_churn} lines. Consider splitting it into smaller PRs.")
    if f.files_changed >= MANY_FILES:
        notes.append(f"Touches {f.files_changed} files, which makes it harder to review.")
    if f.subsystems_touched >= MANY_SUBSYSTEMS:
        notes.append(f"Spans {f.subsystems_touched} top-level areas of the codebase.")
    if f.source_files > 0 and not f.touches_tests:
        notes.append("Source code changed but no test files were updated.")
    return notes


def format_comment(f):
    lines = [COMMENT_MARKER, "## PR Risk Predictor", ""]

    # warnings first cause that's what people actually care about
    notes = observations(f)
    if notes:
        lines.append("**Things to look at:**")
        for note in notes:
            lines.append(f"- {note}")
    else:
        lines.append("No obvious risk signals in the size or spread of this change.")
    lines.append("")

    # then the full feature table, folded up so it doesnt take over the PR
    lines += ["<details><summary>Extracted features</summary>", "",
              "| Feature | Value |", "|---|---|"]
    data = f.to_dict()
    for key, label in FEATURE_LABELS:
        value = data[key]
        if isinstance(value, float):
            value = f"{value:.2f}"   # 1.3333 -> 1.33
        lines.append(f"| {label} | {value} |")
    lines += ["", "</details>", "",
              "_Iteration 1 build: risk score from the trained model coming soon._"]

    return "\n".join(lines)


# ---- NEW: per-file warnings ------------------------------------------

def first_changed_line(file):
    # github gives each file a "patch" (the diff). the first bit looks like
    # "@@ -10,4 +12,7 @@" and the number after + is where the new code starts.
    # we stick the warning on that line so it shows up right next to the change
    match = re.search(r"\+(\d+)", file.get("patch") or "")
    return int(match.group(1)) if match else 1


def file_warnings(changed_files):
    # goes through each file and works out what to warn about.
    # gives back a list of (filename, line, message)
    any_tests = any(is_test_file(f["filename"]) for f in changed_files)
    warnings = []

    for f in changed_files:
        name = f["filename"]
        if f.get("status") == "removed":
            continue   # cant put a warning on a file that's gone
        if is_test_file(name) or not is_source_file(name):
            continue   # only warn about actual code

        churn = f.get("additions", 0) + f.get("deletions", 0)
        messages = []
        if churn >= BIG_FILE_CHURN:
            messages.append(f"{churn} lines changed in this file, worth a careful review.")
        if not any_tests:
            messages.append("Code changed here but no tests were updated in this PR.")

        if messages:
            warnings.append((churn, name, first_changed_line(f), " ".join(messages)))

    # biggest changes first, then cut it down to what github will show
    warnings.sort(reverse=True)
    return [(name, line, msg) for churn, name, line, msg in warnings[:MAX_FILE_WARNINGS]]


def annotation(filename, line, message):
    # github actions turns lines printed like this into the yellow warning boxes:
    #   ::warning file=src/a.py,line=12,title=PR Risk::the message
    # some characters have to be swapped out or github gets confused
    message = message.replace("%", "%25").replace("\n", "%0A")
    filename = filename.replace("%", "%25").replace(",", "%2C").replace(":", "%3A")
    return f"::warning file={filename},line={line},title=PR Risk::{message}"
