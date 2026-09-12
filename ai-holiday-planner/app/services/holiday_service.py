# app/services/holiday_service.py

# This is deliberately boring.
#
# And that's good.
#
# Explain this point
#
# If the user says:
#
# Maximum budget = £3,500
#
# you should not ask an LLM:
#
# “Which hotels cost less than £3,500?”
#
# Python can answer that perfectly.
#
# Your architecture becomes:
#
# User
#  ↓
# FastAPI
#  ↓
# Deterministic filtering
#  ↓
# Eligible holidays
#  ↓
# AI reasoning/explanation

import json
from pathlib import Path

from app.models import HolidayRequest


DATA_PATH = Path(__file__).parent.parent / "data" / "holidays.json"


def load_holidays():
    with open(DATA_PATH, "r") as file:
        return json.load(file)


def search_holidays(request: HolidayRequest):
    holidays = load_holidays()

    results = []

    for holiday in holidays:

        if holiday["departure_airport"].lower() != request.departure_airport.lower():
            continue

        if holiday["month"].lower() != request.month.lower():
            continue

        if holiday["price"] > request.budget:
            continue

        results.append(holiday)

    return results