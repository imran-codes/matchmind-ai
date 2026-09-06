from pydantic import BaseModel, Field
from app.schemas import PredictionRequest


class VertexRequest(BaseModel):
    instances: list[PredictionRequest] = Field(min_length=1, max_length=10)
