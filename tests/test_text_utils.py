"""Unit tests for mojibake repair on LLM output.

Literals use explicit \\u escapes so the tests don't depend on how the source
file or console is encoded. The mojibake sequences repair to *curly* Unicode
punctuation (U+2019 ', U+2014 —, U+201C/U+201D " "), not ASCII lookalikes.
"""

from src.text_utils import fix_mojibake, sanitize

RSQUO = "’"   # ' right single quote
EMDASH = "—"  # — em dash
LDQUO = "“"   # " left double quote


def _corrupt(text: str) -> str:
    """Reproduce the real-world corruption: UTF-8 bytes mis-read as cp1252."""
    return text.encode("utf-8").decode("cp1252")


def test_repairs_smart_quote_mojibake():
    garbled = _corrupt(f"I{RSQUO}m sorry you{RSQUO}re locked out")
    assert garbled != f"I{RSQUO}m sorry you{RSQUO}re locked out"  # corruption happened
    assert fix_mojibake(garbled) == f"I{RSQUO}m sorry you{RSQUO}re locked out"


def test_repairs_the_exact_observed_string():
    # the literal mojibake seen in the /triage API response
    assert fix_mojibake("Iâ€™m") == f"I{RSQUO}m"


def test_repairs_em_dash_mojibake():
    assert fix_mojibake(_corrupt(f"here {EMDASH} we go")) == f"here {EMDASH} we go"


def test_repairs_left_double_quote_mojibake():
    # U+201C (left ") corrupts cleanly via cp1252 (unlike U+201D, whose third
    # byte 0x9D is an undefined cp1252 slot -- an ambiguous edge we don't test).
    assert fix_mojibake(_corrupt(f"say {LDQUO}hi")) == f"say {LDQUO}hi"


def test_clean_ascii_is_unchanged():
    text = "Hi there, please restart the connector."
    assert fix_mojibake(text) is text  # no marker -> returned as-is, no copy


def test_correct_unicode_is_preserved():
    # already-correct curly punctuation must not be mangled
    text = f"I{RSQUO}m sorry {EMDASH} here{RSQUO}s the fix"
    assert fix_mojibake(text) == text


def test_marker_present_but_not_decodable_is_left_alone():
    # a marker byte-pair but not valid mis-encoded UTF-8 -> strict round-trip
    # fails -> original returned unchanged
    text = "\xc3 plus a lone tail"  # "Ã" with no valid continuation byte
    assert fix_mojibake(text) == text


def test_sanitize_recurses_through_nested_structure():
    payload = {
        "draft_response": _corrupt(f"We{RSQUO}ll fix it"),
        "steps": [_corrupt(f"don{RSQUO}t panic"), "restart"],
        "score": 5,
        "nested": {"note": _corrupt(f"you{RSQUO}re set")},
    }
    out = sanitize(payload)
    assert out["draft_response"] == f"We{RSQUO}ll fix it"
    assert out["steps"] == [f"don{RSQUO}t panic", "restart"]
    assert out["score"] == 5
    assert out["nested"]["note"] == f"you{RSQUO}re set"
