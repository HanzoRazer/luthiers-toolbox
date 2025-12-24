"""
Test for /api/saw/compare/batches alias endpoint.

Verifies the convenience lookup:
1. Create compare batch -> get parent_artifact_id
2. GET /api/saw/compare/batches?batch_label=... -> find parent without knowing ID
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """TestClient using app directly."""
    from app.main import app
    return TestClient(app)


def test_compare_batches_alias_returns_parent_by_label(client: TestClient):
    """Create a compare batch, then retrieve it via the alias endpoint."""
    # 1) Create a compare batch first
    req = {
        "batch_label": "pytest-alias-batches",
        "session_id": "sess_pytest_alias",
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
    parent_id = r.json().get("parent_artifact_id")
    assert parent_id, f"Expected parent_artifact_id in response: {r.json()}"

    # 2) Retrieve via alias endpoint (no artifact ID needed)
    q = client.get(
        "/api/saw/compare/batches",
        params={"batch_label": "pytest-alias-batches", "limit": 25},
    )
    assert q.status_code == 200, q.text
    batches = q.json()
    assert isinstance(batches, list), f"Expected list, got: {batches}"

    # Find the parent in the returned batches
    found_ids = [
        it.get("artifact_id") or it.get("id") or it.get("run_id")
        for it in batches
    ]
    assert parent_id in found_ids, {
        "parent_id": parent_id,
        "returned_ids": found_ids,
        "batches_count": len(batches),
    }


def test_compare_batches_alias_filters_by_session(client: TestClient):
    """Verify session_id filter works on the alias endpoint."""
    # Create a batch with specific session
    req = {
        "batch_label": "pytest-session-filter",
        "session_id": "sess_unique_session_123",
        "candidates": [
            {
                "candidate_id": "c1",
                "label": "candidate 1",
                "design": {
                    "cut_depth_mm": 5.0,
                    "cut_length_mm": 50.0,
                    "material": "walnut",
                },
                "context": {
                    "tool_id": "saw:standard",
                    "material_id": "walnut",
                    "machine_id": "router_b",
                    "spindle_rpm": 16000,
                    "feed_rate": 600,
                },
            }
        ],
    }
    r = client.post("/api/saw/compare", json=req)
    assert r.status_code == 200, r.text
    parent_id = r.json().get("parent_artifact_id")

    # Query by session_id
    q = client.get(
        "/api/saw/compare/batches",
        params={"session_id": "sess_unique_session_123"},
    )
    assert q.status_code == 200, q.text
    batches = q.json()

    found_ids = [
        it.get("artifact_id") or it.get("run_id")
        for it in batches
    ]
    assert parent_id in found_ids
