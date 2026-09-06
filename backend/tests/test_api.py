from fastapi.testclient import TestClient
from app.main import create_app
from app.config import Settings


def test_api_validation_and_disabled_agent(predictor):
    with TestClient(create_app(Settings(), predictor=predictor)) as client:
        assert client.get("/health").status_code == 200
        assert client.post("/api/predict", json={"home_team":"Arsenal", "away_team":"Arsenal"}).status_code == 422
        assert client.post("/api/predict", json={"home_team":"Arsenal", "away_team":"Liverpool"}).status_code == 200
        assert client.post("/api/analyse", json={"message":"Predict Arsenal against Liverpool"}).status_code == 503
        assert client.post("/api/analyse", json={"message":"x"*801}).status_code == 422
        assert client.post("/api/analyse", content="x"*9000).status_code == 413


def test_removed_neutral_flag_rejected(predictor):
    with TestClient(create_app(Settings(), predictor=predictor)) as client:
        assert client.post("/api/predict", json={"home_team":"Arsenal", "away_team":"Liverpool", "neutral_venue":True}).status_code == 422


def test_vertex_serving_contract(predictor):
    with TestClient(create_app(Settings(), predictor=predictor)) as client:
        response = client.post("/api/vertex/predict", json={"instances":[{"home_team":"Arsenal", "away_team":"Liverpool"}]})
        assert response.status_code == 200
        assert response.json()["predictions"][0] == predictor.predict("Arsenal", "Liverpool")
