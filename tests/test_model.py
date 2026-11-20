from datetime import datetime

import numpy as np
import pytest

from generate_transactions import generate_transactions
from model import features, parse_transaction, predict_transaction, train_models


@pytest.fixture(scope="module")
def bundle():
    return train_models(n_samples=1500, seed=42)


def test_synthetic_dataset_is_reproducible_and_not_written_by_default(tmp_path):
    a = generate_transactions(200, seed=42)
    b = generate_transactions(200, seed=42)
    assert a.equals(b)
    assert set(a["Synthetic Fraud Label"].unique()) == {0, 1}
    assert not list(tmp_path.iterdir())


def test_currency_and_iso_timestamps_are_supported():
    amount, when = parse_transaction("₹1,250.50", "2026-11-18T14:25")
    assert amount == 1250.5
    assert when == datetime(2026, 11, 18, 14, 25)
    amount, when = parse_transaction(100, "2026-11-18 14:25:00")
    assert amount == 100 and when.hour == 14


@pytest.mark.parametrize("amount", [None, "", "hello", -2, 0, False, float("nan"), float("inf"), 1e9])
def test_invalid_amounts_raise(amount):
    with pytest.raises(ValueError):
        parse_transaction(amount, "2026-11-18T14:25")


@pytest.mark.parametrize("timestamp", [None, 123, "yesterday", "2026-02-31T09:00", "2018-01-01T12:00", "2026-11-18T26:30"])
def test_invalid_dates_raise(timestamp):
    with pytest.raises(ValueError):
        parse_transaction(100, timestamp)


def test_features_are_cyclic_at_midnight():
    x = features(np.array([100.0, 100.0]), np.array([0.0, 24.0]))
    np.testing.assert_allclose(x[0], x[1], atol=1e-12)


def test_models_agree_on_vote_math(bundle):
    for amount, timestamp in [(1250, "2026-11-18T14:25"), (35000, "2026-11-18T02:10")]:
        result = predict_transaction(amount, timestamp, bundle)
        votes = sum(result[name] == "Potential Fraud" for name in ("isolation_forest", "svm", "xgboost"))
        assert votes == result["fraud_votes"]
        assert result["fraud_detected"] == (votes >= 2)
        assert result["training_data"] == "synthetic_only"
        assert len(result["signals"]) >= 2


def test_holdout_metrics_are_explicitly_synthetic(bundle):
    assert bundle["metadata"]["training_data"] == "synthetic_only"
    assert bundle["metadata"]["test_size"] > 0
    assert 0 <= bundle["metadata"]["synthetic_holdout_f1"] <= 1
