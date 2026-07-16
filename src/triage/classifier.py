"""LLM call 1: structured classification with validation + one corrective retry."""

from pydantic import ValidationError

from ..llm_client import chat_json
from ..schemas import Classification, TicketInput
from . import prompts


def classify_ticket(ticket: TicketInput) -> Classification:
    user_msg = prompts.CLASSIFY_USER_TEMPLATE.format(
        subject=ticket.subject, body=ticket.body
    )
    raw = chat_json(prompts.CLASSIFY_SYSTEM, user_msg)
    try:
        return Classification(**raw)
    except ValidationError as e:
        # one corrective retry: show the model its own mistake
        retry_msg = (
            f"{user_msg}\n\nYour previous JSON was invalid: {e}\n"
            "Return a corrected JSON object using ONLY the allowed enum values."
        )
        raw = chat_json(prompts.CLASSIFY_SYSTEM, retry_msg)
        return Classification(**raw)  # if this still fails, let it raise
