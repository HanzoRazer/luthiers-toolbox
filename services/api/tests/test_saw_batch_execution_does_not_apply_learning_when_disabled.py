from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import create_app
    return TestClient(create_app())


def test_batch_execution_stamps_learning_disabled_when_flag_off(client: TestClient, monkeypatch):
    # Learning emission ON (creates events), apply OFF (must not apply)
    monkeypatch.setenv("SAW_LAB_LEARNING_HOOK_ENABLED", "true")
    monkeypatch.setenv("SAW_LAB_APPLY_ACCEPTED_OVERRIDES", "false")

    spec = client.post(
        "/api/saw/batch/spec",
        json={
            "batch_label": "pytest-exec-learn-noapply",
            "session_id": "sess_pytest_exec_learn_noapply",
            "tool_id": "saw:thin_140",
            "items": [
                {"part_id": "p1", "qty": 1, "material_id": "maple", "thickness_mm": 6.0, "length_mm": 300.0, "width_mm": 30.0},
            ],
        },
    )
    assert spec.status_code == 200, spec.text
    plan = client.post("/api/saw/batch/plan", json={"batch_spec_artifact_id": spec.json()["batch_spec_artifact_id"]})
    assert plan.status_code == 200, plan.text
    plan_body = plan.json()
    approve = client.post(
        "/api/saw/batch/approve",
        json={
            "batch_plan_artifact_id": plan_body["batch_plan_artifact_id"],
            "approved_by": "pytest",
            "reason": "exec learning noapply test",
            "setup_order": [s["setup_key"] for s in plan_body["setups"]],
            "op_order": [op["op_id"] for s in plan_body["setups"] for op in s["ops"]],
        },
    )
    assert approve.status_code == 200, approve.text
    decision_id = approve.json()["batch_decision_artifact_id"]

    exec_res = client.post("/api/saw/batch/toolpaths", json={"batch_decision_artifact_id": decision_id})
    assert exec_res.status_code == 200, exec_res.text
    body = exec_res.json()
    assert body["learning"]["apply_enabled"] is False
    # source_count may be nonzero (accepted events may exist), but we MUST NOT apply when disabled.
    stamp = body["learning"]["tuning_stamp"]
    if stamp:
        assert stamp.get("applied") in (False, None)
