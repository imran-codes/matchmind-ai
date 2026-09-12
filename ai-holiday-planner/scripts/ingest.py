# scripts/ingest.py

from pathlib import Path
import sys

import psycopg

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.services.embedding_service import create_embedding


# Source markdown files that will become searchable knowledge rows.
KNOWLEDGE_DIR = Path("knowledge")


# Connect to the local Postgres + pgvector database.
conn = psycopg.connect(
    "postgresql://holiday:holiday@localhost:5432/holidays"
)


# Read each destination file and store its chunks as separate rows.
for file in KNOWLEDGE_DIR.glob("*.md"):
    destination = file.stem
    text = file.read_text()

    # Split on blank lines so each markdown section becomes a chunk.
    chunks = [
        chunk.strip()
        for chunk in text.split("\n\n")
        if chunk.strip()
    ]

    for chunk in chunks:
        # Turn the chunk into an embedding before saving it.
        embedding = create_embedding(chunk)

        # Persist both the raw text and its vector for later similarity search.
        conn.execute(
            """
            INSERT INTO destination_knowledge
            (destination, content, embedding)
            VALUES (%s, %s, %s)
            """,
            (
                destination,
                chunk,
                embedding
            )
        )


conn.commit()
conn.close()
