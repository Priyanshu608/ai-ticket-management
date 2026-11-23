"""FastAPI layer for AI triage, account briefs, and read-only operations views.

Run: uvicorn src.api:app --reload
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .briefs.pipeline import AccountNotFoundError, generate_brief
from .data_loader import load_accounts, load_tickets
from .ops import account_queue, operations_summary, ticket_queue
from .schemas import AccountBrief, TicketInput, TriageResult
from .triage.pipeline import triage_ticket

# Retrieval models initialize lazily when triage is called, so the read-only
# operations dashboard works without downloading embeddings or an LLM key.
app = FastAPI(title="Support AI API", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/operations/summary")
def operations_overview() -> dict:
    """Snapshot metrics calculated from the included synthetic dataset."""
    return operations_summary(load_tickets(), load_accounts())


@app.get("/operations/tickets")
def operations_tickets(
    query: str = Query(default="", max_length=120),
    status: str = "",
    priority: str = "",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=15, ge=1, le=50),
) -> dict:
    try:
        return ticket_queue(load_tickets(), query=query, status=status,
                            priority=priority, page=page, page_size=page_size)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/operations/accounts")
def operations_accounts(
    query: str = Query(default="", max_length=120),
    risk: str = "",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
) -> dict:
    try:
        return account_queue(load_accounts(), query=query, risk=risk,
                             page=page, page_size=page_size)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/triage", response_model=TriageResult)
def triage(ticket: TicketInput) -> TriageResult:
    try:
        return triage_ticket(ticket)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Triage failed: {exc}") from exc


@app.get("/accounts/{account_id}/brief", response_model=AccountBrief)
def account_brief(account_id: str) -> AccountBrief:
    try:
        return generate_brief(account_id)
    except AccountNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown account: {account_id}") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Brief generation failed: {exc}") from exc
