# features.py - Kristian Kesar, C00296348
#
# takes the list of files a PR changed and turns it into numbers the model can use.
# the input is the exact same format github gives back from
#   GET /repos/{owner}/{repo}/pulls/{number}/files
# so it works on live PRs and on the old data for training, no extra code needed

import math
from dataclasses import asdict, dataclass
from pathlib import PurePosixPath

# file types that count as actual code. docs/configs/images get changed loads
# but they rarely break anything so they're kept separate
SOURCE_EXTENSIONS = {
    ".py", ".java", ".kt", ".js", ".ts", ".go", ".c", ".cpp", ".h",
    ".cs", ".rb", ".php", ".rs", ".swift", ".scala", ".dart",
}


@dataclass
class PRFeatures:
    # all the numbers for one PR

    files_changed: int = 0         # total files touched
    source_files: int = 0          # files that are actual code
    test_files: int = 0            # files that look like tests
    lines_added: int = 0
    lines_deleted: int = 0
    total_churn: int = 0           # added + deleted
    max_file_churn: int = 0        # biggest change to a single file
    directories_touched: int = 0   # how many folders it hits
    subsystems_touched: int = 0    # NEW - top level folders, like src/ or docs/
    change_entropy: float = 0.0    # NEW - how spread out the change is over the files
    files_deleted: int = 0
    touches_tests: bool = False    # did it change any tests at all

    def to_dict(self) -> dict:
        # plain dict, makes it easy to stick into pandas later
        return asdict(self)


def is_test_file(filename: str) -> bool:
    # checks if a file looks like a test. covers the usual ways people name them:
    # test_x.py, x_test.go, XTest.java, x.spec.ts, or anything in a tests/ folder
    path = PurePosixPath(filename)
    name = path.name
    stem = name.split(".")[0]
    lower_name = name.lower()

    in_test_dir = any(
        part.lower() in ("test", "tests", "__tests__") for part in path.parts[:-1]
    )
    named_like_test = (
        stem.lower().startswith("test_")
        or stem.lower().endswith("_test")
        or stem.endswith(("Test", "Tests"))   # java/kotlin style, UserTest.java
        or ".spec." in lower_name
        or ".test." in lower_name
    )
    return in_test_dir or named_like_test


def is_source_file(filename: str) -> bool:
    # true if the extension is one of the code ones up top
    return PurePosixPath(filename).suffix.lower() in SOURCE_EXTENSIONS


def subsystem_of(filename: str) -> str:
    # NEW - gets the top level folder, "src/app/main.py" -> "src"
    # files sitting in the root just get "" so they still count as their own area
    parts = PurePosixPath(filename).parts
    return parts[0] if len(parts) > 1 else ""


def change_entropy(churn_per_file: list[int]) -> float:
    # NEW - 0 means the whole change is in one file, bigger means it's spread
    # evenly over loads of files. spread out changes tend to cause more bugs.
    # it's the same thing as the "ent" column in apachejit so the numbers match up
    total = sum(churn_per_file)
    if total == 0:
        return 0.0
    entropy = 0.0
    for churn in churn_per_file:
        if churn > 0:
            p = churn / total
            entropy -= p * math.log2(p)
    return entropy


def extract_features(changed_files: list[dict]) -> PRFeatures:
    # the main one - goes through every file in the PR and adds everything up
    feats = PRFeatures()
    directories = set()
    subsystems = set()    # NEW
    churn_per_file = []   # NEW - needed for the entropy

    for f in changed_files:
        filename = f["filename"]
        added = int(f.get("additions", 0))
        deleted = int(f.get("deletions", 0))
        churn = added + deleted

        feats.files_changed += 1
        feats.lines_added += added
        feats.lines_deleted += deleted
        feats.max_file_churn = max(feats.max_file_churn, churn)

        if f.get("status") == "removed":
            feats.files_deleted += 1

        # tests counted separate from normal code so the model can tell
        # "big change with tests" apart from "big change, no tests"
        if is_test_file(filename):
            feats.test_files += 1
        elif is_source_file(filename):
            feats.source_files += 1

        # parent folder ("." for files in the root) + top level folder
        directories.add(str(PurePosixPath(filename).parent))
        subsystems.add(subsystem_of(filename))
        churn_per_file.append(churn)

    feats.total_churn = feats.lines_added + feats.lines_deleted
    feats.directories_touched = len(directories)
    feats.subsystems_touched = len(subsystems)            # NEW
    feats.change_entropy = change_entropy(churn_per_file)  # NEW
    feats.touches_tests = feats.test_files > 0
    return feats
