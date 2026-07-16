"""Orchestration: raw ticket in -> TriageResult out.
Flow: classify (LLM) -> retrieve (FAISS) -> match+draft (LLM) -> route (rules).
"""

from .. import config
from ..kb.retriever import KBRetriever
from ..schemas import TicketInput, TriageResult
from . import prompts
from .classifier import classify_ticket
from .responder import match_and_draft
from .router import route

_retriever: KBRetriever | None = None


def _get_retriever() -> KBRetriever:
    global _retriever
    if _retriever is None:  # load model + build FAISS index once, reuse
        _retriever = KBRetriever()
    return _retriever


def triage_ticket(ticket: TicketInput) -> TriageResult:
    classification = classify_ticket(ticket)
    query = (
        f"{classification.product} {classification.product_area} "
        f"{ticket.subject} {ticket.body[:500]}"
    )
    chunks = _get_retriever().retrieve(query, k=config.TOP_K_CHUNKS)
    kb_match, draft = match_and_draft(ticket, classification, chunks)
    return TriageResult(
        classification=classification,
        kb_match=kb_match,
        recommended_team=route(classification),
        draft_response=draft,
        prompt_version=f"{prompts.CLASSIFY_VERSION}+{prompts.RESPOND_VERSION}",
    )
