# tests/test_electric_body_smoke.py

"""
Smoke tests for electric body outline generator endpoints.

GAP-07: Verifies Strat and other electric body generators are mounted and functional.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class TestElectricBodyEndpoints:
    """Smoke tests for electric body outline API."""

    def test_generate_strat_outline(self):
        """POST /generate returns Stratocaster outline."""
        response = client.post(
            "/api/instruments/guitar/electric-body/generate",
            json={"style": "stratocaster", "scale": 1.0, "detailed": True},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["style"] == "stratocaster"
        assert data["width_mm"] > 300  # Strat is about 322mm wide
        assert data["point_count"] > 10  # Detailed outline has many points
        assert "points" in data

    def test_generate_lespaul_outline(self):
        """POST /generate returns Les Paul outline."""
        response = client.post(
            "/api/instruments/guitar/electric-body/generate",
            json={"style": "les_paul", "scale": 1.0, "detailed": True},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["style"] == "les_paul"
        assert data["width_mm"] > 350  # LP is wider than Strat

    def test_generate_scaled_outline(self):
        """POST /generate respects scale factor."""
        response = client.post(
            "/api/instruments/guitar/electric-body/generate",
            json={"style": "stratocaster", "scale": 0.5, "detailed": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["scale_factor"] == 0.5
        assert data["width_mm"] < 200  # Half of ~322mm

    def test_generate_strat_endpoint(self):
        """POST /generate/strat returns Strat outline with fret notes."""
        response = client.post(
            "/api/instruments/guitar/electric-body/generate/strat",
            json={"fret_count": 24, "scale": 1.0},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["style"] == "stratocaster"
        # Should have 24-fret related note
        assert any("24-fret" in note.lower() for note in data["notes"])

    def test_list_styles(self):
        """GET /styles returns available body styles."""
        response = client.get("/api/instruments/guitar/electric-body/styles")
        assert response.status_code == 200
        data = response.json()
        assert "styles" in data
        style_ids = [s["id"] for s in data["styles"]]
        assert "stratocaster" in style_ids
        assert "les_paul" in style_ids

    def test_get_style_info(self):
        """GET /styles/{id} returns specific style outline."""
        response = client.get(
            "/api/instruments/guitar/electric-body/styles/stratocaster"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["style"] == "stratocaster"
        assert "points" in data
        assert data["point_count"] > 0

    def test_get_style_svg(self):
        """GET /styles/{id}/svg returns SVG string."""
        response = client.get(
            "/api/instruments/guitar/electric-body/styles/stratocaster/svg"
        )
        assert response.status_code == 200
        data = response.json()
        assert "svg" in data
        assert data["svg"].startswith("<svg")
        assert "stratocaster" in data["style"]

    def test_24fret_strat_preset(self):
        """GET /presets/24fret-strat returns preset outline."""
        response = client.get(
            "/api/instruments/guitar/electric-body/presets/24fret-strat"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["style"] == "stratocaster"
        # Should include 24-fret notes
        assert any("24" in note for note in data["notes"])
