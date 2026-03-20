"""Smoke tests for Workflow Sessions router endpoints."""

import json
import uuid
import pytest
from fastapi.testclient import TestClient


# =============================================================================
# Mock Store
# =============================================================================

class MockWorkflowSessionStore:
    """In-memory mock store for testing (avoids SQLite dependency)."""

    def __init__(self):
        self.sessions = {}

    def create(self, user_id=None, status=None, workflow_type=None,
               current_step=None, machine_id=None, material_id=None,
               tool_id=None, context_json=None, state_data_json=None,
               request_id=None):
        """Create a new session."""
        session_id = str(uuid.uuid4())
        row = {
            "workflow_session_id": session_id,
            "user_id": user_id,
            "status": status or "ACTIVE",
            "workflow_type": workflow_type,
            "current_step": current_step,
            "machine_id": machine_id,
            "material_id": material_id,
            "tool_id": tool_id,
            "context_json": json.dumps(context_json) if context_json else None,
            "state_data_json": json.dumps(state_data_json) if state_data_json else None,
            "created_at_utc": "2024-01-01T00:00:00",
            "updated_at_utc": "2024-01-01T00:00:00",
            "error_message": None,
        }
        self.sessions[session_id] = row
        return row

    def get(self, session_id):
        """Get a session by ID."""
        return self.sessions.get(session_id)

    def patch(self, session_id, status=None, current_step=None, workflow_type=None,
              machine_id=None, material_id=None, tool_id=None, context_json=None,
              state_data_json=None, error_message=None, request_id=None):
        """Update a session."""
        if session_id not in self.sessions:
            return None
        row = self.sessions[session_id]
        if status is not None:
            row["status"] = status
        if current_step is not None:
            row["current_step"] = current_step
        if workflow_type is not None:
            row["workflow_type"] = workflow_type
        if machine_id is not None:
            row["machine_id"] = machine_id
        if material_id is not None:
            row["material_id"] = material_id
        if tool_id is not None:
            row["tool_id"] = tool_id
        if context_json is not None:
            row["context_json"] = json.dumps(context_json)
        if state_data_json is not None:
            row["state_data_json"] = json.dumps(state_data_json)
        if error_message is not None:
            row["error_message"] = error_message
        row["updated_at_utc"] = "2024-01-01T00:00:01"
        return row

    def delete(self, session_id):
        """Delete a session."""
        if session_id not in self.sessions:
            return False
        del self.sessions[session_id]
        return True

    def list(self, limit=50, offset=0, user_id=None, status=None,
             workflow_type=None, since_utc=None, until_utc=None,
             include_total=False):
        """List sessions with optional filtering."""
        items = list(self.sessions.values())
        if user_id:
            items = [s for s in items if s.get("user_id") == user_id]
        if status:
            items = [s for s in items if s.get("status") == status]
        if workflow_type:
            items = [s for s in items if s.get("workflow_type") == workflow_type]
        total = len(items) if include_total else None
        items = items[offset:offset + limit]
        return items, total


# Global mock store instance (reset per test)
_mock_store = MockWorkflowSessionStore()


@pytest.fixture
def client(monkeypatch):
    """Create test client with mocked store."""
    global _mock_store
    _mock_store = MockWorkflowSessionStore()  # Reset for each test
    monkeypatch.setattr("app.workflow.sessions.routes._store", _mock_store)
    from app.main import app
    return TestClient(app)


# =============================================================================
# Endpoint Existence
# =============================================================================

def test_list_sessions_endpoint_exists(client):
    """GET /api/rmos/workflow/sessions endpoint exists."""
    response = client.get("/api/rmos/workflow/sessions")
    assert response.status_code != 404


def test_create_session_endpoint_exists(client):
    """POST /api/rmos/workflow/sessions endpoint exists."""
    response = client.post("/api/rmos/workflow/sessions", json={
        "workflow_type": "test_workflow",
        "status": "ACTIVE"
    })
    assert response.status_code != 404


def test_get_session_endpoint_exists(client):
    """GET /api/rmos/workflow/sessions/{id} endpoint exists."""
    response = client.get("/api/rmos/workflow/sessions/test-session-id")
    assert response.status_code in [200, 404]


def test_patch_session_endpoint_exists(client):
    """PATCH /api/rmos/workflow/sessions/{id} endpoint exists."""
    response = client.patch("/api/rmos/workflow/sessions/test-session-id", json={
        "status": "COMPLETED"
    })
    assert response.status_code in [200, 404]


def test_delete_session_endpoint_exists(client):
    """DELETE /api/rmos/workflow/sessions/{id} endpoint exists."""
    response = client.delete("/api/rmos/workflow/sessions/test-session-id")
    assert response.status_code in [200, 404, 409]


def test_session_runs_endpoint_exists(client):
    """GET /api/rmos/workflow/sessions/{id}/runs endpoint exists."""
    response = client.get("/api/rmos/workflow/sessions/test-session-id/runs")
    assert response.status_code in [200, 404, 501]


def test_session_advisory_summary_endpoint_exists(client):
    """GET /api/rmos/workflow/sessions/{id}/advisory-summary endpoint exists."""
    response = client.get("/api/rmos/workflow/sessions/test-session-id/advisory-summary")
    assert response.status_code in [200, 404, 501]


# =============================================================================
# List Sessions - Response Tests
# =============================================================================

def test_list_sessions_returns_200(client):
    """List sessions returns 200."""
    response = client.get("/api/rmos/workflow/sessions")
    assert response.status_code == 200


def test_list_sessions_returns_list_response(client):
    """List sessions returns expected structure."""
    response = client.get("/api/rmos/workflow/sessions")
    data = response.json()
    assert "items" in data
    assert "limit" in data
    assert "offset" in data


def test_list_sessions_with_limit(client):
    """List sessions accepts limit parameter."""
    response = client.get("/api/rmos/workflow/sessions", params={"limit": 10})
    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 10


def test_list_sessions_with_offset(client):
    """List sessions accepts offset parameter."""
    response = client.get("/api/rmos/workflow/sessions", params={"offset": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["offset"] == 5


def test_list_sessions_with_status_filter(client):
    """List sessions accepts status filter."""
    response = client.get("/api/rmos/workflow/sessions", params={"status": "ACTIVE"})
    assert response.status_code == 200


def test_list_sessions_with_workflow_type_filter(client):
    """List sessions accepts workflow_type filter."""
    response = client.get("/api/rmos/workflow/sessions", params={"workflow_type": "dxf_to_gcode"})
    assert response.status_code == 200


def test_list_sessions_with_user_id_filter(client):
    """List sessions accepts user_id filter."""
    response = client.get("/api/rmos/workflow/sessions", params={"user_id": "test-user"})
    assert response.status_code == 200


def test_list_sessions_with_include_total(client):
    """List sessions can include total count."""
    response = client.get("/api/rmos/workflow/sessions", params={"include_total": True})
    assert response.status_code == 200
    data = response.json()
    assert "total" in data


def test_list_sessions_with_date_range(client):
    """List sessions accepts date range filters."""
    response = client.get("/api/rmos/workflow/sessions", params={
        "since_utc": "2024-01-01T00:00:00",
        "until_utc": "2024-12-31T23:59:59"
    })
    assert response.status_code == 200


# =============================================================================
# Create Session - Response Tests
# =============================================================================

def test_create_session_returns_200(client):
    """Create session returns 200."""
    response = client.post("/api/rmos/workflow/sessions", json={
        "workflow_type": "test_workflow_create"
    })
    assert response.status_code == 200


def test_create_session_returns_session_response(client):
    """Create session returns session response."""
    response = client.post("/api/rmos/workflow/sessions", json={
        "workflow_type": "test_workflow_response"
    })
    data = response.json()
    assert "session_id" in data
    assert data["workflow_type"] == "test_workflow_response"


def test_create_session_with_status(client):
    """Create session accepts status."""
    response = client.post("/api/rmos/workflow/sessions", json={
        "workflow_type": "test_with_status",
        "status": "DRAFT"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "DRAFT"


def test_create_session_with_step(client):
    """Create session accepts current_step."""
    response = client.post("/api/rmos/workflow/sessions", json={
        "workflow_type": "test_with_step",
        "current_step": "upload"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["current_step"] == "upload"


def test_create_session_with_machine_id(client):
    """Create session accepts machine_id."""
    response = client.post("/api/rmos/workflow/sessions", json={
        "workflow_type": "test_with_machine",
        "machine_id": "machine-001"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["machine_id"] == "machine-001"


def test_create_session_with_context(client):
    """Create session accepts context_json."""
    response = client.post("/api/rmos/workflow/sessions", json={
        "workflow_type": "test_with_context",
        "context_json": {"key": "value", "count": 42}
    })
    assert response.status_code == 200
    data = response.json()
    assert data["context"]["key"] == "value"


def test_create_session_with_state_data(client):
    """Create session accepts state_data_json."""
    response = client.post("/api/rmos/workflow/sessions", json={
        "workflow_type": "test_with_state",
        "state_data_json": {"progress": 50, "phase": "processing"}
    })
    assert response.status_code == 200
    data = response.json()
    assert data["state_data"]["progress"] == 50


def test_create_session_minimal(client):
    """Create session with minimal data."""
    response = client.post("/api/rmos/workflow/sessions", json={})
    assert response.status_code == 200


# =============================================================================
# Get Session - Response Tests
# =============================================================================

def test_get_session_not_found(client):
    """Get session returns 404 for unknown ID."""
    response = client.get("/api/rmos/workflow/sessions/nonexistent-session-12345")
    assert response.status_code == 404


def test_get_session_returns_session(client):
    """Get session returns full session."""
    create_response = client.post("/api/rmos/workflow/sessions", json={
        "workflow_type": "test_get_session"
    })
    session_id = create_response.json()["session_id"]

    get_response = client.get(f"/api/rmos/workflow/sessions/{session_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["session_id"] == session_id
    assert data["workflow_type"] == "test_get_session"


# =============================================================================
# Patch Session - Response Tests
# =============================================================================

def test_patch_session_not_found(client):
    """Patch session returns 404 for unknown ID."""
    response = client.patch("/api/rmos/workflow/sessions/nonexistent-session-12345", json={
        "status": "COMPLETED"
    })
    assert response.status_code == 404


def test_patch_session_updates_status(client):
    """Patch session updates status."""
    create_response = client.post("/api/rmos/workflow/sessions", json={
        "workflow_type": "test_patch_status",
        "status": "ACTIVE"
    })
    session_id = create_response.json()["session_id"]

    patch_response = client.patch(f"/api/rmos/workflow/sessions/{session_id}", json={
        "status": "COMPLETED"
    })
    assert patch_response.status_code == 200
    assert patch_response.json()["status"] == "COMPLETED"


def test_patch_session_updates_step(client):
    """Patch session updates current_step."""
    create_response = client.post("/api/rmos/workflow/sessions", json={
        "workflow_type": "test_patch_step",
        "current_step": "draft"
    })
    session_id = create_response.json()["session_id"]

    patch_response = client.patch(f"/api/rmos/workflow/sessions/{session_id}", json={
        "current_step": "processing"
    })
    assert patch_response.status_code == 200
    assert patch_response.json()["current_step"] == "processing"


def test_patch_session_sets_error_message(client):
    """Patch session can set error_message."""
    create_response = client.post("/api/rmos/workflow/sessions", json={
        "workflow_type": "test_patch_error"
    })
    session_id = create_response.json()["session_id"]

    patch_response = client.patch(f"/api/rmos/workflow/sessions/{session_id}", json={
        "status": "ERROR",
        "error_message": "Something went wrong"
    })
    assert patch_response.status_code == 200
    assert patch_response.json()["error_message"] == "Something went wrong"


def test_patch_session_updates_context(client):
    """Patch session updates context_json."""
    create_response = client.post("/api/rmos/workflow/sessions", json={
        "workflow_type": "test_patch_context"
    })
    session_id = create_response.json()["session_id"]

    patch_response = client.patch(f"/api/rmos/workflow/sessions/{session_id}", json={
        "context_json": {"updated": True, "version": 2}
    })
    assert patch_response.status_code == 200
    assert patch_response.json()["context"]["updated"] is True


# =============================================================================
# Delete Session - Response Tests
# =============================================================================

def test_delete_session_not_found(client):
    """Delete session returns 404 for unknown ID."""
    response = client.delete("/api/rmos/workflow/sessions/nonexistent-session-12345")
    assert response.status_code == 404


def test_delete_session_works(client):
    """Delete session removes session."""
    create_response = client.post("/api/rmos/workflow/sessions", json={
        "workflow_type": "test_delete"
    })
    session_id = create_response.json()["session_id"]

    delete_response = client.delete(f"/api/rmos/workflow/sessions/{session_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True

    get_response = client.get(f"/api/rmos/workflow/sessions/{session_id}")
    assert get_response.status_code == 404


def test_delete_session_with_force(client):
    """Delete session accepts force parameter."""
    create_response = client.post("/api/rmos/workflow/sessions", json={
        "workflow_type": "test_delete_force"
    })
    session_id = create_response.json()["session_id"]

    response = client.delete(f"/api/rmos/workflow/sessions/{session_id}", params={"force": True})
    assert response.status_code in [200, 409]


def test_delete_session_with_cascade(client):
    """Delete session accepts cascade parameter."""
    create_response = client.post("/api/rmos/workflow/sessions", json={
        "workflow_type": "test_delete_cascade"
    })
    session_id = create_response.json()["session_id"]

    response = client.delete(f"/api/rmos/workflow/sessions/{session_id}", params={"cascade": True})
    assert response.status_code in [200, 409]


# =============================================================================
# Session Runs - Response Tests
# =============================================================================

def test_session_runs_for_nonexistent_session(client):
    """Session runs returns 404 for unknown session."""
    response = client.get("/api/rmos/workflow/sessions/nonexistent-session-12345/runs")
    assert response.status_code == 404


def test_session_runs_returns_response(client):
    """Session runs returns expected structure."""
    create_response = client.post("/api/rmos/workflow/sessions", json={
        "workflow_type": "test_runs_list"
    })
    session_id = create_response.json()["session_id"]

    response = client.get(f"/api/rmos/workflow/sessions/{session_id}/runs")
    assert response.status_code in [200, 501]

    if response.status_code == 200:
        data = response.json()
        assert "session_id" in data
        assert "runs" in data
        assert "limit" in data
        assert "count" in data


def test_session_runs_with_params(client):
    """Session runs accepts query parameters."""
    create_response = client.post("/api/rmos/workflow/sessions", json={
        "workflow_type": "test_runs_params"
    })
    session_id = create_response.json()["session_id"]

    response = client.get(f"/api/rmos/workflow/sessions/{session_id}/runs", params={
        "limit": 10,
        "offset": 0,
        "status": "ACTIVE",
        "include_total": True
    })
    assert response.status_code in [200, 501]


# =============================================================================
# Advisory Summary - Response Tests
# =============================================================================

def test_advisory_summary_for_nonexistent_session(client):
    """Advisory summary returns 404 for unknown session."""
    response = client.get("/api/rmos/workflow/sessions/nonexistent-session-12345/advisory-summary")
    assert response.status_code == 404


def test_advisory_summary_returns_response(client):
    """Advisory summary returns expected structure."""
    create_response = client.post("/api/rmos/workflow/sessions", json={
        "workflow_type": "test_advisory_summary"
    })
    session_id = create_response.json()["session_id"]

    response = client.get(f"/api/rmos/workflow/sessions/{session_id}/advisory-summary")
    assert response.status_code in [200, 501]

    if response.status_code == 200:
        data = response.json()
        assert "workflow_session_id" in data
        assert "total_runs" in data
        assert "explanation_status_counts" in data


# =============================================================================
# Integration Tests
# =============================================================================

def test_all_workflow_session_endpoints_exist(client):
    """All workflow session endpoints exist."""
    response = client.get("/api/rmos/workflow/sessions")
    assert response.status_code != 404, "GET /sessions returned 404"

    response = client.post("/api/rmos/workflow/sessions", json={"workflow_type": "integration_test"})
    assert response.status_code != 404, "POST /sessions returned 404"

    session_id = response.json()["session_id"]

    response = client.get(f"/api/rmos/workflow/sessions/{session_id}")
    assert response.status_code != 404, "GET /sessions/{id} returned 404"

    response = client.patch(f"/api/rmos/workflow/sessions/{session_id}", json={"status": "TEST"})
    assert response.status_code != 404, "PATCH /sessions/{id} returned 404"

    response = client.get(f"/api/rmos/workflow/sessions/{session_id}/runs")
    assert response.status_code not in [404], "GET /sessions/{id}/runs returned 404"

    response = client.get(f"/api/rmos/workflow/sessions/{session_id}/advisory-summary")
    assert response.status_code not in [404], "GET /sessions/{id}/advisory-summary returned 404"

    response = client.delete(f"/api/rmos/workflow/sessions/{session_id}")
    assert response.status_code != 404, "DELETE /sessions/{id} returned 404"


def test_workflow_session_lifecycle(client):
    """Integration: Full session lifecycle (create -> update -> complete -> delete)."""
    create_response = client.post("/api/rmos/workflow/sessions", json={
        "workflow_type": "lifecycle_test",
        "status": "ACTIVE",
        "current_step": "draft"
    })
    assert create_response.status_code == 200
    session = create_response.json()
    session_id = session["session_id"]
    assert session["status"] == "ACTIVE"
    assert session["current_step"] == "draft"

    patch_response = client.patch(f"/api/rmos/workflow/sessions/{session_id}", json={
        "current_step": "processing",
        "state_data_json": {"progress": 25}
    })
    assert patch_response.status_code == 200
    assert patch_response.json()["current_step"] == "processing"

    patch_response = client.patch(f"/api/rmos/workflow/sessions/{session_id}", json={
        "state_data_json": {"progress": 75}
    })
    assert patch_response.status_code == 200

    patch_response = client.patch(f"/api/rmos/workflow/sessions/{session_id}", json={
        "status": "COMPLETED",
        "current_step": "done",
        "state_data_json": {"progress": 100}
    })
    assert patch_response.status_code == 200
    assert patch_response.json()["status"] == "COMPLETED"

    list_response = client.get("/api/rmos/workflow/sessions", params={
        "workflow_type": "lifecycle_test",
        "status": "COMPLETED"
    })
    assert list_response.status_code == 200
    items = list_response.json()["items"]
    session_ids = [i["session_id"] for i in items]
    assert session_id in session_ids

    delete_response = client.delete(f"/api/rmos/workflow/sessions/{session_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True

    get_response = client.get(f"/api/rmos/workflow/sessions/{session_id}")
    assert get_response.status_code == 404
