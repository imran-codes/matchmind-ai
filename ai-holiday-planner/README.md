# AI Holiday Planner

An end-to-end demo of a holiday recommendation system using:

- FastAPI
- deterministic filtering
- markdown knowledge files
- PostgreSQL + pgvector
- embeddings
- RAG retrieval
- Gemini reasoning

## What this demo shows

1. User submits a holiday request.
2. The API filters a structured inventory.
3. Relevant markdown knowledge is retrieved from PostgreSQL using pgvector.
4. Gemini explains the best matches using the inventory plus retrieved context.

## Project structure

- `app/main.py` — FastAPI routes
- `app/services/holiday_service.py` — deterministic filtering
- `app/services/embedding_service.py` — creates embeddings
- `app/services/rag_service.py` — retrieves context from pgvector
- `app/services/llm_service.py` — Gemini prompt and recommendation
- `knowledge/` — markdown knowledge files
- `scripts/ingest.py` — loads markdown into PostgreSQL

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file:

```env
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=global
GEMINI_MODEL=gemini-3.6-flash
```

Start PostgreSQL:

```bash
docker compose up -d
```

Create the extension and table:

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE destination_knowledge (
    id BIGSERIAL PRIMARY KEY,
    destination TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(768)
);
```

Ingest the markdown knowledge:

```bash
python scripts/ingest.py
```

Run the API:

```bash
uvicorn app.main:app --reload
```

## Demo endpoints

- `GET /knowledge/search?q=...`
- `POST /holidays/search`
- `POST /holidays/recommend`

## Example request

```json
{
  "departure_airport": "Manchester",
  "budget": 3500,
  "adults": 2,
  "children": 2,
  "nights": 7,
  "month": "June",
  "preferences": ["family", "beach", "warm", "short transfer"]
}
```

