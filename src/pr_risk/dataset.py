# dataset.py - Kristian Kesar, C00296348
#
# loads the apachejit data and renames the columns so they match the names
# in features.py. that way the model trains on the exact same features it'll
# see on real PRs later
#
# apachejit = ~106k commits from apache projects, each one marked as
# "buggy" (it caused a bug later) or not
#   https://github.com/hosseinkshvrz/apachejit
#
# heads up: it's commits not PRs, but a PR is basically one big combined
# change so it's the same shape anyway

import pandas as pd

# apachejit column name -> our name from features.py
# only the ones we can work out from a PR's file list
APACHEJIT_COLUMNS = {
    "la": "lines_added",
    "ld": "lines_deleted",
    "nf": "files_changed",
    "nd": "directories_touched",
    "ns": "subsystems_touched",
    "ent": "change_entropy",
}

# what the model actually trains on, always in this order
MODEL_FEATURES = [
    "lines_added",
    "lines_deleted",
    "total_churn",
    "files_changed",
    "directories_touched",
    "subsystems_touched",
    "change_entropy",
]

LABEL = "buggy"


def load_apachejit(csv_path):
    df = pd.read_csv(csv_path)
    df = df.rename(columns=APACHEJIT_COLUMNS)

    # apachejit doesnt have churn so just work it out
    df["total_churn"] = df["lines_added"] + df["lines_deleted"]

    # True/False -> 1/0, models like numbers
    df[LABEL] = df[LABEL].astype(int)

    return df[["commit_id", "project", "year"] + MODEL_FEATURES + [LABEL]]


def load_split(data_dir="data/raw"):
    # apachejit already splits by year for us:
    #   train = 2003-2016 (half buggy half clean)
    #   test  = 2017-2019 (only ~19% buggy, like real life)
    # training on old stuff and testing on newer stuff is how it'd actually get used
    train = load_apachejit(f"{data_dir}/apachejit_train.csv")
    test = load_apachejit(f"{data_dir}/apachejit_test_large.csv")
    return train, test


def to_xy(df):
    # X = the features going in, y = the answer (buggy or not)
    return df[MODEL_FEATURES], df[LABEL]
