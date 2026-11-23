# Support AI Assessment — Triage, Account Briefs, Evals

Production-style LLM tooling for Technical Support and TAM teams.
Built on the provided mock dataset (500 tickets, 50 accounts, product knowledge base).

## SupportFlow web console

This repository now includes a Next.js **support operations workspace** alongside its CLI and API pipelines. The new Overview tab reads the bundled 500 synthetic tickets and 50 synthetic accounts through FastAPI. It offers searchable, paginated queues, ticket details, account risk ranking, historical ticket charts, and links into the existing AI triage and account-brief tools.

**Run the workspace locally**

```bash
# Terminal 1 (repository root, after installing Python requirements)
uvicorn src.api:app --reload

# Terminal 2
cd frontend
npm ci
npm run dev
```

Open **http://localhost:3000**. The overview needs no LLM key and does not download embeddings on startup; AI triage still requires a backend Groq API key and may initialize the embedding model on first use.

Read the [frontend guide](frontend/README.md) for configuration, endpoint documentation, limitations, and checks. This is a **read-only exploratory interface**, not a production helpdesk. The original ticket data is unchanged, and the demo has no authentication, writes, or real customer integrations.

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

## Task 3 — Evaluation & Tests

Two layers of quality measurement, plus a deterministic unit suite.

**1. Classification eval** (`src/eval/harness.py`) — scores the triage
classifier against the dataset's ground-truth labels on a deterministic random
sample: accuracy + macro-F1 + per-class precision/recall for category, urgency
accuracy with a **within-1** tolerance and a confusion matrix, and product
accuracy. Predictions are **cached to disk** keyed by `(model, prompt_version,
ticket_id)`, so growing the sample or re-running never re-calls tickets already
scored (free-tier friendly). Category disagreements vs ground truth are listed —
many are genuinely ambiguous labels, which the report calls out rather than
hides.

**2. LLM-judge** (`src/eval/judge.py`) — the draft first-response has no ground
truth, so a separate LLM scores each draft on **groundedness, relevance,
actionability, and tone** (1–5) plus a hallucination flag, aggregated into a
`hallucination_rate`. This measures the generation surface that accuracy metrics
can't. The judge receives the ticket **and the matched KB excerpt text**, so it
verifies each claim against the actual source rather than guessing (`judge_v2`).

**3. Adversarial suite** (`src/eval/adversarial.py`) — hand-written edge cases
probing *robustness*, not dataset accuracy: data-loss-beats-generic-bug, angry
tone vs trivial impact (must not inflate to P1), how-to vs feature-request
ambiguity, a **prompt-injection** attempt (must not leak/obey), a clear P1
outage (no guaranteed-deadline promises), and near-empty input (must not crash,
must stay schema-valid). Each case asserts a *property* of the output rather than
a single gold label.

**Run it:**

```bash
python scripts/run_eval.py --n 40                 # classification eval, 40 tickets
python scripts/run_eval.py --n 40 --judge 8       # + LLM-judge 8 draft responses
python scripts/run_eval.py --adversarial          # only the edge-case suite
python scripts/run_eval.py --n 40 --refresh       # ignore the prediction cache
```

Predictions and a timestamped JSON report land in `eval_output/` (git-ignored).

### Results — hallucination hardening

The LLM-judge drove a concrete improvement to the responder. The initial prompt
(`respond_v1`) drafted fluent, well-toned replies but **invented** root causes,
error codes, and ETAs — usually by borrowing details from a retrieved excerpt
that was topically near but did not address the ticket (FAISS always returns its
top-k, even when nothing truly matches). Rewriting the responder prompt
(`respond_v2`: a two-source grounding contract, a relevance gate, a structural
no-match branch, an itemised never-invent list, a silent pre-send checklist, and
few-shot examples) moved the numbers on the same 10 judged tickets:

| Metric (n=10)      | respond_v1 | respond_v2 |
|--------------------|:----------:|:----------:|
| Groundedness       |   3.4 / 5  | **5.0 / 5** |
| Hallucination rate |    60%     |  **0%**    |
| Actionability      |   4.9 / 5  |  5.0 / 5   |
| Relevance          |   4.7 / 5  |  4.8 / 5   |
| Tone               |   5.0 / 5  |  4.9 / 5   |

Prompts are versioned with a changelog in `src/triage/prompts.py`, so the
before/after is auditable. (A false positive surfaced along the way — the judge
flagged a "respond within 1 business day" line that is verbatim in the KB — which
is what prompted `judge_v2` to pass the excerpt *text*, not just the citation.)

**4. Unit tests** (`tests/`, `pytest`) — deterministic, no network required,
covering the non-LLM logic: KB chunker citation paths, mojibake repair, metric
implementations, team-routing rules, Pydantic schema validation, and the
churn/health signal rules.

```bash
pytest                    # 35 tests
pytest -m "not llm"       # skip any live-LLM tests
```

## Project layout

```
src/
  config.py            # paths, env, model + determinism settings
  schemas.py           # Pydantic contract (TicketInput, Classification, TriageResult)
  llm_client.py        # Groq wrapper: JSON mode, seed, retry/backoff
  text_utils.py        # repair UTF-8-as-cp1252 mojibake in LLM output
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
  eval/                # Task 3
    harness.py         # classification eval + cached predictions
    metrics.py         # accuracy / macro-F1 / confusion / within-1
    judge.py           # LLM-judge for draft-response quality
    adversarial.py     # edge-case / robustness suite
scripts/
  demo_triage.py       # sample run vs ground-truth labels
  demo_brief.py        # sample account health briefs
  run_eval.py          # eval CLI -> eval_output/ JSON report
tests/                 # unit suite (chunker, metrics, router, schemas, signals)
```
