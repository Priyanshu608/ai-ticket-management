"""REST layer over the triage pipeline.

Run: uvicorn src.api:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from .schemas import TicketInput, TriageResult
from .triage.pipeline import _get_retriever, triage_ticket


@asynccontextmanager
async def lifespan(app: FastAPI):
    # load embedding model + build FAISS index before serving the first request
    _get_retriever()
    yield


app = FastAPI(title="Support Triage API", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/triage", response_model=TriageResult)
def triage(ticket: TicketInput) -> TriageResult:
    try:
        return triage_ticket(ticket)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Triage failed: {e}")
