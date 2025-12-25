from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class EndpointHit:
    ts_utc: float
    status: str
    method: str
    path_pattern: str
    path_actual: str
    replacement: Optional[str]


_LOCK = Lock()

# Counters keyed by (status, method, path_pattern)
_COUNTS: Dict[Tuple[str, str, str], int] = {}

# Optional rolling hit log buffer (small)
_RECENT: List[EndpointHit] = []
_RECENT_MAX = 200


def _get_stats_log_path() -> Optional[str]:
    """
    Optional append-only JSONL log for endpoint hits.
    Enable via env var:
      ENDPOINT_STATS_LOG_PATH=/path/to/endpoint_hits.jsonl

    If unset, file logging is disabled (in-memory only).
    """
    return os.getenv("ENDPOINT_STATS_LOG_PATH") or None


def record_hit(
    *,
    status: str,
    method: str,
    path_pattern: str,
    path_actual: str,
    replacement: Optional[str],
) -> None:
    """
    Record a governed endpoint hit (legacy/shadow/canonical/internal).
    Designed to be cheap and safe. Never throws.
    """
    try:
        now = time.time()
        key = (status, method, path_pattern)

        with _LOCK:
            _COUNTS[key] = _COUNTS.get(key, 0) + 1

            _RECENT.append(
                EndpointHit(
                    ts_utc=now,
                    status=status,
                    method=method,
                    path_pattern=path_pattern,
                    path_actual=path_actual,
                    replacement=replacement,
                )
            )
            if len(_RECENT) > _RECENT_MAX:
                _RECENT[:] = _RECENT[-_RECENT_MAX:]

        log_path = _get_stats_log_path()
        if log_path:
            _append_jsonl(
                log_path,
                {
                    "ts_utc": now,
                    "status": status,
                    "method": method,
                    "path_pattern": path_pattern,
                    "path_actual": path_actual,
                    "replacement": replacement,
                },
            )
    except Exception:
        # Non-fatal by design
        return


def snapshot() -> Dict[str, Any]:
    """
    Return a snapshot suitable for API response.
    """
    with _LOCK:
        counts = dict(_COUNTS)
        recent = list(_RECENT)

    by_status: Dict[str, int] = {}
    items: List[Dict[str, Any]] = []

    for (status, method, path_pattern), n in sorted(counts.items()):
        by_status[status] = by_status.get(status, 0) + n
        items.append(
            {
                "status": status,
                "method": method,
                "path_pattern": path_pattern,
                "count": n,
            }
        )

    recent_out = [
        {
            "ts_utc": h.ts_utc,
            "status": h.status,
            "method": h.method,
            "path_pattern": h.path_pattern,
            "path_actual": h.path_actual,
            "replacement": h.replacement,
        }
        for h in recent
    ]

    return {
        "totals_by_status": by_status,
        "counts": items,
        "recent": recent_out,
        "log_path": _get_stats_log_path(),
    }


def reset() -> None:
    with _LOCK:
        _COUNTS.clear()
        _RECENT.clear()


def _append_jsonl(path: str, obj: Dict[str, Any]) -> None:
    """
    Append one JSON line. Best-effort only.
    """
    line = json.dumps(obj, separators=(",", ":"), ensure_ascii=False)
    # Ensure parent dir exists if possible
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    except Exception:
        pass
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")
