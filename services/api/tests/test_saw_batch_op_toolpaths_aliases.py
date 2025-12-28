from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import create_app
    return TestClient(create_app())


def test_op_toolpaths_aliases_by_execution_and_by_decision(client: TestClient):
    # Create chain
    spec = client.post(
        "/api/saw/batch/spec",
        json={
            "batch_label": "pytest-op-toolpaths-alias",
            "session_id": "sess_pytest_op_toolpaths_alias",
            "tool_id": "saw:thin_140",
            "items": [
                {"part_id": "p1", "qty": 1, "material_id": "maple", "thickness_mm": 6.0, "length_mm": 300.0, "width_mm": 30.0},
                {"part_id": "p2", "qty": 1, "material_id": "ebony", "thickness_mm": 6.0, "length_mm": 200.0, "width_mm": 20.0},
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
            "reason": "op-toolpaths aliases test",
            "setup_order": setup_order,
            "op_order": op_order,
        },
    )
    assert approve.status_code == 200, approve.text
    decision_id = approve.json()["batch_decision_artifact_id"]

    exec_res = client.post("/api/saw/batch/toolpaths", json={"batch_decision_artifact_id": decision_id})
    assert exec_res.status_code == 200, exec_res.text
    execution_id = exec_res.json()["batch_execution_artifact_id"]

    # By decision: should return some op toolpaths artifacts
    by_dec = client.get("/api/saw/batch/op-toolpaths/by-decision", params={"batch_decision_artifact_id": decision_id, "limit": 200})
    assert by_dec.status_code == 200, by_dec.text
    by_dec_items = by_dec.json()
    assert isinstance(by_dec_items, list) and len(by_dec_items) >= 1
    assert all((it.get("kind") == "saw_batch_op_toolpaths") for it in by_dec_items if isinstance(it, dict))

    # By execution: should return referenced children (each is full artifact)
    by_exec = client.get("/api/saw/batch/op-toolpaths/by-execution", params={"batch_execution_artifact_id": execution_id})
    assert by_exec.status_code == 200, by_exec.text
    by_exec_items = by_exec.json()
    assert isinstance(by_exec_items, list) and len(by_exec_items) >= 1
    assert any((it.get("kind") == "saw_batch_op_toolpaths") for it in by_exec_items if isinstance(it, dict))
