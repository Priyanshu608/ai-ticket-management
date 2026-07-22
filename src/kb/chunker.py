"""Chunk knowledge-base markdown files.

Strategy (as recommended in DATA_SCHEMA.md):
- split on '---' horizontal rules (major section boundaries)
- attach the nearest preceding heading as section metadata
"""

from pathlib import Path

from .. import config


def _doc_path(md_file: Path, kb_dir: Path) -> str:
    """Stable citation path: relative to the repo root when the file lives
    under it (the normal case), else relative to the kb_dir passed in."""
    for base in (config.ROOT_DIR, kb_dir):
        try:
            return str(md_file.relative_to(base))
        except ValueError:
            continue
    return md_file.name


def chunk_kb(kb_dir: Path = config.KB_DIR) -> list[dict]:
    chunks = []
    for md_file in sorted(kb_dir.rglob("*.md")):
        rel_path = _doc_path(md_file, kb_dir)
        text = md_file.read_text(encoding="utf-8")
        current_heading = md_file.stem
        for raw in text.split("\n---\n"):
            section = raw.strip()
            if not section:
                continue
            # first heading inside this chunk becomes its section label
            for line in section.splitlines():
                if line.startswith("#"):
                    current_heading = line.lstrip("#").strip()
                    break
            chunks.append(
                {
                    "doc_path": rel_path,
                    "section": current_heading,
                    "text": section,
                }
            )
    return chunks
