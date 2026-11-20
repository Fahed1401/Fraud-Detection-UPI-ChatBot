"""Pre-train and persist a local, reproducible model artifact."""
from model import MODEL_PATH, get_model

if __name__ == "__main__":
    model = get_model()
    print(f"Model artifact ready: {MODEL_PATH}")
    print("Synthetic-only holdout metrics (NOT real-world fraud performance):")
    for key, value in model["metadata"].items():
        print(f"  {key}: {value}")
