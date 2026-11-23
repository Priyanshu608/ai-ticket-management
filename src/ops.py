"""Deterministic operations views over the bundled, synthetic support dataset.

These endpoints deliberately avoid LLM calls. They reflect snapshot data,
not a production ticketing system or a mutable ticket queue.
"""
from collections import Counter
from datetime import datetime, timezone

from .briefs.signals import compute_signals

ACTIVE_STATES = {"Open", "In Progress", "Pending Customer"}
VALID_STATUSES = ACTIVE_STATES | {"Resolved", "Closed"}
VALID_PRIORITIES = {"P1", "P2", "P3", "P4"}


def ticket_queue(tickets: list[dict], *, query: str = "", status: str = "",
                 priority: str = "", page: int = 1, page_size: int = 15) -> dict:
    """Search and paginate tickets with deterministic newest-updated ordering."""
    if status and status not in VALID_STATUSES:
        raise ValueError("Unknown ticket status")
    if priority and priority not in VALID_PRIORITIES:
        raise ValueError("Unknown ticket priority")
    term = query.strip().casefold()
    matches = []
    for ticket in tickets:
        if status and ticket.get("status") != status:
            continue
        if priority and ticket.get("urgency") != priority:
            continue
        searchable = " ".join(str(ticket.get(field, "")) for field in
                              ("ticket_id", "subject", "company", "account_id", "product", "category"))
        if term and term not in searchable.casefold():
            continue
        matches.append(ticket)

    matches.sort(key=lambda t: (str(t.get("updated_at") or ""), str(t.get("ticket_id") or "")),
                 reverse=True)
    start = (page - 1) * page_size
    return {
        "items": matches[start:start + page_size],
        "total": len(matches),
        "page": page,
        "page_size": page_size,
        "pages": max(1, (len(matches) + page_size - 1) // page_size),
    }


def account_queue(accounts: list[dict], *, query: str = "", risk: str = "",
                  page: int = 1, page_size: int = 12) -> dict:
    if risk and risk not in {"Low", "Medium", "High"}:
        raise ValueError("Unknown account risk")
    term = query.strip().casefold()
    matches = []
    for account in accounts:
        _, level = compute_signals(account)
        if risk and level != risk:
            continue
        if term and term not in " ".join(str(account.get(k, "")) for k in
                                         ("company", "account_id", "tam", "region")).casefold():
            continue
        matches.append({
            "account_id": account.get("account_id"),
            "company": account.get("company"),
            "tam": account.get("tam"),
            "plan_tier": account.get("plan_tier"),
            "health_status": account.get("health_status"),
            "usage_trend": account.get("usage_trend"),
            "open_tickets": account.get("open_tickets", 0),
            "arr_usd": account.get("arr_usd", 0),
            "renewal_date": account.get("renewal_date"),
            "risk_level": level,
        })
    order = {"High": 0, "Medium": 1, "Low": 2}
    matches.sort(key=lambda a: (order[a["risk_level"]], -int(a["open_tickets"] or 0), a["company"] or ""))
    start = (page - 1) * page_size
    return {"items": matches[start:start + page_size], "total": len(matches),
            "page": page, "page_size": page_size,
            "pages": max(1, (len(matches) + page_size - 1) // page_size)}


def operations_summary(tickets: list[dict], accounts: list[dict]) -> dict:
    status_counts = Counter(t.get("status", "Unknown") for t in tickets)
    priority_counts = Counter(t.get("urgency", "Unknown") for t in tickets)
    active = [t for t in tickets if t.get("status") in ACTIVE_STATES]
    at_risk = sum(1 for a in accounts if compute_signals(a)[1] == "High")
    month_counts = Counter(
        str(t.get("created_at", ""))[:7]
        for t in tickets if len(str(t.get("created_at", ""))) >= 7
    )
    monthly = [{"month": month, "tickets": month_counts[month]}
               for month in sorted(month_counts)[-8:]]
    return {
        "source": "synthetic_dataset",
        "total_tickets": len(tickets),
        "active_tickets": len(active),
        "critical_active": sum(1 for t in active if t.get("urgency") == "P1"),
        "total_accounts": len(accounts),
        "high_risk_accounts": at_risk,
        "priority_counts": {key: priority_counts.get(key, 0) for key in ("P1", "P2", "P3", "P4")},
        "status_counts": {key: status_counts.get(key, 0) for key in
                          ("Open", "In Progress", "Pending Customer", "Resolved", "Closed")},
        "monthly_volume": monthly,
    }
