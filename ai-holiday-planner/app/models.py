# app/models.py

# Why this exists
#
# Without validation:
#
# Frontend
#    ↓
# random JSON
#    ↓
# AI
#
# With Pydantic:
#
# Frontend
#    ↓
# validated contract
#    ↓
# application
#
# You can explain:
#
# “The LLM is probabilistic. My API contract should not be.”

from pydantic import BaseModel, Field
from typing import List


class HolidayRequest(BaseModel):
    departure_airport: str
    budget: float = Field(gt=0)
    adults: int = Field(default=2, ge=1)
    children: int = Field(default=0, ge=0)
    nights: int = Field(default=7, ge=1)
    month: str

    preferences: List[str] = []


class HolidayOption(BaseModel):
    destination: str
    hotel: str
    price: float
    stars: int
    board: str
    transfer_minutes: int
    temperature_c: int


class Recommendation(BaseModel):
    destination: str
    hotel: str
    price: float
    score: float
    reason: str