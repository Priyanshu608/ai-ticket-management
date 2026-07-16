"""Demo: generate TAM account health briefs.

Usage:
  python scripts/demo_brief.py                 # a few at-risk accounts
  python scripts/demo_brief.py ACC-3336        # one specific account
"""

import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")  # KB/LLM text may exceed cp1252
except (AttributeError, ValueError):
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.briefs.pipeline import generate_brief  # noqa: E402
from src.data_loader import load_accounts  # noqa: E402


def pick_default_accounts(n: int = 3) -> list[str]:
    """A churning/at-risk account, an at-risk one with a linked ticket, and a
    healthy one -- so the demo shows the full range."""
    accounts = load_accounts()
    churning = [a for a in accounts if a["health_status"] == "Churning"]
    at_risk = [a for a in accounts if a["health_status"] == "At Risk"]
    healthy = [a for a in accounts if a["health_status"] == "Healthy"]
    picks: list[str] = []
    for bucket in (churning, at_risk, healthy):
        if bucket:
            picks.append(bucket[0]["account_id"])
    return picks[:n] or [a["account_id"] for a in accounts[:n]]


def show(account_id: str) -> None:
    b = generate_brief(account_id)
    print("=" * 76)
    print(f"{b.company} ({b.account_id})  |  TAM: {b.tam}")
    print(
        f"  {b.plan_tier} | ARR ${b.arr_usd:,} | health: {b.health_status} | "
        f"usage: {b.usage_trend}"
    )
    print(f"  RISK LEVEL: {b.risk_level}  |  renewal {b.renewal_date} "
          f"({b.days_to_renewal} days)")
    print(f"  signals ({len(b.risk_signals)}):")
    for s in b.risk_signals:
        print(f"    - [{s.severity}] {s.factor}: {s.detail}")
    print(f"  linked tickets: {b.ticket_digest.linked_ticket_count}")
    for h in b.ticket_digest.highlights:
        print(f"      {h}")
    print(f"  EXECUTIVE SUMMARY:\n    {b.executive_summary}")
    print("  RECOMMENDED ACTIONS:")
    for i, a in enumerate(b.recommended_actions, 1):
        print(f"    {i}. {a}")


if __name__ == "__main__":
    ids = sys.argv[1:] or pick_default_accounts()
    for j, aid in enumerate(ids):
        show(aid)
        if j < len(ids) - 1:
            time.sleep(2)  # free tier: 30 RPM, 1 LLM call per brief
