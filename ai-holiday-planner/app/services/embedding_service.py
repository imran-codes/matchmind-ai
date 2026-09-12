# app/services/embedding_service.py

import os
from google import genai
from dotenv import load_dotenv


load_dotenv()


# Reuse one client for all embedding requests.
# This talks to Vertex AI using the configured GCP project and region.
client = genai.Client(
    vertexai=True,
    project=os.environ["GOOGLE_CLOUD_PROJECT"],
    location=os.getenv("GOOGLE_CLOUD_LOCATION", "global")
)


def create_embedding(text: str):
    # Convert text into a numeric vector that represents meaning, not exact words.
    # The vector length must match the PostgreSQL VECTOR(n) column you use.
    response = client.models.embed_content(
        model="text-embedding-005",
        contents=text
    )

    # Return the raw embedding values so they can be stored or compared in pgvector.
    return response.embeddings[0].values