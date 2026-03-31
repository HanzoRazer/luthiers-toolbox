"""
Endpoint smoke tests for spiral soundhole API.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestSpiralSoundholeEndpoints:
    """Smoke tests for /api/woodworking/soundhole/spiral/* endpoints."""

    def test_spiral_geometry_endpoint(self):
        """POST /api/woodworking/soundhole/spiral/geometry returns geometry."""
        response = client.post(
            "/api/woodworking/soundhole/spiral/geometry",
            json={
                "bout_radius_mm": 195.0,
                "slot_width_mm": 8.0,
                "spiral_start_r_mm": 20.0,
                "spiral_turns": 0.85,
                "growth_rate": 15.0,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert "spec" in data
        assert "geometry" in data
        assert "acoustic_notes" in data

        # Verify geometry fields
        geom = data["geometry"]
        assert "centerline_points" in geom
        assert "outer_wall" in geom
        assert "inner_wall" in geom
        assert "area_mm2" in geom
        assert "perimeter_mm" in geom
        assert "pa_ratio_mm_inv" in geom

        # Sanity checks
        assert geom["area_mm2"] > 0
        assert geom["pa_ratio_mm_inv"] > 0

    def test_spiral_geometry_defaults(self):
        """POST with minimal params uses defaults."""
        response = client.post(
            "/api/woodworking/soundhole/spiral/geometry",
            json={"bout_radius_mm": 180.0},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify defaults were applied
        spec = data["spec"]
        assert spec["slot_width_mm"] == 8.0
        assert spec["spiral_start_r_mm"] == 20.0
        assert spec["spiral_turns"] == 0.85
        assert spec["growth_rate"] == 15.0

    def test_spiral_dxf_endpoint(self):
        """POST /api/woodworking/soundhole/spiral/dxf returns DXF file."""
        response = client.post(
            "/api/woodworking/soundhole/spiral/dxf",
            json={
                "bout_radius_mm": 195.0,
                "slot_width_mm": 8.0,
                "spiral_start_r_mm": 20.0,
                "spiral_turns": 0.85,
                "growth_rate": 15.0,
            },
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/dxf"
        assert "spiral_soundhole.dxf" in response.headers["content-disposition"]

        # DXF should have content
        assert len(response.content) > 100

        # Should contain DXF markers
        content = response.content.decode("utf-8", errors="ignore")
        assert "SECTION" in content
        assert "ENTITIES" in content

    def test_spiral_geometry_validation(self):
        """Invalid params return 422."""
        response = client.post(
            "/api/woodworking/soundhole/spiral/geometry",
            json={"bout_radius_mm": -100},  # Invalid: must be > 0
        )

        assert response.status_code == 422
