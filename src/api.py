"""REST layer over the triage + account-brief pipelines.

Run: uvicorn src.api:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from .briefs.pipeline import AccountNotFoundError, generate_brief
from .schemas import AccountBrief, TicketInput, TriageResult
from .triage.pipeline import _get_retriever, triage_ticket


@asynccontextmanager
async def lifespan(app: FastAPI):
    # load embedding model + build FAISS index before serving the first request
    _get_retriever()
    yield


app = FastAPI(title="Support AI API", version="0.2.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/triage", response_model=TriageResult)
def triage(ticket: TicketInput) -> TriageResult:
    try:
        return triage_ticket(ticket)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Triage failed: {e}")


@app.get("/accounts/{account_id}/brief", response_model=AccountBrief)
def account_brief(account_id: str) -> AccountBrief:
    try:
        return generate_brief(account_id)
    except AccountNotFoundError:
        raise HTTPException(status_code=404, detail=f"Unknown account: {account_id}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Brief generation failed: {e}")
