"""Team routing = pure business rules. Deterministic and unit-testable.
An LLM adds nothing here except nondeterminism.
"""

from ..schemas import Classification

_CATEGORY_TEAM = {
    "Billing": "Billing Operations",
    "Feature Request": "Product Management",
    "How-To": "Tier-1 Support",
    "Onboarding": "Customer Onboarding",
    "Integration": "Integrations Team",
    "Performance": "Tier-2 Support",
    "Bug": "Tier-2 Support",
    "Data Loss": "Tier-2 Escalation (On-call)",
}


def route(c: Classification) -> str:
    if c.urgency == "P1":
        return "Tier-2 Escalation (On-call)"  # criticals always escalate
    if c.category in ("Bug", "Performance") and c.urgency == "P4":
        return "Tier-1 Support"  # minor issues stay tier-1
    return _CATEGORY_TEAM[c.category]
