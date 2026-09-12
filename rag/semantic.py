from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np

from rag.chunk import Chunk
from rag.store import TfidfIndex

ROOT = Path(__file__).resolve().parent.parent
SEMANTIC_INDEX_PATH = ROOT / "data" / "semantic_index.npz"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def embedding_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL)


def build_semantic_index(chunks: list[Chunk]) -> None:
    texts = [
        f"Document: {chunk.source}\nSection: {chunk.heading}\n{chunk.text}"
        for chunk in chunks
    ]
    embeddings = embedding_model().encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    SEMANTIC_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        SEMANTIC_INDEX_PATH,
        ids=np.asarray([chunk.id for chunk in chunks]),
        embeddings=np.asarray(embeddings, dtype=np.float32),
    )


def semantic_scores(index: TfidfIndex, query: str) -> np.ndarray | None:
    if not SEMANTIC_INDEX_PATH.exists():
        return None
    payload = np.load(SEMANTIC_INDEX_PATH)
    ids = payload["ids"].tolist()
    expected = [chunk.id for chunk in index.chunks]
    if ids != expected:
        return None
    query_embedding = embedding_model().encode(
        [query],
        normalize_embeddings=True,
        convert_to_numpy=True,
    )[0]
    return payload["embeddings"] @ query_embedding


def semantic_ready() -> bool:
    return SEMANTIC_INDEX_PATH.exists()
