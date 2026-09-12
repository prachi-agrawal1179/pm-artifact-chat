from __future__ import annotations

from functools import lru_cache

from rag.retrieve import Hit

SUMMARY_MODEL = "sshleifer/distilbart-cnn-12-6"


@lru_cache(maxsize=1)
def summarizer():
    from transformers import pipeline

    return pipeline(
        "summarization",
        model=SUMMARY_MODEL,
        tokenizer=SUMMARY_MODEL,
        device=-1,
    )


def summarize_hits(hits: list[Hit]) -> str:
    """Summarize retrieved chunks from one source with a local HF model."""
    seen: set[str] = set()
    sections: list[str] = []
    for hit in hits:
        if hit.chunk.id in seen:
            continue
        seen.add(hit.chunk.id)
        sections.append(f"{hit.chunk.heading}. {hit.chunk.text}")

    pipe = summarizer()
    tokenizer = pipe.tokenizer
    joined = "\n\n".join(sections)
    encoded = tokenizer(
        joined,
        max_length=900,
        truncation=True,
        return_tensors="pt",
    )
    input_text = tokenizer.decode(encoded["input_ids"][0], skip_special_tokens=True)
    result = pipe(
        input_text,
        max_length=150,
        min_length=55,
        do_sample=False,
        no_repeat_ngram_size=3,
    )[0]["summary_text"].strip()
    return result
