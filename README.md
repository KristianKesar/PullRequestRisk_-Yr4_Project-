# PR Risk Predictor

Kristian Kesar, C00296348
SETU Year 4 Software Development Project

## What is this

When someone opens a pull request, it's hard to tell at a glance whether it's
a safe little fix or something that's going to break stuff. This project looks
at a PR and flags the stuff that tends to go with buggy changes, like loads of
lines changed, changes spread all over the codebase, or code changed with no
tests. It puts all that right on the PR so whoever's reviewing it sees it
straight away.

The end goal is a machine learning model that gives each PR a risk score and
tells you why it got that score. I'm training it on ApacheJIT, a dataset of
about 106k commits from real Apache projects where each one is marked as
having caused a bug or not.

## What it does right now

Every time a PR gets opened or updated:

1. A GitHub Action kicks off and runs my `pr-risk` command
2. It gets the list of files the PR changed from the GitHub API
3. It works out the features (how big the change is, how spread out it is, if any tests were touched etc.)
4. It posts a comment on the PR with any warnings and a table of the features
5. It puts yellow warnings right next to the risky files in the Files changed tab

If you push again, it updates the same comment instead of posting a new one,
so the PR doesn't get spammed.

There's also a CI workflow that runs the linter and all the tests every time I
push, so I find out straight away if I've broken something.

On the machine learning side, I've trained a first basic model (logistic
regression) on the dataset. It's about 2.5 times better than random guessing
and a bit better than a simple "flag anything over 400 lines" rule. It isn't
hooked up to the PR comment yet, that's next iteration. The full results are
in [the iteration 1 notes](docs/iterations/iteration-1.md).

## Where it's at

Iteration 1, due 30th October 2026

- [x] GitHub Action that comments on every PR
- [x] Pulling features out of a PR's changed files
- [x] PR comment built from my own features (this replaced the linter I started with)
- [x] Yellow warnings next to risky files
- [x] Dataset picked (ApacheJIT) and loading in
- [x] CI running the tests and linter
- [x] First basic model (logistic regression), tested against a simple rule
- [x] Charts for the dataset and the model results

## How the code is laid out

```
src/pr_risk/
  features.py        turns a PR's changed files into numbers
  dataset.py         loads ApacheJIT and renames the columns to match my features
  github_client.py   talks to the GitHub API
  report.py          builds the PR comment and the file warnings
  cli.py             the pr-risk command
  model.py           the logistic regression model + how it gets scored
scripts/
  download_data.py   downloads the dataset
  train.py           trains the model, tests it and saves it
  make_charts.py     makes the charts in docs/images
tests/               unit tests, none of them need the internet
examples/            a fake PR you can try it on
data/                info about the dataset (the actual files aren't in git)
models/              the trained model ends up here (not in git either)
docs/                iteration notes, charts and a walkthrough of how it all works
.github/workflows/   pr-risk.yml (comments + warnings) and ci.yml (tests + lint)
```

If you want the proper explanation of how each part works, have a look at
[docs/how-it-works.md](docs/how-it-works.md).

## Setting it up

You need Python 3.10 or newer.

```bash
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Mac / Linux
source .venv/bin/activate

pip install -e ".[dev]"
python scripts/download_data.py
```

The last one downloads the dataset into `data/raw/`. It's about 30MB so it's
not kept in git.

If PowerShell says running scripts is disabled, run
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once and try again.

## Trying it out

Run the tests and the linter:

```bash
python -m pytest
ruff check src tests scripts
```

Try it on the fake PR in `examples/` (no GitHub needed):

```bash
pr-risk features examples/sample_pr_files.json --markdown
pr-risk features examples/sample_pr_files.json --annotate
```

The first one shows the comment it would post, the second shows the file
warnings.

To see what it'd say about a real PR without actually posting anything, you
need a GitHub token in `GITHUB_TOKEN`, then:

```bash
pr-risk comment --repo owner/name --pr 3 --dry-run
```

Train the model and make the charts (needs the dataset downloaded first):

```bash
python scripts/train.py
python scripts/make_charts.py
```

Training takes a couple of seconds. It prints the results and saves the model
to `models/risk_model.joblib`.

## The dataset

ApacheJIT, from Keshavarz & Nagappan (MSR 2022). There's more about it, and
what I found when I first looked at it, in [data/README.md](data/README.md).
