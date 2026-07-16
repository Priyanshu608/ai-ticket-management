"""Deterministic account health / churn-risk signals.

Same philosophy as triage/router.py: anything a rule can decide, a rule decides.
The LLM later narrates these signals but never invents them, so the risk_level
and the facts in a brief are reproducible and auditable.

Reference "today" is the system date; days_to_renewal / QBR staleness are
derived from it.
"""

from datetime import date

from ..schemas import RiskLevel, RiskSignal

# health_status -> base risk contribution
_HEALTH_BASE: dict[str, int] = {
    "Churning": 4,
    "At Risk": 3,
    "New": 1,
    "Healthy": 0,
}
_SEVERITY_WEIGHT: dict[RiskLevel, int] = {"High": 2, "Medium": 1, "Low": 0}


def _parse_date(value: str | None) -> date | None:
    try:
        return date.fromisoformat(value) if value else None
    except (ValueError, TypeError):
        return None


def days_until(value: str | None, today: date) -> int | None:
    d = _parse_date(value)
    return (d - today).days if d else None


def compute_signals(
    account: dict, today: date | None = None
) -> tuple[list[RiskSignal], RiskLevel]:
    """Return (signals, overall_risk_level) for an account record."""
    today = today or date.today()
    signals: list[RiskSignal] = []

    def add(factor: str, severity: RiskLevel, detail: str) -> None:
        signals.append(RiskSignal(factor=factor, severity=severity, detail=detail))

    # 1. Curated escalation notes -- these are hand-flagged churn signals.
    for note in account.get("escalation_notes") or []:
        add("escalation_note", "High", note)

    # 2. Health status.
    health = account.get("health_status", "Unknown")
    if health == "Churning":
        add("health_status", "High", "Account flagged as Churning.")
    elif health == "At Risk":
        add("health_status", "High", "Account flagged as At Risk.")
    elif health == "New":
        add("health_status", "Low", "New account -- still in adoption ramp.")

    # 3. Usage trend.
    trend = account.get("usage_trend", "Unknown")
    if trend == "Inactive":
        add("usage_trend", "High", "Usage is Inactive -- no meaningful activity.")
    elif trend == "Declining":
        add("usage_trend", "Medium", "Usage trend is Declining.")

    # 4. Seat utilization (adoption depth).
    licensed = account.get("seats_licensed") or 0
    active = account.get("seats_active") or 0
    if licensed:
        util = active / licensed
        if util < 0.5:
            add(
                "seat_utilization",
                "High",
                f"Only {active}/{licensed} seats active ({util:.0%}) -- underadopted.",
            )
        elif util < 0.75:
            add(
                "seat_utilization",
                "Medium",
                f"{active}/{licensed} seats active ({util:.0%}) -- adoption below target.",
            )

    # 5. NPS.
    nps = account.get("nps_score")
    if isinstance(nps, int):
        if nps <= 6:
            add("nps_score", "High", f"NPS {nps} -- detractor.")
        elif nps <= 8:
            add("nps_score", "Medium", f"NPS {nps} -- passive, not a promoter.")

    # 6. P1 volume.
    p1 = account.get("p1_tickets_last_30d") or 0
    if p1 >= 3:
        add("p1_tickets_last_30d", "High", f"{p1} P1 tickets in the last 30 days.")
    elif p1 >= 1:
        add("p1_tickets_last_30d", "Medium", f"{p1} P1 ticket(s) in the last 30 days.")

    # 7. Open ticket backlog. Operational load, not churn on its own -> caps
    # at Medium so it can't alone push a healthy account to High risk.
    open_t = account.get("open_tickets") or 0
    if open_t >= 8:
        add("open_tickets", "Medium", f"{open_t} open support tickets.")

    # 8. Renewal proximity. This is a *timing* signal that amplifies other risk
    # and drives prioritization; a healthy account near renewal is not itself
    # at risk, so it caps at Medium.
    dtr = days_until(account.get("renewal_date"), today)
    if dtr is not None and dtr <= 0:
        add("renewal_date", "Medium", "Contract is past its renewal date.")
    elif dtr is not None and dtr <= 30:
        add("renewal_date", "Medium", f"Renewal in {dtr} days.")
    elif dtr is not None and dtr <= 90:
        add("renewal_date", "Low", f"Renewal in {dtr} days.")

    # 9. QBR staleness.
    last_qbr = _parse_date(account.get("last_qbr_date"))
    if last_qbr is not None:
        stale = (today - last_qbr).days
        if stale > 180:
            add("last_qbr_date", "Medium", f"Last QBR was {stale} days ago (overdue).")

    # 10. Login recency.
    login_days = account.get("last_login_days_ago")
    if isinstance(login_days, int) and login_days >= 30:
        add(
            "last_login_days_ago",
            "High" if login_days >= 60 else "Medium",
            f"Primary activity last seen {login_days} days ago.",
        )

    return signals, _overall_risk(account, signals)


def _overall_risk(account: dict, signals: list[RiskSignal]) -> RiskLevel:
    """Aggregate to a single level. Churning is always High; otherwise a
    weighted score over the health base + signal severities decides."""
    if account.get("health_status") == "Churning":
        return "High"
    score = _HEALTH_BASE.get(account.get("health_status", ""), 0)
    score += sum(_SEVERITY_WEIGHT[s.severity] for s in signals)
    if score >= 6:
        return "High"
    if score >= 3:
        return "Medium"
    return "Low"
