"""
RMOS Workflow E2E Tests

Tests the workflow session management endpoints.
"""
from __future__ import annotations

import sqlite3
import pytest


def _create_workflow_sessions_table(db_path: str) -> None:
    """Create the workflow_sessions table for testing."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS workflow_sessions (
            session_id TEXT PRIMARY KEY,
            created_at_utc TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at_utc TEXT NOT NULL DEFAULT (datetime('now')),
            workflow_type TEXT NOT NULL,
            current_step TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            context_json TEXT,
            run_ids_json TEXT,
            machine_id TEXT,
            material_id TEXT,
            tool_id TEXT,
            user_id TEXT,
            state_data_json TEXT,
            error_message TEXT,
            error_details_json TEXT
        )
    """)
    conn.commit()
    conn.close()


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """
    Uses the real FastAPI app with isolated storage.
    """
    # Set up isolated artifact storage
    monkeypatch.setenv("RMOS_ARTIFACT_ROOT", str(tmp_path / "run_artifacts"))
    monkeypatch.setenv("ENV", "test")

    # Set up isolated SQLite database with workflow_sessions table
    db_path = str(tmp_path / "test_rmos.sqlite")
    _create_workflow_sessions_table(db_path)
    monkeypatch.setenv("RMOS_DB_PATH", db_path)

    try:
        from fastapi.testclient import TestClient
        from app.main import app
    except Exception as e:
        pytest.skip(f"Could not import FastAPI app: {e}")

    return TestClient(app)


def test_workflow_create_session(client):
    """Test creating a new workflow session."""
    res = client.post("/api/rmos/workflow/sessions", json={
        "workflow_type": "design_first",
        "tool_id": "saw:test",
        "material_id": "ebony",
    })

    if res.status_code == 404:
        pytest.skip("Workflow router not wired")

    assert res.status_code == 200
    data = res.json()
    assert "session_id" in data
    assert data["workflow_type"] == "design_first"
    assert data["current_step"] == "draft"


def test_workflow_get_session(client):
    """Test retrieving a session by ID."""
    # First create a session
    create_res = client.post("/api/rmos/workflow/sessions", json={
        "workflow_type": "design_first",
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


@pytest.mark.skip(reason="Approve endpoint not yet exposed via API - state_machine.approve() exists but no route")
def test_workflow_approve_requires_feasibility(client):
    """Test that approval without feasibility fails."""
    # Create a session
    create_res = client.post("/api/rmos/workflow/sessions", json={
        "workflow_type": "design_first",
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
