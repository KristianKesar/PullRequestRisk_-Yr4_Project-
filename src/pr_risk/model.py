# model.py - Kristian Kesar, C00296348
#
# the first basic model: logistic regression.
# it takes the features and gives back a chance (0 to 1) that the change is buggy
#
# 3 steps, all wrapped up in one "pipeline" so they always happen in the same order:
#   1. log1p   - squashes the big numbers down. a 5000 line change isnt 100x riskier
#                than a 50 line one, so this stops the huge ones taking over
#   2. scaler  - puts every feature on the same scale so none of them win just
#                because their numbers are bigger
#   3. logistic regression - the actual model

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

from .dataset import MODEL_FEATURES


def train(X, y):
    model = make_pipeline(
        FunctionTransformer(np.log1p),
        StandardScaler(),
        LogisticRegression(max_iter=1000),
    )
    model.fit(X, y)
    return model


def evaluate(model, X, y, threshold=0.5):
    # probs = how likely the model thinks each change is buggy
    probs = model.predict_proba(X)[:, 1]
    flagged = probs >= threshold
    return {
        # pr_auc = main score. random guessing would just get the % of buggy ones
        "pr_auc": average_precision_score(y, probs),
        "roc_auc": roc_auc_score(y, probs),
        # recall = out of all the buggy changes, how many did it catch
        "recall": recall_score(y, flagged),
        # precision = out of everything it flagged, how many were actually buggy
        "precision": precision_score(y, flagged),
        "flagged": flagged.mean(),   # % of changes it flagged
    }


def rule_baseline(X, y, churn=400):
    # the simple rule from the PR comment: flag anything over 400 lines.
    # if the model cant beat this there's no point having a model
    flagged = X["total_churn"] >= churn
    return {
        "recall": recall_score(y, flagged),
        "precision": precision_score(y, flagged),
        "flagged": flagged.mean(),
    }


def feature_weights(model):
    # how much each feature pushes the risk up (+) or down (-).
    # because everything got scaled first, the numbers can be compared to each other
    weights = model[-1].coef_[0]
    return dict(sorted(zip(MODEL_FEATURES, weights), key=lambda w: -abs(w[1])))


def save(model, path):
    joblib.dump(model, path)


def load(path):
    return joblib.load(path)
