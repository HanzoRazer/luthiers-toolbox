"""PR-2: Grouping fallback telemetry surfaces on extraction provenance."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
PHOTO_VECTORIZER = REPO_ROOT / "services" / "photo-vectorizer"
if str(PHOTO_VECTORIZER) not in sys.path:
    sys.path.insert(0, str(PHOTO_VECTORIZER))


def test_record_grouping_fallback_increments_counters():
    from grouping_telemetry import (
        build_topology_provenance,
        get_grouping_telemetry_snapshot,
        record_grouping_fallback,
        reset_grouping_telemetry_for_tests,
    )

    reset_grouping_telemetry_for_tests()
    record_grouping_fallback(reason="selection_failed", group_count=2, source="test")
    snap = get_grouping_telemetry_snapshot()
    assert snap["grouping_fallback_total"] == 1
    assert snap["grouping_fallback_by_reason"]["selection_failed"] == 1

    prov = build_topology_provenance(
        {
            "grouping_fallback_used": True,
            "fallback_reason": "selection_failed",
            "group_count": 2,
        }
    )
    assert prov["grouping_fallback_used"] is True
    assert prov["grouping_algorithm"] == "legacy_isolation"


def test_build_topology_provenance_happy_path():
    from grouping_telemetry import build_topology_provenance

    prov = build_topology_provenance(
        {"grouping_fallback_used": False, "group_count": 3}
    )
    assert prov["grouping_fallback_used"] is False
    assert prov["grouping_algorithm"] == "primary"


def test_isolate_with_grouping_no_nodes_records_telemetry():
    import edge_to_dxf as etd
    from grouping_telemetry import get_grouping_telemetry_snapshot, reset_grouping_telemetry_for_tests

    reset_grouping_telemetry_for_tests()
    with patch.object(etd, "_isolate_body_contours", return_value=[]):
        _, group_result = etd._isolate_with_grouping([], None, 100, 100)
    assert group_result is not None
    assert group_result.fallback_used is True
    snap = get_grouping_telemetry_snapshot()
    assert snap["grouping_fallback_total"] >= 1
