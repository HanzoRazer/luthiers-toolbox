from __future__ import annotations

import os
import re
from typing import Iterable, List, Set

from .feature_hunt_types import Endpoint

_METHODS = r"(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)"
LINE_RE = re.compile(rf"\b{_METHODS}\b\s+(/[-A-Za-z0-9_{{}}./:]+)")

DEFAULT_TRUTH_MAP_PATH = os.getenv("ENDPOINT_TRUTH_MAP_PATH", "ENDPOINT_TRUTH_MAP.md")


def parse_truth_map_lines(lines: Iterable[str]) -> List[Endpoint]:
    out: List[Endpoint] = []
    for line in lines:
        m = LINE_RE.search(line)
        if not m:
            continue
        method = m.group(1).upper()
        path = m.group(2)
        out.append(Endpoint(method=method, path=path))
    # deterministic unique
    seen: Set[str] = set()
    uniq: List[Endpoint] = []
    for e in out:
        k = e.key()
        if k in seen:
            continue
        seen.add(k)
        uniq.append(e)
    uniq.sort(key=lambda e: (e.path, e.method))
    return uniq


def parse_truth_map_file(path: str = DEFAULT_TRUTH_MAP_PATH) -> List[Endpoint]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return parse_truth_map_lines(f.readlines())
