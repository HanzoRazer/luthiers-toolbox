"""
Test: Toolpaths Lookup Alias

Verifies GET /api/saw/compare/toolpaths?decision_artifact_id=... returns
the latest toolpaths artifact for a given decision.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import create_app
    return TestClient(create_app())


def test_toolpaths_lookup_alias_returns_latest_by_decision(client: TestClient):
    # 1) Compare
    r = client.post(
        "/api/saw/compare",
        json={
            "batch_label": "pytest-toolpaths-lookup",
            "session_id": "sess_pytest_toolpaths_lookup",
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

    # 3) Generate toolpaths
    t = client.post("/api/saw/compare/toolpaths", json={"decision_artifact_id": decision_id})
    assert t.status_code == 200, t.text
    toolpaths_id = t.json()["toolpaths_artifact_id"]

    # 4) Lookup latest toolpaths by decision
    g = client.get("/api/saw/compare/toolpaths", params={"decision_artifact_id": decision_id})
    assert g.status_code == 200, g.text
    it = g.json()
    assert (it.get("artifact_id") == toolpaths_id or it.get("id") == toolpaths_id)
    meta = it.get("index_meta") or {}
    assert meta.get("parent_decision_artifact_id") == decision_id
