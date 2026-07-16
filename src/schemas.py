"""Pydantic models = the structured-output contract for the whole pipeline.

Literal types make invalid LLM output fail loudly at validation time, so a
malformed classification never silently propagates downstream.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field

Category = Literal[
    "Bug",
    "Feature Request",
    "How-To",
    "Performance",
    "Billing",
    "Integration",
    "Onboarding",
    "Data Loss",
]
Urgency = Literal["P1", "P2", "P3", "P4"]


class TicketInput(BaseModel):
    subject: str = Field(min_length=1)
    body: str = Field(min_length=1)


class Classification(BaseModel):
    product: str
    product_area: str
    category: Category
    urgency: Urgency
    reasoning: str


class KBMatch(BaseModel):
    is_known_issue: bool
    doc_path: Optional[str] = None
    section: Optional[str] = None
    match_score: Optional[float] = None


class TriageResult(BaseModel):
    classification: Classification
    kb_match: KBMatch
    recommended_team: str
    draft_response: str
    prompt_version: str


# --- Task 2: account health briefs -----------------------------------------

RiskLevel = Literal["Low", "Medium", "High"]


class RiskSignal(BaseModel):
    """One deterministically-derived churn/health signal.

    `factor` is the account attribute it came from; `severity` and `detail`
    are computed by rules in briefs/signals.py, never by the LLM.
    """

    factor: str
    severity: RiskLevel
    detail: str


class TicketDigest(BaseModel):
    """Compact view of the tickets linked to an account (often empty --
    ticket.account_id rarely matches accounts.json, by design)."""

    linked_ticket_count: int
    open_categories: list[str] = []
    highlights: list[str] = []  # "TKT-10293 [Data Loss/P2] subject..."


class AccountBrief(BaseModel):
    account_id: str
    company: str
    tam: str
    plan_tier: str
    arr_usd: int
    health_status: str
    usage_trend: str
    risk_level: RiskLevel
    renewal_date: str
    days_to_renewal: Optional[int] = None
    risk_signals: list[RiskSignal]
    ticket_digest: TicketDigest
    executive_summary: str
    recommended_actions: list[str]
    prompt_version: str
