# services/api/app/tests/test_art_studio_cam_promotion_contract.py
"""
Phase 33.0 — CAM Promotion Request Contract Tests

Contract tests for the CAM promotion bridge:
1) Unapproved sessions cannot promote (blocked)
2) Approved sessions can promote and get a valid CamPromotionRequestV1
3) Idempotency: re-promoting returns the same request ID
4) GET endpoint returns the created request
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _start_session() -> str:
    """
    Start a DRAFT design-first workflow session with minimal RosetteParamSpec.
    """
    r = client.post(
        "/api/art/design-first-workflow/sessions/start",
        json={
            "mode": "design_first",
            "design": {
                "outer_diameter_mm": 110.0,
                "inner_diameter_mm": 90.0,
                "ring_params": [
                    {"ring_index": 0, "width_mm": 2.0, "pattern_type": "SOLID"}
                ],
            },
            "feasibility": {
                "overall_score": 0.92,
                "risk_bucket": "GREEN",
                "material_efficiency": 0.88,
                "estimated_cut_time_min": 12.5,
                "warnings": [],
            },
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert "session" in data
    return data["session"]["session_id"]


def _transition(session_id: str, to_state: str) -> None:
    r = client.post(
        f"/api/art/design-first-workflow/sessions/{session_id}/transition",
        json={"to_state": to_state, "actor": "pytest"},
    )
    assert r.status_code == 200, r.text


def _approve_session(session_id: str) -> None:
    # Contract: must go DRAFT -> IN_REVIEW -> APPROVED
    _transition(session_id, "in_review")
    _transition(session_id, "approved")


def test_promote_blocked_when_not_approved() -> None:
    """Unapproved sessions cannot promote to CAM."""
    session_id = _start_session()

    r = client.post(
        f"/api/art/design-first-workflow/sessions/{session_id}/promote_to_cam"
    )
    assert r.status_code == 200, r.text
    data = r.json()

    assert data["ok"] is False
    assert data.get("request") is None
    assert isinstance(data.get("blocked_reason"), str)
    assert data["blocked_reason"] == "workflow_not_approved"


def test_promote_succeeds_when_approved() -> None:
    """Approved sessions can promote to CAM and get a valid request."""
    session_id = _start_session()
    _approve_session(session_id)

    r = client.post(
        f"/api/art/design-first-workflow/sessions/{session_id}/promote_to_cam"
    )
    assert r.status_code == 200, r.text
    data = r.json()

    assert data["ok"] is True
    assert data.get("blocked_reason") in (None, "")
    
    request = data.get("request")
    assert isinstance(request, dict)
    
    # Validate CamPromotionRequestV1 shape
    assert request["promotion_request_version"] == "v1"
    assert request["session_id"] == session_id
    assert request["source"] == "art_studio"
    assert request["status"] == "QUEUED"
    assert isinstance(request["promotion_request_id"], str)
    assert len(request["promotion_request_id"]) > 0
    assert isinstance(request["design_fingerprint"], str)
    assert len(request["design_fingerprint"]) > 0
    assert isinstance(request["feasibility_fingerprint"], str)
    assert len(request["feasibility_fingerprint"]) > 0
    assert isinstance(request["created_at"], str)


def test_promote_idempotent() -> None:
    """Re-promoting the same intent returns the same request ID."""
    session_id = _start_session()
    _approve_session(session_id)

    # First promotion
    r1 = client.post(
        f"/api/art/design-first-workflow/sessions/{session_id}/promote_to_cam"
    )
    assert r1.status_code == 200, r1.text
    data1 = r1.json()
    assert data1["ok"] is True
    request_id_1 = data1["request"]["promotion_request_id"]

    # Second promotion (should be idempotent)
    r2 = client.post(
        f"/api/art/design-first-workflow/sessions/{session_id}/promote_to_cam"
    )
    assert r2.status_code == 200, r2.text
    data2 = r2.json()
    assert data2["ok"] is True
    request_id_2 = data2["request"]["promotion_request_id"]

    # Same request ID
    assert request_id_1 == request_id_2


def test_get_promotion_request() -> None:
    """GET endpoint returns the created request."""
    session_id = _start_session()
    _approve_session(session_id)

    # Create promotion request
    r = client.post(
        f"/api/art/design-first-workflow/sessions/{session_id}/promote_to_cam"
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["ok"] is True
    request_id = data["request"]["promotion_request_id"]

    # Retrieve by ID
    r2 = client.get(
        f"/api/art/design-first-workflow/cam-promotion/requests/{request_id}"
    )
    assert r2.status_code == 200, r2.text
    retrieved = r2.json()

    assert retrieved["promotion_request_id"] == request_id
    assert retrieved["session_id"] == session_id
    assert retrieved["promotion_request_version"] == "v1"


def test_get_promotion_request_404() -> None:
    """GET returns 404 for non-existent request."""
    r = client.get(
        "/api/art/design-first-workflow/cam-promotion/requests/nonexistent123"
    )
    assert r.status_code == 404
