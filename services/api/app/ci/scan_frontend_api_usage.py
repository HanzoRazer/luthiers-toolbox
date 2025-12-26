from __future__ import annotations

import os
import re
from typing import Dict, List, Set

API_RE = re.compile(r"""["'`](\/api\/[A-Za-z0-9_\-\/{}:.?=&]+)["'`]""")

DEFAULT_FRONTEND_ROOTS = [
    "packages/client/src",
    "packages/sdk/src",
]


def _iter_files(root: str) -> List[str]:
    out: List[str] = []
    for base, _, files in os.walk(root):
        for fn in files:
            if fn.endswith((".ts", ".tsx", ".js", ".jsx", ".vue")):
                out.append(os.path.join(base, fn))
    out.sort()
    return out


def scan_frontend_api_paths(roots: List[str] | None = None) -> Set[str]:
    roots = roots or DEFAULT_FRONTEND_ROOTS
    paths: Set[str] = set()

    for r in roots:
        if not os.path.isdir(r):
            continue
        for fp in _iter_files(r):
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    text = f.read()
            except Exception:
                continue

            for m in API_RE.finditer(text):
                paths.add(m.group(1))

    return set(sorted(paths))


def summarize_frontend_paths(paths: Set[str]) -> Dict[str, int]:
    """
    Return counts grouped by the first two path segments, e.g.
    /api/rmos/* -> "rmos"
    /api/cam/*  -> "cam"
    """
    out: Dict[str, int] = {}
    for p in paths:
        parts = p.split("/")
        # ["", "api", "rmos", "runs"...]
        key = parts[2] if len(parts) > 2 else "unknown"
        out[key] = out.get(key, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: (-kv[1], kv[0])))
