"""Unit tests for deterministic team routing."""

from src.schemas import Classification
from src.triage.router import route


def _c(category: str, urgency: str) -> Classification:
    return Classification(
        product="X", product_area="Y", category=category, urgency=urgency, reasoning="t"
    )


def test_p1_always_escalates():
    for cat in ["Bug", "How-To", "Billing", "Feature Request"]:
        assert route(_c(cat, "P1")) == "Tier-2 Escalation (On-call)"


def test_minor_bug_stays_tier1():
    assert route(_c("Bug", "P4")) == "Tier-1 Support"
    assert route(_c("Performance", "P4")) == "Tier-1 Support"


def test_category_routing():
    assert route(_c("Billing", "P3")) == "Billing Operations"
    assert route(_c("Feature Request", "P3")) == "Product Management"
    assert route(_c("Integration", "P2")) == "Integrations Team"
    assert route(_c("Onboarding", "P3")) == "Customer Onboarding"
    assert route(_c("How-To", "P3")) == "Tier-1 Support"


def test_data_loss_escalates_even_when_not_p1():
    assert route(_c("Data Loss", "P2")) == "Tier-2 Escalation (On-call)"


def test_bug_non_p4_goes_tier2():
    assert route(_c("Bug", "P2")) == "Tier-2 Support"
    assert route(_c("Performance", "P3")) == "Tier-2 Support"
