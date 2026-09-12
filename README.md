# PM artifact RAG chatbot

Point this at specs, research notes, or a competitor’s **public** docs and ask questions. It chunks locally, retrieves the closest passages, and answers only from those passages — with citations. Nothing is trained.

## Why this shape

| Piece | What it demonstrates |
| --- | --- |
| Heading-aware chunking + overlap | You are not dumping whole PRDs into a prompt |
| MiniLM semantic + TF-IDF hybrid retrieval | Paraphrases and exact PM terms both rank well |
| Local DistilBART summaries | Fluent summaries without an API key |
| Optional OpenAI generation | Synthesis still has to cite retrieved excerpts |
| Source panel + scores | You can inspect *why* an answer appeared |

## Run it

Python 3.11+ recommended (3.9+ should work).

```bash
cd ~/pm-rag-chatbot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional: add OPENAI_API_KEY
uvicorn app:app --reload --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

The default **Hugging Face (local, grounded)** mode uses MiniLM for
semantic retrieval and DistilBART for summaries. The first run downloads model
weights; afterward it works locally. OpenAI remains optional.

## Sample corpus

`docs/` is a fictional checkout-recovery pack so you can demo immediately:

- PRD with metrics, non-goals, and a three-email sequence
- Interview synthesis (`n = 11`)
- Competitive teardown from public mystery-shopping
- Hold/resume spec
- Decision log (no coupon, 24h hold)

Try:

- *What is the primary success metric for recovery emails?*
- *Why did we reject a 10% win-back coupon?*
- *What did competitor Lumen Pets do that we should copy?*
- *How long is the inventory hold and who decided that?*

Then drop in your own files under `docs/` (or upload / paste a public URL in the sidebar) and hit **Re-index**. Supported: `.md`, `.txt`, `.pdf`, `.docx`, Excel (`.xlsx` / `.xlsm` / `.xls`), `.csv`, `.html`.

## How a question is answered

1. **Parse** markdown, text, HTML, PDF, Word (`.docx`), or Excel. Sheets become heading + row text so retrieval can hit a specific tab.
2. **Chunk** on headings, then pack ~1200 characters with 200-character overlap.
3. **Index** with TF-IDF vectors on disk (`data/index.json`).
4. **Retrieve** top-k by cosine similarity (default 5, score floor 0.08).
5. **Generate** from those excerpts only. If retrieval is empty, the model must refuse rather than guess.

Swap in OpenAI embeddings later by changing `EMBEDDING_PROVIDER` — the retrieve → cite contract stays the same.
