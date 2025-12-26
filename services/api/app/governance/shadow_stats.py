from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Dict


@dataclass
class ShadowEndpointStatsSnapshot:
    total_hits: int
    legacy_hits: int
    by_legacy_route: Dict[str, int]
    generated_at_utc: str
    window: Dict[str, str]


_LOCK = Lock()
_TOTAL_HITS = 0
_LEGACY_HITS = 0
_BY_LEGACY_ROUTE: Dict[str, int] = {}


def record_hit(*, is_legacy: bool, route: str) -> None:
    """
    Called by your shadow endpoint middleware/router wrapper (H5.1 writer hook later).
    Safe to call even if not yet used — no side effects besides counters.
    """
    global _TOTAL_HITS, _LEGACY_HITS
    with _LOCK:
        _TOTAL_HITS += 1
        if is_legacy:
            _LEGACY_HITS += 1
            _BY_LEGACY_ROUTE[route] = _BY_LEGACY_ROUTE.get(route, 0) + 1


def snapshot() -> ShadowEndpointStatsSnapshot:
    with _LOCK:
        total = int(_TOTAL_HITS)
        legacy = int(_LEGACY_HITS)
        by_route = dict(_BY_LEGACY_ROUTE)

    return ShadowEndpointStatsSnapshot(
        total_hits=total,
        legacy_hits=legacy,
        by_legacy_route=by_route,
        generated_at_utc=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        window={"kind": "since_process_start"},
    )


def _default_stats_path() -> str:
    return os.getenv("ENDPOINT_STATS_PATH", "services/api/data/endpoint_shadow_stats.json")


def write_shadow_stats_json(path: str | None = None) -> str:
    """
    Writes the current counters to ENDPOINT_STATS_PATH (or provided path).
    Returns the resolved path written to.

    This file is the input to:
      python -m app.governance.cli_deprecation_budget check
    """
    stats_path = path or _default_stats_path()
    p = Path(stats_path)
    p.parent.mkdir(parents=True, exist_ok=True)

    snap = snapshot()
    payload = asdict(snap)

    # Ensure deterministic key order for diffs / CI logs.
    p.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return str(p)


def reset() -> None:
    """For tests only."""
    global _TOTAL_HITS, _LEGACY_HITS, _BY_LEGACY_ROUTE
    with _LOCK:
        _TOTAL_HITS = 0
        _LEGACY_HITS = 0
        _BY_LEGACY_ROUTE = {}
