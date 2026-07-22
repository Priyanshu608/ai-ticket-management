"""Unit tests for KB chunking (split on '---', heading metadata)."""

from src.kb.chunker import chunk_kb


def test_splits_on_hr_and_captures_heading(tmp_path):
    (tmp_path / "sub").mkdir()
    doc = tmp_path / "sub" / "widget.md"
    doc.write_text(
        "# Widget Overview\nIntro text.\n"
        "\n---\n"
        "## Error Codes\nERR_TIMEOUT means the connector stalled.\n"
        "\n---\n"
        "## Fixes\nRestart the connector.\n",
        encoding="utf-8",
    )
    # chunk_kb resolves rel paths against config.ROOT_DIR; monkeypatch via arg
    chunks = chunk_kb(tmp_path)
    assert len(chunks) == 3
    sections = [c["section"] for c in chunks]
    assert sections == ["Widget Overview", "Error Codes", "Fixes"]
    assert "ERR_TIMEOUT" in chunks[1]["text"]
    assert all(c["doc_path"].endswith("widget.md") for c in chunks)


def test_empty_sections_skipped(tmp_path):
    doc = tmp_path / "a.md"
    doc.write_text("# Only\ncontent\n\n---\n\n\n---\n", encoding="utf-8")
    chunks = chunk_kb(tmp_path)
    assert len(chunks) == 1
    assert chunks[0]["section"] == "Only"


def test_heading_falls_back_to_filename(tmp_path):
    doc = tmp_path / "noheading.md"
    doc.write_text("just a paragraph with no markdown heading", encoding="utf-8")
    chunks = chunk_kb(tmp_path)
    assert len(chunks) == 1
    assert chunks[0]["section"] == "noheading"
