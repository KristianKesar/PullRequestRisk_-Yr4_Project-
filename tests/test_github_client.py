# test_github_client.py - Kristian Kesar, C00296348
#
# tests for the github stuff. never actually touches the internet,
# FakeClient swaps out _request and just gives back made up answers

import pytest

from pr_risk.github_client import COMMENT_MARKER, PER_PAGE, GitHubClient


class FakeClient(GitHubClient):
    def __init__(self, answers):
        super().__init__("fake-token", "owner/repo")
        self.answers = answers   # (method, path) -> what to give back
        self.calls = []          # remembers every call so we can check them

    def _request(self, method, path, body=None):
        self.calls.append((method, path, body))
        return self.answers.get((method, path), [])


def files_url(pr, page):
    return f"/repos/owner/repo/pulls/{pr}/files?per_page={PER_PAGE}&page={page}"


def comments_url(pr, page):
    return f"/repos/owner/repo/issues/{pr}/comments?per_page={PER_PAGE}&page={page}"


def test_repo_needs_owner_and_name():
    with pytest.raises(ValueError):
        GitHubClient("token", "just-a-name")


def test_gets_pr_files():
    files = [{"filename": "a.py", "additions": 1, "deletions": 0}]
    client = FakeClient({("GET", files_url(7, 1)): files})
    assert client.get_pr_files(7) == files


def test_keeps_going_through_pages():
    # page 1 is full (100 files) so it should ask for page 2 as well
    full_page = [{"filename": f"f{i}.py"} for i in range(PER_PAGE)]
    client = FakeClient({
        ("GET", files_url(7, 1)): full_page,
        ("GET", files_url(7, 2)): [{"filename": "last.py"}],
    })
    files = client.get_pr_files(7)
    assert len(files) == PER_PAGE + 1
    assert files[-1]["filename"] == "last.py"


def test_makes_new_comment_if_none_yet():
    client = FakeClient({("GET", comments_url(3, 1)): [{"id": 1, "body": "someone else"}]})
    client.upsert_comment(3, "hello")

    method, path, body = client.calls[-1]
    assert method == "POST"
    assert path == "/repos/owner/repo/issues/3/comments"
    assert COMMENT_MARKER in body["body"]   # hidden tag gets added
    assert "hello" in body["body"]


def test_updates_our_old_comment():
    old = {"id": 99, "body": COMMENT_MARKER + "\nold report"}
    client = FakeClient({("GET", comments_url(3, 1)): [old]})
    client.upsert_comment(3, "new report")

    method, path, body = client.calls[-1]
    assert method == "PATCH"   # edit, not a new comment
    assert path == "/repos/owner/repo/issues/comments/99"
    assert "new report" in body["body"]
