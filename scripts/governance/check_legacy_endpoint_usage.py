#!/usr/bin/env python3
"""
Legacy Endpoint Usage Gate

Scans the repo for usages of endpoints marked deprecated=true in:
  services/api/app/data/endpoint_truth.json

Primary use:
  - Prevent new legacy endpoint usage from creeping into the frontend SDK/client.
  - Keep migration measurable with a budget (default 10).

Defaults:
  - Scans: packages/client/src, packages/client/tests, packages/sdk, services/api
  - Budget: 10 (env LEGACY_USAGE_BUDGET)
  - Truth file: services/api/app/data/endpoint_truth.json

Env:
  LEGACY_USAGE_BUDGET=10
  ENDPOINT_TRUTH_FILE=services/api/app/data/endpoint_truth.json
  LEGACY_SCAN_PATHS=comma-separated paths (optional)
  LEGACY_IGNORE_GLOBS=comma-separated globs to ignore (optional)

Exit:
  0 if usages <= budget
  1 if usages > budget
  2 on config error
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


DEFAULT_SCAN_PATHS = [
    "packages/client/src",
    "packages/client/tests",
    "packages/sdk",
    "services/api",
]


def _csv(name: str, default: Sequence[str]) -> List[str]:
    v = os.getenv(name)
    if not v:
        return list(default)
    return [x.strip() for x in v.split(",") if x.strip()]


def _int(name: str, default: int) -> int:
    v = os.getenv(name)
    if not v:
        return default
    try:
        return int(v)
    except ValueError:
        raise SystemExit(f"Invalid int for {name}: {v!r}")


def _read_truth(path: Path) -> Dict:
    if not path.exists():
        raise SystemExit(f"Truth file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _deprecated_paths(truth: Dict) -> List[Tuple[str, Optional[str]]]:
    routes = truth.get("routes")
    if not isinstance(routes, list):
        raise SystemExit("Truth file missing 'routes' list")
    out: List[Tuple[str, Optional[str]]] = []
    for r in routes:
        if not isinstance(r, dict):
            continue
        if r.get("deprecated") is True:
            p = r.get("path")
            if not isinstance(p, str) or not p.startswith("/"):
                continue
            succ = r.get("successor")
            succ = succ if isinstance(succ, str) else None
            out.append((p, succ))
    # Prefer longer paths first (avoid counting /api/foo inside /api/foo/bar twice)
    out.sort(key=lambda x: len(x[0]), reverse=True)
    return out


def _should_ignore(path: Path, ignore_globs: Sequence[str]) -> bool:
    s = str(path).replace("\\", "/")
    for g in ignore_globs:
        if fnmatch.fnmatch(s, g):
            return True
    return False


@dataclass(frozen=True)
class Hit:
    file: str
    line: int
    legacy_path: str
    successor: Optional[str]
    excerpt: str


def _iter_files(root: Path) -> Iterable[Path]:
    if root.is_file():
        yield root
        return
    if not root.exists():
        return
    for p in root.rglob("*"):
        if p.is_file():
            yield p


def _scan_file(path: Path, legacy: List[Tuple[str, Optional[str]]]) -> List[Hit]:
    # Only scan text-like files to keep it fast/noisy-proof
    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".7z", ".exe", ".dll"}:
        return []
    try:
        txt = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []

    hits: List[Hit] = []
    lines = txt.splitlines()

    for i, line in enumerate(lines, start=1):
        # quick prefilter
        if "/api/" not in line and "/meta/" not in line and "/art" not in line and "/cam" not in line and "/rmos" not in line:
            continue
        for legacy_path, succ in legacy:
            if legacy_path in line:
                excerpt = line.strip()
                hits.append(
                    Hit(
                        file=str(path).replace("\\", "/"),
                        line=i,
                        legacy_path=legacy_path,
                        successor=succ,
                        excerpt=excerpt[:240],
                    )
                )
    return hits


def main() -> int:
    truth_file = Path(os.getenv("ENDPOINT_TRUTH_FILE", "services/api/app/data/endpoint_truth.json"))
    budget = _int("LEGACY_USAGE_BUDGET", 10)
    scan_paths = _csv("LEGACY_SCAN_PATHS", DEFAULT_SCAN_PATHS)
    ignore_globs = _csv(
        "LEGACY_IGNORE_GLOBS",
        [
            "**/node_modules/**",
            "**/.git/**",
            "**/dist/**",
            "**/build/**",
            "**/.venv/**",
            "**/__pycache__/**",
        ],
    )

    truth = _read_truth(truth_file)
    legacy = _deprecated_paths(truth)
    if not legacy:
        print("✅ No deprecated=true routes in truth file — nothing to scan.")
        return 0

    all_hits: List[Hit] = []
    for sp in scan_paths:
        root = Path(sp)
        for f in _iter_files(root):
            if _should_ignore(f, ignore_globs):
                continue
            all_hits.extend(_scan_file(f, legacy))

    # Deduplicate identical hits (same file/line/path)
    uniq: Dict[Tuple[str, int, str], Hit] = {}
    for h in all_hits:
        uniq[(h.file, h.line, h.legacy_path)] = h
    hits = list(uniq.values())

    # Group summary
    by_path: Dict[str, int] = {}
    for h in hits:
        by_path[h.legacy_path] = by_path.get(h.legacy_path, 0) + 1

    print("--- Legacy Endpoint Usage Gate ---")
    print(f"Truth file: {truth_file}")
    print(f"Deprecated endpoints in truth: {len(legacy)}")
    print(f"Scan paths: {scan_paths}")
    print(f"Budget: {budget}")
    print(f"Found hits: {len(hits)}")

    if hits:
        print("\nTop legacy endpoints hit:")
        for p, n in sorted(by_path.items(), key=lambda x: x[1], reverse=True)[:25]:
            print(f"  - {p}: {n}")

        print("\nHits (file:line legacy -> successor):")
        for h in sorted(hits, key=lambda x: (x.legacy_path, x.file, x.line))[:200]:
            succ = f" -> {h.successor}" if h.successor else ""
            print(f"  - {h.file}:{h.line}  {h.legacy_path}{succ}")
            print(f"      {h.excerpt}")

        if len(hits) > 200:
            print(f"\n… truncated (showing first 200 of {len(hits)} hits)")

    if len(hits) > budget:
        print(f"\n❌ FAIL: legacy endpoint usages {len(hits)} exceed budget {budget}.")
        print("Fix by migrating callers to successors listed in endpoint_truth.json,")
        print("or temporarily raise LEGACY_USAGE_BUDGET (not recommended long-term).")
        return 1

    print("\n✅ PASS: legacy endpoint usage within budget.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
