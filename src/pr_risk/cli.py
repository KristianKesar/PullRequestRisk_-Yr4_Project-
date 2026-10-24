# cli.py - Kristian Kesar, C00296348
#
# the command line bit. after pip install it's just the `pr-risk` command
#
#   pr-risk comment --repo owner/name --pr 12            -> looks at a PR and comments on it
#   pr-risk comment --repo owner/name --pr 12 --dry-run  -> same but just prints it, doesnt post
#   pr-risk features some_files.json                     -> test it on a saved file, no github needed
#
# the github token comes from the GITHUB_TOKEN environment variable

import argparse
import json
import os

from .features import extract_features
from .github_client import GitHubClient, GitHubError
from .report import format_comment


def run_comment(args):
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("need a GITHUB_TOKEN environment variable set")
        return 2

    client = GitHubClient(token, args.repo)
    try:
        files = client.get_pr_files(args.pr)
        body = format_comment(extract_features(files))
        if args.dry_run:
            print(body)
        else:
            client.upsert_comment(args.pr, body)
            print(f"commented on PR #{args.pr} ({len(files)} files looked at)")
    except GitHubError as e:
        print(f"github error: {e}")
        return 1
    return 0


def run_features(args):
    with open(args.json_file) as f:
        files = json.load(f)
    feats = extract_features(files)
    if args.markdown:
        print(format_comment(feats))   # show what the PR comment would look like
    else:
        print(json.dumps(feats.to_dict(), indent=2))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="pr-risk", description="scores PRs for bug risk")
    commands = parser.add_subparsers(dest="command", required=True)

    c = commands.add_parser("comment", help="look at a github PR and comment on it")
    c.add_argument("--repo", required=True, help="owner/name")
    c.add_argument("--pr", required=True, type=int, help="PR number")
    c.add_argument("--dry-run", action="store_true", help="print it instead of posting")
    c.set_defaults(run=run_comment)

    f = commands.add_parser("features", help="get features from a json file of changed files")
    f.add_argument("json_file")
    f.add_argument("--markdown", action="store_true", help="show the PR comment instead")
    f.set_defaults(run=run_features)

    args = parser.parse_args(argv)
    return args.run(args)


if __name__ == "__main__":
    raise SystemExit(main())
