from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re
from typing import Iterable


KNOWLEDGE_DIR = Path(__file__).resolve().parents[2] / "knowledge"
WORD_RE = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class KnowledgeChunk:
    source: str
    heading: str
    text: str


def load_knowledge_chunks() -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []

    for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        chunks.extend(chunk_markdown_file(path))

    return chunks


def chunk_markdown_file(path: Path) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    current_heading = path.stem.replace("_", " ").title()
    paragraphs: list[str] = []

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()

        if not stripped:
            flush_paragraphs(path, current_heading, paragraphs, chunks)
            continue

        if stripped.startswith("#"):
            flush_paragraphs(path, current_heading, paragraphs, chunks)
            current_heading = stripped.lstrip("#").strip() or current_heading
            continue

        paragraphs.append(stripped)

    flush_paragraphs(path, current_heading, paragraphs, chunks)
    return chunks


def flush_paragraphs(
    path: Path,
    heading: str,
    paragraphs: list[str],
    chunks: list[KnowledgeChunk],
) -> None:
    if not paragraphs:
        return

    chunks.append(
        KnowledgeChunk(
            source=path.name,
            heading=heading,
            text=" ".join(paragraphs),
        )
    )
    paragraphs.clear()


def retrieve_knowledge(query: str, limit: int = 3) -> list[dict[str, str]]:
    query_terms = set(tokenize(query))
    scored_chunks = []

    for chunk in load_knowledge_chunks():
        score = score_chunk(chunk, query_terms)
        if score > 0:
            scored_chunks.append((score, chunk))

    scored_chunks.sort(key=lambda item: item[0], reverse=True)

    return [asdict(chunk) for _, chunk in scored_chunks[:limit]]


def score_chunk(chunk: KnowledgeChunk, query_terms: set[str]) -> int:
    if not query_terms:
        return 0

    text_terms = set(tokenize(f"{chunk.heading} {chunk.text}"))
    return len(query_terms & text_terms)


def tokenize(text: str) -> Iterable[str]:
    return WORD_RE.findall(text.lower())

