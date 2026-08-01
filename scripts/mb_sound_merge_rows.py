#!/usr/bin/env python3
"""Merge staging JSONL rows into mb_sound_panels.json.

  python scripts/mb_sound_merge_rows.py \\
    --rows docs/reference/mb-sound/staging/rows.jsonl
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROWS = ROOT / "docs" / "reference" / "mb-sound" / "staging" / "rows.jsonl"
DEFAULT_OUT = (
    ROOT
    / "services"
    / "api"
    / "app"
    / "data_registry"
    / "system"
    / "materials"
    / "panel_acoustic"
    / "mb_sound_panels.json"
)

REQUIRED_TOP = ("id", "record_kind", "vendor", "product_line", "provenance")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.is_file() or path.stat().st_size == 0:
        return rows
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{i}: invalid JSON — {exc}") from exc
        if not isinstance(obj, dict):
            raise SystemExit(f"{path}:{i}: expected object")
        rows.append(obj)
    return rows


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rows", type=Path, default=DEFAULT_ROWS)
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    p.add_argument("--replace", action="store_true", help="Replace panels instead of merge-by-id")
    args = p.parse_args(argv)

    new_rows = load_jsonl(args.rows)
    for row in new_rows:
        for key in REQUIRED_TOP:
            if key not in row:
                raise SystemExit(f"row {row.get('id')!r} missing required key {key!r}")

    if args.out.is_file():
        corpus = json.loads(args.out.read_text(encoding="utf-8"))
    else:
        corpus = {"_meta": {}, "panels": []}

    if args.replace:
        panels = new_rows
    else:
        by_id = {p["id"]: p for p in corpus.get("panels", []) if "id" in p}
        for row in new_rows:
            by_id[row["id"]] = row
        panels = sorted(by_id.values(), key=lambda r: r["id"])

    meta = corpus.get("_meta") or {}
    meta["panel_count"] = len(panels)
    meta["status"] = "extracted" if panels else "scaffold — no panels extracted yet"
    corpus["_meta"] = meta
    corpus["panels"] = panels

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(corpus, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(panels)} panels → {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
