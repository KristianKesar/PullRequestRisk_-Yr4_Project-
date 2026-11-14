# threshold.py - Kristian Kesar, C00296348
#
# iteration 2, week 2: picking a proper cut-off.
# the model gives each change a chance of being buggy (0 to 1). by default
# anything over 0.5 gets flagged, which flags 46% of everything because the
# model trained on a 50/50 set. so instead, pick the cut-off on data that
# looks like real life

import numpy as np
from sklearn.metrics import precision_recall_curve

from .dataset import load_apachejit


def validation_split(data_dir="data/raw", last_train_year=2014):
    # train: the balanced training file, but only up to 2014
    # validation: ALL the real 2015-2016 commits from the full file (about 30% buggy, like real life)
    # the test set (2017-2019) stays untouched for the final check
    train = load_apachejit(f"{data_dir}/apachejit_train.csv")
    total = load_apachejit(f"{data_dir}/apachejit_total.csv")
    train = train[train["year"] <= last_train_year]
    val = total[(total["year"] > last_train_year) & (total["year"] <= 2016)]
    return train, val


def best_threshold(probs, y):
    # tries every possible cut-off and keeps the one with the best F1.
    # F1 balances recall (catching bugs) and precision (not crying wolf)
    precision, recall, thresholds = precision_recall_curve(y, probs)
    precision, recall = precision[:-1], recall[:-1]   # last point has no threshold
    f1 = 2 * precision * recall / np.maximum(precision + recall, 1e-12)
    best = int(np.argmax(f1))
    return float(thresholds[best])


def budget_threshold(probs, rate=0.20):
    # the more practical option: reviewers only have time to look closely at so
    # many changes, so set the cut-off to flag the riskiest `rate` share of them
    # (0.20 = the riskiest 20%). picked on validation data, then reused as is
    return float(np.quantile(probs, 1 - rate))
