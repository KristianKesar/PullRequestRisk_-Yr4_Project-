# PR Risk Predictor

Kristian Kesar, C00296348 — SETU Year 4 Software Development Project

A tool that scores GitHub pull requests for defect risk and explains the
reasons behind each score, posted straight onto the PR as a comment.

## Status

**Iteration 1 (due 30 Oct 2026)** — in progress
- [x] GitHub Actions hook that comments on every PR (`.github/workflows/pr-risk.yml`)
- [x] Feature extraction from PR changed files (`src/pr_risk/features.py`)
- [ ] Dataset selected and explored
- [ ] Baseline model trained
- [ ] Plain-English explanations for scores
- [ ] Model wired into the PR comment

## Project layout

```
src/pr_risk/      core package (features, model, explanations, GitHub client)
tests/            unit tests
data/             datasets (not committed, see data/README.md)
models/           trained models (not committed)
docs/             spec, iteration notes, meeting notes
.github/workflows GitHub Actions integration
```

## Running the tests

```bash
pip install pytest
python -m pytest
```
