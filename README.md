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

## Task 2 — Account Health Briefs (for TAMs)

Given an `account_id`, produce a TAM-facing health brief: an overall **risk
level**, the **churn/health signals** behind it, a digest of any linked
tickets, an **executive summary**, and **prioritized recommended actions**.

**Design:** churn signals and the overall risk level are computed by
**deterministic rules** in `src/briefs/signals.py` (health status, usage trend,
seat utilization, NPS, P1 volume, open-ticket load, renewal proximity, QBR
staleness, login recency, and the curated `escalation_notes`). The LLM only
writes the narrative (summary + actions), grounded strictly in those
pre-computed signals — so the numbers and the risk level are reproducible and
auditable, and the brief degrades to a deterministic fallback if the LLM is
unavailable. The computed risk can deliberately disagree with the CRM
`health_status` label (e.g. an account marked "Healthy" but underadopted with a
stale QBR surfaces as Medium/High) — surfacing that gap is the point.

The ticket↔account join is intentionally sparse in the dataset (most
`ticket.account_id` values don't match `accounts.json`), so briefs are driven
by the account record and treat linked tickets as best-effort enrichment.

**Sample run (CLI):**

```bash
python scripts/demo_brief.py              # churning + at-risk + healthy examples
python scripts/demo_brief.py ACC-3336     # a specific account
```

**REST endpoint:**

```bash
# GET /accounts/{account_id}/brief   -> structured AccountBrief  (404 if unknown)
```

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
  briefs/
    signals.py         # deterministic churn/health signals + risk level
    prompts.py         # versioned brief prompt + changelog
    generator.py       # LLM narrative (grounded) + deterministic fallback
    pipeline.py        # orchestration: generate_brief(account_id)
  api.py               # FastAPI app (entry point)
scripts/
  demo_triage.py       # sample run vs ground-truth labels
  demo_brief.py        # sample account health briefs
tests/                 # Task 3
```
