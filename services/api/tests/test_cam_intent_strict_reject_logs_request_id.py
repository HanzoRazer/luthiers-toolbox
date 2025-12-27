# services/api/tests/test_cam_intent_strict_reject_logs_request_id.py
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_strict_reject_logs_include_request_id(client: TestClient, caplog) -> None:
    """
    Verify that strict-mode rejects log the request_id for incident correlation.
    
    This test ensures H7.2.3.1 compliance: when normalize_cam_intent_v1 emits issues
    and strict=true, the warning log must include the request_id.
    """
    # Endpoint path matches router prefix + route: /api/rmos/cam/intent/normalize
    normalize_path = "/api/rmos/cam/intent/normalize"

    req_id = "req_test_strict_reject_1"

    # Minimal / intentionally-invalid payload to trigger issues.
    # If your CamIntentV1 requires different fields, keep it invalid on purpose.
    payload = {
        "tool_id": "router:unknown",
        "mode": "roughing",
        "design": {},  # likely to produce issues in normalizer
    }

    with caplog.at_level("WARNING"):
        r = client.post(
            f"{normalize_path}?strict=true",
            json=payload,
            headers={"x-request-id": req_id},
        )

    assert r.status_code == 422

    # Ensure the warning line includes the explicit request_id token
    joined = "\n".join(rec.getMessage() for rec in caplog.records)
    assert f"request_id={req_id}" in joined, f"Expected 'request_id={req_id}' in logs, got: {joined}"


def test_strict_false_does_not_reject(client: TestClient) -> None:
    """
    Verify that strict=false (default) returns issues without rejecting.
    """
    normalize_path = "/api/rmos/cam/intent/normalize"

    payload = {
        "tool_id": "router:unknown",
        "mode": "roughing",
        "design": {},
    }

    r = client.post(
        normalize_path,
        json=payload,
        headers={"x-request-id": "req_test_permissive"},
    )

    # Should succeed even with issues
    assert r.status_code == 200
    data = r.json()
    assert "intent" in data
    assert "issues" in data
