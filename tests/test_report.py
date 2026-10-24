# test_report.py - Kristian Kesar, C00296348
# checks the PR comment comes out right

from pr_risk.features import PRFeatures
from pr_risk.github_client import COMMENT_MARKER
from pr_risk.report import LARGE_CHURN, format_comment, observations


def test_small_change_with_tests_gets_no_warnings():
    f = PRFeatures(files_changed=2, source_files=1, test_files=1,
                   total_churn=20, touches_tests=True, subsystems_touched=1)
    assert observations(f) == []


def test_warns_about_big_change():
    f = PRFeatures(total_churn=LARGE_CHURN + 1)
    assert any("Large change" in n for n in observations(f))


def test_warns_when_code_changed_but_no_tests():
    f = PRFeatures(source_files=3, touches_tests=False)
    assert any("no test files" in n for n in observations(f))


def test_comment_has_tag_heading_and_table():
    body = format_comment(PRFeatures(files_changed=4, change_entropy=1.5))
    assert body.startswith(COMMENT_MARKER)   # hidden tag has to be there to find it later
    assert "## PR Risk Predictor" in body
    assert "| Files changed | 4 |" in body
    assert "| Change spread (entropy) | 1.50 |" in body   # decimals rounded to 2


def test_says_so_when_nothing_found():
    assert "No obvious risk signals" in format_comment(PRFeatures())
