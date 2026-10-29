# How it works

Kristian Kesar, C00296348

This goes through what happens from the moment someone opens a PR to the
moment the comment shows up, and what each file in the project does.

## The whole flow

```
someone opens or updates a PR
        |
GitHub Action (pr-risk.yml) starts up
        |
pr-risk comment --annotate          (cli.py)
        |
get the PR's changed files          (github_client.py)
        |
work out the features               (features.py)
        |
build the comment + file warnings   (report.py)
        |
post or update the comment          (github_client.py)
print the warnings for GitHub to show next to the files
```

## features.py

This is the core of it. It takes the list of files a PR changed, in the exact
format the GitHub API gives back (filename, lines added, lines deleted,
status), and turns it into numbers.

- **files_changed, lines_added, lines_deleted, total_churn**: the basics of how big the change is
- **max_file_churn**: the biggest change to any one file
- **source_files / test_files**: splits code files from test files, so the model can tell "big change with tests" apart from "big change with no tests"
- **directories_touched**: how many different folders it hits
- **subsystems_touched**: how many top-level folders it hits (like `src/` and `docs/`)
- **change_entropy**: how evenly the change is spread over the files. 0 means it's all in one file, and the higher it goes the more spread out it is. Spread-out changes are harder to review and tend to cause more bugs.
- **files_deleted, touches_tests**: pretty self explanatory

The reason it takes the GitHub format is so the same code works on live PRs
and on the training data. There's no separate version for training.

## dataset.py

Loads the ApacheJIT CSVs and renames the columns to the names `features.py`
uses (so `la` becomes `lines_added`, `ent` becomes `change_entropy`, and so
on). It also works out `total_churn` and turns the `buggy` column from
True/False into 1/0.

`load_split()` gives back the training data (2003-2016) and the test data
(2017-2019), and `to_xy()` splits a table into the features going in (X) and
the answer (y). There's a test that checks every feature the model trains on
can also be made from a real PR, so they can't drift apart.

## github_client.py

Talks to the GitHub API. It only needs three things:

- get the list of files a PR changed
- post a new comment
- edit an old comment

GitHub sends lists back in pages of 100, so `_get_all()` keeps asking for the
next page until it gets one that isn't full.

Every comment it posts has a hidden tag in it (`<!-- pr-risk-predictor -->`).
GitHub doesn't show it, but it means next time the tool can find its own
comment and update it instead of posting another one.

It only uses built-in Python stuff (`urllib`), so the GitHub Action doesn't
need to install anything extra to run it.

## report.py

Builds what you actually see on the PR.

The **comment** has the warnings at the top, then a folded-up table with all
the features. The warnings are:

- 400+ lines changed
- 10+ files changed
- 3+ top-level areas touched
- code changed but no tests updated

The **file warnings** are the yellow boxes in the Files changed tab. A code
file gets one if it has 200+ lines changed, or if the PR changed code without
touching any tests. The warning goes on the first line that changed in that
file. It works that out from the diff, which starts with something like
`@@ -10,4 +12,7 @@`, and the number after the `+` is where the new code
starts. GitHub only shows 10 of these per run, so the biggest changes go
first.

These limits are placeholders for now. They're based on the dataset (see
[data/README.md](../data/README.md)), but the model's score will replace them.

## cli.py

The `pr-risk` command. It has two modes:

- `pr-risk comment` is what the GitHub Action runs. It does the whole flow on a real PR. `--dry-run` prints the comment instead of posting it, and `--annotate` prints the file warnings.
- `pr-risk features some_file.json` runs it on a saved list of files, so you can try it without GitHub at all.

## model.py

The first basic model. It's logistic regression, which takes the features and
gives back a chance between 0 and 1 that the change is buggy. Before the model
sees the numbers they go through two steps, all wrapped up in one pipeline so
they always happen in the same order:

1. **log1p** squashes the big numbers down. A 5000 line change isn't 100 times
   riskier than a 50 line one, and without this the huge changes would take over.
2. **scaler** puts every feature on the same scale, so none of them win just
   because their numbers are bigger.

It also has `rule_baseline()`, which scores the simple "flag anything over 400
lines" rule the same way. If the model can't beat that, there's no point
having a model.

## scripts/train.py

Trains the model on 2003-2016, tests it on 2017-2019, and prints:

- **PR-AUC**, the main score. Random guessing gets the share of buggy changes
  (about 0.19 here), so that's the number to beat.
- **Recall**, out of all the buggy changes, how many it caught
- **Precision**, out of everything it flagged, how many were actually buggy
- the same numbers for the 400 line rule
- the model again, but only allowed to flag as many changes as the rule does,
  so it's a fair comparison
- how much each feature pushes the risk up or down

Then it saves the model to `models/risk_model.joblib` and the numbers to
`models/results.json`.

## scripts/make_charts.py

Makes the two charts in `docs/images/` from the dataset and the saved model:
buggy vs clean commits, and the model vs the 400 line rule.

## The workflows

- **pr-risk.yml** runs on every PR. It installs the project and runs `pr-risk comment --annotate`. It's only allowed to read the code and write PR comments, nothing else.
- **ci.yml** runs on every push and PR. It installs everything, runs the linter (`ruff`), then runs all the tests.

The file warnings work because GitHub Actions watches for lines printed like
`::warning file=src/a.py,line=12::message` and turns them into the yellow
boxes. There's no extra API call for it.

## Tests

Every file in `src/` has its own test file in `tests/` (44 tests in total).
None of the tests touch the internet. The GitHub client tests use a fake
client that gives back made-up answers, the dataset tests use a tiny 2-row CSV
in the same format as the real one, and the model tests train on 200 made-up
commits where the big ones are buggy, so the model should easily learn it. That keeps the tests fast and means they work anywhere,
including in CI.
