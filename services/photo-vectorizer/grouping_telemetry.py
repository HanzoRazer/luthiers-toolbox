"""
Grouping fallback telemetry (PR-2 Safe Remediation Lane).

Instrumentation only — does not change isolation or grouping algorithms.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_LOG_KEY = "GROUPING_FALLBACK"


@dataclass
class GroupingTelemetryCounters:
    grouping_fallback_total: int = 0
    grouping_fallback_by_reason: Dict[str, int] = field(
        default_factory=lambda: defaultdict(int)
    )


_COUNTERS = GroupingTelemetryCounters()


def record_grouping_fallback(
    *,
    reason: str,
    group_count: int = 0,
    source: str = "edge_to_dxf",
) -> None:
    """Increment counters and emit structured log line for aggregation."""
    normalized = (reason or "unknown").strip()[:120]
    _COUNTERS.grouping_fallback_total += 1
    _COUNTERS.grouping_fallback_by_reason[normalized] += 1
    logger.warning(
        "%s | reason=%s | group_count=%s | source=%s",
        _LOG_KEY,
        normalized,
        group_count,
        source,
    )


def build_topology_provenance(
    grouping: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """API-facing provenance block (not debug-only)."""
    if not grouping:
        return {
            "grouping_fallback_used": False,
            "grouping_fallback_reason": None,
            "grouping_algorithm": "legacy_isolation",
        }
    fallback = bool(grouping.get("grouping_fallback_used", False))
    reason = grouping.get("fallback_reason") if fallback else None
    return {
        "grouping_fallback_used": fallback,
        "grouping_fallback_reason": reason,
        "grouping_algorithm": "legacy_isolation" if fallback else "primary",
        "group_count": grouping.get("group_count", 0),
    }


def get_grouping_telemetry_snapshot() -> Dict[str, Any]:
    """In-process counters for tests and optional metrics endpoints."""
    return {
        "grouping_fallback_total": _COUNTERS.grouping_fallback_total,
        "grouping_fallback_by_reason": dict(_COUNTERS.grouping_fallback_by_reason),
    }


def reset_grouping_telemetry_for_tests() -> None:
    """Test helper only."""
    _COUNTERS.grouping_fallback_total = 0
    _COUNTERS.grouping_fallback_by_reason.clear()
