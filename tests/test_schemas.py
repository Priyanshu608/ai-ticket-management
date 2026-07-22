"""Unit tests for the Pydantic contract -- invalid LLM output must fail loudly."""

import pytest
from pydantic import ValidationError

from src.schemas import Classification, TicketInput, TriageResult, KBMatch


def test_ticket_input_requires_nonempty():
    with pytest.raises(ValidationError):
        TicketInput(subject="", body="x")
    with pytest.raises(ValidationError):
        TicketInput(subject="x", body="")
    assert TicketInput(subject="s", body="b").subject == "s"


def test_classification_rejects_bad_category():
    with pytest.raises(ValidationError):
        Classification(
            product="P", product_area="A", category="NotACategory",
            urgency="P1", reasoning="r",
        )


def test_classification_rejects_bad_urgency():
    with pytest.raises(ValidationError):
        Classification(
            product="P", product_area="A", category="Bug",
            urgency="P9", reasoning="r",
        )


def test_valid_classification_roundtrips():
    c = Classification(
        product="CloudSync", product_area="Webhooks", category="Integration",
        urgency="P2", reasoning="third-party failure",
    )
    assert c.category == "Integration"
    assert Classification(**c.model_dump()) == c


def test_triage_result_assembles():
    r = TriageResult(
        classification=Classification(
            product="P", product_area="A", category="Bug", urgency="P3", reasoning="r"
        ),
        kb_match=KBMatch(is_known_issue=False),
        recommended_team="Tier-2 Support",
        draft_response="hello",
        prompt_version="classify_v1+respond_v1",
    )
    assert r.kb_match.is_known_issue is False
    assert r.recommended_team == "Tier-2 Support"
