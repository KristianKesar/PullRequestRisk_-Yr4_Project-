# test_threshold.py - Kristian Kesar, C00296348
# tests for picking the cut-off, with tiny made up data

import numpy as np
import pytest

from pr_risk.threshold import best_threshold, budget_threshold, validation_split

CSV_HEADER = "commit_id,project,buggy,fix,year,author_date,la,ld,nf,nd,ns,ent,ndev,age,nuc,aexp,arexp,asexp\n"


def row(cid, buggy, year):
    return f"{cid},apache/kafka,{buggy},False,{year},0,10,2,1,1,1,0.0,1.0,1.0,1.0,1,1.0,1.0\n"


def test_best_threshold_separates_clean_and_buggy():
    # buggy ones all score 0.7 or more, clean ones 0.4 or less
    probs = np.array([0.1, 0.2, 0.3, 0.4, 0.7, 0.8, 0.9])
    y = np.array([0, 0, 0, 0, 1, 1, 1])
    t = best_threshold(probs, y)
    assert 0.4 < t <= 0.7


def test_best_threshold_is_a_real_cutoff():
    rng = np.random.default_rng(2)
    probs = rng.random(200)
    y = (probs + rng.normal(0, 0.3, 200) > 0.6).astype(int)
    assert 0 <= best_threshold(probs, y) <= 1


def test_validation_split_uses_the_right_years(tmp_path):
    train = CSV_HEADER + row("a", True, 2013) + row("b", False, 2014) + row("c", True, 2015)
    total = CSV_HEADER + row("d", False, 2014) + row("e", True, 2015) + row("f", False, 2016) + row("g", True, 2017)
    (tmp_path / "apachejit_train.csv").write_text(train)
    (tmp_path / "apachejit_total.csv").write_text(total)

    tr, val = validation_split(tmp_path)
    assert sorted(tr["commit_id"]) == ["a", "b"]        # training stops at 2014
    assert sorted(val["commit_id"]) == ["e", "f"]       # validation is 2015-2016 only, no 2017


@pytest.mark.parametrize("year", [2017, 2018, 2019])
def test_validation_never_touches_test_years(tmp_path, year):
    (tmp_path / "apachejit_train.csv").write_text(CSV_HEADER + row("a", True, 2010))
    (tmp_path / "apachejit_total.csv").write_text(CSV_HEADER + row("z", True, year))
    _, val = validation_split(tmp_path)
    assert len(val) == 0


def test_budget_threshold_flags_the_right_share():
    probs = np.linspace(0, 1, 101)       # 0.00, 0.01 ... 1.00
    t = budget_threshold(probs, 0.20)
    assert (probs >= t).mean() == pytest.approx(0.20, abs=0.02)
