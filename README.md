# Support AI Assessment — Triage, Account Briefs, Evals

Production-style LLM tooling for Technical Support and TAM teams.
Built on the provided mock dataset (500 tickets, 50 accounts, product knowledge base).

## Setup

```bash
python -m venv .venv
# Windows (PowerShell):  .venv\Scripts\Activate.ps1
# Linux / macOS:         source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your Groq API key (free: console.groq.com/keys)
```

First run downloads the `all-MiniLM-L6-v2` embedding model (~90 MB) automatically
to your local cache — zero manual steps.

> The `data/` and `knowledge-base/` folders must contain the provided starter
> dataset before running (`tickets.json`, `accounts.json`, and the product /
> troubleshooting / billing / onboarding markdown docs).

## Task 1 — Intelligent Ticket Triage

**Pipeline:** classify (LLM, structured JSON validated by Pydantic) → retrieve
(FAISS semantic search over MiniLM embeddings of the knowledge base, chunked
on `---` with heading metadata) → known-issue match + draft first response
(LLM, grounded in retrieved excerpts) → team routing (deterministic rules).

**Sample run (CLI):**

```bash
python scripts/demo_triage.py 3
```

**REST endpoint:**

```bash
uvicorn src.api:app --reload
# POST /triage  {"subject": "...", "body": "..."}   -> structured TriageResult
# GET  /health
# interactive docs at http://127.0.0.1:8000/docs
```

Prompts are versioned in `src/triage/prompts.py` with a changelog.

## Project layout

```
src/
  config.py            # paths, env, model + determinism settings
  schemas.py           # Pydantic contract (TicketInput, Classification, TriageResult)
  llm_client.py        # Groq wrapper: JSON mode, seed, retry/backoff
  data_loader.py       # tickets / accounts loaders
  kb/
    chunker.py         # split KB docs on '---', heading metadata
    retriever.py       # local MiniLM embeddings + FAISS index + search
  triage/
    prompts.py         # versioned prompts + changelog
    classifier.py      # LLM call 1 (structured classification)
    responder.py       # LLM call 2 (KB match + draft reply)
    router.py          # deterministic team routing
    pipeline.py        # orchestration: triage_ticket()
  api.py               # FastAPI app (entry point)
scripts/
  demo_triage.py       # sample run vs ground-truth labels
tests/                 # Task 3
```
