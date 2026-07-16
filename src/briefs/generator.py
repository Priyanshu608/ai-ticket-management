"""LLM call: turn deterministic signals into TAM-facing narrative prose.

Validates the LLM output shape; on failure falls back to a deterministic
summary so a brief is always produced (the hard facts already live in the
signals, so the brief is useful even without the LLM).
"""

from ..llm_client import chat_json
from ..schemas import RiskLevel, RiskSignal, TicketDigest
from . import prompts


def _signals_block(signals: list[RiskSignal]) -> str:
    if not signals:
        return "(none -- no material risk signals detected)"
    return "\n".join(f"- [{s.severity}] {s.factor}: {s.detail}" for s in signals)


def _ticket_block(digest: TicketDigest) -> str:
    if digest.linked_ticket_count == 0:
        return "(no support tickets linked to this account)"
    lines = [f"{digest.linked_ticket_count} linked ticket(s)."]
    if digest.open_categories:
        lines.append("Categories: " + ", ".join(digest.open_categories))
    lines.extend(digest.highlights)
    return "\n".join(lines)


def _renewal_phrase(days_to_renewal: int | None) -> str:
    if days_to_renewal is None:
        return "renewal date unknown"
    if days_to_renewal < 0:
        return f"{-days_to_renewal} days overdue"
    return f"in {days_to_renewal} days"


def generate_narrative(
    account: dict,
    risk_level: RiskLevel,
    signals: list[RiskSignal],
    digest: TicketDigest,
    days_to_renewal: int | None,
) -> tuple[str, list[str]]:
    contact = account.get("primary_contact") or {}
    user_msg = prompts.BRIEF_USER_TEMPLATE.format(
        company=account.get("company", "Unknown"),
        account_id=account.get("account_id", "?"),
        tam=account.get("tam", "Unassigned"),
        plan_tier=account.get("plan_tier", "?"),
        arr_usd=account.get("arr_usd", 0),
        health_status=account.get("health_status", "Unknown"),
        usage_trend=account.get("usage_trend", "Unknown"),
        risk_level=risk_level,
        renewal_date=account.get("renewal_date", "unknown"),
        renewal_phrase=_renewal_phrase(days_to_renewal),
        products=", ".join(account.get("products") or []) or "none listed",
        primary_contact=f"{contact.get('name', '?')} ({contact.get('title', '?')})",
        signals_block=_signals_block(signals),
        ticket_block=_ticket_block(digest),
    )

    try:
        raw = chat_json(prompts.BRIEF_SYSTEM, user_msg)
        summary = str(raw["executive_summary"]).strip()
        actions = [str(a).strip() for a in raw["recommended_actions"] if str(a).strip()]
        if not summary or not actions:
            raise ValueError("empty summary or actions")
        return summary, actions
    except Exception:
        return _fallback(account, risk_level, signals, days_to_renewal)


def _fallback(
    account: dict,
    risk_level: RiskLevel,
    signals: list[RiskSignal],
    days_to_renewal: int | None,
) -> tuple[str, list[str]]:
    """Deterministic brief if the LLM is unavailable -- never leave the TAM
    without a summary."""
    top = [s for s in signals if s.severity == "High"][:3]
    reasons = "; ".join(s.detail for s in top) or "no material risk signals"
    summary = (
        f"{account.get('company', 'This account')} is {risk_level} risk "
        f"(health: {account.get('health_status', 'Unknown')}, "
        f"renewal {_renewal_phrase(days_to_renewal)}). Key drivers: {reasons}."
    )
    actions = [s.detail for s in top] or [
        "Maintain regular check-ins and look for expansion opportunities."
    ]
    return summary, actions
