"""
Tests for the deprecation sunset checker status short-circuit (CI-RED-017).

The checker historically treated a route as "removed" (good) ONLY when its
module file was absent. A route explicitly marked ``status: "removed"`` in the
registry whose module file is *intentionally retained* for a canonical/compat
path therefore fell through to the overdue check and was wrongly flagged as a
blocking violation (the false positive that parked CI-RED-017).

These tests verify both directions of the fix:
  - the gate STILL catches a genuine overdue sunset (true positive intact —
    the fix must not blind the gate);
  - a ``status: "removed"`` route with a retained file is counted as REMOVED,
    not OVERDUE (false positive gone).
"""
from __future__ import annotations

from app.ci import check_deprecation_sunset as cds


def _registry(routes):
    return {"routes": routes}


def test_unmarked_overdue_route_still_flagged(monkeypatch):
    """True-positive guard: an overdue route that is NOT marked removed and
    whose module file still exists must still be flagged OVERDUE."""
    monkeypatch.setattr(cds, "check_module_exists", lambda module: True)
    reg = _registry(
        [
            {
                "id": "legacy-still-live",
                "module": "app.routers.legacy.still_live_router",
                "sunset_date": "2020-01-01",  # long past
            }
        ]
    )

    overdue, upcoming, removed = cds.check_sunsets(reg)

    assert [r["id"] for r in overdue] == ["legacy-still-live"]
    assert removed == []


def test_status_removed_with_retained_file_not_flagged(monkeypatch):
    """False-positive fix: a route explicitly marked status:'removed' whose
    module file is intentionally retained (compat path) is counted as REMOVED,
    not OVERDUE — even though the file still exists and the sunset is past."""
    monkeypatch.setattr(cds, "check_module_exists", lambda module: True)
    reg = _registry(
        [
            {
                "id": "compat-geometry",
                "module": "app.routers.compat.geometry_router",
                "sunset_date": "2020-01-01",  # long past
                "status": "removed",
            }
        ]
    )

    overdue, upcoming, removed = cds.check_sunsets(reg)

    assert [r["id"] for r in removed] == ["compat-geometry"]
    assert overdue == []
