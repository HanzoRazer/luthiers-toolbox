"""
Test GET /sessions/{session_id}/promotion_intent.json endpoint (Bundle 32.8.5)

Verifies canonical PromotionIntentV1 export returns correct schema.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client() -> TestClient:
    from app.main import app
    return TestClient(app)


def _start_and_approve_session(client: TestClient) -> str:
    """Create a session, approve it, return session_id."""
    # Start
    r = client.post(
        "/api/art/design-first-workflow/sessions/start",
        json={
            "mode": "design_first",
            "design": {
                "outer_diameter_mm": 100.0,
                "inner_diameter_mm": 10.0,
                "ring_params": [{"ring_index": 0, "width_mm": 5.0}],
            },
            "feasibility": {
                "overall_score": 0.85,
                "risk_bucket": "GREEN",
                "material_efficiency": 0.75,
                "estimated_cut_time_min": 45,
                "warnings": [],
            },
        },
    )
    assert r.status_code == 200, r.text
    session_id = r.json()["session"]["session_id"]

    # Transition DRAFT -> IN_REVIEW
    r = client.post(
        f"/api/art/design-first-workflow/sessions/{session_id}/transition",
        json={"to_state": "in_review", "actor": "test"},
    )
    assert r.status_code == 200, r.text

    # Transition IN_REVIEW -> APPROVED
    r = client.post(
        f"/api/art/design-first-workflow/sessions/{session_id}/transition",
        json={"to_state": "approved", "actor": "test"},
    )
    assert r.status_code == 200, r.text

    return session_id


@pytest.mark.allow_missing_request_id
def test_promotion_intent_json_returns_canonical_schema(client: TestClient):
    """GET /promotion_intent.json returns PromotionIntentV1 schema."""
    session_id = _start_and_approve_session(client)

    r = client.get(f"/api/art/design-first-workflow/sessions/{session_id}/promotion_intent.json")
    assert r.status_code == 200, r.text
    j = r.json()

    # Required top-level keys
    assert "intent_version" in j
    assert j["intent_version"] == "v1"
    assert "session_id" in j
    assert j["session_id"] == session_id
    assert "mode" in j
    assert "created_at" in j
    assert "design" in j
    assert "feasibility" in j
    assert "design_fingerprint" in j
    assert "feasibility_fingerprint" in j
    assert "fingerprint_algo" in j

    # Design required keys
    design = j["design"]
    assert "outer_diameter_mm" in design
    assert "inner_diameter_mm" in design
    assert "ring_params" in design

    # Feasibility required keys
    feas = j["feasibility"]
    assert "overall_score" in feas
    assert "risk_bucket" in feas
    assert "material_efficiency" in feas
    assert "estimated_cut_time_min" in feas
    assert "warnings" in feas


@pytest.mark.allow_missing_request_id
def test_promotion_intent_json_with_overrides(client: TestClient):
    """GET /promotion_intent.json accepts query param overrides."""
    session_id = _start_and_approve_session(client)

    r = client.get(
        f"/api/art/design-first-workflow/sessions/{session_id}/promotion_intent.json",
        params={
            "tool_id": "OVERRIDE_TOOL",
            "material_id": "OVERRIDE_MATERIAL",
            "risk_tolerance": "ALLOW_YELLOW",
        },
    )
    assert r.status_code == 200, r.text
    j = r.json()

    # context_refs should contain overrides
    ctx = j.get("context_refs", {})
    assert ctx.get("tool_id") == "OVERRIDE_TOOL"
    assert ctx.get("material_id") == "OVERRIDE_MATERIAL"

    # risk_tolerance should be applied
    assert j.get("risk_tolerance") == "ALLOW_YELLOW"


@pytest.mark.allow_missing_request_id
def test_promotion_intent_json_403_for_unapproved(client: TestClient):
    """GET /promotion_intent.json returns 403 for non-APPROVED sessions."""
    # Start session (DRAFT state)
    r = client.post(
        "/api/art/design-first-workflow/sessions/start",
        json={
            "mode": "design_first",
            "design": {"outer_diameter_mm": 100.0, "inner_diameter_mm": 10.0},
            "feasibility": {"overall_score": 0.5, "risk_bucket": "GREEN"},
        },
    )
    assert r.status_code == 200, r.text
    session_id = r.json()["session"]["session_id"]

    # Try to export - should fail since not approved
    r = client.get(f"/api/art/design-first-workflow/sessions/{session_id}/promotion_intent.json")
    assert r.status_code == 403
    assert "workflow_not_approved" in r.text


@pytest.mark.allow_missing_request_id
def test_promotion_intent_json_404_for_missing(client: TestClient):
    """GET /promotion_intent.json returns 404 for missing session."""
    r = client.get("/api/art/design-first-workflow/sessions/DOES_NOT_EXIST/promotion_intent.json")
    assert r.status_code == 404
    assert "design_first_session_not_found" in r.text

# ==========================================================================
# POST /promotion_intent_v1 - Wrapper endpoint tests
# ==========================================================================


@pytest.mark.allow_missing_request_id
def test_promotion_intent_v1_post_returns_wrapper_with_intent(client: TestClient):
    """POST /promotion_intent_v1 returns { ok, intent } wrapper."""
    session_id = _start_and_approve_session(client)

    r = client.post(f"/api/art/design-first-workflow/sessions/{session_id}/promotion_intent_v1")
    assert r.status_code == 200, r.text
    j = r.json()

    # Wrapper structure
    assert j["ok"] is True
    assert j["blocked_reason"] is None
    assert "intent" in j

    # Intent should be PromotionIntentV1
    intent = j["intent"]
    assert intent["intent_version"] == "v1"
    assert intent["session_id"] == session_id


@pytest.mark.allow_missing_request_id
def test_promotion_intent_v1_post_with_overrides(client: TestClient):
    """POST /promotion_intent_v1 accepts query param overrides."""
    session_id = _start_and_approve_session(client)

    r = client.post(
        f"/api/art/design-first-workflow/sessions/{session_id}/promotion_intent_v1",
        params={
            "tool_id": "OVERRIDE_TOOL",
            "risk_tolerance": "ALLOW_YELLOW",
        },
    )
    assert r.status_code == 200, r.text
    j = r.json()

    assert j["ok"] is True
    intent = j["intent"]
    assert intent.get("context_refs", {}).get("tool_id") == "OVERRIDE_TOOL"
    assert intent.get("risk_tolerance") == "ALLOW_YELLOW"


@pytest.mark.allow_missing_request_id
def test_promotion_intent_v1_post_blocked_for_unapproved(client: TestClient):
    """POST /promotion_intent_v1 returns ok=False for non-APPROVED sessions."""
    # Start session (DRAFT state)
    r = client.post(
        "/api/art/design-first-workflow/sessions/start",
        json={
            "mode": "design_first",
            "design": {"outer_diameter_mm": 100.0, "inner_diameter_mm": 10.0},
            "feasibility": {"overall_score": 0.5, "risk_bucket": "GREEN"},
        },
    )
    assert r.status_code == 200, r.text
    session_id = r.json()["session"]["session_id"]

    # Try to get intent - should return ok=False (not 403)
    r = client.post(f"/api/art/design-first-workflow/sessions/{session_id}/promotion_intent_v1")
    assert r.status_code == 200, r.text
    j = r.json()

    assert j["ok"] is False
    assert j["blocked_reason"] == "workflow_not_approved"
    assert j["intent"] is None


@pytest.mark.allow_missing_request_id
def test_promotion_intent_v1_post_404_for_missing(client: TestClient):
    """POST /promotion_intent_v1 returns 404 for missing session."""
    r = client.post("/api/art/design-first-workflow/sessions/DOES_NOT_EXIST/promotion_intent_v1")
    assert r.status_code == 404
    assert "design_first_session_not_found" in r.text
