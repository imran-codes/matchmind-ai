"""Request shape used by the Vertex AI prediction endpoint."""
from pydantic import BaseModel, Field
from app.schemas import PredictionRequest


class VertexRequest(BaseModel):
    """Wrap a list of prediction requests in the format Vertex expects."""
    instances: list[PredictionRequest] = Field(min_length=1, max_length=10)
