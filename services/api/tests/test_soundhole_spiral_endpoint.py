"""
Endpoint smoke tests for spiral soundhole as a type option.

Tests the refactored spiral integration into the main soundhole generator.
Spiral is now one option in the soundhole_type dropdown (round, oval, spiral, fhole).
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestSoundholeTypeEndpoints:
    """Smoke tests for soundhole type selection via /api/instrument/soundhole."""

    def test_soundhole_types_endpoint(self):
        """GET /api/instrument/soundhole/types returns type list."""
        response = client.get("/api/instrument/soundhole/types")

        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert "types" in data
        assert "spiral_presets" in data

        # Verify types
        types = data["types"]
        type_values = [t["type"] for t in types]
        assert "round" in type_values
        assert "oval" in type_values
        assert "spiral" in type_values
        assert "fhole" in type_values

        # Verify spiral presets
        presets = data["spiral_presets"]
        assert len(presets) > 0
        assert any(p["id"] == "standard_14mm" for p in presets)

    def test_soundhole_round_type(self):
        """POST /api/instrument/soundhole with type=round."""
        response = client.post(
            "/api/instrument/soundhole",
            json={
                "body_style": "dreadnought",
                "body_length_mm": 500.0,
                "soundhole_type": "round",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["soundhole_type"] == "round"
        assert data["diameter_mm"] == 100.0  # dreadnought standard
        assert data["gate"] == "GREEN"
        assert data["area_mm2"] is not None
        assert data["perimeter_mm"] is not None

    def test_soundhole_spiral_type(self):
        """POST /api/instrument/soundhole with type=spiral."""
        response = client.post(
            "/api/instrument/soundhole",
            json={
                "body_style": "carlos_jumbo",
                "body_length_mm": 520.0,
                "soundhole_type": "spiral",
                "spiral_params": {
                    "slot_width_mm": 14.0,
                    "start_radius_mm": 10.0,
                    "growth_rate_k": 0.18,
                    "turns": 1.1,
                },
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify spiral type
        assert data["soundhole_type"] == "spiral"
        assert data["spiral_params"] is not None

        # Verify geometry
        assert data["area_mm2"] is not None
        assert data["perimeter_mm"] is not None
        assert data["pa_ratio_mm_inv"] is not None

        # P:A should be approximately 2/slot_width = 2/14 ≈ 0.143
        assert 0.10 <= data["pa_ratio_mm_inv"] <= 0.20

        # Should be above Williams threshold
        assert any("above" in note.lower() or "threshold" in note.lower() for note in data["notes"])

    def test_soundhole_spiral_default_params(self):
        """POST spiral without params uses defaults."""
        response = client.post(
            "/api/instrument/soundhole",
            json={
                "body_style": "dreadnought",
                "body_length_mm": 500.0,
                "soundhole_type": "spiral",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["soundhole_type"] == "spiral"
        # Should use default params (14mm slot width)
        assert data["pa_ratio_mm_inv"] is not None
        assert data["pa_ratio_mm_inv"] > 0.10  # Above Williams threshold

    def test_soundhole_oval_type(self):
        """POST /api/instrument/soundhole with type=oval."""
        response = client.post(
            "/api/instrument/soundhole",
            json={
                "body_style": "dreadnought",
                "body_length_mm": 500.0,
                "soundhole_type": "oval",
                "custom_diameter_mm": 80.0,  # Major axis
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["soundhole_type"] == "oval"
        assert "Oval" in data["notes"][0] or "oval" in data["notes"][0].lower()

    def test_soundhole_fhole_type(self):
        """POST /api/instrument/soundhole with type=fhole."""
        response = client.post(
            "/api/instrument/soundhole",
            json={
                "body_style": "archtop",
                "body_length_mm": 520.0,
                "soundhole_type": "fhole",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["soundhole_type"] == "fhole"
        assert data["gate"] == "YELLOW"  # F-holes use separate calculator

    def test_soundhole_spiral_pa_validation(self):
        """Spiral with narrow slot gets P:A warning."""
        response = client.post(
            "/api/instrument/soundhole",
            json={
                "body_style": "dreadnought",
                "body_length_mm": 500.0,
                "soundhole_type": "spiral",
                "spiral_params": {
                    "slot_width_mm": 25.0,  # Wide slot = low P:A
                    "start_radius_mm": 10.0,
                    "growth_rate_k": 0.18,
                    "turns": 1.1,
                },
            },
        )

        assert response.status_code == 200
        data = response.json()

        # P:A = 2/25 = 0.08 — below threshold
        assert data["pa_ratio_mm_inv"] < 0.10
        # Should have warning about being below threshold
        assert any("below" in note.lower() for note in data["notes"])

    def test_soundhole_backward_compatibility(self):
        """Default request (no type) returns round soundhole."""
        response = client.post(
            "/api/instrument/soundhole",
            json={
                "body_style": "om_000",
                "body_length_mm": 495.0,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Should default to round
        assert data["soundhole_type"] == "round"
        assert data["diameter_mm"] == 98.0  # OM standard
