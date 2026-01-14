# services/api/tests/test_art_studio_design_first_workflow.py
"""
Tests for Art Studio Design-First Workflow (Bundle 32.7.0)

Tests the lightweight workflow binding:
- Session start, get, transition
- Promotion intent generation
- State machine validation
"""
import os
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="function")
def client(tmp_path):
    """Test client with isolated workflow storage."""
    os.environ["ART_STUDIO_DESIGN_FIRST_WORKFLOW_DIR"] = str(tmp_path / "wf")
    
    from app.main import app
    return TestClient(app)


@pytest.fixture
def minimal_spec():
    """Minimal RosetteParamSpec for testing."""
    return {
        "outer_diameter_mm": 180.0,
        "inner_diameter_mm": 100.0,
        "ring_params": [],
    }


class TestDesignFirstWorkflow:
    """Test design-first workflow endpoints."""

    def test_start_session(self, client, minimal_spec):
        """Test starting a new workflow session."""
        r = client.post(
            "/api/art/design-first-workflow/sessions/start",
            json={"mode": "design_first", "design": minimal_spec},
        )
        assert r.status_code == 200
        data = r.json()
        assert "session" in data
        assert data["session"]["state"] == "draft"
        assert data["session"]["mode"] == "design_first"
        assert data["session"]["design"]["outer_diameter_mm"] == 180.0

    def test_get_session(self, client, minimal_spec):
        """Test getting an existing session."""
        # Create session
        r = client.post(
            "/api/art/design-first-workflow/sessions/start",
            json={"mode": "design_first", "design": minimal_spec},
        )
        assert r.status_code == 200
        session_id = r.json()["session"]["session_id"]

        # Get session
        r = client.get(f"/api/art/design-first-workflow/sessions/{session_id}")
        assert r.status_code == 200
        assert r.json()["session"]["session_id"] == session_id

    def test_get_nonexistent_session(self, client):
        """Test 404 for nonexistent session."""
        r = client.get("/api/art/design-first-workflow/sessions/nonexistent123")
        assert r.status_code == 404
        assert "not_found" in r.json()["detail"]

    def test_transition_draft_to_in_review(self, client, minimal_spec):
        """Test transitioning from DRAFT to IN_REVIEW."""
        # Create session
        r = client.post(
            "/api/art/design-first-workflow/sessions/start",
            json={"mode": "design_first", "design": minimal_spec},
        )
        session_id = r.json()["session"]["session_id"]

        # Transition to IN_REVIEW
        r = client.post(
            f"/api/art/design-first-workflow/sessions/{session_id}/transition",
            json={"to_state": "in_review"},
        )
        assert r.status_code == 200
        assert r.json()["session"]["state"] == "in_review"
        assert len(r.json()["session"]["history"]) == 1

    def test_full_approval_flow(self, client, minimal_spec):
        """Test full DRAFT → IN_REVIEW → APPROVED flow."""
        # Create session
        r = client.post(
            "/api/art/design-first-workflow/sessions/start",
            json={"mode": "design_first", "design": minimal_spec},
        )
        session_id = r.json()["session"]["session_id"]

        # DRAFT → IN_REVIEW
        r = client.post(
            f"/api/art/design-first-workflow/sessions/{session_id}/transition",
            json={"to_state": "in_review"},
        )
        assert r.status_code == 200
        assert r.json()["session"]["state"] == "in_review"

        # IN_REVIEW → APPROVED
        r = client.post(
            f"/api/art/design-first-workflow/sessions/{session_id}/transition",
            json={"to_state": "approved", "note": "Looks good!"},
        )
        assert r.status_code == 200
        assert r.json()["session"]["state"] == "approved"
        assert len(r.json()["session"]["history"]) == 2

    def test_invalid_transition(self, client, minimal_spec):
        """Test that invalid transitions return 400."""
        # Create session (in DRAFT state)
        r = client.post(
            "/api/art/design-first-workflow/sessions/start",
            json={"mode": "design_first", "design": minimal_spec},
        )
        session_id = r.json()["session"]["session_id"]

        # Try invalid DRAFT → APPROVED (must go through IN_REVIEW)
        r = client.post(
            f"/api/art/design-first-workflow/sessions/{session_id}/transition",
            json={"to_state": "approved"},
        )
        assert r.status_code == 400
        assert "invalid_transition" in r.json()["detail"]

    def test_promotion_intent_when_approved(self, client, minimal_spec):
        """Test promotion intent is available when approved."""
        # Create and approve session
        r = client.post(
            "/api/art/design-first-workflow/sessions/start",
            json={"mode": "design_first", "design": minimal_spec},
        )
        session_id = r.json()["session"]["session_id"]

        # Transition to approved
        client.post(
            f"/api/art/design-first-workflow/sessions/{session_id}/transition",
            json={"to_state": "in_review"},
        )
        client.post(
            f"/api/art/design-first-workflow/sessions/{session_id}/transition",
            json={"to_state": "approved"},
        )

        # Get promotion intent
        r = client.post(
            f"/api/art/design-first-workflow/sessions/{session_id}/promotion_intent"
        )
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is True
        assert body["intent"]["session_id"] == session_id
        assert body["intent"]["mode"] == "design_first"
        assert body["intent"]["recommended_next_step"] == "hand_off_to_cam_lane"

    def test_promotion_intent_blocked_when_not_approved(self, client, minimal_spec):
        """Test promotion intent blocked when session not approved."""
        # Create session (stays in DRAFT)
        r = client.post(
            "/api/art/design-first-workflow/sessions/start",
            json={"mode": "design_first", "design": minimal_spec},
        )
        session_id = r.json()["session"]["session_id"]

        # Try to get promotion intent (should be blocked)
        r = client.post(
            f"/api/art/design-first-workflow/sessions/{session_id}/promotion_intent"
        )
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is False
        assert body["blocked_reason"] == "workflow_not_approved"

    def test_reopen_approved_session(self, client, minimal_spec):
        """Test reopening an approved session (APPROVED → DRAFT)."""
        # Create and approve session
        r = client.post(
            "/api/art/design-first-workflow/sessions/start",
            json={"mode": "design_first", "design": minimal_spec},
        )
        session_id = r.json()["session"]["session_id"]

        client.post(
            f"/api/art/design-first-workflow/sessions/{session_id}/transition",
            json={"to_state": "in_review"},
        )
        client.post(
            f"/api/art/design-first-workflow/sessions/{session_id}/transition",
            json={"to_state": "approved"},
        )

        # Reopen (APPROVED → DRAFT)
        r = client.post(
            f"/api/art/design-first-workflow/sessions/{session_id}/transition",
            json={"to_state": "draft", "note": "Need to revise design"},
        )
        assert r.status_code == 200
        assert r.json()["session"]["state"] == "draft"

    def test_transition_updates_design(self, client, minimal_spec):
        """Test that design can be updated during transition."""
        # Create session
        r = client.post(
            "/api/art/design-first-workflow/sessions/start",
            json={"mode": "design_first", "design": minimal_spec},
        )
        session_id = r.json()["session"]["session_id"]

        # Update design during transition
        updated_spec = {
            "outer_diameter_mm": 200.0,  # Changed
            "inner_diameter_mm": 110.0,  # Changed
            "ring_params": [],
        }

        r = client.post(
            f"/api/art/design-first-workflow/sessions/{session_id}/transition",
            json={"to_state": "in_review", "design": updated_spec},
        )
        assert r.status_code == 200
        assert r.json()["session"]["design"]["outer_diameter_mm"] == 200.0
        assert r.json()["session"]["design"]["inner_diameter_mm"] == 110.0
