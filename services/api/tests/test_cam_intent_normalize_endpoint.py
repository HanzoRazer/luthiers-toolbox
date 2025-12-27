"""
CAM Intent Normalize Endpoint Tests (H7.1.2)

Integration tests for POST /api/rmos/cam/intent/normalize
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.mark.unit
def test_cam_intent_normalize_endpoint_returns_intent_and_issues(client: TestClient) -> None:
    """Basic normalization returns intent and issues list."""
    payload = {
        "intent": {
            "mode": "saw",
            "units": "mm",
            "design": {
                "cuts": [{"type": "rip", "length_mm": 300, "depth_mm": 10}],
            },
        },
        "normalize_to_units": "mm",
        "strict": False,
    }

    r = client.post(
        "/api/rmos/cam/intent/normalize",
        json=payload,
        headers={"X-Request-Id": "test-req-123"},
    )
    assert r.status_code == 200, r.text
    data = r.json()

    assert "intent" in data
    assert "issues" in data
    assert isinstance(data["issues"], list)
    assert data["intent"]["mode"] == "saw"
    # Should include created_at_utc even if client omitted
    assert data["intent"].get("created_at_utc")
    # Should include normalized_at_utc
    assert "normalized_at_utc" in data


@pytest.mark.unit
def test_cam_intent_normalize_endpoint_strict_422(client: TestClient) -> None:
    """Strict mode returns 422 for missing recommended fields."""
    payload = {
        "intent": {
            "mode": "saw",
            "units": "mm",
            "design": {
                "cuts": [{"type": "rip", "length_mm": 300, "depth_mm": 10}],
            },
        },
        "normalize_to_units": "mm",
        "strict": True,
    }

    r = client.post(
        "/api/rmos/cam/intent/normalize",
        json=payload,
        headers={"X-Request-Id": "test-req-456"},
    )
    assert r.status_code == 422, r.text
    detail = r.json().get("detail") or {}
    assert "message" in detail
    assert "issues" in detail


@pytest.mark.unit
def test_cam_intent_normalize_endpoint_inch_to_mm(client: TestClient) -> None:
    """Converts inch units to mm."""
    payload = {
        "intent": {
            "mode": "router_3axis",
            "units": "inch",
            "design": {
                "geometry": {"type": "polyline", "points": [[0, 0], [1, 0]]},
                "depth_mm": 0.5,
            },
        },
        "normalize_to_units": "mm",
        "strict": False,
    }

    r = client.post(
        "/api/rmos/cam/intent/normalize",
        json=payload,
        headers={"X-Request-Id": "test-req-789"},
    )
    assert r.status_code == 200, r.text
    data = r.json()

    assert data["intent"]["units"] == "mm"
    # 0.5 inch = 12.7 mm
    assert abs(data["intent"]["design"]["depth_mm"] - 12.7) < 0.01
    # 1 inch = 25.4 mm
    pts = data["intent"]["design"]["geometry"]["points"]
    assert abs(pts[1][0] - 25.4) < 0.01


@pytest.mark.unit
def test_cam_intent_normalize_endpoint_preserves_fields(client: TestClient) -> None:
    """Preserves optional fields through normalization."""
    payload = {
        "intent": {
            "mode": "router_3axis",
            "units": "mm",
            "intent_id": "my-custom-id",
            "tool_id": "endmill-6mm",
            "material_id": "spruce",
            "machine_id": "router-1",
            "design": {
                "geometry": {"type": "rect", "width": 10, "height": 5},
            },
            "context": {"max_feed_rate": 1000},
            "options": {"preview": True},
            "requested_by": "test-user",
        },
        "normalize_to_units": "mm",
        "strict": False,
    }

    r = client.post(
        "/api/rmos/cam/intent/normalize",
        json=payload,
        headers={"X-Request-Id": "test-req-preserve"},
    )
    assert r.status_code == 200, r.text
    data = r.json()

    intent = data["intent"]
    assert intent["intent_id"] == "my-custom-id"
    assert intent["tool_id"] == "endmill-6mm"
    assert intent["material_id"] == "spruce"
    assert intent["machine_id"] == "router-1"
    assert intent["context"]["max_feed_rate"] == 1000
    assert intent["options"]["preview"] is True
    assert intent["requested_by"] == "test-user"


@pytest.mark.unit
def test_cam_intent_normalize_endpoint_invalid_mode(client: TestClient) -> None:
    """Invalid mode returns 422."""
    payload = {
        "intent": {
            "mode": "invalid_mode",
            "units": "mm",
            "design": {},
        },
    }

    r = client.post(
        "/api/rmos/cam/intent/normalize",
        json=payload,
        headers={"X-Request-Id": "test-req-invalid"},
    )
    assert r.status_code == 422, r.text


@pytest.mark.unit
def test_cam_intent_normalize_endpoint_echoes_request_id(client: TestClient) -> None:
    """Echoes X-Request-Id header back."""
    payload = {
        "intent": {
            "mode": "router_3axis",
            "units": "mm",
            "design": {"geometry": {"type": "rect"}},
        },
    }

    r = client.post(
        "/api/rmos/cam/intent/normalize",
        json=payload,
        headers={"X-Request-Id": "echo-test-id"},
    )
    assert r.status_code == 200
    assert r.headers.get("x-request-id") == "echo-test-id"
