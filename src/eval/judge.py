"""LLM-as-judge for the parts of triage with no ground-truth labels: the draft
response and the KB match.

Ground truth covers classification, but a draft reply has no gold answer -- so
we score it with a rubric-based LLM judge. To reduce self-preference bias the
judge grades against an explicit rubric and must cite evidence; groundedness
(no invented facts vs the ticket + KB excerpt) is the metric that matters most
for a support agent, so it is scored separately and hard-capped.
"""

from ..llm_client import chat_json
from ..schemas import TriageResult

JUDGE_VERSION = "judge_v1"

_JUDGE_SYSTEM = """You are a strict QA reviewer scoring a support agent's DRAFT first-response to a customer ticket. You are given the ticket, the knowledge-base excerpt the system matched (if any), and the draft.

Score on a 1-5 integer scale for each dimension and respond ONLY with a JSON object:
- "groundedness": 5 = every claim is supported by the ticket or the KB excerpt; 1 = invents product behaviour, fixes, dates, or promises not present in the inputs.
- "relevance": 5 = directly addresses the specific issue the customer raised; 1 = generic or off-topic.
- "actionability": 5 = gives the customer a concrete next step or a specific diagnostic request; 1 = no useful next step.
- "tone": 5 = professional and empathetic; 1 = curt, robotic, or inappropriate.
- "hallucinated": true if the draft states any fact/fix/commitment not supported by the ticket or KB excerpt, else false.
- "rationale": one sentence citing the most important evidence for the groundedness score.

Be conservative: if the draft promises a resolution deadline or invents a fix not in the excerpt, groundedness is at most 2 and hallucinated is true."""

_JUDGE_USER = """Ticket subject: {subject}
Ticket body:
{body}

Matched KB excerpt: {kb}

Draft response:
{draft}"""


def judge_response(
    subject: str, body: str, result: TriageResult
) -> dict:
    kb = "(none matched)"
    if result.kb_match.is_known_issue and result.kb_match.doc_path:
        kb = f"{result.kb_match.doc_path} :: {result.kb_match.section}"
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
