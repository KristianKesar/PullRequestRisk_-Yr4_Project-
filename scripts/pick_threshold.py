# pick_threshold.py - Kristian Kesar, C00296348
#
# iteration 2, week 2: picks a sensible cut-off for when to warn someone.
#   1. train on 2003-2014
#   2. pick the cut-off on the real 2015-2016 commits
#   3. check it on 2017-2019, which neither step has seen
# run from the main project folder:
#   python scripts/pick_threshold.py

import json
from pathlib import Path

from pr_risk.dataset import load_split, to_xy
from pr_risk.model import evaluate, rule_baseline, train
from pr_risk.threshold import best_threshold, budget_threshold, validation_split

train_df, val_df = validation_split("data/raw")
_, test_df = load_split("data/raw")
X_train, y_train = to_xy(train_df)
X_val, y_val = to_xy(val_df)
X_test, y_test = to_xy(test_df)
print(f"train 2003-2014: {len(X_train)} commits ({y_train.mean():.0%} buggy)")
print(f"pick cut-off on 2015-2016: {len(X_val)} commits ({y_val.mean():.0%} buggy)")
print(f"test 2017-2019: {len(X_test)} commits ({y_test.mean():.0%} buggy)\n")

model = train(X_train, y_train)
val_probs = model.predict_proba(X_val)[:, 1]
cutoff = best_threshold(val_probs, y_val)        # option 1: best F1
budget = budget_threshold(val_probs, 0.20)       # option 2: flag the riskiest 20%

default = evaluate(model, X_test, y_test, threshold=0.5)
picked = evaluate(model, X_test, y_test, threshold=cutoff)
budgeted = evaluate(model, X_test, y_test, threshold=budget)
rule = rule_baseline(X_test, y_test)

print(f"{'on 2017-2019':<28}{'recall':>9}{'precision':>11}{'flagged':>10}")
print(f"{'default cut-off (0.50)':<28}{default['recall']:>9.1%}{default['precision']:>11.1%}{default['flagged']:>10.1%}")
print(f"{f'best F1 cut-off ({cutoff:.2f})':<28}{picked['recall']:>9.1%}{picked['precision']:>11.1%}{picked['flagged']:>10.1%}")
print(f"{f'20% budget cut-off ({budget:.2f})':<28}{budgeted['recall']:>9.1%}{budgeted['precision']:>11.1%}{budgeted['flagged']:>10.1%}")
print(f"{'rule: over 400 lines':<28}{rule['recall']:>9.1%}{rule['precision']:>11.1%}{rule['flagged']:>10.1%}")
print(f"\nPR-AUC on 2017-2019: {picked['pr_auc']:.3f} (random {y_test.mean():.3f})")

Path("models").mkdir(exist_ok=True)
with open("models/threshold.json", "w") as f:
    json.dump({"f1_cutoff": cutoff, "budget_cutoff": budget, "default": default,
               "best_f1": picked, "budget_20": budgeted, "rule": rule}, f, indent=2)
print("saved models/threshold.json")
