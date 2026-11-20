"""Reproducible synthetic transaction dataset for the educational ML prototype.

IMPORTANT: The label is simulated. It is not evidence of actual UPI fraud.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


def generate_transactions(num_transactions: int = 4200, output_path: str | Path | None = None, seed: int = 42) -> pd.DataFrame:
    """Generate a labelled synthetic dataset without modifying files by default."""
    if num_transactions < 100:
        raise ValueError("At least 100 synthetic transactions are required.")
    rng = np.random.default_rng(seed)
    fraud_count = max(1, int(round(num_transactions * 0.08)))
    normal_count = num_transactions - fraud_count

    # Most normal transfers occur in daytime; suspicious *synthetic* examples
    # are over-represented at night and in higher amount ranges.
    hour_weights = np.array([0.18 if h < 6 else 2.0 if 7 <= h <= 22 else 0.7 for h in range(24)], dtype=float)
    hour_weights /= hour_weights.sum()
    normal_hours = rng.choice(24, size=normal_count, p=hour_weights)
    fraud_hours = np.where(rng.random(fraud_count) < 0.65,
                           rng.integers(0, 6, fraud_count),
                           rng.integers(6, 24, fraud_count))
    normal_amount = np.clip(rng.lognormal(np.log(1850), .70, normal_count), 20, 30000)
    fraud_amount = np.clip(rng.lognormal(np.log(9000), .85, fraud_count), 50, 100000)

    labels = np.r_[np.zeros(normal_count, dtype=int), np.ones(fraud_count, dtype=int)]
    amounts = np.round(np.r_[normal_amount, fraud_amount], 2)
    hours = np.r_[normal_hours, fraud_hours]
    minutes = rng.integers(0, 60, num_transactions)
    days = rng.integers(0, 366, num_transactions)
    first = datetime(2024, 1, 1)
    stamps = [(first + timedelta(days=int(day), hours=int(hour), minutes=int(minute))).strftime("%Y-%m-%d %H:%M:%S")
              for day, hour, minute in zip(days, hours, minutes)]
    permutation = rng.permutation(num_transactions)
    frame = pd.DataFrame({"Timestamp": np.array(stamps)[permutation],
                          "Amount (INR)": amounts[permutation],
                          "Synthetic Fraud Label": labels[permutation]})
    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(path, index=False)
    return frame


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic labelled UPI examples.")
    parser.add_argument("--count", type=int, default=4200)
    parser.add_argument("--output", default="transactions_synthetic.csv")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    df = generate_transactions(args.count, args.output, args.seed)
    print(f"Wrote {len(df)} synthetic records to {args.output}. Not real fraud data.")
