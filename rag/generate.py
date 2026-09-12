from __future__ import annotations

import os
import re
from pathlib import Path

from dotenv import dotenv_values

from rag.retrieve import Hit, is_summary_query

SYSTEM_PROMPT = """You are a PM research assistant answering strictly from the provided source excerpts.

Rules:
- Use only the excerpts. If they are insufficient, say you don't have that in the indexed docs.
- Cite sources inline as [n] matching the excerpt numbers.
- Prefer specific numbers, owners, dates, and decisions from the text.
- Do not invent competitors, metrics, or quotes.
- Keep answers concise and decision-useful.

If the user asked for a summary: write 4–5 short sentences on what the document is, the problem, the proposed change, and how success is measured. Do not list every section or paste the PRD.
"""


def generate_answer(question: str, hits: list[Hit], mode: str = "extractive") -> str:
    if not hits:
        return (
            "I don't have enough grounded material for that. "
            "Try re-indexing docs/, adding a file, or asking about a topic covered in the sources."
        )

    env_file = Path(__file__).resolve().parent.parent / ".env"
    file_vals = dotenv_values(env_file) if env_file.exists() else {}
    api_key = (file_vals.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
    if mode == "huggingface":
        if is_summary_query(question):
            from rag.hf_generate import summarize_hits

            return summarize_hits(hits)
        return _extractive_answer(hits)
    if mode != "openai" or not api_key:
        if is_summary_query(question):
            return _brief_doc_summary(hits)
        return _extractive_answer(hits)

    context = _format_context(hits)
    extra = ""
    if is_summary_query(question):
        extra = (
            "\n\nWrite a short executive summary (4–5 sentences). "
            "Explain what the document is and what it is trying to change. Do not dump section headings."
        )
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    model = file_vals.get("OPENAI_MODEL") or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    response = client.chat.completions.create(
        model=model,
        temperature=0.1,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Question: {question}\n\nExcerpts:\n{context}{extra}",
            },
        ],
    )
    return (response.choices[0].message.content or "").strip()


def _format_context(hits: list[Hit]) -> str:
    blocks = []
    for i, hit in enumerate(hits, start=1):
        heading = f" — {hit.chunk.heading}" if hit.chunk.heading else ""
        blocks.append(
            f"[{i}] {hit.chunk.source}{heading} (score {hit.score:.2f})\n{hit.chunk.text}"
        )
    return "\n\n".join(blocks)


def _body(hit: Hit) -> str:
    heading = (hit.chunk.heading or "").strip()
    text = hit.chunk.text.strip()
    if heading and text.lower().startswith(heading.lower()):
        text = text[len(heading) :].strip()
    return " ".join(text.split())


def _first_sentences(text: str, n: int = 2, max_chars: int = 220) -> str:
    if not text:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", text)
    clipped = " ".join(parts[:n]).strip()
    if len(clipped) > max_chars:
        clipped = clipped[:max_chars].rsplit(" ", 1)[0] + "…"
    return clipped


def _find_section(hits: list[Hit], *needles: str) -> str:
    for hit in hits:
        heading = (hit.chunk.heading or "").lower()
        if any(needle in heading for needle in needles):
            return _first_sentences(_body(hit))
    return ""


def _doc_kind(source: str) -> str:
    name = Path(source.split(":", 1)[-1]).name.lower()
    if "prd" in name:
        return "product requirements document (PRD)"
    if "spec" in name:
        return "spec"
    if "research" in name or "interview" in name:
        return "research note"
    if "metric" in name or "experiment" in name:
        return "metrics / experiment plan"
    if "decision" in name:
        return "decision log"
    return "document"


def _brief_doc_summary(hits: list[Hit]) -> str:
    source = hits[0].chunk.source
    name = Path(source.split(":", 1)[-1]).name
    kind = _doc_kind(source)

    overview = _find_section(hits, "overview", "purpose", "summary")
    problem = _find_section(hits, "problem")
    goals = _find_section(hits, "goal", "success", "north star", "objective")
    non_goals = _find_section(hits, "non-goal", "out of scope")

    lines = [f"{name} is a {kind}."]
    if overview:
        lead = overview[0].lower() + overview[1:] if overview[0].isupper() else overview
        lines.append(f"In short, it proposes to {lead}")
    if problem:
        lines.append(f"It exists because {problem[0].lower() + problem[1:] if problem else problem}")
    if goals:
        lines.append(f"Success looks like: {goals}")
    if non_goals:
        lines.append(f"Out of scope: {non_goals}")
    if len(lines) == 1:
        lines.append(_first_sentences(_body(hits[0]), n=3, max_chars=320))
    return "\n\n".join(lines)


def _extractive_answer(hits: list[Hit]) -> str:
    top = hits[0]
    body = _first_sentences(_body(top), n=3, max_chars=420)
    heading = top.chunk.heading
    lead = f"From {top.chunk.source}"
    if heading and heading not in {"Document", "Introduction"}:
        lead += f" ({heading})"
    return f"{lead}:\n\n{body}"
