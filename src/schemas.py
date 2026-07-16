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
