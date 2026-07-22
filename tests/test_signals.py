"""Unit tests for deterministic account churn/health signals."""

from datetime import date

from src.briefs.signals import compute_signals, days_until

REF = date(2026, 7, 16)


def _account(**overrides) -> dict:
    base = {
        "account_id": "ACC-TEST",
        "company": "Test Co",
        "health_status": "Healthy",
        "usage_trend": "Stable",
        "seats_licensed": 100,
        "seats_active": 95,
        "nps_score": None,
        "p1_tickets_last_30d": 0,
        "open_tickets": 0,
        "renewal_date": "2027-01-01",
        "last_qbr_date": "2026-06-01",
        "last_login_days_ago": 2,
        "escalation_notes": [],
    }
    base.update(overrides)
    return base


def _factors(signals) -> set[str]:
    return {s.factor for s in signals}


def test_healthy_account_low_risk():
    signals, risk = compute_signals(_account(), today=REF)
    assert risk == "Low"
    assert signals == []


def test_churning_always_high():
    _, risk = compute_signals(_account(health_status="Churning"), today=REF)
    assert risk == "High"


def test_escalation_notes_are_high_signals():
    signals, risk = compute_signals(
        _account(escalation_notes=["Champion left", "Evaluating competitor"]), today=REF
    )
    notes = [s for s in signals if s.factor == "escalation_note"]
    assert len(notes) == 2
    assert all(s.severity == "High" for s in notes)


def test_seat_utilization_thresholds():
    high, _ = compute_signals(_account(seats_active=40, seats_licensed=100), today=REF)
    assert any(s.factor == "seat_utilization" and s.severity == "High" for s in high)
    med, _ = compute_signals(_account(seats_active=70, seats_licensed=100), today=REF)
    assert any(s.factor == "seat_utilization" and s.severity == "Medium" for s in med)
    none, _ = compute_signals(_account(seats_active=95, seats_licensed=100), today=REF)
    assert "seat_utilization" not in _factors(none)


def test_nps_detractor_vs_passive():
    det, _ = compute_signals(_account(nps_score=4), today=REF)
    assert any(s.factor == "nps_score" and s.severity == "High" for s in det)
    pas, _ = compute_signals(_account(nps_score=8), today=REF)
    assert any(s.factor == "nps_score" and s.severity == "Medium" for s in pas)
    promoter, _ = compute_signals(_account(nps_score=10), today=REF)
    assert "nps_score" not in _factors(promoter)


def test_renewal_proximity_caps_at_medium():
    # a healthy account near renewal must not be pushed to High by timing alone
    signals, risk = compute_signals(_account(renewal_date="2026-07-20"), today=REF)
    renewal = [s for s in signals if s.factor == "renewal_date"]
    assert renewal and renewal[0].severity == "Medium"
    assert risk in ("Low", "Medium")


def test_missing_fields_do_not_crash():
    signals, risk = compute_signals({"account_id": "ACC-X"}, today=REF)
    assert isinstance(signals, list)
    assert risk in ("Low", "Medium", "High")


def test_days_until():
    assert days_until("2026-07-20", REF) == 4
    assert days_until("2026-07-10", REF) == -6
    assert days_until(None, REF) is None
    assert days_until("not-a-date", REF) is None
