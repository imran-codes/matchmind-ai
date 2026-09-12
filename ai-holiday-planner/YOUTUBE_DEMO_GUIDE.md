# YouTube Demo Guide

## Goal

Show a complete lower-environment AI holiday planner with:

- structured filtering
- markdown knowledge
- embeddings
- PostgreSQL + pgvector
- RAG retrieval
- Gemini explanation with prompt safety

## Stage 1 — Project setup

Show:

- project folder
- `app/`
- `knowledge/`
- `scripts/`

Explain:

- this is a demo app
- the API and knowledge base are separated

## Stage 2 — Environment setup

Run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Explain:

- virtual environments isolate dependencies
- `uvicorn` runs FastAPI
- `psycopg` connects to PostgreSQL
- `google-genai` talks to Vertex AI

## Stage 3 — Google Cloud configuration

Show `.env`:

```env
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=global
GEMINI_MODEL=gemini-3.6-flash
```

Explain:

- the app reads the project and region from environment variables
- the embedding and LLM services both use Vertex AI

## Stage 4 — Docker Postgres

Show `docker-compose.yml`.

Run:

```bash
docker compose up -d
```

Then connect and create the extension/table:

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE destination_knowledge (
    id BIGSERIAL PRIMARY KEY,
    destination TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(768)
);
```

Explain:

- PostgreSQL stores both structured rows and vectors
- pgvector enables similarity search

## Stage 5 — Knowledge files

Show the files in `knowledge/`:

- `majorca.md`
- `tenerife.md`
- `antalya.md`
- `algarve.md`
- `solo.md`
- `couples.md`
- `family.md`
- `group.md`

Explain:

- markdown is the knowledge source
- headings help chunking and retrieval

## Stage 6 — Ingest

Run:

```bash
python scripts/ingest.py
```

Explain:

- each markdown chunk becomes an embedding
- each embedding is stored in PostgreSQL

## Stage 7 — Retrieval

Show `app/services/rag_service.py`.

Explain:

- request text is embedded
- PostgreSQL finds nearby vectors
- the top results become retrieved context

Demo:

```bash
curl "http://127.0.0.1:8000/knowledge/search?q=family beach resort in Majorca&limit=3"
```

## Stage 8 — Filtering

Show `app/services/holiday_service.py`.

Explain:

- this is deterministic logic
- it filters inventory by airport, month, and budget
- no LLM needed for this step

Demo:

```bash
POST /holidays/search
```

## Stage 9 — Recommendation

Show `app/services/llm_service.py`.

Explain:

- Gemini sees only approved inventory
- retrieved context is reference material only
- prompt injection is handled with explicit instructions

Demo:

```bash
POST /holidays/recommend
```

## Stage 10 — Full flow

Use this payload:

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

Explain the chain:

1. request arrives in FastAPI
2. inventory is filtered
3. retrieval query is built
4. pgvector returns context
5. Gemini ranks the options

## Stage 11 — Wrap-up

Summarise:

- FastAPI for the API
- PostgreSQL for inventory and vectors
- markdown knowledge for explainability
- Gemini for reasoning
- safety through separation of concerns

