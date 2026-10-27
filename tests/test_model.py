# test_model.py - Kristian Kesar, C00296348
#
# tests the model code on a small made up dataset where big changes are buggy,
# so the model should easily learn it. no real data needed

import numpy as np
import pandas as pd
import pytest

from pr_risk.dataset import MODEL_FEATURES
from pr_risk.model import evaluate, feature_weights, load, rule_baseline, save, train


@pytest.fixture
def fake_data():
    # 200 fake commits, the bigger they are the more likely they're buggy
    rng = np.random.default_rng(1)
    size = rng.integers(1, 2000, 200)
    X = pd.DataFrame({
        "lines_added": size,
        "lines_deleted": size // 4,
        "total_churn": size + size // 4,
        "files_changed": size // 100 + 1,
        "directories_touched": size // 300 + 1,
        "subsystems_touched": 1,
        "change_entropy": np.log2(size // 100 + 1),
    })[MODEL_FEATURES]
    y = pd.Series((size > 800).astype(int))
    return X, y


def test_model_learns_big_changes_are_risky(fake_data):
    X, y = fake_data
    model = train(X, y)
    results = evaluate(model, X, y)
    assert results["roc_auc"] > 0.9   # should find this easy
    assert 0 <= results["recall"] <= 1


def test_gives_a_chance_between_0_and_1(fake_data):
    X, y = fake_data
    probs = train(X, y).predict_proba(X)[:, 1]
    assert ((probs >= 0) & (probs <= 1)).all()


def test_rule_baseline(fake_data):
    X, y = fake_data
    rule = rule_baseline(X, y, churn=1000)
    assert set(rule) == {"recall", "precision", "flagged"}


def test_weights_cover_every_feature(fake_data):
    X, y = fake_data
    assert set(feature_weights(train(X, y))) == set(MODEL_FEATURES)


def test_save_and_load(fake_data, tmp_path):
    X, y = fake_data
    model = train(X, y)
    save(model, tmp_path / "m.joblib")
    loaded = load(tmp_path / "m.joblib")
    assert (loaded.predict(X) == model.predict(X)).all()
