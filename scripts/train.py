# train.py - Kristian Kesar, C00296348
#
# trains the first model on apachejit, tests it, and saves it.
# run it from the main project folder (after download_data.py):
#   python scripts/train.py

import json
from pathlib import Path

import numpy as np

from pr_risk.dataset import load_split, to_xy
from pr_risk.model import evaluate, feature_weights, rule_baseline, save, train

# train on 2003-2016, test on 2017-2019
train_df, test_df = load_split("data/raw")
X_train, y_train = to_xy(train_df)
X_test, y_test = to_xy(test_df)
print(f"training on {len(X_train)} commits, testing on {len(X_test)}")
print(f"{y_test.mean():.1%} of the test commits are buggy\n")

model = train(X_train, y_train)

results = evaluate(model, X_test, y_test)
rule = rule_baseline(X_test, y_test)

print("logistic regression")
print(f"  PR-AUC     {results['pr_auc']:.3f}   (random guessing = {y_test.mean():.3f})")
print(f"  ROC-AUC    {results['roc_auc']:.3f}   (random guessing = 0.500)")
print(f"  recall     {results['recall']:.1%}   of buggy changes caught")
print(f"  precision  {results['precision']:.1%}   of flagged changes actually buggy")
print(f"  flagged    {results['flagged']:.1%}   of all changes\n")

print("simple rule (flag anything over 400 lines)")
print(f"  recall     {rule['recall']:.1%}")
print(f"  precision  {rule['precision']:.1%}")
print(f"  flagged    {rule['flagged']:.1%}\n")

# fair fight: let the model flag the same amount of changes as the rule does,
# otherwise it's not a fair comparison (flagging more = catching more)
probs = model.predict_proba(X_test)[:, 1]
same_threshold = np.quantile(probs, 1 - rule["flagged"])
fair = evaluate(model, X_test, y_test, threshold=same_threshold)
print(f"model flagging the same {rule['flagged']:.1%} of changes as the rule")
print(f"  recall     {fair['recall']:.1%}")
print(f"  precision  {fair['precision']:.1%}\n")

print("what pushes the risk up (+) or down (-)")
weights = feature_weights(model)
for name, w in weights.items():
    print(f"  {name:<22}{w:+.2f}")

# save the model + the results so they can go in the iteration notes
Path("models").mkdir(exist_ok=True)
save(model, "models/risk_model.joblib")
with open("models/results.json", "w") as f:
    json.dump({"model": results, "rule": rule, "model_same_flag_rate": fair,
               "weights": weights}, f, indent=2)
print("\nsaved models/risk_model.joblib and models/results.json")
