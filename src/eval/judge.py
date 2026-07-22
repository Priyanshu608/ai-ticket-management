"""LLM-as-judge for the parts of triage with no ground-truth labels: the draft
response and the KB match.

Ground truth covers classification, but a draft reply has no gold answer -- so
we score it with a rubric-based LLM judge. To reduce self-preference bias the
judge grades against an explicit rubric and must cite evidence; groundedness
(no invented facts vs the ticket + KB excerpt) is the metric that matters most
for a support agent, so it is scored separately and hard-capped.

CHANGELOG
---------
judge_v1 (2026-07-22): initial rubric-based judge. Passed only the KB *citation*
    (doc_path :: section), not the excerpt text.
judge_v2 (2026-07-22): pass the matched excerpt's TEXT to the judge. v1 could
    not see the KB content, so it flagged KB-grounded statements as
    hallucinations (e.g. "Sales will respond within 1 business day", which is
    verbatim in billing-and-plans.md) -- a false positive that inflated the
    hallucination rate and understated groundedness. The text is recovered from
    chunk_kb() by (doc_path, section), so no change to the retriever, pipeline,
    or schemas is needed.
"""

from functools import lru_cache

from ..kb.chunker import chunk_kb
from ..llm_client import chat_json
from ..schemas import TriageResult

JUDGE_VERSION = "judge_v2"

# Cap on excerpt text handed to the judge -- comfortably covers a KB section and
# keeps the judge prompt bounded (the responder itself sees the first 1500).
_MAX_KB_CHARS = 2000


@lru_cache(maxsize=1)
def _kb_text_index() -> dict:
    """{(doc_path, section): text} built once from the KB.

    Sections can repeat within a doc (a chunk with no heading inherits the
    previous one), so texts sharing a key are joined -- this never drops the
    grounding text, at worst it gives the judge slightly more context.
    """
    idx: dict = {}
    for c in chunk_kb():
        idx.setdefault((c["doc_path"], c["section"]), []).append(c["text"])
    return {k: "\n\n".join(v) for k, v in idx.items()}


def _matched_kb_text(result: TriageResult) -> str:
    """The actual KB text the draft was allowed to ground on, or a no-match note.

    Groundedness is judged against the ticket + this text. When nothing matched,
    the draft must be grounded in the ticket alone, so we say so explicitly.
    """
    m = result.kb_match
    if not (m.is_known_issue and m.doc_path):
        return "(no KB excerpt matched -- judge groundedness against the ticket alone)"
    text = _kb_text_index().get((m.doc_path, m.section))
    if not text:  # citation didn't resolve to text; fall back to the citation
        return f"{m.doc_path} :: {m.section}"
    return f"Source: {m.doc_path} :: {m.section}\n{text[:_MAX_KB_CHARS]}"

_JUDGE_SYSTEM = """You are a strict QA reviewer scoring a support agent's DRAFT first-response to a customer ticket. You are given the ticket, the full text of the knowledge-base (KB) excerpt the system matched (if any), and the draft.

A claim is "supported" if it appears in, or directly follows from, the ticket or the KB excerpt text below. Verify each claim against that text -- do not rely on your own product knowledge, and do not flag a statement as invented if it is actually present in the excerpt (e.g. a response time or step written in the KB is grounded, not a hallucination).

Score on a 1-5 integer scale for each dimension and respond ONLY with a JSON object:
- "groundedness": 5 = every claim is supported by the ticket or the KB excerpt text; 1 = invents product behaviour, fixes, dates, or promises not present in the inputs.
- "relevance": 5 = directly addresses the specific issue the customer raised; 1 = generic or off-topic.
- "actionability": 5 = gives the customer a concrete next step or a specific diagnostic request; 1 = no useful next step.
- "tone": 5 = professional and empathetic; 1 = curt, robotic, or inappropriate.
- "hallucinated": true if the draft states any fact/fix/commitment not supported by the ticket or KB excerpt text, else false.
- "rationale": one sentence citing the most important evidence for the groundedness score.

Be conservative about genuine inventions: if the draft promises a deadline or a fix that is NOT in the excerpt text, groundedness is at most 2 and hallucinated is true. But if the excerpt text contains the claim, it is grounded -- score it accordingly."""

_JUDGE_USER = """Ticket subject: {subject}
Ticket body:
{body}

Matched KB excerpt:
{kb}

Draft response:
{draft}"""


def judge_response(
    subject: str, body: str, result: TriageResult
) -> dict:
    kb = _matched_kb_text(result)
    raw = chat_json(
        _JUDGE_SYSTEM,
        _JUDGE_USER.format(subject=subject, body=body, kb=kb, draft=result.draft_response),
    )

    def _int(key: str) -> int:
        try:
            return max(1, min(5, int(raw.get(key, 0))))
        except (TypeError, ValueError):
            return 0

    return {
        "groundedness": _int("groundedness"),
        "relevance": _int("relevance"),
        "actionability": _int("actionability"),
        "tone": _int("tone"),
        "hallucinated": bool(raw.get("hallucinated", False)),
        "rationale": str(raw.get("rationale", "")).strip(),
        "judge_version": JUDGE_VERSION,
    }


def aggregate(scores: list[dict]) -> dict:
    if not scores:
        return {}
    dims = ["groundedness", "relevance", "actionability", "tone"]
    out = {
        d: round(sum(s[d] for s in scores) / len(scores), 2) for d in dims
    }
    out["hallucination_rate"] = round(
        sum(1 for s in scores if s["hallucinated"]) / len(scores), 3
    )
    out["n"] = len(scores)
    return out
