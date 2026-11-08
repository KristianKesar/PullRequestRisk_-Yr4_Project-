# candidates.py - Kristian Kesar, C00296348
#
# iteration 2, week 1: a few different models to try against each other.
# all of them take the same features and give back a chance (0 to 1) that
# a change is buggy, so they can be swapped in and out easily

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

KINDS = ["logistic", "forest", "boosting"]


def make_model(kind):
    if kind == "logistic":
        # same as model.py: squash big numbers, same scale, then logistic regression
        return make_pipeline(FunctionTransformer(np.log1p), StandardScaler(),
                             LogisticRegression(max_iter=1000))
    if kind == "forest":
        # loads of decision trees voting together. min_samples_leaf stops
        # each tree memorising tiny groups of commits
        return RandomForestClassifier(n_estimators=200, min_samples_leaf=20,
                                      n_jobs=-1, random_state=1)
    if kind == "boosting":
        # trees built one after another, each fixing the last one's mistakes
        return HistGradientBoostingClassifier(random_state=1)
    raise ValueError(f"unknown model kind: {kind}")


def score_at_rate(probs, y, rate):
    # flag the riskiest `rate` share of changes (eg 0.187 = same as the 400 line rule)
    # and see how many buggy ones that catches. keeps comparisons fair
    threshold = np.quantile(probs, 1 - rate)
    flagged = probs >= threshold
    return {"recall": recall_score(y, flagged), "precision": precision_score(y, flagged)}
