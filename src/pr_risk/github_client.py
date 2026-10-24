# github_client.py - Kristian Kesar, C00296348
#
# talks to the github api. only needs 3 calls:
#   GET   /repos/{owner}/{repo}/pulls/{number}/files     -> what files the PR changed
#   POST  /repos/{owner}/{repo}/issues/{number}/comments -> make a new comment
#   PATCH /repos/{owner}/{repo}/issues/comments/{id}     -> edit an old comment
#
# only uses built in python stuff (urllib) so the github action
# doesnt have to install anything extra

import json
import urllib.error
import urllib.request

API_URL = "https://api.github.com"

# hidden tag stuck in every comment we post. github doesnt show it but it means
# we can find our own comment later and update it instead of spamming new ones
COMMENT_MARKER = "<!-- pr-risk-predictor -->"

PER_PAGE = 100   # most github will give back in one go


class GitHubError(Exception):
    pass


class GitHubClient:
    def __init__(self, token, repo, api_url=API_URL):
        # token = github token, repo = "owner/name" like "KristianKesar/pr-risk-predictor"
        if "/" not in repo:
            raise ValueError(f"repo should look like owner/name, got {repo}")
        self.token = token
        self.repo = repo
        self.api_url = api_url

    def _request(self, method, path, body=None):
        # sends one request and gives back the json.
        # all the api calls go through here so the tests can swap it for a fake one
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(
            self.api_url + path,
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "pr-risk-predictor",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            raise GitHubError(f"{method} {path} failed with {e.code}") from e

    def _get_all(self, path):
        # github splits big lists into pages of 100, so keep asking
        # for the next page until one comes back not full
        results = []
        page = 1
        while True:
            batch = self._request("GET", f"{path}?per_page={PER_PAGE}&page={page}")
            results += batch
            if len(batch) < PER_PAGE:
                return results
            page += 1

    def get_pr_files(self, pr_number):
        # every file the PR changed, in the format extract_features() wants
        return self._get_all(f"/repos/{self.repo}/pulls/{pr_number}/files")

    def find_own_comment(self, pr_number):
        # looks through the PR's comments for one with our hidden tag
        comments = self._get_all(f"/repos/{self.repo}/issues/{pr_number}/comments")
        for comment in comments:
            if COMMENT_MARKER in (comment.get("body") or ""):
                return comment
        return None

    def upsert_comment(self, pr_number, body):
        # "upsert" = update it if it's there, otherwise make a new one.
        # keeps it to one comment on the PR that stays up to date
        if COMMENT_MARKER not in body:
            body = COMMENT_MARKER + "\n" + body

        old = self.find_own_comment(pr_number)
        if old:
            return self._request("PATCH", f"/repos/{self.repo}/issues/comments/{old['id']}",
                                 {"body": body})
        return self._request("POST", f"/repos/{self.repo}/issues/{pr_number}/comments",
                             {"body": body})
