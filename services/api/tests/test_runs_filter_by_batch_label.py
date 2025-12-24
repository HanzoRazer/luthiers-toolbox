from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


def test_runs_filter_batch_label_finds_parent_batch_artifact(client: TestClient):
    # 1) Create a compare batch
    req = {
        "batch_label": "pytest-batchlabel",
        "session_id": "sess_pytest_batchlabel",
        "candidates": [
            {
                "candidate_id": "c1",
                "label": "candidate 1",
                "design": {"cut_depth_mm": 10.0, "cut_length_mm": 100.0, "material": "maple"},
                "context": {"tool_id": "saw:thin_140", "material_id": "maple", "machine_id": "router_a", "spindle_rpm": 18000, "feed_rate": 800},
            }
        ],
    }
    r = client.post("/api/saw/compare", json=req)
    assert r.status_code == 200, r.text
    parent_id = r.json().get("parent_artifact_id")
    assert parent_id

    # 2) Retrieve parent by batch label (no ID knowledge)
    q = client.get("/api/rmos/runs", params={"batch_label": "pytest-batchlabel", "limit": 10})
    assert q.status_code == 200, q.text
    response_data = q.json()
    
    # Handle both list and paginated response formats
    if isinstance(response_data, dict) and "items" in response_data:
        runs = response_data["items"]
    else:
        runs = response_data
    
    assert isinstance(runs, list)
    assert any((it.get("run_id") == parent_id) for it in runs), f"Parent {parent_id} not found in runs list"

    # 3) Verify filtering by session_id also works
    q2 = client.get("/api/rmos/runs", params={"session_id": "sess_pytest_batchlabel", "limit": 10})
    assert q2.status_code == 200, q2.text
    response_data2 = q2.json()
    
    # Handle both list and paginated response formats
    if isinstance(response_data2, dict) and "items" in response_data2:
        runs2 = response_data2["items"]
    else:
        runs2 = response_data2
    
