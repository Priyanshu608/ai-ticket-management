"""LLM call 2: known-issue confirmation + grounded draft response, one call."""

from ..llm_client import chat_json
from ..schemas import Classification, KBMatch, TicketInput
from . import prompts


def match_and_draft(
    ticket: TicketInput,
    classification: Classification,
    kb_chunks: list[dict],
) -> tuple[KBMatch, str]:
    kb_context = (
        "\n\n".join(
            f"[Excerpt {i + 1}] source: {c['doc_path']} | section: {c['section']}\n{c['text'][:1500]}"
            for i, c in enumerate(kb_chunks)
        )
        or "No knowledge-base excerpts found."
    )

    raw = chat_json(
        prompts.RESPOND_SYSTEM,
        prompts.RESPOND_USER_TEMPLATE.format(
            subject=ticket.subject,
            body=ticket.body,
            classification=classification.model_dump_json(),
            kb_context=kb_context,
        ),
    )

    idx = raw.get("matched_chunk")
    matched = (
        kb_chunks[idx - 1]
        if raw.get("is_known_issue")
        and isinstance(idx, int)
        and 1 <= idx <= len(kb_chunks)
        else None
    )
    kb_match = KBMatch(
        is_known_issue=matched is not None,
        doc_path=matched["doc_path"] if matched else None,
        section=matched["section"] if matched else None,
        match_score=matched["score"] if matched else None,
    )
    return kb_match, raw.get("draft_response", "")
