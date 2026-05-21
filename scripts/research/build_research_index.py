#!/usr/bin/env python3
"""
Build a deterministic JSON index from docs/research/*.md.

Research Wave 1A — institutional snapshot; markdown remains source of truth.

Usage:
    python scripts/research/build_research_index.py

Output:
    reports/research/research_index.json
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RESEARCH_DIR = REPO_ROOT / "docs" / "research"
OUTPUT_PATH = REPO_ROOT / "reports" / "research" / "research_index.json"

HEADING_RE = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def parse_markdown(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    headings = [
        {"level": len(m.group(1)), "title": m.group(2).strip()}
        for m in HEADING_RE.finditer(text)
    ]
    links = sorted(
        [
            {"label": m.group(1), "target": m.group(2)}
            for m in LINK_RE.finditer(text)
            if not m.group(2).startswith("http")
        ],
        key=lambda x: (x["target"], x["label"]),
    )
    return {
        "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "headings": headings,
        "internal_links": links,
        "line_count": len(text.splitlines()),
    }


def main() -> int:
    if not RESEARCH_DIR.is_dir():
        print(f"Missing {RESEARCH_DIR}", flush=True)
        return 1

    docs = sorted(RESEARCH_DIR.glob("*.md"), key=lambda p: p.name.lower())
    documents = [parse_markdown(p) for p in docs]
    index = {
        "schema_version": 1,
        "research_dir": "docs/research",
        "document_count": len(documents),
        "documents": documents,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(index, indent=2, sort_keys=True) + "\n"
    OUTPUT_PATH.write_text(payload, encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH} ({index['document_count']} documents)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
