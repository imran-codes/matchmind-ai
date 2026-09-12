# app/main.py

from fastapi import FastAPI

from app.models import HolidayRequest
from app.services.knowledge_service import retrieve_knowledge
from app.services.holiday_service import search_holidays
from app.services.rag_service import retrieve_context


app = FastAPI(
    title="AI Holiday Planner",
    version="1.0.0"
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/holidays/search")
def holiday_search(request: HolidayRequest):

    holidays = search_holidays(request)

    return {
        "count": len(holidays),
        "results": holidays
    }


@app.get("/knowledge/search")
def knowledge_search(q: str, limit: int = 3):
    return {
        "query": q,
        "results": retrieve_knowledge(q, limit=limit),
    }

from app.services.llm_service import explain_holidays

# You now have:
#
# User
#  ↓
# FastAPI
#  ↓
# Filter inventory
#  ↓
# Gemini
#  ↓
# Recommendation
# YouTube point
#
# Say:
#
# “Gemini isn't searching the holiday inventory. My software does that. Gemini is explaining and reasoning over an already controlled candidate set.”
#
# That is a great production-AI distinction.


def build_retrieval_query(request: HolidayRequest) -> str:
    # Keep the retrieval prompt aligned with the trip type instead of hardcoding
    # "family" for every request.
    if request.children > 0:
        trip_type = "Family holiday"
    elif request.adults == 1:
        trip_type = "Solo holiday"
    elif request.adults == 2:
        trip_type = "Couples holiday"
    else:
        trip_type = "Group holiday"

    # This query is only for RAG retrieval; it is not the user payload itself.
    return f"""
    {trip_type}.
    Travelling with {request.adults} adults and {request.children} children.
    Preferences: {request.preferences}
    Month: {request.month}.
    """

@app.post("/holidays/recommend")
def recommend(request: HolidayRequest):

    holidays = search_holidays(request)

    if not holidays:
        return {
            "recommendation": None,
            "reason": "No holidays matched the hard constraints."
        }

    # Retrieve only the knowledge chunks that match the trip profile.
    context = retrieve_context(build_retrieval_query(request))

    explanation = explain_holidays(
        request=request,
        holidays=holidays,
        context=context,
    )

    return {
        "eligible_holidays": holidays,
        "context": context,
        "recommendation": explanation
    }