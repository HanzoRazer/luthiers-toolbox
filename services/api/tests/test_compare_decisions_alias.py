"""
Test for /api/saw/compare/decisions alias endpoint.

Mirrors the batches alias test - verifies decision lookup by batch_label/session_id.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """TestClient using app directly."""
    from app.main import app
    return TestClient(app)


def test_compare_decisions_alias_returns_decision_by_label(client: TestClient):
    """End-to-end: create batch, approve decision, retrieve via alias."""
    # 1) Create compare batch
    r = client.post(
        "/api/saw/compare",
        json={
            "batch_label": "pytest-decisions-alias",
            "session_id": "sess_decisions_alias",
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
        },
    )
    assert r.status_code == 200, r.text
    parent_id = r.json()["parent_artifact_id"]
    child_id = r.json()["items"][0]["artifact_id"]

    # 2) Approve decision
    d = client.post(
        "/api/saw/compare/approve",
        json={
            "parent_batch_artifact_id": parent_id,
            "selected_child_artifact_id": child_id,
            "approved_by": "pytest",
            "reason": "best score",
        },
    )
    assert d.status_code == 200, d.text
    decision_id = d.json()["decision_artifact_id"]

    # 3) Retrieve via alias endpoint
    q = client.get(
        "/api/saw/compare/decisions",
        params={"batch_label": "pytest-decisions-alias"},
    )
    assert q.status_code == 200, q.text
    results = q.json()
    assert isinstance(results, list), f"Expected list, got: {results}"

    # Find the decision in results
    found_ids = [
        it.get("artifact_id") or it.get("run_id") or it.get("id")
        for it in results
    ]
    assert decision_id in found_ids, {
        "decision_id": decision_id,
        "found_ids": found_ids,
    }


def test_compare_decisions_alias_filters_by_session(client: TestClient):
    """Verify session_id filter works on the decisions alias."""
    # Create batch with unique session
    r = client.post(
        "/api/saw/compare",
        json={
            "batch_label": "pytest-decisions-session",
            "session_id": "sess_unique_decisions_456",
            "candidates": [
                {
                    "candidate_id": "c1",
                    "label": "candidate 1",
                    "design": {"cut_depth_mm": 5.0, "cut_length_mm": 50.0, "material": "walnut"},
                    "context": {
                        "tool_id": "saw:standard",
                        "material_id": "walnut",
                        "machine_id": "router_b",
                        "spindle_rpm": 16000,
                        "feed_rate": 600,
                    },
                }
            ],
        },
    )
    assert r.status_code == 200, r.text
    parent_id = r.json()["parent_artifact_id"]
    child_id = r.json()["items"][0]["artifact_id"]

    # Approve
    d = client.post(
        "/api/saw/compare/approve",
        json={
            "parent_batch_artifact_id": parent_id,
            "selected_child_artifact_id": child_id,
            "approved_by": "session-tester",
            "reason": "session filter test",
        },
    )
    assert d.status_code == 200, d.text
    decision_id = d.json()["decision_artifact_id"]

    # Query by session_id
    q = client.get(
        "/api/saw/compare/decisions",
        params={"session_id": "sess_unique_decisions_456"},
    )
    assert q.status_code == 200, q.text
    results = q.json()

    found_ids = [it.get("artifact_id") or it.get("run_id") for it in results]
    assert decision_id in found_ids
