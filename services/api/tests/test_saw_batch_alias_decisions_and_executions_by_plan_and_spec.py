from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import create_app
    return TestClient(create_app())


def test_aliases_by_plan_and_spec_return_expected_items(client: TestClient):
    # Spec
    spec = client.post(
        "/api/saw/batch/spec",
        json={
            "batch_label": "pytest-alias-by-plan-spec",
            "session_id": "sess_pytest_alias_by_plan_spec",
            "tool_id": "saw:thin_140",
            "items": [
                {"part_id": "p1", "qty": 1, "material_id": "maple", "thickness_mm": 6.0, "length_mm": 300.0, "width_mm": 30.0},
                {"part_id": "p2", "qty": 1, "material_id": "ebony", "thickness_mm": 6.0, "length_mm": 200.0, "width_mm": 20.0},
            ],
        },
    )
    assert spec.status_code == 200, spec.text
    spec_id = spec.json()["batch_spec_artifact_id"]

    # Plan
    plan = client.post("/api/saw/batch/plan", json={"batch_spec_artifact_id": spec_id})
    assert plan.status_code == 200, plan.text
    plan_body = plan.json()
    plan_id = plan_body["batch_plan_artifact_id"]

    setup_order = [s["setup_key"] for s in plan_body["setups"]]
    op_order = [op["op_id"] for s in plan_body["setups"] for op in s["ops"]]
    assert setup_order and op_order

    # Decision
    approve = client.post(
        "/api/saw/batch/approve",
        json={
            "batch_plan_artifact_id": plan_id,
            "approved_by": "pytest",
            "reason": "alias by plan/spec test",
            "setup_order": setup_order,
            "op_order": op_order,
        },
    )
    assert approve.status_code == 200, approve.text
    decision_id = approve.json()["batch_decision_artifact_id"]

    # Execution
    exec_res = client.post("/api/saw/batch/toolpaths", json={"batch_decision_artifact_id": decision_id})
    assert exec_res.status_code == 200, exec_res.text
    execution_id = exec_res.json()["batch_execution_artifact_id"]

    # Decisions by plan
    d_by_plan = client.get("/api/saw/batch/decisions/by-plan", params={"batch_plan_artifact_id": plan_id, "limit": 50})
    assert d_by_plan.status_code == 200, d_by_plan.text
    assert any((it.get("artifact_id") == decision_id or it.get("id") == decision_id) for it in d_by_plan.json())

    # Decisions by spec
    d_by_spec = client.get("/api/saw/batch/decisions/by-spec", params={"batch_spec_artifact_id": spec_id, "limit": 50})
    assert d_by_spec.status_code == 200, d_by_spec.text
    assert any((it.get("artifact_id") == decision_id or it.get("id") == decision_id) for it in d_by_spec.json())

    # Executions by plan
    e_by_plan = client.get("/api/saw/batch/executions/by-plan", params={"batch_plan_artifact_id": plan_id, "limit": 50})
    assert e_by_plan.status_code == 200, e_by_plan.text
    assert any((it.get("artifact_id") == execution_id or it.get("id") == execution_id) for it in e_by_plan.json())

    # Executions by spec
    e_by_spec = client.get("/api/saw/batch/executions/by-spec", params={"batch_spec_artifact_id": spec_id, "limit": 50})
    assert e_by_spec.status_code == 200, e_by_spec.text
    assert any((it.get("artifact_id") == execution_id or it.get("id") == execution_id) for it in e_by_spec.json())
