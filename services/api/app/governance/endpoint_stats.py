from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from threading import Lock
from typing import Any, Dict, List, Optional, Set, Tuple

from .otel_metrics import otel_increment_endpoint_hit


# ---------------------------------------------------------------------
# Prometheus series cardinality guardrails (H5.3)
# ---------------------------------------------------------------------

_OTHER_LABEL = os.getenv("ENDPOINT_METRICS_OTHER_LABEL", "__other__")


def _get_max_series() -> int:
    """
    Max unique (status, method, path_pattern) series allowed in /metrics.
    Prevents cardinality blowups. Default is conservative.
    """
    try:
        return int(os.getenv("ENDPOINT_METRICS_MAX_SERIES", "2000"))
    except Exception:
        return 2000


# Tracks observed label sets (in-memory, per-process).
# This is sufficient to prevent accidental label explosions in prod.
_SERIES_SEEN: Set[Tuple[str, str, str]] = set()

# Tracks which path_patterns are allowed to appear as-is (bounded).
_PATHPATTERNS_ALLOWED: Set[str] = set()

# Counts how many times we had to collapse to __other__
_OVERFLOW_COUNT = 0


def _coerce_path_pattern_for_metrics(status: str, method: str, path_pattern: str) -> str:
    """
    Ensure path_pattern label does not explode series count.
    Once max series would be exceeded, collapse new patterns to __other__.
    """
    global _OVERFLOW_COUNT

    max_series = _get_max_series()

    pp = (path_pattern or "").strip()
    if not pp:
        pp = "/(unknown)"

    key = (status, method, pp)

    # If already seen, keep as-is
    if key in _SERIES_SEEN:
        return pp

    # If we're under cap, allow this new series
    if len(_SERIES_SEEN) < max_series:
        _SERIES_SEEN.add(key)
        _PATHPATTERNS_ALLOWED.add(pp)
        return pp

    # Over cap: collapse to __other__
    _OVERFLOW_COUNT += 1
    return _OTHER_LABEL


def get_metrics_overflow_count() -> int:
    return int(_OVERFLOW_COUNT)


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

        # Optional OTEL emission (no-op if OTEL not installed / not configured)
        try:
            otel_increment_endpoint_hit(
                status=str(status),
                method=str(method),
                path_pattern=str(path_pattern),
            )
        except Exception:
            pass

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


# =============================================================================
# Prometheus Exposition Format (H5.2)
# =============================================================================

_METRIC_NAME = "ltb_endpoint_hits_total"
_METRIC_INFO_NAME = "ltb_endpoint_stats_info"

_LABEL_SAFE = re.compile(r"[^a-zA-Z0-9_:]")


def _prom_escape(s: str) -> str:
    """Prometheus label value escaping."""
    return s.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def _sanitize_label_key(k: str) -> str:
    """Prometheus label keys must match [a-zA-Z_][a-zA-Z0-9_]*"""
    k = _LABEL_SAFE.sub("_", k)
    if not k:
        return "label"
    if not (k[0].isalpha() or k[0] == "_"):
        k = "_" + k
    return k


def snapshot_prometheus_text() -> str:
    """
    Prometheus exposition format (text).
    Graphs endpoint usage without polling JSON endpoints.

    H5.3: Applies cardinality guardrails - new patterns beyond max series
    are collapsed to __other__ label.
    """
    snap = snapshot()
    counts: List[Dict[str, Any]] = snap.get("counts") or []

    lines: List[str] = []
    lines.append(f"# HELP {_METRIC_NAME} Count of governed endpoint hits by status/method/path_pattern.")
    lines.append(f"# TYPE {_METRIC_NAME} counter")

    for item in counts:
        status_raw = str(item.get("status", ""))
        method_raw = str(item.get("method", ""))
        path_pattern_raw = str(item.get("path_pattern", ""))

        coerced_pp = _coerce_path_pattern_for_metrics(status_raw, method_raw, path_pattern_raw)

        status = _prom_escape(status_raw)
        method = _prom_escape(method_raw)
        path_pattern = _prom_escape(coerced_pp)
        count = int(item.get("count", 0))

        lines.append(
            f'{_METRIC_NAME}{{status="{status}",method="{method}",path_pattern="{path_pattern}"}} {count}'
        )

    # Optional info gauge (so dashboards can confirm exporter is alive)
    lines.append(f"# HELP {_METRIC_INFO_NAME} Static info about the endpoint stats exporter.")
    lines.append(f"# TYPE {_METRIC_INFO_NAME} gauge")
    log_path = _prom_escape(str(snap.get("log_path") or ""))
    lines.append(f'{_METRIC_INFO_NAME}{{log_path="{log_path}"}} 1')

    # Overflow metric: how many observations were collapsed into __other__
    lines.append("# HELP ltb_endpoint_metrics_overflow_total Count of collapsed metrics due to cardinality cap.")
    lines.append("# TYPE ltb_endpoint_metrics_overflow_total counter")
    lines.append(f"ltb_endpoint_metrics_overflow_total {get_metrics_overflow_count()}")

    return "\n".join(lines) + "\n"


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


# =============================================================================
# Shadow Stats Snapshot (H5.4 - Deprecation Budget)
# =============================================================================

def _get_endpoint_stats_path() -> str:
    return os.getenv("ENDPOINT_STATS_PATH", "services/api/data/endpoint_shadow_stats.json")


def write_shadow_stats_snapshot(*, total_hits: int, legacy_hits: int, by_legacy_route: Dict[str, int]) -> None:
    """
    Writes a stable JSON contract used by CI deprecation budget.
    This is intentionally simple and forward-compatible.

    Shape:
    {
      "total_hits": 1234,
      "legacy_hits": 12,
      "by_legacy_route": {"/api/old/x": 7, "/api/old/y": 5},
      "window": {"kind": "since_start"},
      "generated_at_utc": "2025-12-25T00:00:00Z"
    }
    """
    from datetime import datetime, timezone
    from pathlib import Path

    payload = {
        "total_hits": int(total_hits),
        "legacy_hits": int(legacy_hits),
        "by_legacy_route": dict(sorted(by_legacy_route.items(), key=lambda kv: (-kv[1], kv[0]))),
        "window": {"kind": "since_start"},
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    path = Path(_get_endpoint_stats_path())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def compute_shadow_stats_from_counts() -> Dict[str, Any]:
    """
    Compute shadow stats from in-memory counters.
    Returns dict with total_hits, legacy_hits, by_legacy_route.
    """
    with _LOCK:
        counts = dict(_COUNTS)

    total_hits = 0
    legacy_hits = 0
    by_legacy_route: Dict[str, int] = {}

    for (status, method, path_pattern), n in counts.items():
        total_hits += n
        if status == "legacy":
            legacy_hits += n
            route_key = f"{method} {path_pattern}"
            by_legacy_route[route_key] = by_legacy_route.get(route_key, 0) + n

    return {
        "total_hits": total_hits,
        "legacy_hits": legacy_hits,
        "by_legacy_route": by_legacy_route,
    }


def flush_shadow_stats_snapshot() -> None:
    """
    Compute current shadow stats from in-memory counters and write to disk.
    Call this at test session teardown or process shutdown for CI integration.
    """
    stats = compute_shadow_stats_from_counts()
    write_shadow_stats_snapshot(
        total_hits=stats["total_hits"],
        legacy_hits=stats["legacy_hits"],
        by_legacy_route=stats["by_legacy_route"],
    )
