"""
Blueprint CAM Bridge Tests (Phase 3.2)

Tests for DXF preflight and contour reconstruction endpoints.
Converted from test_blueprint_phase3_ci.py to use FastAPI TestClient.

Run:
    pytest tests/test_blueprint_cam_bridge.py -v

Coverage:
    - /api/blueprint/cam/health
    - /api/blueprint/cam/preflight
    - /api/blueprint/cam/reconstruct-contours
"""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "dxf"


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def load_fixture(name: str) -> bytes:
    """Load DXF fixture file."""
    path = FIXTURES_DIR / name
    if not path.exists():
        pytest.skip(f"Missing fixture: {path}")
    return path.read_bytes()


class TestBlueprintCAMHealth:
    """Tests for Blueprint CAM bridge health endpoint."""

    def test_health_returns_200(self, client):
        """GET /api/blueprint/cam/health returns 200."""
        response = client.get("/api/blueprint/cam/health")
        assert response.status_code == 200

    def test_health_returns_phase_32(self, client):
        """Health check returns phase 3.2."""
        response = client.get("/api/blueprint/cam/health")
        data = response.json()
        assert data.get("phase") == "3.2"

    def test_health_includes_endpoints(self, client):
        """Health check lists available endpoints."""
        response = client.get("/api/blueprint/cam/health")
        data = response.json()
        endpoints = data.get("endpoints", [])
        
        required = ["/reconstruct-contours", "/preflight", "/to-adaptive"]
        for endpoint in required:
            assert endpoint in endpoints, f"Missing endpoint: {endpoint}"


class TestDXFPreflight:
    """Tests for DXF preflight validation."""

    def test_preflight_json_response(self, client):
        """POST /api/blueprint/cam/preflight returns JSON report."""
        dxf_content = load_fixture("minimal.dxf")
        
        response = client.post(
            "/api/blueprint/cam/preflight",
            files={"file": ("test.dxf", dxf_content, "application/dxf")},
            data={"format": "json"},
        )
        
        assert response.status_code == 200
        report = response.json()
        
        # Check required fields
        required_fields = ["filename", "passed", "issues", "summary"]
        for field in required_fields:
            assert field in report, f"Missing field: {field}"
        
        assert report["filename"] == "test.dxf"

    def test_preflight_html_response(self, client):
        """POST /api/blueprint/cam/preflight returns HTML report."""
        dxf_content = load_fixture("minimal.dxf")
        
        response = client.post(
            "/api/blueprint/cam/preflight",
            files={"file": ("test.dxf", dxf_content, "application/dxf")},
            data={"format": "html"},
        )
        
        assert response.status_code == 200
        html = response.text
        
        # Check required content
        assert "DXF Preflight Report" in html or "test.dxf" in html

    def test_preflight_rejects_non_dxf(self, client):
        """Preflight rejects non-DXF files."""
        response = client.post(
            "/api/blueprint/cam/preflight",
            files={"file": ("test.txt", b"not a dxf file", "text/plain")},
            data={"format": "json"},
        )
        
        # Should return 400 for invalid file type
        assert response.status_code == 400


class TestContourReconstruction:
    """Tests for contour reconstruction from DXF."""

    def test_reconstruct_contours_basic(self, client):
        """POST /api/blueprint/cam/reconstruct-contours works."""
        dxf_content = load_fixture("contours_rectangle.dxf")
        
        response = client.post(
            "/api/blueprint/cam/reconstruct-contours",
            files={"file": ("test.dxf", dxf_content, "application/dxf")},
            data={
                "layer_name": "Contours",
                "tolerance": "0.1",
                "min_loop_points": "3",
            },
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Check required fields
        required_fields = ["message", "loops", "stats"]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"

    def test_reconstruct_accepts_custom_tolerance(self, client):
        """Reconstruction accepts custom tolerance parameter."""
        dxf_content = load_fixture("contours_rectangle.dxf")
        
        response = client.post(
            "/api/blueprint/cam/reconstruct-contours",
            files={"file": ("test.dxf", dxf_content, "application/dxf")},
            data={
                "layer_name": "Contours",
                "tolerance": "0.5",  # Higher tolerance
                "min_loop_points": "3",
            },
        )
        
        assert response.status_code == 200
