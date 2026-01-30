"""
H7.2.3: Tests for strict mode on /api/cam/roughing/gcode_intent endpoint.

Covers:
- strict=False (default): 200 even with normalization issues
- strict=True: 422 when normalization issues exist
- Prometheus counter increments on strict rejection

Response format (H7.2):
{
    "gcode": "G90\\nG0 Z5.000\\n...",
    "issues": [{"code": "...", "message": "...", "path": "..."}],
    "status": "OK" | "OK_WITH_ISSUES"
}
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def _metrics_text(client: TestClient) -> str:
    """Fetch Prometheus metrics text."""
    r = client.get("/metrics")
    assert r.status_code == 200
    return r.text


def _metric_value(text: str, metric_name: str) -> float:
    """
    Parse metric value from Prometheus text format.
    Returns sum of all matching lines (handles labels).
    """
    total = 0.0
    for line in text.splitlines():
        if not line.startswith(metric_name):
            continue
        # Format: "name{labels} value" or "name value"
        parts = line.split()
        if len(parts) >= 2:
            try:
                total += float(parts[-1])
            except ValueError:
                pass
    return total


# Valid request body that will NOT trigger normalization issues
# Must conform to CamIntentV1 schema with router_3axis mode requirements
VALID_INTENT_BODY = {
    "mode": "router_3axis",  # Required by CamIntentV1
    "design": {
        "geometry": {
            "type": "rectangle",
            "width_mm": 100.0,
            "height_mm": 50.0,
        },
        "depth_mm": 10.0,
        "stepdown_mm": 2.0,
        "stepover_mm": 5.0,
        "width_mm": 100.0,  # Keep for backward compat with field mapping
        "height_mm": 50.0,
    },
    "context": {
        "feed_rate": 1000.0,
    },
    "units": "mm",
}

# Request body that WILL trigger normalization issues (missing geometry)
# The normalizer reports "missing_field" when geometry is absent
ISSUE_INTENT_BODY = {
    "mode": "router_3axis",  # Required by CamIntentV1
    "design": {
        # NOTE: geometry intentionally omitted to trigger missing_field issue
        "depth_mm": 5.0,
        "stepdown_mm": 2.0,
        "stepover_mm": 5.0,
        "width_mm": 100.0,
        "height_mm": 50.0,
    },
    "context": {
        "feed_rate": 1000.0,
    },
    "units": "mm",
}


class TestRoughingIntentStrictMode:
    """H7.2.3: Strict mode behavior tests."""

    def test_strict_off_allows_issues(self, client: TestClient):
        """Non-strict mode returns 200 even when issues exist."""
        r = client.post("/api/cam/roughing/gcode_intent", json=ISSUE_INTENT_BODY)
        assert r.status_code == 200

        data = r.json()
        assert "gcode" in data
        assert "issues" in data
        assert len(data["issues"]) > 0
        assert data["status"] == "OK_WITH_ISSUES"

        # Check for the expected issue code (missing_field from normalizer)
        codes = [i["code"] for i in data["issues"]]
        assert "missing_field" in codes

    def test_strict_on_rejects_with_issues(self, client: TestClient):
        """Strict mode returns 422 when normalization issues exist."""
        r = client.post(
            "/api/cam/roughing/gcode_intent?strict=true",
            json=ISSUE_INTENT_BODY,
        )
        assert r.status_code == 422

        data = r.json()
        assert data["detail"]["error"] == "CAM_INTENT_NORMALIZATION_ISSUES"
        assert isinstance(data["detail"]["issues"], list)
        assert len(data["detail"]["issues"]) > 0

    def test_strict_on_allows_clean_request(self, client: TestClient):
        """Strict mode returns 200 when no normalization issues."""
        r = client.post(
            "/api/cam/roughing/gcode_intent?strict=true",
            json=VALID_INTENT_BODY,
        )
        assert r.status_code == 200

        data = r.json()
        assert "gcode" in data
        assert data["issues"] == []
        assert data["status"] == "OK"

    def test_strict_query_param_variations(self, client: TestClient):
        """Strict accepts various truthy values."""
        # Test ?strict=1
        r = client.post(
            "/api/cam/roughing/gcode_intent?strict=1",
            json=ISSUE_INTENT_BODY,
        )
        assert r.status_code == 422

        # Test ?strict=True (capital T)
        r = client.post(
            "/api/cam/roughing/gcode_intent?strict=True",
            json=ISSUE_INTENT_BODY,
        )
        assert r.status_code == 422

    def test_strict_reject_increments_counter(self, client: TestClient):
        """Prometheus counter increments on strict rejection."""
        before = _metric_value(
            _metrics_text(client),
            "cam_roughing_gcode_intent_strict_reject_total",
        )

        # Trigger a strict rejection
        r = client.post(
            "/api/cam/roughing/gcode_intent?strict=true",
            json=ISSUE_INTENT_BODY,
        )
        assert r.status_code == 422

        after = _metric_value(
            _metrics_text(client),
            "cam_roughing_gcode_intent_strict_reject_total",
        )
        assert after >= before + 1.0

    def test_non_strict_does_not_increment_strict_counter(self, client: TestClient):
        """Non-strict path does not increment strict_rejects counter."""
        before = _metric_value(
            _metrics_text(client),
            "cam_roughing_intent_strict_rejects_total",
        )

        # Non-strict request with issues - now returns G-code (200)
        r = client.post("/api/cam/roughing/gcode_intent", json=ISSUE_INTENT_BODY)
        assert r.status_code == 200

        after = _metric_value(
            _metrics_text(client),
            "cam_roughing_intent_strict_rejects_total",
        )
        # Counter should not have changed
        assert after == before


class TestRoughingIntentNonStrictIssuesHeader:
    """Verify non-strict mode still reports issues in response body."""

    def test_issues_in_response_body(self, client: TestClient):
        """Non-strict mode includes issues in JSON response."""
        r = client.post("/api/cam/roughing/gcode_intent", json=ISSUE_INTENT_BODY)
        assert r.status_code == 200

        data = r.json()
        assert "issues" in data
        assert len(data["issues"]) > 0
        # Normalizer reports missing_field for missing geometry
        assert data["issues"][0]["code"] == "missing_field"
