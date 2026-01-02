from __future__ import annotations

import pytest


def test_list_by_decision_executions_returns_newest_first_and_includes_execution(client):
    # 1) Spec
    spec = client.post(
        "/api/saw/batch/spec",
        json={
            "batch_label": "pytest-exec-list-by-decision",
            "session_id": "sess_pytest_exec_list_by_decision",
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
            "reason": "generate executions for list-by-decision alias",
            "setup_order": setup_order,
            "op_order": op_order,
        },
    )
    assert approve.status_code == 200, approve.text
    decision_id = approve.json()["batch_decision_artifact_id"]

    # 4) Execute (toolpaths) twice to ensure list has multiple entries
    exec1 = client.post("/api/saw/batch/toolpaths", json={"batch_decision_artifact_id": decision_id})
    assert exec1.status_code == 200, exec1.text
    exec1_id = exec1.json()["batch_execution_artifact_id"]

    exec2 = client.post("/api/saw/batch/toolpaths", json={"batch_decision_artifact_id": decision_id})
    assert exec2.status_code == 200, exec2.text
    exec2_id = exec2.json()["batch_execution_artifact_id"]

    # 5) List-by-decision alias includes both, newest-first best-effort
    lst = client.get(
        "/api/saw/batch/executions/by-decision",
        params={"batch_decision_artifact_id": decision_id, "limit": 50},
    )
    assert lst.status_code == 200, lst.text
    items = lst.json()
    assert isinstance(items, list) and len(items) >= 2

    ids = [(it.get("artifact_id") or it.get("id")) for it in items]
    assert exec1_id in ids
    assert exec2_id in ids

    # Should be newest-first (exec2 created after exec1) if created_utc ordering is present
    if ids[0] and exec2_id in ids:
        assert ids[0] == exec2_id
