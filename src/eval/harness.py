"""Classification eval harness.

Runs the triage classifier over a sample of labelled tickets and scores it
against the dataset's ground-truth labels. Only the classification step is
scored (that's the surface with ground truth); KB match + draft quality are
handled separately by eval/judge.py.

Cost control: classification is one LLM call per ticket. Predictions are cached
to disk keyed by (model, prompt_version, ticket_id), so re-running the eval or
growing the sample never re-calls tickets already scored. Free-tier friendly.
"""

import json
import random
import time
from pathlib import Path

from typing import get_args

from .. import config
from ..data_loader import load_tickets
from ..schemas import Category, TicketInput, Urgency
from ..triage import prompts
from ..triage.classifier import classify_ticket
from . import metrics

_CACHE_DIR = config.ROOT_DIR / "eval_output"
_SAMPLE_SEED = 42


def _cache_path() -> Path:
    tag = f"{config.GROQ_MODEL}__{prompts.CLASSIFY_VERSION}".replace("/", "-")
    return _CACHE_DIR / f"predictions__{tag}.json"


def _load_cache() -> dict[str, dict]:
    path = _cache_path()
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _save_cache(cache: dict[str, dict]) -> None:
    _CACHE_DIR.mkdir(exist_ok=True)
    _cache_path().write_text(
        json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def sample_tickets(n: int) -> list[dict]:
    tickets = load_tickets()
    if n >= len(tickets):
        return tickets
    # deterministic random sample -> representative + reproducible
    return random.Random(_SAMPLE_SEED).sample(tickets, n)


def predict(
    tickets: list[dict], refresh: bool = False, sleep_s: float = 1.2, verbose: bool = True
) -> dict[str, dict]:
    """Return {ticket_id: prediction dict}, using/refreshing the disk cache."""
    cache = {} if refresh else _load_cache()
    made_calls = 0
    for i, t in enumerate(tickets, 1):
        tid = t["ticket_id"]
        if tid in cache:
            continue
        pred = classify_ticket(TicketInput(subject=t["subject"], body=t["body"]))
        cache[tid] = pred.model_dump()
        made_calls += 1
        if verbose:
            print(f"  [{i}/{len(tickets)}] {tid} -> {pred.category}/{pred.urgency}")
        if made_calls % 10 == 0:
            _save_cache(cache)  # checkpoint so a crash doesn't lose progress
        time.sleep(sleep_s)  # free tier: 30 RPM
    _save_cache(cache)
    return cache


def evaluate(tickets: list[dict], cache: dict[str, dict]) -> dict:
    """Compute the metrics report from cached predictions vs ground truth."""
    scored = [t for t in tickets if t["ticket_id"] in cache]
    cat_labels = list(get_args(Category))
    urg_labels = list(get_args(Urgency))

    cat_pred = [cache[t["ticket_id"]]["category"] for t in scored]
    cat_gold = [t["category"] for t in scored]
    urg_pred = [cache[t["ticket_id"]]["urgency"] for t in scored]
    urg_gold = [t["urgency"] for t in scored]
    prod_pred = [cache[t["ticket_id"]]["product"].lower().strip() for t in scored]
    prod_gold = [t["product"].lower().strip() for t in scored]

    disagreements = [
        {
            "ticket_id": t["ticket_id"],
            "subject": t["subject"][:70],
            "gold": f"{t['category']}/{t['urgency']}",
            "pred": f"{cache[t['ticket_id']]['category']}/{cache[t['ticket_id']]['urgency']}",
            "reasoning": cache[t["ticket_id"]].get("reasoning", ""),
        }
        for t in scored
        if cache[t["ticket_id"]]["category"] != t["category"]
    ]

    return {
        "model": config.GROQ_MODEL,
        "prompt_version": prompts.CLASSIFY_VERSION,
        "n_scored": len(scored),
        "category": {
            "accuracy": round(metrics.accuracy(cat_pred, cat_gold), 3),
            "macro_f1": metrics.macro_f1(cat_pred, cat_gold, cat_labels),
            "per_class": metrics.per_class_prf(cat_pred, cat_gold, cat_labels),
            "confusion": metrics.confusion_matrix(cat_pred, cat_gold, cat_labels),
        },
        "urgency": {
            "accuracy": round(metrics.accuracy(urg_pred, urg_gold), 3),
            "within_1": round(metrics.within_n_accuracy(urg_pred, urg_gold, 1), 3),
            "per_class": metrics.per_class_prf(urg_pred, urg_gold, urg_labels),
            "confusion": metrics.confusion_matrix(urg_pred, urg_gold, urg_labels),
        },
        "product": {"accuracy": round(metrics.accuracy(prod_pred, prod_gold), 3)},
        "category_disagreements": disagreements,
    }


def run(n: int, refresh: bool = False, verbose: bool = True) -> dict:
    tickets = sample_tickets(n)
    cache = predict(tickets, refresh=refresh, verbose=verbose)
    return evaluate(tickets, cache)
