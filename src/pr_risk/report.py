# report.py - Kristian Kesar, C00296348
#
# builds the comment that gets posted on the PR (github markdown).
# for now it just shows the features + a few simple warnings.
# once the model's trained the risk score + reasons go in here too

from .github_client import COMMENT_MARKER

# rough limits for the warnings, just placeholders til the model does it properly.
# from the apachejit data buggy commits were around 193 lines and 6 files
# (the middle value), so these only flag stuff well over that
LARGE_CHURN = 400
MANY_FILES = 10
MANY_SUBSYSTEMS = 3

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
