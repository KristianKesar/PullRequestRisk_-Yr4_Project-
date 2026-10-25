# test_cli.py - Kristian Kesar, C00296348
# tests for the pr-risk command, no internet used

import json

from pr_risk import cli


def test_features_prints_json(tmp_path, capsys):
    path = tmp_path / "files.json"
    path.write_text(json.dumps([{"filename": "src/a.py", "additions": 10, "deletions": 2}]))

    assert cli.main(["features", str(path)]) == 0
    out = json.loads(capsys.readouterr().out)   # capsys grabs what got printed
    assert out["total_churn"] == 12


def test_features_markdown(tmp_path, capsys):
    path = tmp_path / "files.json"
    path.write_text("[]")
    assert cli.main(["features", str(path), "--markdown"]) == 0
    assert "## PR Risk Predictor" in capsys.readouterr().out


def test_comment_needs_a_token(monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    assert cli.main(["comment", "--repo", "o/r", "--pr", "1"]) == 2
    assert "GITHUB_TOKEN" in capsys.readouterr().out


def test_comment_posts(monkeypatch):
    posted = {}

    # fake github client that just remembers what it was told to post
    class FakeClient:
        def __init__(self, token, repo):
            pass

        def get_pr_files(self, pr):
            return [{"filename": "a.py", "additions": 5, "deletions": 0}]

        def upsert_comment(self, pr, body):
            posted["pr"] = pr
            posted["body"] = body

    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setattr(cli, "GitHubClient", FakeClient)   # swap the real one out

    assert cli.main(["comment", "--repo", "o/r", "--pr", "4"]) == 0
    assert posted["pr"] == 4
    assert "PR Risk Predictor" in posted["body"]
