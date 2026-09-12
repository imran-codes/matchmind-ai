# app/services/rag_service.py

import psycopg

from app.services.embedding_service import create_embedding


DATABASE_URL = "postgresql://holiday:holiday@localhost:5432/holidays"


def retrieve_context(query: str, limit: int = 5):
    embedding = create_embedding(query)

    with psycopg.connect(DATABASE_URL) as conn:
        rows = conn.execute(
            """
            SELECT
                destination,
                content,
                embedding <=> %s::vector AS distance
            FROM destination_knowledge
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (
                embedding,
                embedding,
                limit,
            ),
        ).fetchall()

    return [
        {
            "destination": row[0],
            "content": row[1],
            "distance": row[2],
        }
        for row in rows
    ]
