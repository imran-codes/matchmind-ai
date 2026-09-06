import math
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    home_team: str = Field(min_length=2, max_length=60)
    away_team: str = Field(min_length=2, max_length=60)

    @model_validator(mode="after")
    def different_teams(self):
        if self.home_team.casefold() == self.away_team.casefold():
            raise ValueError("Choose two different teams")
        return self


class Prediction(BaseModel):
    home_team: str
    away_team: str
    predicted_outcome: str
    probabilities: dict[str, float]
    explanation: str
    statistics: list[str]
    model_version: str
    data_origin: str
    data_as_of: str

    @model_validator(mode="after")
    def valid_distribution(self):
        if set(self.probabilities) != {"home_win", "draw", "away_win"}:
            raise ValueError("Unexpected probability classes")
        values = list(self.probabilities.values())
        if any(not math.isfinite(p) or not 0 <= p <= 1 for p in values):
            raise ValueError("Invalid probability")
        if abs(sum(values) - 1.0) > 0.00001:
            raise ValueError("Probabilities must sum to one")
        return self


class AnalyseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    message: str = Field(min_length=5, max_length=800)


class Analysis(BaseModel):
    request_id: str
    status: Literal["complete", "no_prediction", "partial"]
    message: str
    agent_commentary: str
    predictions: list[Prediction]
    tool_calls: list[str]
    input_tokens: int = 0
    output_tokens: int = 0
