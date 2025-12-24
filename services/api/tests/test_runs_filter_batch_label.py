"""
Test for batch_label filter on /api/rmos/runs endpoint.

Verifies the operator workflow:
1. Create compare batch -> get parent_artifact_id
2. Query /api/rmos/runs?batch_label=... -> find parent without knowing ID

Part of Bundle #2 - Global deterministic run-attachments isolation.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """TestClient using app directly (not create_app factory)."""
    from app.main import app
    return TestClient(app)


def test_runs_filter_batch_label_finds_parent_batch_artifact(client: TestClient):
    """
    End-to-end test: create a compare batch, then retrieve it by batch_label.

    This proves the operator-friendly lookup path:
    batch_label -> /api/rmos/runs -> parent batch artifact
    """
    # 1) Create a compare batch (creates child artifacts + 1 parent batch artifact)
    req = {
        "batch_label": "pytest-batchlabel",
        "session_id": "sess_pytest_batchlabel",
        "candidates": [
            {
                "candidate_id": "c1",
                "label": "candidate 1",
                "design": {
                    "cut_depth_mm": 10.0,
                    "cut_length_mm": 100.0,
                    "material": "maple",
                },
                "context": {
                    "tool_id": "saw:thin_140",
                    "material_id": "maple",
                    "machine_id": "router_a",
                    "spindle_rpm": 18000,
                    "feed_rate": 800,
                },
            }
        ],
    }
    r = client.post("/api/saw/compare", json=req)
    assert r.status_code == 200, r.text
    body = r.json()
    parent_id = body.get("parent_artifact_id")
    assert parent_id, f"Expected parent_artifact_id in response: {body}"

    # 2) Retrieve parent by batch_label (no artifact ID knowledge required)
    q = client.get(
        "/api/rmos/runs",
        params={
            "batch_label": "pytest-batchlabel",
            "limit": 25,
        },
    )
    assert q.status_code == 200, q.text
    runs = q.json()
    assert isinstance(runs, list), f"Expected list, got: {runs}"

    # Support either key naming: artifact_id, id, or run_id (depends on schema)
    found_ids = []
    for it in runs:
        found_id = it.get("artifact_id") or it.get("id") or it.get("run_id")
        found_ids.append(found_id)

    assert parent_id in found_ids, {
        "parent_id": parent_id,
        "returned_ids": found_ids,
        "runs_count": len(runs),
    }
