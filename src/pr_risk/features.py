"""
features.py
Kristian Kesar, C00296348

Turns the list of files changed in a pull request into numeric features
the risk model can learn from.

Input is the same shape GitHub returns from
    GET /repos/{owner}/{repo}/pulls/{number}/files
i.e. a list of dicts with at least "filename", "additions", "deletions"
and "status". That means the same code works on live PRs (via the
GitHub API) and on historical data used for training.
"""

from dataclasses import dataclass, asdict
from pathlib import PurePosixPath

# File extensions counted as source code. Docs, configs and images are
# changed often but rarely introduce defects, so they're tracked apart.
SOURCE_EXTENSIONS = {
    ".py", ".java", ".kt", ".js", ".ts", ".go", ".c", ".cpp", ".h",
    ".cs", ".rb", ".php", ".rs", ".swift", ".scala", ".dart",
}


@dataclass
class PRFeatures:
    """Feature values for one pull request."""

    files_changed: int = 0       # total files touched
    source_files: int = 0        # files that are actual code
    test_files: int = 0          # files that look like tests
    lines_added: int = 0
    lines_deleted: int = 0
    total_churn: int = 0         # added + deleted
    max_file_churn: int = 0      # biggest single-file change
    directories_touched: int = 0 # how spread out the change is
    files_deleted: int = 0
    touches_tests: bool = False  # did the PR change any tests at all

    def to_dict(self) -> dict:
        """Plain dict, handy for building a pandas DataFrame later."""
        return asdict(self)


def is_test_file(filename: str) -> bool:
    """True if the path looks like a test file.

    Covers the common conventions: test_x.py, x_test.go, XTest.java,
    x.spec.ts, and anything inside a tests/ or test/ folder.
    """
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
        or stem.endswith(("Test", "Tests"))   # Java/Kotlin style: UserTest.java
        or ".spec." in lower_name
        or ".test." in lower_name
    )
    return in_test_dir or named_like_test


def is_source_file(filename: str) -> bool:
    """True if the file extension is one of the code extensions above."""
    return PurePosixPath(filename).suffix.lower() in SOURCE_EXTENSIONS


def extract_features(changed_files: list[dict]) -> PRFeatures:
    """Build the feature set for one PR from its list of changed files."""
    feats = PRFeatures()
    directories = set()

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

        # Tests are counted separately from source so the model can
        # tell "big change with tests" apart from "big change, no tests"
        if is_test_file(filename):
            feats.test_files += 1
        elif is_source_file(filename):
            feats.source_files += 1

        # Parent folder ("" for files at the repo root)
        directories.add(str(PurePosixPath(filename).parent))

    feats.total_churn = feats.lines_added + feats.lines_deleted
    feats.directories_touched = len(directories)
    feats.touches_tests = feats.test_files > 0
    return feats
