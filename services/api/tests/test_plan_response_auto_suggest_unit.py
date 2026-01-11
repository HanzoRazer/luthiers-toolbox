"""
Unit tests for plan_auto_suggest feature in batch_router.py

Tests the Decision Intelligence auto-suggest block:
- applied_override shown when operator has CHOSEN a tuning decision
- recommended_latest_approved only shown when override is CLEARED
"""

from __future__ import annotations

import os
import pytest


@pytest.mark.unit
def test_plan_auto_suggest_shows_recommended_when_override_cleared(monkeypatch):
    """When override state is CLEARED, recommended_latest_approved should be populated."""
    os.environ["SAW_LAB_APPLY_APPROVED_TUNING_ON_PLAN"] = "false"

    spec = {
        "id": "spec1",
        "payload": {
            "items": [{"part_id": "p1"}],
            "tool_id": "saw:thin_140",
            "batch_label": "b1",
            "session_id": "s1",
        },
    }

    def _fake_get_artifact(_id: str):
        return spec if _id == "spec1" else None

    def _fake_store_artifact(
        kind: str, payload: dict, parent_id=None, session_id=None, **kwargs
    ):
        return "plan1"

    # Latest choose is CLEARED + an approved decision exists
    plan_choose_cleared = {
        "id": "choose_clear_1",
        "kind": "saw_batch_plan_choose",
        "payload": {
            "created_utc": "2026-01-01T00:05:00+00:00",
            "state": "CLEARED",
            "session_id": "s1",
            "batch_label": "b1",
        },
    }
    approved_decision = {
        "id": "dec1",
        "kind": "saw_lab_tuning_decision",
        "payload": {
            "created_utc": "2026-01-01T00:06:00+00:00",
            "state": "APPROVED",
            "tuning": {"rpm_multiplier": 0.92},
        },
    }

    def _fake_list_runs_filtered(**kwargs):
        kind = kwargs.get("kind", "")
        if kind == "saw_batch_plan_choose":
            return {"items": [plan_choose_cleared]}
        elif kind == "saw_lab_tuning_decision":
            return {"items": [approved_decision]}
        return {"items": []}

    monkeypatch.setattr("app.saw_lab.batch_router.get_artifact", _fake_get_artifact)
    monkeypatch.setattr("app.saw_lab.batch_router.store_artifact", _fake_store_artifact)
    monkeypatch.setattr(
        "app.rmos.runs_v2.store.list_runs_filtered", _fake_list_runs_filtered
    )

    from app.saw_lab.batch_router import BatchPlanRequest, create_batch_plan

    resp = create_batch_plan(BatchPlanRequest(batch_spec_artifact_id="spec1"))

    assert resp.batch_plan_artifact_id == "plan1"
    assert resp.plan_auto_suggest is not None
    assert resp.plan_auto_suggest["override_state"] == "CLEARED"
    assert resp.plan_auto_suggest["applied_override"] is None
    assert resp.plan_auto_suggest["recommended_latest_approved"] is not None
    assert (
        resp.plan_auto_suggest["recommended_latest_approved"]["decision_artifact_id"]
        == "dec1"
    )


@pytest.mark.unit
def test_plan_auto_suggest_shows_applied_override_when_chosen(monkeypatch):
    """When override state is CHOSEN, applied_override should be populated and recommended is None."""
    os.environ["SAW_LAB_APPLY_APPROVED_TUNING_ON_PLAN"] = "false"

    spec = {
        "id": "spec1",
        "payload": {
            "items": [{"part_id": "p1"}],
            "tool_id": "saw:thin_140",
            "batch_label": "b1",
            "session_id": "s1",
        },
    }

    def _fake_get_artifact(_id: str):
        return spec if _id == "spec1" else None

    def _fake_store_artifact(
        kind: str, payload: dict, parent_id=None, session_id=None, **kwargs
    ):
        return "plan1"

    plan_choose = {
        "id": "choose1",
        "kind": "saw_batch_plan_choose",
        "payload": {
            "created_utc": "2026-01-01T00:05:00+00:00",
            "state": "CHOSEN",
            "chosen_decision_artifact_id": "dec_choose",
            "tuning": {"rpm_multiplier": 0.90},
            "note": "operator override",
            "session_id": "s1",
            "batch_label": "b1",
        },
    }
    approved_decision = {
        "id": "dec_latest",
        "kind": "saw_lab_tuning_decision",
        "payload": {
            "created_utc": "2026-01-01T00:06:00+00:00",
            "state": "APPROVED",
            "tuning": {"rpm_multiplier": 0.92},
        },
    }

    def _fake_list_runs_filtered(**kwargs):
        kind = kwargs.get("kind", "")
        if kind == "saw_batch_plan_choose":
            return {"items": [plan_choose]}
        elif kind == "saw_lab_tuning_decision":
            return {"items": [approved_decision]}
        return {"items": []}

    monkeypatch.setattr("app.saw_lab.batch_router.get_artifact", _fake_get_artifact)
    monkeypatch.setattr("app.saw_lab.batch_router.store_artifact", _fake_store_artifact)
    monkeypatch.setattr(
        "app.rmos.runs_v2.store.list_runs_filtered", _fake_list_runs_filtered
    )

    from app.saw_lab.batch_router import BatchPlanRequest, create_batch_plan

    resp = create_batch_plan(BatchPlanRequest(batch_spec_artifact_id="spec1"))

    assert resp.plan_auto_suggest is not None
    assert resp.plan_auto_suggest["override_state"] == "CHOSEN"
    assert resp.plan_auto_suggest["applied_override"] is not None
    assert (
        resp.plan_auto_suggest["applied_override"]["decision_artifact_id"]
        == "dec_choose"
    )
    # recommended should be omitted (None) when override is active
    assert resp.plan_auto_suggest["recommended_latest_approved"] is None
