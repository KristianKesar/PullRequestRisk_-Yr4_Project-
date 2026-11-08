# test_candidates.py - Kristian Kesar, C00296348
# tests the iteration 2 models on made up data where big changes are buggy

import numpy as np
import pandas as pd
import pytest

from pr_risk.candidates import KINDS, make_model, score_at_rate
from pr_risk.dataset import MODEL_FEATURES


@pytest.fixture
def fake_data():
    rng = np.random.default_rng(1)
    size = rng.integers(1, 2000, 300)
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


@pytest.mark.parametrize("kind", KINDS)
def test_every_model_learns_big_changes_are_risky(fake_data, kind):
    X, y = fake_data
    probs = make_model(kind).fit(X, y).predict_proba(X)[:, 1]
    assert ((probs >= 0) & (probs <= 1)).all()
    # bigger changes should get a higher chance of being buggy on average
    assert probs[y == 1].mean() > probs[y == 0].mean()


def test_unknown_model_kind():
    with pytest.raises(ValueError):
        make_model("magic")


def test_score_at_rate_flags_the_right_share():
    probs = np.array([0.9, 0.8, 0.1, 0.2, 0.3, 0.05, 0.6, 0.4, 0.7, 0.15])
    y = pd.Series([1, 1, 0, 0, 0, 0, 1, 0, 0, 0])
    # top 30% = the 3 highest (0.9, 0.8, 0.7): 2 of them buggy
    scores = score_at_rate(probs, y, 0.3)
    assert scores["precision"] == pytest.approx(2 / 3)
    assert scores["recall"] == pytest.approx(2 / 3)
