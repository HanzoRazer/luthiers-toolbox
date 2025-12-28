"""
Tests for Saw Lab Batch Execution Lookup Alias

Tests the convenience endpoint:
  GET /api/saw/batch/execution?batch_decision_artifact_id=...

Returns the latest parent execution artifact for a given decision.
"""
from __future__ import annotations

import pytest


def test_batch_execution_lookup_alias_returns_latest_by_decision(client):
    """
    Full workflow test: spec → plan → approve → toolpaths → lookup.

    Verifies:
    - Lookup alias returns the execution artifact
    - Returned artifact matches the one from toolpaths endpoint
    - index_meta contains parent_batch_decision_artifact_id
    """
    # 1) Spec
    spec = client.post(
        "/api/saw/batch/spec",
        json={
            "batch_label": "pytest-exec-lookup",
            "session_id": "sess_pytest_exec_lookup",
            "tool_id": "saw:thin_140",
            "items": [
                {"part_id": "p1", "qty": 1, "material_id": "maple", "thickness_mm": 6.0, "length_mm": 300.0, "width_mm": 30.0},
                {"part_id": "p2", "qty": 1, "material_id": "ebony", "thickness_mm": 6.0, "length_mm": 200.0, "width_mm": 20.0},
            ],
        },
    )
    assert spec.status_code == 200, spec.text
    spec_id = spec.json()["batch_spec_artifact_id"]

    # 2) Plan
    plan = client.post("/api/saw/batch/plan", json={"batch_spec_artifact_id": spec_id})
    assert plan.status_code == 200, plan.text
    plan_body = plan.json()
    plan_id = plan_body["batch_plan_artifact_id"]

    setup_order = [s["setup_key"] for s in plan_body["setups"]]
    op_order = [op["op_id"] for s in plan_body["setups"] for op in s["ops"]]
    assert setup_order and op_order

    # 3) Approve
    approve = client.post(
        "/api/saw/batch/approve",
        json={
            "batch_plan_artifact_id": plan_id,
            "approved_by": "pytest",
            "reason": "execute and lookup",
            "setup_order": setup_order,
            "op_order": op_order,
        },
    )
    assert approve.status_code == 200, approve.text
    decision_id = approve.json()["batch_decision_artifact_id"]

    # 4) Execute (toolpaths)
    exec_res = client.post("/api/saw/batch/toolpaths", json={"batch_decision_artifact_id": decision_id})
    assert exec_res.status_code == 200, exec_res.text
    execution_id = exec_res.json()["batch_execution_artifact_id"]

    # 5) Lookup alias
    lookup = client.get("/api/saw/batch/execution", params={"batch_decision_artifact_id": decision_id})
    assert lookup.status_code == 200, lookup.text
    it = lookup.json()

    got_id = it.get("artifact_id") or it.get("id")
    assert got_id == execution_id

    meta = it.get("index_meta") or {}
    assert meta.get("parent_batch_decision_artifact_id") == decision_id


def test_batch_execution_lookup_alias_returns_404_for_unknown_decision(client):
    """
    Lookup alias should return 404 if no execution exists for the decision.
    """
    lookup = client.get(
        "/api/saw/batch/execution",
        params={"batch_decision_artifact_id": "nonexistent_decision_abc123"},
    )
    assert lookup.status_code == 404
    assert "No execution artifact found" in lookup.json().get("detail", "")


def test_batch_execution_lookup_returns_correct_metadata(client):
    """
    Verify that the lookup response contains expected metadata fields.
    """
    # Create spec
    spec = client.post(
        "/api/saw/batch/spec",
        json={
            "batch_label": "pytest-meta-check",
            "session_id": "sess_pytest_meta",
            "tool_id": "saw:thin_140",
            "items": [
                {"part_id": "m1", "qty": 1, "material_id": "cherry", "thickness_mm": 4.0, "length_mm": 150.0, "width_mm": 25.0},
            ],
        },
    )
    assert spec.status_code == 200
    spec_id = spec.json()["batch_spec_artifact_id"]

    # Plan
    plan = client.post("/api/saw/batch/plan", json={"batch_spec_artifact_id": spec_id})
    assert plan.status_code == 200
    plan_body = plan.json()
    plan_id = plan_body["batch_plan_artifact_id"]

    setup_order = [s["setup_key"] for s in plan_body["setups"]]
    op_order = [op["op_id"] for s in plan_body["setups"] for op in s["ops"]]

    # Approve
    approve = client.post(
        "/api/saw/batch/approve",
        json={
            "batch_plan_artifact_id": plan_id,
            "approved_by": "pytest",
            "reason": "metadata check",
            "setup_order": setup_order,
            "op_order": op_order,
        },
    )
    assert approve.status_code == 200
    decision_id = approve.json()["batch_decision_artifact_id"]

    # Execute
    exec_res = client.post("/api/saw/batch/toolpaths", json={"batch_decision_artifact_id": decision_id})
    assert exec_res.status_code == 200

    # Lookup
    lookup = client.get("/api/saw/batch/execution", params={"batch_decision_artifact_id": decision_id})
    assert lookup.status_code == 200
    it = lookup.json()

    # Verify metadata fields
    assert it.get("kind") == "saw_batch_execution"
    assert it.get("status") in ("OK", "ERROR")

    meta = it.get("index_meta") or {}
    assert meta.get("batch_label") == "pytest-meta-check"
    assert meta.get("session_id") == "sess_pytest_meta"
    assert meta.get("tool_kind") == "saw_lab"
    assert meta.get("kind_group") == "batch"
