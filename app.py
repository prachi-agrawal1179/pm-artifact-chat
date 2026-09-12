from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from dotenv import dotenv_values, load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from rag.generate import generate_answer
from rag.ingest import FETCHED_DIR, INDEX_PATH, UPLOADS_DIR, ingest_docs, load_or_build
from rag.parse import SUPPORTED_SUFFIXES
from rag.retrieve import is_summary_query, retrieve
from rag.store import TfidfIndex

load_dotenv()

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"

app = FastAPI(title="Local RAG")
app.mount("/assets", StaticFiles(directory=STATIC), name="assets")

_index: TfidfIndex | None = None


def get_index() -> TfidfIndex:
    global _index
    if _index is None:
        _index = load_or_build()
    return _index


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    k: int = Field(default=5, ge=1, le=12)
    mode: str = Field(default="extractive", pattern="^(extractive|huggingface|openai)$")


class IngestUrlRequest(BaseModel):
    url: str = Field(min_length=8, max_length=2000)


class SettingsRequest(BaseModel):
    openai_api_key: str = Field(default="", max_length=400)


class DeleteSourceRequest(BaseModel):
    source: str = Field(min_length=1, max_length=500)


def _api_key() -> str:
    env_file = ROOT / ".env"
    file_vals = dotenv_values(env_file) if env_file.exists() else {}
    return (file_vals.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()


def _source_path(source: str) -> Path | None:
    if source.startswith("upload:"):
        path = UPLOADS_DIR / source.split(":", 1)[1]
    elif source.startswith("url:"):
        path = FETCHED_DIR / source.split(":", 1)[1]
    else:
        path = ROOT / source
    return path if path.exists() else None


def _category(source: str) -> str:
    low = source.lower()
    if "research" in low or "interview" in low or "competitive" in low:
        return "Research"
    if "spec" in low:
        return "Specs"
    if "checkout-recovery" in low:
        return "Growth"
    if "prd" in low or "homepage" in low:
        return "Product"
    if source.startswith("upload:"):
        return "Product"
    if source.startswith("url:"):
        return "Web"
    if "decision" in low:
        return "Decisions"
    return "Docs"


@app.get("/")
def home() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
def health() -> dict:
    try:
        chunks = len(get_index().chunks)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "index": INDEX_PATH.exists()}
    return {
        "ok": True,
        "chunks": chunks,
        "llm": bool(_api_key()),
        "embedding": os.getenv("EMBEDDING_PROVIDER", "huggingface"),
        "huggingface": (ROOT / "data" / "semantic_index.npz").exists(),
    }


@app.get("/api/sources")
def sources() -> dict:
    index = get_index()
    by_source: dict[str, int] = {}
    for chunk in index.chunks:
        by_source[chunk.source] = by_source.get(chunk.source, 0) + 1
    rows = []
    for source, count in by_source.items():
        path = _source_path(source)
        name = Path(source.split(":", 1)[-1]).name
        suffix = Path(name).suffix.lower().lstrip(".") or "md"
        mtime = path.stat().st_mtime if path else 0
        rows.append(
            {
                "source": source,
                "name": name,
                "path": source,
                "chunks": count,
                "category": _category(source),
                "kind": suffix,
                "added": mtime,
                "date": datetime.fromtimestamp(mtime).strftime("%b %d, %Y").replace(" 0", " ") if mtime else "",
                "deletable": source.startswith("upload:") or source.startswith("url:"),
            }
        )
    rows.sort(key=lambda r: r["added"], reverse=True)
    return {"chunk_count": len(index.chunks), "sources": rows}


@app.post("/api/chat")
def chat(req: ChatRequest) -> dict:
    index = get_index()
    k = 10 if is_summary_query(req.question) else req.k
    hits = retrieve(index, req.question, k=k)
    try:
        answer = generate_answer(req.question, hits, mode=req.mode)
    except Exception as exc:  # noqa: BLE001
        if req.mode != "huggingface":
            raise
        raise HTTPException(
            status_code=503,
            detail=f"Local Hugging Face model is not ready: {exc}",
        ) from exc
    return {
        "answer": answer,
        "citations": [
            {
                "n": i,
                "source": hit.chunk.source,
                "heading": hit.chunk.heading,
                "score": round(hit.score, 4),
                "excerpt": hit.chunk.text[:500],
            }
            for i, hit in enumerate(hits, start=1)
        ],
    }


@app.post("/api/ingest")
def ingest() -> dict:
    global _index
    try:
        _index = ingest_docs()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "chunks": len(_index.chunks)}


@app.post("/api/ingest/url")
def ingest_url(req: IngestUrlRequest) -> dict:
    global _index
    try:
        _index = ingest_docs(urls=[req.url.strip()])
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "chunks": len(_index.chunks)}


@app.post("/api/ingest/upload")
async def ingest_upload(file: UploadFile = File(...)) -> dict:
    global _index
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPLOADS_DIR / Path(file.filename or "upload.txt").name
    if dest.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported type {dest.suffix or '(none)'}. Use txt, pdf, docx, or Excel.",
        )
    dest.write_bytes(await file.read())
    try:
        _index = ingest_docs()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "chunks": len(_index.chunks), "file": dest.name}


@app.post("/api/settings")
def save_settings(req: SettingsRequest) -> dict:
    env_path = ROOT / ".env"
    key = req.openai_api_key.strip()
    existing = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
    lines = existing.splitlines() if existing else []
    wrote = False
    out = []
    for line in lines:
        if line.startswith("OPENAI_API_KEY="):
            out.append(f"OPENAI_API_KEY={key}")
            wrote = True
        else:
            out.append(line)
    if not wrote:
        out.append(f"OPENAI_API_KEY={key}")
    env_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return {"ok": True, "llm": bool(key)}


@app.post("/api/sources/delete")
def delete_source(req: DeleteSourceRequest) -> dict:
    global _index
    path = _source_path(req.source)
    if not path or not (req.source.startswith("upload:") or req.source.startswith("url:")):
        raise HTTPException(status_code=400, detail="Only uploaded or fetched files can be removed.")
    path.unlink(missing_ok=True)
    _index = ingest_docs()
    return {"ok": True, "chunks": len(_index.chunks)}
