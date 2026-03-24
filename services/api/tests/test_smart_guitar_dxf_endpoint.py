"""
Test Smart Guitar DXF Endpoint
==============================

Tests for GET /api/instruments/smart-guitar/dxf
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app

    return TestClient(app)


class TestSmartGuitarDxfEndpoint:
    """Tests for the Smart Guitar DXF generation endpoint."""

    def test_get_smart_guitar_dxf_returns_200(self, client):
        """GET /api/instruments/smart-guitar/dxf returns 200."""
        response = client.get("/api/instruments/smart-guitar/dxf")
        assert response.status_code == 200

    def test_content_disposition_contains_dxf(self, client):
        """Response includes Content-Disposition with .dxf filename."""
        response = client.get("/api/instruments/smart-guitar/dxf")
        assert response.status_code == 200
        content_disp = response.headers.get("Content-Disposition", "")
        assert ".dxf" in content_disp
        assert "attachment" in content_disp

    def test_response_starts_with_ac10_magic_bytes(self, client):
        """DXF file starts with AC10 (ezdxf R2010 magic bytes)."""
        response = client.get("/api/instruments/smart-guitar/dxf")
        assert response.status_code == 200
        # R2010 DXF starts with "  0\nSECTION" or similar, but the
        # AC1024 version string appears in the HEADER section
        content = response.content
        assert b"AC1024" in content or b"SECTION" in content[:100]

    def test_response_length_greater_than_1000_bytes(self, client):
        """DXF file is non-trivial (>1000 bytes)."""
        response = client.get("/api/instruments/smart-guitar/dxf")
        assert response.status_code == 200
        assert len(response.content) > 1000

    def test_version_query_param_affects_filename(self, client):
        """Version query param changes filename."""
        response = client.get("/api/instruments/smart-guitar/dxf?version=v4")
        assert response.status_code == 200
        content_disp = response.headers.get("Content-Disposition", "")
        assert "smart_guitar_v4.dxf" in content_disp

    def test_include_cavities_false_reduces_size(self, client):
        """Excluding cavities produces smaller DXF."""
        full = client.get("/api/instruments/smart-guitar/dxf")
        no_cav = client.get(
            "/api/instruments/smart-guitar/dxf?include_cavities=false"
        )
        assert full.status_code == 200
        assert no_cav.status_code == 200
        # Body-only should be smaller
        assert len(no_cav.content) < len(full.content)

    def test_dxf_contains_body_outline_layer(self, client):
        """DXF contains BODY_OUTLINE layer."""
        response = client.get("/api/instruments/smart-guitar/dxf")
        assert response.status_code == 200
        assert b"BODY_OUTLINE" in response.content

    def test_dxf_contains_neck_pocket_layer(self, client):
        """DXF contains NECK_POCKET layer when cavities included."""
        response = client.get("/api/instruments/smart-guitar/dxf")
        assert response.status_code == 200
        assert b"NECK_POCKET" in response.content
