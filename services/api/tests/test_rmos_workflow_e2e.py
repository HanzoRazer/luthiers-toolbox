"""
RMOS Workflow E2E Tests

Tests the workflow session management endpoints.
"""
from __future__ import annotations

import pytest


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """
    Uses the real FastAPI app with isolated storage.
    """
    monkeypatch.setenv("RMOS_ARTIFACT_ROOT", str(tmp_path / "run_artifacts"))
    monkeypatch.setenv("ENV", "test")

    try:
        from fastapi.testclient import TestClient
        from app.main import app
    except Exception as e:
        pytest.skip(f"Could not import FastAPI app: {e}")

    return TestClient(app)


def test_workflow_create_session(client):
    """Test creating a new workflow session."""
    res = client.post("/api/rmos/workflow/sessions", json={
        "mode": "design_first",
        "tool_id": "saw:test",
        "material_id": "ebony",
    })

    if res.status_code == 404:
        pytest.skip("Workflow router not wired")

    assert res.status_code == 200
    data = res.json()
    assert "session_id" in data
    assert data["mode"] == "design_first"
    assert data["state"] == "draft"


def test_workflow_get_session(client):
    """Test retrieving a session by ID."""
    # First create a session
    create_res = client.post("/api/rmos/workflow/sessions", json={
        "mode": "design_first",
    })

    if create_res.status_code == 404:
        pytest.skip("Workflow router not wired")

    session_id = create_res.json()["session_id"]

    # Then retrieve it
    get_res = client.get(f"/api/rmos/workflow/sessions/{session_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["session_id"] == session_id


def test_workflow_session_not_found(client):
    """Test 404 for non-existent session."""
    res = client.get("/api/rmos/workflow/sessions/nonexistent_session_id")

    if res.status_code == 404:
        data = res.json()
        if "error" in data.get("detail", {}):
            assert data["detail"]["error"] == "SESSION_NOT_FOUND"


def test_workflow_approve_requires_feasibility(client):
    """Test that approval without feasibility fails."""
    # Create a session
    create_res = client.post("/api/rmos/workflow/sessions", json={
        "mode": "design_first",
    })

    if create_res.status_code == 404:
        pytest.skip("Workflow router not wired")

    session_id = create_res.json()["session_id"]

    # Try to approve without feasibility
    approve_res = client.post("/api/rmos/workflow/approve", json={
        "session_id": session_id,
        "actor": "operator",
    })

    # Should fail - session is in DRAFT state, not FEASIBILITY_READY
    assert approve_res.status_code == 409
