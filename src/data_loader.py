"""Loaders for the provided mock dataset (tickets + accounts).

Loaders are cached so repeated brief/triage calls don't re-read + re-parse the
JSON on every request (tickets.json is ~440 KB).
"""

import json
from functools import lru_cache

from . import config


@lru_cache(maxsize=1)
def load_tickets() -> list[dict]:
    with open(config.DATA_DIR / "tickets.json", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_accounts() -> list[dict]:
    with open(config.DATA_DIR / "accounts.json", encoding="utf-8") as f:
        return json.load(f)


def get_account(account_id: str) -> dict | None:
    """Return the account record, or None if the id is unknown."""
    return next((a for a in load_accounts() if a["account_id"] == account_id), None)


def tickets_for_account(account_id: str) -> list[dict]:
    """Tickets linked to an account. Frequently empty: most ticket.account_id
    values intentionally do not match accounts.json -- callers must cope."""
    return [t for t in load_tickets() if t.get("account_id") == account_id]
