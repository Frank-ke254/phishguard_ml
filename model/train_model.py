from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split


ROOT_DIR = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT_DIR / "phishing_dataset.csv"
ARTIFACTS_DIR = ROOT_DIR / "model" / "artifacts"
MODEL_PATH = ARTIFACTS_DIR / "phishing_model.pkl"
FEATURES_PATH = ARTIFACTS_DIR / "feature_columns.pkl"

TARGET_COLUMN = "CLASS_LABEL"
DROP_COLUMNS = {"id"}
RANDOM_STATE = 42


def train() -> None:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    df = pd.read_csv(DATASET_PATH)
    feature_columns = [c for c in df.columns if c not in DROP_COLUMNS and c != TARGET_COLUMN]

    X = df[feature_columns]
    y = df[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=300,
        random_state=RANDOM_STATE,
        class_weight="balanced",
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print("Classification Report:")
    print(classification_report(y_test, y_pred))

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(feature_columns, FEATURES_PATH)
    print(f"Saved model to: {MODEL_PATH}")
    print(f"Saved features to: {FEATURES_PATH}")


if __name__ == "__main__":
    train()
