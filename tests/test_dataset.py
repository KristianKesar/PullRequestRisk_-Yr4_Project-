# test_dataset.py - Kristian Kesar, C00296348
#
# tests the apachejit loader with a tiny fake csv (same columns as the real one)
# so the tests dont need the whole 30MB download

import pytest

from pr_risk.dataset import MODEL_FEATURES, load_apachejit, to_xy
from pr_risk.features import PRFeatures

# 2 rows copied in the real apachejit format
FAKE_CSV = """commit_id,project,buggy,fix,year,author_date,la,ld,nf,nd,ns,ent,ndev,age,nuc,aexp,arexp,asexp
abc,apache/kafka,True,False,2015,1420070400,100,20,5,3,2,1.9,1.0,2.0,3.0,10,10.0,1.0
def,apache/kafka,False,False,2016,1451606400,4,1,1,1,1,0.0,1.0,2.0,3.0,10,10.0,1.0
"""


@pytest.fixture
def fake_csv(tmp_path):
    # pytest gives us a temp folder, write the fake csv into it
    path = tmp_path / "fake.csv"
    path.write_text(FAKE_CSV)
    return path


def test_columns_get_our_names(fake_csv):
    row = load_apachejit(fake_csv).iloc[0]
    assert row["lines_added"] == 100
    assert row["lines_deleted"] == 20
    assert row["files_changed"] == 5
    assert row["directories_touched"] == 3
    assert row["subsystems_touched"] == 2
    assert row["change_entropy"] == pytest.approx(1.9)


def test_churn_gets_worked_out(fake_csv):
    assert load_apachejit(fake_csv).iloc[0]["total_churn"] == 120


def test_buggy_becomes_1_or_0(fake_csv):
    assert load_apachejit(fake_csv)["buggy"].tolist() == [1, 0]


def test_every_model_feature_exists_on_real_prs():
    # if the model trains on something features.py cant make,
    # we couldnt score real PRs, so this catches that
    assert set(MODEL_FEATURES) <= set(PRFeatures().to_dict())


def test_to_xy(fake_csv):
    X, y = to_xy(load_apachejit(fake_csv))
    assert list(X.columns) == MODEL_FEATURES
    assert len(y) == 2
