"""Pure classification metrics. No LLM, no IO -- trivially unit-testable.

All functions take parallel lists of predicted / gold labels (same length).
"""

from collections import defaultdict


def accuracy(pred: list[str], gold: list[str]) -> float:
    if not gold:
        return 0.0
    correct = sum(p == g for p, g in zip(pred, gold))
    return correct / len(gold)


def confusion_matrix(
    pred: list[str], gold: list[str], labels: list[str]
) -> dict[str, dict[str, int]]:
    """matrix[gold_label][pred_label] = count."""
    matrix = {g: {p: 0 for p in labels} for g in labels}
    for p, g in zip(pred, gold):
        if g in matrix and p in matrix[g]:
            matrix[g][p] += 1
    return matrix


def per_class_prf(
    pred: list[str], gold: list[str], labels: list[str]
) -> dict[str, dict[str, float]]:
    """Precision / recall / F1 / support for each label."""
    tp = defaultdict(int)
    fp = defaultdict(int)
    fn = defaultdict(int)
    support = defaultdict(int)
    for p, g in zip(pred, gold):
        support[g] += 1
        if p == g:
            tp[p] += 1
        else:
            fp[p] += 1
            fn[g] += 1

    out: dict[str, dict[str, float]] = {}
    for label in labels:
        prec = tp[label] / (tp[label] + fp[label]) if (tp[label] + fp[label]) else 0.0
        rec = tp[label] / (tp[label] + fn[label]) if (tp[label] + fn[label]) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        out[label] = {
            "precision": round(prec, 3),
            "recall": round(rec, 3),
            "f1": round(f1, 3),
            "support": support[label],
        }
    return out


def macro_f1(pred: list[str], gold: list[str], labels: list[str]) -> float:
    prf = per_class_prf(pred, gold, labels)
    # macro = unweighted mean over labels that actually appear in gold
    present = [lbl for lbl in labels if prf[lbl]["support"] > 0]
    if not present:
        return 0.0
    return round(sum(prf[lbl]["f1"] for lbl in present) / len(present), 3)


# --- urgency is ordinal (P1 > P2 > P3 > P4), so exact accuracy under-credits a
# P2-vs-P3 miss versus a P1-vs-P4 miss. within_n measures ordinal closeness. ---

_URGENCY_RANK = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}


def urgency_distance(p: str, g: str) -> int | None:
    if p not in _URGENCY_RANK or g not in _URGENCY_RANK:
        return None
    return abs(_URGENCY_RANK[p] - _URGENCY_RANK[g])


def within_n_accuracy(pred: list[str], gold: list[str], n: int = 1) -> float:
    """Fraction of predictions within n ordinal steps of the gold urgency."""
    if not gold:
        return 0.0
    ok = 0
    for p, g in zip(pred, gold):
        d = urgency_distance(p, g)
        if d is not None and d <= n:
            ok += 1
    return ok / len(gold)
