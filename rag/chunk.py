from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Chunk:
    id: str
    source: str
    text: str
    heading: str
    start: int
    end: int


def chunk_document(
    source: str,
    text: str,
    *,
    max_chars: int = 1200,
    overlap: int = 200,
) -> list[Chunk]:
    """Split on headings, then pack sections into overlapping windows."""
    cleaned = _normalize(text)
    if not cleaned:
        return []

    sections = _split_sections(cleaned)
    chunks: list[Chunk] = []
    index = 0
    cursor = 0

    for heading, body in sections:
        windows = _window(body, max_chars=max_chars, overlap=overlap)
        for window in windows:
            start = cleaned.find(window, cursor)
            if start < 0:
                start = cursor
            end = start + len(window)
            chunks.append(
                Chunk(
                    id=f"{source}::{index}",
                    source=source,
                    text=window,
                    heading=heading,
                    start=start,
                    end=end,
                )
            )
            index += 1
            cursor = start
    return chunks


def _normalize(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _split_sections(text: str) -> list[tuple[str, str]]:
    parts = re.split(r"(?m)^(#{1,6} .+)$", text)
    if len(parts) == 1:
        return [("Document", text)]

    sections: list[tuple[str, str]] = []
    preamble = parts[0].strip()
    if preamble:
        sections.append(("Introduction", preamble))
    for i in range(1, len(parts), 2):
        heading = parts[i].lstrip("# ").strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        if body:
            sections.append((heading, f"{heading}\n\n{body}"))
    return sections or [("Document", text)]


def _window(text: str, *, max_chars: int, overlap: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]

    pieces: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        if end < len(text):
            break_at = text.rfind("\n\n", start + max_chars // 2, end)
            if break_at == -1:
                break_at = text.rfind(". ", start + max_chars // 2, end)
            if break_at != -1:
                end = break_at + 1
        pieces.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return [p for p in pieces if p]
