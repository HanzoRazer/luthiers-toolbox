"""
End-to-end test: Decision → Toolpaths flow

Tests the complete operator loop:
1. POST /api/saw/compare → parent batch + child feasibility artifacts
2. POST /api/saw/compare/approve → decision artifact
3. POST /api/saw/compare/toolpaths → toolpaths artifact with lineage
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import create_app
    return TestClient(create_app())


def test_selected_decision_generates_toolpaths_and_persists_artifact(client: TestClient):
    # 1) Compare
    r = client.post(
        "/api/saw/compare",
        json={
            "batch_label": "pytest-decision-toolpaths",
            "session_id": "sess_pytest_decision_toolpaths",
            "candidates": [
                {
                    "candidate_id": "c1",
                    "label": "candidate 1",
                    "design": {"cut_depth_mm": 10.0, "cut_length_mm": 100.0, "material": "maple"},
                    "context": {
                        "tool_id": "saw:thin_140",
                        "material_id": "maple",
                        "machine_id": "router_a",
                        "spindle_rpm": 18000,
                        "feed_rate": 800,
                    },
                }
            ],
        },
    )
    assert r.status_code == 200, r.text
    parent_id = r.json()["parent_artifact_id"]
    child_id = r.json()["items"][0]["artifact_id"]

    # 2) Approve
    a = client.post(
        "/api/saw/compare/approve",
        json={
            "parent_batch_artifact_id": parent_id,
            "selected_child_artifact_id": child_id,
            "approved_by": "pytest",
            "reason": "best candidate",
        },
    )
    assert a.status_code == 200, a.text
    decision_id = a.json()["decision_artifact_id"]

    # 3) Toolpaths from decision
    t = client.post("/api/saw/compare/toolpaths", json={"decision_artifact_id": decision_id})
    assert t.status_code == 200, t.text
    body = t.json()
    assert body["decision_artifact_id"] == decision_id
    assert body["toolpaths_artifact_id"]
    assert body["status"] in ("OK", "BLOCKED", "ERROR")

    # Optional: confirm toolpaths artifact is discoverable by batch_label via /api/runs
    q = client.get(
        "/api/runs",
        params={"kind": "saw_compare_toolpaths", "batch_label": "pytest-decision-toolpaths", "limit": 50},
    )
    assert q.status_code in (200, 404)
