import pytest


def test_curve_preflight_closed_polyline(api_client):
    body = {
        "points": [
            {"x": 0.0, "y": 0.0},
            {"x": 100.0, "y": 0.0},
            {"x": 100.0, "y": 40.0},
            {"x": 0.0, "y": 40.0},
            {"x": 0.0, "y": 0.0},
        ],
        "units": "mm",
        "tolerance_mm": 0.2,
        "layer": "CURVE",
    }
    response = api_client.post("/api/dxf/preflight/curve_report", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["cam_ready"] is True
    assert data["polyline"]["closed"] is True
    assert data["polyline"]["point_count"] == 5
    assert data["warnings_count"] == 0
    assert data["issues"] == []


def test_curve_preflight_open_polyline_warns(api_client):
    body = {
        "points": [
            {"x": 0.0, "y": 0.0},
            {"x": 80.0, "y": 0.0},
            {"x": 80.0, "y": 40.0},
            {"x": 0.0, "y": 40.0},
        ],
        "units": "mm",
        "tolerance_mm": 0.05,
        "layer": "CUT_LAYER",
    }
    response = api_client.post("/api/dxf/preflight/curve_report", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["cam_ready"] is False
    assert data["warnings_count"] >= 1
    assert any("Open polyline" in issue["message"] for issue in data["issues"])
    assert data["polyline"]["closed"] is False
    assert data["polyline"]["duplicate_count"] == 0


def test_curve_preflight_duplicate_detection(api_client):
    body = {
        "points": [
            {"x": 0.0, "y": 0.0},
            {"x": 10.0, "y": 0.0},
            {"x": 10.0, "y": 0.0},
            {"x": 0.0, "y": 10.0},
            {"x": 0.0, "y": 0.0},
        ],
        "units": "mm",
        "tolerance_mm": 0.1,
        "layer": "CURVE",
    }
    response = api_client.post("/api/dxf/preflight/curve_report", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["warnings_count"] >= 1
    assert data["polyline"]["duplicate_count"] == 1
