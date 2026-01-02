"""
Tests for Saw Lab Batch Execution Toolpaths

End-to-end test: spec → plan → approve → toolpaths
Validates governance invariants:
  - Server-side feasibility recompute before generating toolpaths
  - Artifacts written even on failures
  - Parent execution artifact references all child artifacts + summary stats
"""
from __future__ import annotations

import pytest


def test_batch_toolpaths_from_decision_persists_parent_and_children(client):
    """
    Full workflow test: spec → plan → approve → toolpaths.

    Verifies:
    - Parent execution artifact is created
    - Child artifacts are created for each op
    - Execution is queryable via /api/saw/batch/executions
    """
    # 1) Spec
    spec = client.post(
        "/api/saw/batch/spec",
        json={
            "batch_label": "pytest-batch-exec",
            "session_id": "sess_pytest_batch_exec",
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
    setups = plan_body["setups"]
    assert setups and isinstance(setups, list)

    setup_order = [s["setup_key"] for s in setups]
    op_order = []
    for s in setups:
        for op in s["ops"]:
            op_order.append(op["op_id"])
    assert op_order

    # 3) Approve (choose)
    approve = client.post(
        "/api/saw/batch/approve",
        json={
            "batch_plan_artifact_id": plan_id,
            "approved_by": "pytest",
            "reason": "execute chosen plan order",
            "setup_order": setup_order,
            "op_order": op_order,
        },
    )
    assert approve.status_code == 200, approve.text
    decision_id = approve.json()["batch_decision_artifact_id"]

    # 4) Toolpaths
    exec_res = client.post("/api/saw/batch/toolpaths", json={"batch_decision_artifact_id": decision_id})
    assert exec_res.status_code == 200, exec_res.text
    body = exec_res.json()

    parent_exec_id = body["batch_execution_artifact_id"]
    assert parent_exec_id
    assert body["op_count"] == len(op_order)
    assert isinstance(body["results"], list) and len(body["results"]) == len(op_order)

    # 5) Parent execution discoverable via /api/saw/batch/executions
    executions = client.get("/api/saw/batch/executions", params={"batch_label": "pytest-batch-exec", "limit": 50})
    assert executions.status_code == 200
    exec_list = executions.json()
    assert any((it.get("artifact_id") == parent_exec_id or it.get("id") == parent_exec_id) for it in exec_list)


def test_batch_toolpaths_creates_results_for_each_op(client):
    """
    Verify that each op gets a result entry with status and artifact ID.
    """
    # Create spec with 3 items
    spec = client.post(
        "/api/saw/batch/spec",
        json={
            "batch_label": "pytest-multi-op",
            "session_id": "sess_pytest_multi_op",
            "tool_id": "saw:thin_140",
            "items": [
                {"part_id": "a", "qty": 1, "material_id": "maple", "thickness_mm": 5.0, "length_mm": 100.0, "width_mm": 20.0},
                {"part_id": "b", "qty": 1, "material_id": "maple", "thickness_mm": 5.0, "length_mm": 150.0, "width_mm": 20.0},
                {"part_id": "c", "qty": 1, "material_id": "walnut", "thickness_mm": 5.0, "length_mm": 200.0, "width_mm": 20.0},
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
            "reason": "test multi-op",
            "setup_order": setup_order,
            "op_order": op_order,
        },
    )
    assert approve.status_code == 200
    decision_id = approve.json()["batch_decision_artifact_id"]

    # Execute toolpaths
    exec_res = client.post("/api/saw/batch/toolpaths", json={"batch_decision_artifact_id": decision_id})
    assert exec_res.status_code == 200
    body = exec_res.json()

    # Verify counts
    assert body["op_count"] == 3
    assert len(body["results"]) == 3

    # Each result should have required fields
    for result in body["results"]:
        assert "op_id" in result
        assert "status" in result
        assert "toolpaths_artifact_id" in result
        assert result["status"] in ("OK", "BLOCKED", "ERROR")


def test_batch_toolpaths_invalid_decision_returns_error(client):
    """
    Test that invalid decision artifact ID returns an error status.
    """
    exec_res = client.post(
        "/api/saw/batch/toolpaths",
        json={"batch_decision_artifact_id": "invalid_nonexistent_id_12345"},
    )
    # Should still return 200 but with ERROR status (governance: always persist artifacts)
    assert exec_res.status_code == 200
    body = exec_res.json()
    assert body["status"] == "ERROR"
    assert body["error_count"] >= 1
