"""Pure dataset view tests; no Groq key or embedding model needed."""
from src.ops import account_queue, operations_summary, ticket_queue


def tickets():
    return [
        {"ticket_id": "TKT-1", "subject": "Login error", "company": "Alpha", "status": "Open",
         "urgency": "P1", "updated_at": "2026-02-01", "created_at": "2026-01-10"},
        {"ticket_id": "TKT-2", "subject": "Billing issue", "company": "Beta", "status": "Closed",
         "urgency": "P3", "updated_at": "2026-03-01", "created_at": "2026-02-10"},
        {"ticket_id": "TKT-3", "subject": "Login issue", "company": "Alpha", "status": "In Progress",
         "urgency": "P2", "updated_at": "2026-04-01", "created_at": "2026-02-11"},
    ]


def test_ticket_queue_filters_and_orders():
    result = ticket_queue(tickets(), query="alpha")
    assert [t["ticket_id"] for t in result["items"]] == ["TKT-3", "TKT-1"]
    assert ticket_queue(tickets(), priority="P1")["total"] == 1
    assert ticket_queue(tickets(), status="Closed")["items"][0]["ticket_id"] == "TKT-2"


def test_ticket_queue_pagination():
    result = ticket_queue(tickets(), page=2, page_size=1)
    assert result["total"] == 3 and result["pages"] == 3
    assert len(result["items"]) == 1
    assert ticket_queue(tickets(), page=5, page_size=1)["items"] == []


def test_ticket_queue_rejects_unknown_filters():
    import pytest
    with pytest.raises(ValueError):
        ticket_queue(tickets(), priority="P9")
    with pytest.raises(ValueError):
        ticket_queue(tickets(), status="Deleted")


def test_summary_counts_active_and_priority():
    summary = operations_summary(tickets(), [])
    assert summary["active_tickets"] == 2
    assert summary["critical_active"] == 1
    assert summary["priority_counts"] == {"P1": 1, "P2": 1, "P3": 1, "P4": 0}
    assert summary["monthly_volume"] == [
        {"month": "2026-01", "tickets": 1}, {"month": "2026-02", "tickets": 2},
    ]
    assert summary["source"] == "synthetic_dataset"


def test_accounts_filter_by_deterministic_risk():
    accounts = [
        {"account_id": "ACC-1", "company": "Alpha", "tam": "Sam", "health_status": "Churning",
         "usage_trend": "Inactive", "open_tickets": 7},
        {"account_id": "ACC-2", "company": "Beta", "tam": "Lee", "health_status": "Healthy",
         "usage_trend": "Increasing", "open_tickets": 0},
    ]
    result = account_queue(accounts, risk="High")
    assert result["total"] == 1 and result["items"][0]["account_id"] == "ACC-1"
    assert account_queue(accounts, query="beta")["items"][0]["risk_level"] == "Low"
