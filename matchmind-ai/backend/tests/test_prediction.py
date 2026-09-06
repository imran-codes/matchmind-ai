import pytest
from pydantic import ValidationError
from app.schemas import Prediction


def test_distribution_and_origin(predictor):
    result = predictor.predict("Arsenal", "Liverpool")
    assert sum(result["probabilities"].values()) == pytest.approx(1)
    assert result["data_origin"] == "synthetic_demo"
    assert "data_as_of" in result


@pytest.mark.parametrize("home,away", [("Arsenal", "Arsenal"), ("Fake FC", "Arsenal")])
def test_invalid_fixture_rejected_inside_tool_boundary(predictor, home, away):
    with pytest.raises(ValueError):
        predictor.predict(home, away)


def test_nan_is_not_a_valid_probability(predictor):
    result = predictor.predict("Arsenal", "Liverpool")
    result["probabilities"]["home_win"] = float("nan")
    with pytest.raises(ValidationError):
        Prediction(**result)
