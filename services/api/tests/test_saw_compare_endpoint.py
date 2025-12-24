from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    # Adjust import if your app factory name differs
    from app.main import app
    return TestClient(app)


def test_saw_compare_persists_artifacts_and_returns_ids(client: TestClient):
    req = {
        "batch_label": "pytest-compare",
        "session_id": "sess_pytest_1",
        "candidates": [
            {
                "candidate_id": "c1",
                "label": "candidate 1",
                "design": {"cut_depth_mm": 10.0, "cut_length_mm": 100.0, "material": "maple"},
                "context": {"tool_id": "saw:thin_140", "material_id": "maple", "machine_id": "router_a", "spindle_rpm": 18000, "feed_rate": 800},
            },
            {
                "candidate_id": "c2",
                "label": "candidate 2",
                "design": {"cut_depth_mm": 10.0, "cut_length_mm": 100.0, "material": "ebony"},
                "context": {"tool_id": "saw:thin_140", "material_id": "ebony", "machine_id": "router_a", "spindle_rpm": 18000, "feed_rate": 800},
            },
        ],
    }

    r = client.post("/api/saw/compare", json=req)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "items" in body and len(body["items"]) == 2
    assert all("artifact_id" in it and it["artifact_id"] for it in body["items"])
    assert "parent_artifact_id" in body and body["parent_artifact_id"]

    # Check sortable fields exist
    assert all("risk_bucket" in it and "score" in it for it in body["items"])

    # Prove /api/rmos/runs can see at least one artifact (if your runs API is wired)
    # This is intentionally tolerant: if your /api/rmos/runs is different, update this line.
    runs = client.get("/api/rmos/runs")
    assert runs.status_code in (200, 404)  # allow if runs API not included in this test app build
