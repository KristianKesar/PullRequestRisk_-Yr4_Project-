"""
test_features.py
Kristian Kesar, C00296348

Unit tests for feature extraction. Each test builds a fake PR file list
in the same shape the GitHub API returns.
"""

from pr_risk.features import extract_features, is_source_file, is_test_file


def make_file(filename, additions=0, deletions=0, status="modified"):
    """Helper: one entry as returned by the GitHub PR files endpoint."""
    return {
        "filename": filename,
        "additions": additions,
        "deletions": deletions,
        "status": status,
    }


# ---- test file detection --------------------------------------------

def test_detects_common_test_file_names():
    assert is_test_file("tests/test_features.py")
    assert is_test_file("pkg/handler_test.go")
    assert is_test_file("src/UserTest.java")
    assert is_test_file("web/app.spec.ts")


def test_normal_code_is_not_a_test():
    assert not is_test_file("src/pr_risk/features.py")
    assert not is_test_file("main.go")
    assert not is_test_file("src/latest.py")    # ends in "test" but isn't one
    assert not is_test_file("src/contest.py")


def test_source_file_detection():
    assert is_source_file("src/app.py")
    assert is_source_file("Main.JAVA")      # case shouldn't matter
    assert not is_source_file("README.md")
    assert not is_source_file("logo.png")


# ---- feature extraction ---------------------------------------------

def test_empty_pr_gives_all_zeros():
    feats = extract_features([])
    assert feats.files_changed == 0
    assert feats.total_churn == 0
    assert feats.touches_tests is False


def test_counts_lines_and_files():
    files = [
        make_file("src/a.py", additions=10, deletions=2),
        make_file("src/b.py", additions=5, deletions=5),
    ]
    feats = extract_features(files)
    assert feats.files_changed == 2
    assert feats.lines_added == 15
    assert feats.lines_deleted == 7
    assert feats.total_churn == 22
    assert feats.max_file_churn == 12


def test_separates_source_tests_and_other_files():
    files = [
        make_file("src/a.py", 10, 0),
        make_file("tests/test_a.py", 8, 0),
        make_file("README.md", 3, 1),
    ]
    feats = extract_features(files)
    assert feats.source_files == 1
    assert feats.test_files == 1
    assert feats.touches_tests is True


def test_counts_directories_and_deletions():
    files = [
        make_file("src/a.py", 1, 0),
        make_file("src/b.py", 1, 0),
        make_file("docs/old.md", 0, 40, status="removed"),
        make_file("setup.py", 2, 0),          # repo root
    ]
    feats = extract_features(files)
    assert feats.directories_touched == 3     # src, docs, root
    assert feats.files_deleted == 1


def test_to_dict_has_every_feature():
    feats = extract_features([make_file("src/a.py", 1, 1)])
    d = feats.to_dict()
    assert d["total_churn"] == 2
    assert set(d) >= {"files_changed", "source_files", "touches_tests"}
