from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.features import FEATURES, build_training_frame


def metrics(y_true: pd.Series, probabilities: np.ndarray, classes: np.ndarray) -> dict[str, float]:
    """Calculate the evaluation numbers used to compare candidate models."""
    predicted = classes[np.argmax(probabilities, axis=1)]
    one_hot = np.column_stack([(y_true.to_numpy() == label).astype(float) for label in classes])
    return {
        "accuracy": round(float(accuracy_score(y_true, predicted)), 4),
        "log_loss": round(float(log_loss(y_true, probabilities, labels=classes)), 4),
        "multiclass_brier": round(float(np.mean(np.sum((probabilities - one_hot) ** 2, axis=1))), 4),
    }


def train(data_path: Path, artifact_dir: Path) -> dict[str, object]:
    """Train candidate models, pick the best one, and save release artifacts."""
    raw = pd.read_csv(data_path)
    training, profiles = build_training_frame(raw)
    if len(training) < 200:
        raise ValueError("At least 200 usable chronological matches are required")

    # Split the data chronologically so later matches stay out of training.
    dates = sorted(training["Date"].unique())
    first_date, second_date = dates[int(len(dates) * .70)], dates[int(len(dates) * .85)]
    train_set, validation_set, test_set = (
        training[training.Date < first_date],
        training[(training.Date >= first_date) & (training.Date < second_date)],
        training[training.Date >= second_date],
    )
    if set(train_set.label) != {"A", "D", "H"}:
        raise ValueError("Training set must include all three outcomes")
    # Compare a simple baseline with two real classifiers.
    candidates: dict[str, object] = {
        "prior_baseline": DummyClassifier(strategy="prior"),
        "logistic_regression": Pipeline(
            [("scale", StandardScaler()), ("model", LogisticRegression(max_iter=2000, C=0.6))]
        ),
        "gradient_boosting": HistGradientBoostingClassifier(
            learning_rate=0.05, max_iter=180, max_leaf_nodes=15, l2_regularization=0.5,
            random_state=42,
        ),
    }

    scoreboard: dict[str, dict[str, float]] = {}
    fitted: dict[str, object] = {}
    for name, model in candidates.items():
        # Train each candidate and score it on validation data.
        model.fit(train_set[FEATURES], train_set["label"])
        scoreboard[name] = metrics(
            validation_set["label"], model.predict_proba(validation_set[FEATURES]), model.classes_
        )
        fitted[name] = model

    # Choose the model with the lowest validation log loss.
    winner = min(scoreboard, key=lambda name: scoreboard[name]["log_loss"])
    selected = fitted[winner]
    test_metrics = metrics(test_set["label"], selected.predict_proba(test_set[FEATURES]), selected.classes_)
    data_hash = hashlib.sha256(data_path.read_bytes()).hexdigest()
    artifact_dir.mkdir(parents=True, exist_ok=True)
    # Save the trained model and the final team profiles for inference.
    joblib.dump(selected, artifact_dir / "model.joblib")
    (artifact_dir / "profiles.json").write_text(json.dumps(profiles, indent=2))
    checksums = {name: hashlib.sha256((artifact_dir / name).read_bytes()).hexdigest()
                 for name in ("model.joblib", "profiles.json")}
    # Bake the data hash and file checksums into a release identifier.
    release_hash = hashlib.sha256(json.dumps([data_hash, checksums, FEATURES, "2.0"]).encode()).hexdigest()[:16]
    metadata: dict[str, object] = {
        "model_name": "matchmind-outcome-classifier",
        "model_version": f"2.0-{release_hash}",
        "sklearn_version": sklearn.__version__,
        "checksums": checksums,
        "selected_model": winner,
        "candidate_validation_metrics": scoreboard,
        "test_metrics": test_metrics,
        "features": FEATURES,
        "classes": list(selected.classes_),
        "training_rows": len(train_set),
        "validation_rows": len(validation_set),
        "test_rows": len(test_set),
        "trained_at": datetime.now(UTC).isoformat(),
        "data_hash": data_hash,
        "data_as_of": str(training.Date.max().date()),
        "split_dates": {"validation_start": str(pd.Timestamp(first_date).date()), "test_start": str(pd.Timestamp(second_date).date())},
        "data_origin": str(raw.get("data_origin", pd.Series(["football_data_csv"])).iloc[0]),
        "limitations": [
            "Demo model excludes injuries, line-ups, transfers and live match context.",
            "Probabilities are educational estimates and must not be presented as betting advice.",
        ],
    }
    # Write the release metadata alongside the model artifacts.
    (artifact_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
    return metadata


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    result = train(root / "data" / "matches.csv", root / "artifacts")
    print(json.dumps(result, indent=2))
