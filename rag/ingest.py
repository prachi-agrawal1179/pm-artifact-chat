from __future__ import annotations

import os
from pathlib import Path

from rag.chunk import chunk_document
from rag.parse import iter_doc_paths, parse_file, parse_url
from rag.store import TfidfIndex

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"
UPLOADS_DIR = ROOT / "data" / "uploads"
FETCHED_DIR = ROOT / "data" / "fetched"
INDEX_PATH = ROOT / "data" / "index.json"


def _add_tree(chunks: list, root: Path, prefix: str | None = None) -> None:
    if not root.exists():
        return
    for path in iter_doc_paths(root):
        text = parse_file(path)
        if prefix:
            source = f"{prefix}{path.name}"
        else:
            source = str(path.relative_to(ROOT))
        chunks.extend(chunk_document(source, text))


def ingest_docs(extra_files: list[Path] | None = None, urls: list[str] | None = None) -> TfidfIndex:
    FETCHED_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    for url in urls or []:
        label, text = parse_url(url)
        safe = "".join(ch if ch.isalnum() or ch in "-._" else "_" for ch in label)[:120]
        dest = FETCHED_DIR / f"{safe}.txt"
        dest.write_text(f"Source: {url}\n\n{text}", encoding="utf-8")

    for path in extra_files or []:
        dest = UPLOADS_DIR / path.name
        if path.resolve() != dest.resolve():
            dest.write_bytes(path.read_bytes())

    chunks = []
    _add_tree(chunks, DOCS_DIR)
    _add_tree(chunks, UPLOADS_DIR, prefix="upload:")
    _add_tree(chunks, FETCHED_DIR, prefix="url:")

    if not chunks:
        raise ValueError("No readable documents found. Add files under docs/ and try again.")

    index = TfidfIndex.build(chunks)
    index.save(INDEX_PATH)
    if os.getenv("EMBEDDING_PROVIDER", "huggingface") == "huggingface":
        try:
            from rag.semantic import build_semantic_index

            build_semantic_index(chunks)
        except (ImportError, OSError) as exc:
            print(f"Semantic index unavailable; using TF-IDF: {exc}")
    return index


def load_or_build() -> TfidfIndex:
    if INDEX_PATH.exists():
        return TfidfIndex.load(INDEX_PATH)
    return ingest_docs()
