"""Repair mojibake in model output.

Some models (e.g. gpt-oss-120b) intermittently emit UTF-8 text that was
mis-encoded as Windows-1252 in their training data, so a smart quote (') comes
back as the literal three-character sequence "â€™". The bytes really are those
wrong code points, so the fix is to reverse the mis-encoding:
`encode('cp1252').decode('utf-8')` maps "â€™" -> "'".

This is applied to every string value coming out of the LLM (see
`llm_client.chat_json`), so drafts and briefs are clean in the API JSON and the
CLI alike.
"""

# Telltale byte-pairs that a UTF-8 lead byte produces when mis-decoded as
# cp1252. If none are present, the text is left untouched.
_MOJIBAKE_MARKERS = ("â€", "Ã", "Â", "â\x80")


def fix_mojibake(text: str) -> str:
    """Repair UTF-8-as-cp1252 mojibake, leaving already-correct text unchanged.

    Only strings containing a mojibake marker are touched, and only when the
    cp1252->utf-8 round-trip succeeds strictly -- which happens exactly when the
    text really is mis-encoded UTF-8. Any legitimate string (including one that
    genuinely contains these characters) fails the strict round-trip and is
    returned as-is.
    """
    if not any(marker in text for marker in _MOJIBAKE_MARKERS):
        return text
    try:
        repaired = text.encode("cp1252", errors="strict").decode("utf-8", errors="strict")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text
    return repaired


def sanitize(obj):
    """Recursively apply fix_mojibake to every string in a JSON-like structure."""
    if isinstance(obj, str):
        return fix_mojibake(obj)
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize(v) for v in obj]
    return obj
