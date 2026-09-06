"""Deterministic inference used by both the API and ADK's tool."""
import hashlib
import json
from pathlib import Path
import joblib
import pandas as pd
import sklearn
from app.features import FEATURES, feature_vector
from app.schemas import Prediction, PredictionRequest


class UnsupportedFixture(ValueError):
    pass


class PredictionService:
    def __init__(self, artifact_dir: Path):
        self.metadata = json.loads((artifact_dir / "metadata.json").read_text())
        if self.metadata["sklearn_version"] != sklearn.__version__:
            raise RuntimeError("Model/library version mismatch: retrain with the installed requirements")
        for name, expected in self.metadata["checksums"].items():
            if hashlib.sha256((artifact_dir / name).read_bytes()).hexdigest() != expected:
                raise RuntimeError(f"Artifact checksum mismatch: {name}")
        # joblib can execute code. Load only our trusted, checksum-verified release.
        self.model = joblib.load(artifact_dir / "model.joblib")
        self.profiles = json.loads((artifact_dir / "profiles.json").read_text())

    @property
    def teams(self) -> list[str]:
        return sorted(self.profiles)

    def predict(self, home_team: str, away_team: str) -> dict:
        try:
            request = PredictionRequest(home_team=home_team, away_team=away_team)
        except ValueError as error:
            raise UnsupportedFixture("Choose two different supported teams") from error
        home_team, away_team = request.home_team, request.away_team
        if home_team not in self.profiles or away_team not in self.profiles:
            raise UnsupportedFixture("Unsupported team; use exact names from /api/teams")
        home, away = self.profiles[home_team], self.profiles[away_team]
        values = feature_vector(home, away)
        scores = self.model.predict_proba(pd.DataFrame([values], columns=FEATURES))[0]
        classes = {label: float(scores[i]) for i, label in enumerate(self.model.classes_)}
        leader = max(classes, key=classes.get)
        labels = {"H": f"{home_team} win", "D": "Draw", "A": f"{away_team} win"}
        result = Prediction(
            home_team=home_team, away_team=away_team, predicted_outcome=labels[leader],
            probabilities={"home_win": classes["H"], "draw": classes["D"], "away_win": classes["A"]},
            explanation=(f"{labels[leader]} has the largest estimated probability, {classes[leader]:.1%}. "
                         "The recent statistics below describe model inputs; they are not causal explanations or feature attributions."),
            statistics=[
                f"Last five matches, points per game: {home_team} {home['points']:.1f}; {away_team} {away['points']:.1f}.",
                f"Goals scored per game: {home_team} {home['gf']:.1f}; {away_team} {away['gf']:.1f}.",
                f"Goals conceded per game: {home_team} {home['ga']:.1f}; {away_team} {away['ga']:.1f}.",
            ],
            model_version=self.metadata["model_version"], data_origin=self.metadata["data_origin"],
            data_as_of=self.metadata["data_as_of"],
        )
        return result.model_dump()
