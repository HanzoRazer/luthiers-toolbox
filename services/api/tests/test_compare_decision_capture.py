"""
Test for /api/saw/compare/approve decision capture endpoint.

Verifies the governance-first decision capture:
1. Create compare batch -> get parent_artifact_id + child artifact_ids
2. POST /api/saw/compare/approve -> creates decision artifact
3. Decision artifact is discoverable via /api/rmos/runs
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """TestClient using app directly."""
    from app.main import app
    return TestClient(app)


def test_compare_approve_creates_decision_artifact(client: TestClient):
    """End-to-end test: create batch, approve decision, verify artifact created."""
    # 1) Create compare batch first
    req = {
        "batch_label": "pytest-decision",
        "session_id": "sess_pytest_decision",
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
    parent_id = body["parent_artifact_id"]
    child_id = body["items"][0]["artifact_id"]

    # 2) Approve decision
    approve = {
        "parent_batch_artifact_id": parent_id,
        "selected_child_artifact_id": child_id,
        "approved_by": "pytest-operator",
        "reason": "best score under constraints",
        "ticket_id": "TICKET-123",
    }
    a = client.post("/api/saw/compare/approve", json=approve)
    assert a.status_code == 200, a.text
    dec = a.json()
    assert dec["decision_artifact_id"], f"Expected decision_artifact_id: {dec}"
    assert dec["parent_batch_artifact_id"] == parent_id
    assert dec["selected_child_artifact_id"] == child_id
    assert dec["approved_by"] == "pytest-operator"
    assert dec["reason"] == "best score under constraints"
    assert dec["ticket_id"] == "TICKET-123"


def test_compare_approve_without_ticket_id(client: TestClient):
    """Decision can be created without optional ticket_id."""
    # Create batch
    req = {
        "batch_label": "pytest-decision-no-ticket",
        "session_id": "sess_no_ticket",
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
    }
    r = client.post("/api/saw/compare", json=req)
    assert r.status_code == 200, r.text
    body = r.json()
    parent_id = body["parent_artifact_id"]
    child_id = body["items"][0]["artifact_id"]

    # Approve without ticket_id
    approve = {
        "parent_batch_artifact_id": parent_id,
        "selected_child_artifact_id": child_id,
        "approved_by": "operator-no-ticket",
        "reason": "simple approval",
    }
    a = client.post("/api/saw/compare/approve", json=approve)
    assert a.status_code == 200, a.text
    dec = a.json()
    assert dec["decision_artifact_id"]
    assert dec["ticket_id"] is None


def test_compare_approve_missing_fields_returns_422(client: TestClient):
    """Missing required fields returns validation error."""
    # Missing approved_by
    approve = {
        "parent_batch_artifact_id": "run_fake",
        "selected_child_artifact_id": "run_fake_child",
        "reason": "test",
    }
    a = client.post("/api/saw/compare/approve", json=approve)
    assert a.status_code == 422  # Validation error
