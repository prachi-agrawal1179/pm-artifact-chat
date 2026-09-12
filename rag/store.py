from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from rag.chunk import Chunk

TOKEN_RE = re.compile(r"[a-z0-9]{2,}")


@dataclass
class IndexedChunk:
    id: str
    source: str
    text: str
    heading: str
    start: int
    end: int


class TfidfIndex:
    def __init__(self, chunks: list[IndexedChunk], vocab: dict[str, int], idf: list[float], matrix: np.ndarray):
        self.chunks = chunks
        self.vocab = vocab
        self.idf = np.array(idf, dtype=np.float32)
        self.matrix = matrix

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "chunks": [asdict(c) for c in self.chunks],
            "vocab": self.vocab,
            "idf": self.idf.tolist(),
            "matrix": self.matrix.tolist(),
        }
        path.write_text(json.dumps(payload), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "TfidfIndex":
        payload = json.loads(path.read_text(encoding="utf-8"))
        chunks = [IndexedChunk(**row) for row in payload["chunks"]]
        matrix = np.array(payload["matrix"], dtype=np.float32)
        return cls(chunks, payload["vocab"], payload["idf"], matrix)

    @classmethod
    def build(cls, chunks: list[Chunk]) -> "TfidfIndex":
        indexed = [
            IndexedChunk(
                id=c.id,
                source=c.source,
                text=c.text,
                heading=c.heading,
                start=c.start,
                end=c.end,
            )
            for c in chunks
        ]
        docs = [tokenize(c.text) for c in indexed]
        df: Counter[str] = Counter()
        for tokens in docs:
            df.update(set(tokens))
        vocab = {term: i for i, term in enumerate(sorted(df))}
        n_docs = max(len(docs), 1)
        idf = [math.log((1 + n_docs) / (1 + df[term])) + 1.0 for term in sorted(df)]
        matrix = np.zeros((len(docs), len(vocab)), dtype=np.float32)
        for row, tokens in enumerate(docs):
            counts = Counter(tokens)
            length = max(sum(counts.values()), 1)
            for term, count in counts.items():
                col = vocab[term]
                matrix[row, col] = (count / length) * idf[col]
        matrix = _l2_normalize(matrix)
        return cls(indexed, vocab, idf, matrix)

    def encode_query(self, query: str) -> np.ndarray:
        tokens = tokenize(query)
        counts = Counter(tokens)
        vec = np.zeros((len(self.vocab),), dtype=np.float32)
        length = max(sum(counts.values()), 1)
        for term, count in counts.items():
            col = self.vocab.get(term)
            if col is None:
                continue
            vec[col] = (count / length) * self.idf[col]
        return _l2_normalize(vec.reshape(1, -1))[0]


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def _l2_normalize(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms
