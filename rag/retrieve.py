from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

import numpy as np

from rag.store import IndexedChunk, TfidfIndex, tokenize

STOPWORDS = {
    "a",
    "an",
    "and",
    "about",
    "for",
    "from",
    "give",
    "how",
    "in",
    "is",
    "it",
    "me",
    "of",
    "on",
    "please",
    "summarise",
    "summarize",
    "summary",
    "tell",
    "the",
    "this",
    "to",
    "what",
    "whats",
    "with",
}

SUMMARY_RE = re.compile(
    r"\b(summar(?:y|ise|ize)|overview|tl;dr|key points)\b",
    re.I,
)


@dataclass
class Hit:
    chunk: IndexedChunk
    score: float


def query_terms(query: str) -> list[str]:
    terms = [t for t in tokenize(query) if t not in STOPWORDS]
    expanded: list[str] = []
    for term in terms:
        expanded.append(term)
        if term.endswith("ise") and len(term) > 4:
            expanded.append(term[:-3] + "ize")
        if term.endswith("ize") and len(term) > 4:
            expanded.append(term[:-3] + "ise")
    return expanded


def is_summary_query(query: str) -> bool:
    return bool(SUMMARY_RE.search(query))


def _fuzzy_hit(term: str, blob_tokens: set[str]) -> bool:
    if term in blob_tokens:
        return True
    return any(
        SequenceMatcher(None, term, other).ratio() >= 0.82
        for other in blob_tokens
        if abs(len(other) - len(term)) <= 2
    )


def _source_overlap(source: str, heading: str, terms: list[str]) -> int:
    blob = set(tokenize(source.replace("_", " ").replace(":", " ") + " " + heading))
    return sum(1 for term in set(terms) if _fuzzy_hit(term, blob))


def retrieve(index: TfidfIndex, query: str, k: int = 5, min_score: float = 0.05) -> list[Hit]:
    if not index.chunks:
        return []

    terms = query_terms(query)
    search_text = " ".join(terms) if terms else query
    query_vec = index.encode_query(search_text)
    lexical_scores = index.matrix @ query_vec
    scores = lexical_scores.copy()

    try:
        from rag.semantic import semantic_scores

        dense_scores = semantic_scores(index, query)
    except (ImportError, OSError):
        dense_scores = None
    if dense_scores is not None:
        # Semantic similarity handles paraphrases; lexical similarity protects
        # exact PM terms, IDs and metrics.
        scores = 0.72 * np.maximum(dense_scores, 0) + 0.28 * lexical_scores

    for i, chunk in enumerate(index.chunks):
        overlap = _source_overlap(chunk.source, chunk.heading, terms)
        scores[i] = float(scores[i]) + 0.12 * overlap

    if is_summary_query(query):
        source_best: dict[str, float] = {}
        source_file_overlap: dict[str, int] = {}
        for i, chunk in enumerate(index.chunks):
            source_best[chunk.source] = max(source_best.get(chunk.source, 0.0), float(scores[i]))
            source_file_overlap[chunk.source] = _source_overlap(chunk.source, "", terms)
        winner = max(
            source_best,
            key=lambda s: (source_file_overlap.get(s, 0), source_best[s]),
        )
        ordered = sorted(
            (c for c in index.chunks if c.source == winner),
            key=lambda c: c.start,
        )
        take = min(10, max(k, 8), len(ordered))
        return [Hit(chunk=c, score=float(source_best[winner])) for c in ordered[:take]]

    order = np.argsort(-scores)
    hits: list[Hit] = []
    seen_text: set[str] = set()
    for i in order:
        score = float(scores[i])
        if score < min_score:
            break
        chunk = index.chunks[int(i)]
        key = chunk.text[:180]
        if key in seen_text:
            continue
        seen_text.add(key)
        hits.append(Hit(chunk=chunk, score=score))
        if len(hits) >= k:
            break
    return hits
