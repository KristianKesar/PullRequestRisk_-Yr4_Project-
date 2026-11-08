# compare_models.py - Kristian Kesar, C00296348
#
# iteration 2, week 1: trains 3 different models on the same data and compares
# them fairly. also tries logistic regression without total_churn to fix the
# weird weights from iteration 1.
# run from the main project folder (after download_data.py):
#   python scripts/compare_models.py

import json
from pathlib import Path

from sklearn.metrics import average_precision_score, roc_auc_score

from pr_risk.candidates import KINDS, make_model, score_at_rate
from pr_risk.dataset import load_split, to_xy
from pr_risk.model import rule_baseline

train_df, test_df = load_split("data/raw")
X_train, y_train = to_xy(train_df)
X_test, y_test = to_xy(test_df)

# the 400 line rule is the thing to beat, so every model flags the same share it does
rule = rule_baseline(X_test, y_test)
rate = rule["flagged"]
print(f"testing on {len(X_test)} commits, {y_test.mean():.1%} buggy")
print(f"every model flags the riskiest {rate:.1%}, same as the 400 line rule\n")

results = {"rule": {"recall": rule["recall"], "precision": rule["precision"]}}
print(f"{'model':<24}{'PR-AUC':>8}{'ROC-AUC':>9}{'recall':>9}{'precision':>11}")
print(f"{'rule: over 400 lines':<24}{'':>8}{'':>9}{rule['recall']:>9.1%}{rule['precision']:>11.1%}")


def run(name, model, X_tr, X_te):
    model.fit(X_tr, y_train)
    probs = model.predict_proba(X_te)[:, 1]
    fair = score_at_rate(probs, y_test, rate)
    row = {"pr_auc": average_precision_score(y_test, probs), "roc_auc": roc_auc_score(y_test, probs), **fair}
    results[name] = row
    print(f"{name:<24}{row['pr_auc']:>8.3f}{row['roc_auc']:>9.3f}{row['recall']:>9.1%}{row['precision']:>11.1%}")
    return model


for kind in KINDS:
    run(kind, make_model(kind), X_train, X_test)

# the overlap fix: total_churn is just added + deleted, so drop it and see
# if the logistic weights start making sense
no_churn = [c for c in X_train.columns if c != "total_churn"]
lr = run("logistic (no churn)", make_model("logistic"), X_train[no_churn], X_test[no_churn])

print("\nlogistic weights without total_churn, up (+) or down (-)")
weights = dict(zip(no_churn, lr[-1].coef_[0]))
for name, w in sorted(weights.items(), key=lambda kv: -abs(kv[1])):
    print(f"  {name:<22}{w:+.2f}")
results["logistic (no churn) weights"] = weights

Path("models").mkdir(exist_ok=True)
with open("models/comparison.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nsaved models/comparison.json")
