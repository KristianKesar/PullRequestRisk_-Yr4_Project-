# test_annotations.py - Kristian Kesar, C00296348
# NEW - tests for the per-file warnings (the yellow boxes in "Files changed")

from pr_risk import cli
from pr_risk.report import BIG_FILE_CHURN, annotation, file_warnings, first_changed_line


def make_file(name, added=0, deleted=0, status="modified", patch=""):
    return {"filename": name, "additions": added, "deletions": deleted,
            "status": status, "patch": patch}


def test_finds_first_changed_line_in_the_diff():
    assert first_changed_line({"patch": "@@ -10,4 +12,7 @@ def thing():"}) == 12
    assert first_changed_line({}) == 1   # no diff (eg huge files) -> just use line 1


def test_warns_about_code_with_no_tests():
    warnings = file_warnings([make_file("src/a.py", 10, 0)])
    assert len(warnings) == 1
    name, _, msg = warnings[0]   
    assert name == "src/a.py"
    assert "no tests" in msg


def test_no_test_warning_if_pr_has_tests():
    files = [make_file("src/a.py", 10, 0), make_file("tests/test_a.py", 5, 0)]
    assert file_warnings(files) == []


def test_warns_about_one_big_file():
    files = [make_file("src/big.py", BIG_FILE_CHURN, 0), make_file("tests/test_big.py", 5, 0)]
    warnings = file_warnings(files)
    assert len(warnings) == 1
    assert "200 lines changed" in warnings[0][2]


def test_skips_docs_and_deleted_files():
    files = [make_file("README.md", 500, 0), make_file("src/old.py", 0, 300, status="removed")]
    assert file_warnings(files) == []


def test_biggest_file_comes_first():
    files = [make_file("src/small.py", 5, 0), make_file("src/huge.py", 300, 0)]
    assert file_warnings(files)[0][0] == "src/huge.py"


def test_annotation_format():
    line = annotation("src/a.py", 12, "careful")
    assert line == "::warning file=src/a.py,line=12,title=PR Risk::careful"


def test_annotate_flag_prints_warnings(tmp_path, capsys):
    path = tmp_path / "files.json"
    path.write_text('[{"filename": "src/a.py", "additions": 10, "deletions": 0}]')
    assert cli.main(["features", str(path), "--annotate"]) == 0
    assert "::warning file=src/a.py" in capsys.readouterr().out
