"""Loaders for the provided mock dataset (tickets + accounts)."""

import json

from . import config


def load_tickets() -> list[dict]:
    with open(config.DATA_DIR / "tickets.json", encoding="utf-8") as f:
        return json.load(f)


def load_accounts() -> list[dict]:
    with open(config.DATA_DIR / "accounts.json", encoding="utf-8") as f:
        return json.load(f)
