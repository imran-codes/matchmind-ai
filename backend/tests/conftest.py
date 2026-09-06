from pathlib import Path
import pytest
from app.prediction import PredictionService
from app.train import train


@pytest.fixture(scope="session")
def predictor(tmp_path_factory):
    artifacts = tmp_path_factory.mktemp("artifacts")
    train(Path(__file__).resolve().parents[1] / "data" / "matches.csv", artifacts)
    return PredictionService(artifacts)
