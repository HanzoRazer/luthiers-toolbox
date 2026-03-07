"""Smoke tests for AI advisory endpoint (proxied to rmos.ai_advisory service)."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


# =============================================================================
# Endpoint Existence
# =============================================================================

def test_ai_advisories_request_endpoint_exists(client):
    """POST /api/ai/advisories/request endpoint exists."""
    response = client.post("/api/ai/advisories/request", json={})
    # Should return 200 (with error response), not 404
    assert response.status_code == 200


def test_ai_advisories_request_returns_ok_field(client):
    """POST /api/ai/advisories/request returns ok field."""
    response = client.post("/api/ai/advisories/request", json={})
    data = response.json()
    assert "ok" in data


def test_ai_advisories_request_returns_advisory_id_field(client):
    """POST /api/ai/advisories/request returns advisory_id field."""
    response = client.post("/api/ai/advisories/request", json={})
    data = response.json()
    assert "advisory_id" in data


def test_ai_advisories_request_returns_status_field(client):
    """POST /api/ai/advisories/request returns status field."""
    response = client.post("/api/ai/advisories/request", json={})
    data = response.json()
    assert "status" in data


# =============================================================================
# Schema Validation
# =============================================================================

def test_ai_advisories_request_empty_payload_fails_validation(client):
    """POST /api/ai/advisories/request with empty payload returns schema error."""
    response = client.post("/api/ai/advisories/request", json={})
    data = response.json()
    assert data["ok"] is False
    assert data["status"] == "error"
    assert "SCHEMA_VALIDATION_ERROR" in data.get("error_code", "") or "schema" in data.get("message", "").lower()


def test_ai_advisories_request_missing_request_field_fails(client):
    """POST /api/ai/advisories/request without request field fails."""
    response = client.post("/api/ai/advisories/request", json={
        "schema_id": "ai_context_packet_v1",
        "created_at_utc": "2024-01-01T00:00:00Z",
        # missing request and evidence
    })
    data = response.json()
    assert data["ok"] is False


def test_ai_advisories_request_missing_evidence_field_fails(client):
    """POST /api/ai/advisories/request without evidence field fails."""
    response = client.post("/api/ai/advisories/request", json={
        "schema_id": "ai_context_packet_v1",
        "created_at_utc": "2024-01-01T00:00:00Z",
        "request": {
            "kind": "explanation",
            "template_id": "test",
            "template_version": "1.0",
        },
        # missing evidence
    })
    data = response.json()
    assert data["ok"] is False


# =============================================================================
# Valid Request with Mocked CLI
# =============================================================================

def test_ai_advisories_request_valid_payload_with_mocked_cli(client):
    """POST /api/ai/advisories/request with valid payload returns ok when CLI is mocked."""
    # Create a valid payload
    payload = {
        "schema_id": "ai_context_packet_v1",
        "created_at_utc": "2024-01-01T00:00:00Z",
        "request": {
            "kind": "explanation",
            "template_id": "tap_tone_explanation",
            "template_version": "1.0",
        },
        "evidence": {
            "bundle_sha256": "abc123def456abc123def456abc123def456",
            "schema_id": "viewer_pack_v1",
            "selected": {
                "pointId": "point_001",
                "freqHz": 440.0,
                "activeRelpath": "spectra/point_001.json",
            },
            "refs": [],
        },
    }

    # Mock the CLI runner to return a valid draft
    mock_draft = {
        "schema_id": "advisory_draft_v1",
        "kind": "explanation",
        "model": {"id": "claude-3", "version": "1.0", "runtime": "local"},
        "template": {"id": "tap_tone_explanation", "version": "1.0"},
        "claims": [{"text": "Test explanation", "evidence_refs": []}],
        "caveats": [],
    }

    with patch("app.rmos.ai_advisory.service.run_ai_integrator_job", return_value=mock_draft):
        with patch("app.rmos.ai_advisory.service.persist_advisory", return_value="/tmp/test.json"):
            response = client.post("/api/ai/advisories/request", json=payload)
            data = response.json()
            assert data["ok"] is True
            assert data["advisory_id"] is not None
            assert data["advisory_id"].startswith("adv_")
            assert data["status"] == "draft"


def test_ai_advisories_request_unsupported_kind_fails(client):
    """POST /api/ai/advisories/request with unsupported kind returns error."""
    payload = {
        "schema_id": "ai_context_packet_v1",
        "created_at_utc": "2024-01-01T00:00:00Z",
        "request": {
            "kind": "comparison",  # Not supported in v1
            "template_id": "test",
            "template_version": "1.0",
        },
        "evidence": {
            "bundle_sha256": "abc123def456abc123def456abc123def456",
            "schema_id": "viewer_pack_v1",
            "selected": {
                "pointId": "point_001",
                "freqHz": 440.0,
                "activeRelpath": "spectra/point_001.json",
            },
            "refs": [],
        },
    }

    response = client.post("/api/ai/advisories/request", json=payload)
    data = response.json()
    assert data["ok"] is False
    # Should fail with schema error for unsupported kind
    assert "error" in data["status"]


def test_ai_advisories_request_returns_error_code_on_failure(client):
    """POST /api/ai/advisories/request returns error_code on failure."""
    response = client.post("/api/ai/advisories/request", json={})
    data = response.json()
    # On failure, should include error_code
    if not data["ok"]:
        assert "error_code" in data or "message" in data
