from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Set


"""
Fence Baseline Delta Renderer
-----------------------------

Given "base" and "head" baseline JSON files, produces a Markdown report showing:
  - new violations added (should be rare / suspicious)
  - violations removed (good progress)
  - net totals

This is designed to run in CI for governance PRs that update baseline files.

Supported baseline formats:
  Import baseline:
    {"version":1, "imports":[...], "symbols":[...]}
  Pattern baseline:
    {"version":1, "patterns":[...]}
"""


@dataclass(frozen=True)
class Delta:
    title: str
    base_total: int
    head_total: int
    added: List[str]
    removed: List[str]


def _load_json(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_set(obj: Dict, key: str) -> Set[str]:
    vals = obj.get(key, [])
    if not isinstance(vals, list):
        return set()
    return set(str(x) for x in vals)


def _compute_delta(title: str, base: Set[str], head: Set[str]) -> Delta:
    added = sorted(head - base)
    removed = sorted(base - head)
    return Delta(
        title=title,
        base_total=len(base),
        head_total=len(head),
        added=added,
        removed=removed,
    )


def _bullet_block(items: Sequence[str], limit: int) -> str:
    if not items:
        return "_None._\n"
    out: List[str] = []
    shown = items[:limit]
    for s in shown:
        out.append(f"- `{s}`")
    if len(items) > limit:
        out.append(f"- … _({len(items) - limit} more)_")
    return "\n".join(out) + "\n"


def render_markdown(deltas: List[Delta], *, limit: int) -> str:
    lines: List[str] = []
    lines.append("# Fence baseline diff report\n")
    lines.append("This report summarizes changes to fence baselines in this PR.\n")
    lines.append("> **Goal:** baseline changes should be intentional (governance-labeled) and ideally reduce debt.\n")

    for d in deltas:
        net = d.head_total - d.base_total
        net_sign = "+" if net > 0 else ""
        lines.append(f"## {d.title}\n")
        lines.append(f"- Base total: **{d.base_total}**")
        lines.append(f"- Head total: **{d.head_total}**")
        lines.append(f"- Net change: **{net_sign}{net}**\n")

        lines.append("### Added (new violations)\n")
        lines.append(_bullet_block(d.added, limit))

        lines.append("### Removed (resolved violations)\n")
        lines.append(_bullet_block(d.removed, limit))

    return "\n".join(lines).rstrip() + "\n"


def _detect_kind(obj: Dict) -> str:
    if obj.get("version") != 1:
        return "unknown"
    if "patterns" in obj:
        return "patterns"
    if "imports" in obj or "symbols" in obj:
        return "imports"
    return "unknown"


def main() -> int:
    ap = argparse.ArgumentParser(prog="render_fence_baseline_delta.py")
    ap.add_argument("--base-imports", type=str, default=None)
    ap.add_argument("--head-imports", type=str, default=None)
    ap.add_argument("--base-patterns", type=str, default=None)
    ap.add_argument("--head-patterns", type=str, default=None)
    ap.add_argument("--out", type=str, required=True, help="Output markdown path")
    ap.add_argument("--limit", type=int, default=80, help="Max bullet items per section")
    args = ap.parse_args()

    deltas: List[Delta] = []

    if args.base_imports and args.head_imports:
        b = _load_json(Path(args.base_imports))
        h = _load_json(Path(args.head_imports))
        if _detect_kind(b) != "imports" or _detect_kind(h) != "imports":
            raise SystemExit("Invalid imports baseline JSON format")
        deltas.append(
            _compute_delta("Import fences — imports", _as_set(b, "imports"), _as_set(h, "imports"))
        )
        deltas.append(
            _compute_delta("Import fences — symbols", _as_set(b, "symbols"), _as_set(h, "symbols"))
        )

    if args.base_patterns and args.head_patterns:
        b = _load_json(Path(args.base_patterns))
        h = _load_json(Path(args.head_patterns))
        if _detect_kind(b) != "patterns" or _detect_kind(h) != "patterns":
            raise SystemExit("Invalid patterns baseline JSON format")
        deltas.append(
            _compute_delta("Pattern fences", _as_set(b, "patterns"), _as_set(h, "patterns"))
        )

    if not deltas:
        raise SystemExit("No baseline pairs provided")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_markdown(deltas, limit=args.limit), encoding="utf-8")
    print(f"Wrote baseline diff report: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
