"""Orchestration: account_id in -> AccountBrief out.

Flow: load account (rules) -> join tickets (best-effort) -> compute signals
(rules) -> narrate (LLM, grounded) -> assemble.
"""

from datetime import date

from ..data_loader import get_account, tickets_for_account
from ..schemas import AccountBrief, TicketDigest
from . import prompts
from .generator import generate_narrative
from .signals import compute_signals, days_until


class AccountNotFoundError(KeyError):
    """Raised when account_id has no record in accounts.json."""


def _build_digest(account_id: str) -> TicketDigest:
    tickets = tickets_for_account(account_id)
    if not tickets:
        return TicketDigest(linked_ticket_count=0)
    categories = sorted({t.get("category", "Unknown") for t in tickets})
    highlights = [
        f"{t.get('ticket_id', '?')} [{t.get('category', '?')}/{t.get('urgency', '?')}]"
        f" {t.get('status', '?')}: {t.get('subject', '')[:70]}"
        for t in tickets[:5]
    ]
    return TicketDigest(
        linked_ticket_count=len(tickets),
        open_categories=categories,
        highlights=highlights,
    )


def generate_brief(account_id: str, today: date | None = None) -> AccountBrief:
    account = get_account(account_id)
    if account is None:
        raise AccountNotFoundError(account_id)

    today = today or date.today()
    signals, risk_level = compute_signals(account, today=today)
    digest = _build_digest(account_id)
    dtr = days_until(account.get("renewal_date"), today)
    summary, actions = generate_narrative(account, risk_level, signals, digest, dtr)

    return AccountBrief(
        account_id=account["account_id"],
        company=account.get("company", "Unknown"),
        tam=account.get("tam", "Unassigned"),
        plan_tier=account.get("plan_tier", "?"),
        arr_usd=account.get("arr_usd", 0),
        health_status=account.get("health_status", "Unknown"),
        usage_trend=account.get("usage_trend", "Unknown"),
        risk_level=risk_level,
        renewal_date=account.get("renewal_date", "unknown"),
        days_to_renewal=dtr,
        risk_signals=signals,
        ticket_digest=digest,
        executive_summary=summary,
        recommended_actions=actions,
        prompt_version=prompts.BRIEF_VERSION,
    )
