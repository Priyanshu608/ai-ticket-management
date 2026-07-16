"""Thin Groq wrapper. One place for: JSON mode, temperature/seed,
retries with exponential backoff (handles 429 rate limits + transient errors).
"""

import json
import time

from groq import Groq

from . import config

_client = Groq(api_key=config.GROQ_API_KEY)


def chat_json(system: str, user: str, max_retries: int = 3) -> dict:
    """Call the LLM in JSON mode and return a parsed dict.

    Note: Groq's JSON mode requires the word 'JSON' to appear in the prompt --
    all prompts in prompts.py satisfy this.
    """
    last_err: Exception | None = None
    for attempt in range(max_retries):
        try:
            resp = _client.chat.completions.create(
                model=config.GROQ_MODEL,
                temperature=config.LLM_TEMPERATURE,
                seed=config.LLM_SEED,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            return json.loads(resp.choices[0].message.content)
        except Exception as e:  # 429s, network blips, malformed JSON
            last_err = e
            time.sleep(2**attempt)  # 1s, 2s, 4s
    raise RuntimeError(f"LLM call failed after {max_retries} attempts: {last_err}")
