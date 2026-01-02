from __future__ import annotations

import pytest


def test_runs_filter_parent_batch_decision_artifact_id(client):
    # Create a full batch execution (spec -> plan -> approve -> toolpaths)
    spec = client.post(
        "/api/saw/batch/spec",
        json={
            "batch_label": "pytest-runs-parent-decision",
            "session_id": "sess_pytest_runs_parent_decision",
            "tool_id": "saw:thin_140",
            "items": [
                {"part_id": "p1", "qty": 1, "material_id": "maple", "thickness_mm": 6.0, "length_mm": 300.0, "width_mm": 30.0},
            ],
        },
    )
    assert spec.status_code == 200, spec.text
    spec_id = spec.json()["batch_spec_artifact_id"]

    plan = client.post("/api/saw/batch/plan", json={"batch_spec_artifact_id": spec_id})
    assert plan.status_code == 200, plan.text
    plan_body = plan.json()
    plan_id = plan_body["batch_plan_artifact_id"]

    setup_order = [s["setup_key"] for s in plan_body["setups"]]
    op_order = [op["op_id"] for s in plan_body["setups"] for op in s["ops"]]

    approve = client.post(
        "/api/saw/batch/approve",
        json={
            "batch_plan_artifact_id": plan_id,
            "approved_by": "pytest",
            "reason": "runs filter test",
            "setup_order": setup_order,
            "op_order": op_order,
        },
    )
    assert approve.status_code == 200, approve.text
    decision_id = approve.json()["batch_decision_artifact_id"]

    exec_res = client.post("/api/saw/batch/toolpaths", json={"batch_decision_artifact_id": decision_id})
    assert exec_res.status_code == 200, exec_res.text
    execution_id = exec_res.json()["batch_execution_artifact_id"]

    # Retrieve via /api/saw/batch/executions/by-decision using the parent filter
    runs = client.get(
        "/api/saw/batch/executions/by-decision",
        params={
            "batch_decision_artifact_id": decision_id,
            "limit": 50,
        },
    )
    assert runs.status_code == 200, runs.text
    items = runs.json()

    assert isinstance(items, list)
    assert any((it.get("artifact_id") == execution_id or it.get("id") == execution_id) for it in items)
