"""Deterministic educational anomaly ensemble and feature preparation.

No model in this module is validated for real financial decision-making.
"""
from __future__ import annotations

import math
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM
from xgboost import XGBClassifier

from generate_transactions import generate_transactions

ROOT = Path(__file__).resolve().parent
# The bundled model was generated from this repository's own synthetic data.
# On Vercel, always load the read-only artifact. Never train or save on an HTTP request.
# Local development keeps a separate writable cache (and may use older Python wheels).
IS_VERCEL = bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))
BUNDLED_MODEL_PATH = ROOT / "model_artifacts" / "ensemble.joblib"
DEFAULT_PATH = BUNDLED_MODEL_PATH if IS_VERCEL else ROOT / ".model_cache" / "ensemble.joblib"
MODEL_PATH = Path(os.getenv("MODEL_PATH", str(DEFAULT_PATH)))
_LOCK = threading.Lock()
_BUNDLE: dict | None = None


def parse_transaction(amount: object, timestamp: object) -> tuple[float, datetime]:
    """Validate an amount and parse a local datetime. No currency conversion."""
    if isinstance(amount, bool) or amount is None:
        raise ValueError("Amount must be a positive number in INR.")
    if isinstance(amount, str):
        amount = amount.strip().replace("₹", "").replace(",", "")
        if not amount:
            raise ValueError("Amount must be a positive number in INR.")
    try:
        parsed_amount = float(amount)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Amount must be a positive number in INR.") from exc
    if not math.isfinite(parsed_amount) or not (0.01 <= parsed_amount <= 10_000_000):
        raise ValueError("Amount must be between ₹0.01 and ₹1,00,00,000.")
    if not isinstance(timestamp, str) or len(timestamp) > 40:
        raise ValueError("Timestamp must be a valid ISO date/time string.")
    try:
        parsed_time = datetime.fromisoformat(timestamp.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Timestamp must be a valid ISO date/time string.") from exc
    if not (2020 <= parsed_time.year <= 2100):
        raise ValueError("Transaction year must be between 2020 and 2100.")
    return parsed_amount, parsed_time


def features(amounts: np.ndarray, hours: np.ndarray) -> np.ndarray:
    """Log amount; encode time of day cyclically so 23:00 is near 00:00."""
    amounts = np.asarray(amounts, dtype=float)
    hours = np.asarray(hours, dtype=float)
    return np.column_stack((np.log1p(amounts),
                            np.sin(2 * np.pi * hours / 24),
                            np.cos(2 * np.pi * hours / 24)))


def train_models(n_samples: int = 4200, seed: int = 42) -> dict:
    """Fit three models and evaluate their vote only on held-out *synthetic* labels."""
    data = generate_transactions(num_transactions=n_samples, seed=seed)
    timestamps = np.array([datetime.fromisoformat(s).hour for s in data["Timestamp"]])
    x = features(data["Amount (INR)"].to_numpy(), timestamps)
    y = data["Synthetic Fraud Label"].to_numpy(dtype=int)
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=.2, stratify=y, random_state=seed)
    scaler = StandardScaler()
    scaler.fit(x_train[y_train == 0])
    train_scaled, test_scaled = scaler.transform(x_train), scaler.transform(x_test)
    normal_scaled = train_scaled[y_train == 0]

    iso = IsolationForest(n_estimators=120, contamination=.04, random_state=seed, n_jobs=1)
    iso.fit(normal_scaled)
    svm = OneClassSVM(kernel="rbf", nu=.04, gamma="scale")
    svm.fit(normal_scaled)
    xgb = XGBClassifier(n_estimators=120, max_depth=3, learning_rate=.06,
                        subsample=.9, colsample_bytree=1.0, min_child_weight=3,
                        eval_metric="logloss", random_state=seed, n_jobs=1,
                        scale_pos_weight=3)
    xgb.fit(train_scaled, y_train)

    iso_votes = (iso.predict(test_scaled) == -1).astype(int)
    svm_votes = (svm.predict(test_scaled) == -1).astype(int)
    xgb_votes = xgb.predict(test_scaled).astype(int)
    majority = ((iso_votes + svm_votes + xgb_votes) >= 2).astype(int)
    return {
        "scaler": scaler, "isolation_forest": iso, "svm": svm, "xgboost": xgb,
        "normal_p95_amount": float(np.quantile(data.loc[data["Synthetic Fraud Label"] == 0, "Amount (INR)"], .95)),
        "metadata": {
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "n_synthetic_samples": n_samples,
            "training_data": "synthetic_only",
            "test_size": len(y_test),
            "synthetic_holdout_precision": round(float(precision_score(y_test, majority, zero_division=0)), 3),
            "synthetic_holdout_recall": round(float(recall_score(y_test, majority, zero_division=0)), 3),
            "synthetic_holdout_f1": round(float(f1_score(y_test, majority, zero_division=0)), 3),
        },
    }


def model_ready() -> bool:
    return _BUNDLE is not None or MODEL_PATH.is_file()


def get_model() -> dict:
    """Load a deterministic model from the immutable Vercel deployment or local cache.

    The production HTTP request path never trains a model or writes to disk.
    """
    global _BUNDLE
    if _BUNDLE is not None:
        return _BUNDLE
    with _LOCK:
        if _BUNDLE is None:
            if MODEL_PATH.is_file():
                _BUNDLE = joblib.load(MODEL_PATH)
            elif IS_VERCEL:
                raise FileNotFoundError(
                    "Bundled model_artifacts/ensemble.joblib is missing. "
                    "Check vercel.json includeFiles and project root."
                )
            else:
                bundle = train_models()
                MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
                tmp = MODEL_PATH.with_name(MODEL_PATH.name + ".tmp")
                try:
                    joblib.dump(bundle, tmp)
                    os.replace(tmp, MODEL_PATH)
                finally:
                    tmp.unlink(missing_ok=True)
                _BUNDLE = bundle
    return _BUNDLE


def predict_transaction(amount: object, timestamp: object, bundle: dict | None = None) -> dict:
    value, when = parse_transaction(amount, timestamp)
    model = bundle if bundle is not None else get_model()
    x = model["scaler"].transform(features(np.array([value]), np.array([when.hour + when.minute / 60])))
    results = {
        "isolation_forest": "Potential Fraud" if model["isolation_forest"].predict(x)[0] == -1 else "Normal",
        "svm": "Potential Fraud" if model["svm"].predict(x)[0] == -1 else "Normal",
        "xgboost": "Potential Fraud" if model["xgboost"].predict(x)[0] == 1 else "Normal",
    }
    votes = sum(prediction == "Potential Fraud" for prediction in results.values())
    details = []
    if value > model["normal_p95_amount"]:
        details.append("Amount exceeds the 95th percentile of the synthetic routine-payment training profile.")
    else:
        details.append("Amount is within the synthetic routine profile's 95th-percentile range; this is not a safety guarantee.")
    if 0 <= when.hour < 6:
        details.append("Transaction time falls in the overnight (00:00–05:59) window.")
    else:
        details.append("Transaction time is outside the overnight (00:00–05:59) window.")
    details.append("Context indicators describe inputs; they are not causal model explanations.")
    return {
        **results,
        "fraud_detected": votes >= 2,
        "fraud_votes": votes,
        "risk_level": "elevated" if votes >= 2 else "low",
        "signals": details,
        "training_data": "synthetic_only",
        "disclaimer": "Research prototype only. Not validated for real UPI fraud decisions.",
    }
