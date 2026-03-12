# tests/test_pickup_calculator_smoke.py

"""
Smoke tests for pickup position calculator endpoints.

GAP-04: Verifies pickup calculator API is mounted and functional.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class TestPickupCalculatorEndpoints:
    """Smoke tests for pickup calculator API."""

    def test_calculate_sss_layout(self):
        """POST /calculate returns valid SSS layout."""
        response = client.post(
            "/api/instruments/guitar/pickup-calculator/calculate",
            json={
                "scale_length_mm": 647.7,
                "fret_count": 22,
                "configuration": "SSS",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["configuration"] == "SSS"
        assert len(data["pickups"]) == 3
        assert data["pickups"][0]["position"] == "bridge"
        assert data["pickups"][1]["position"] == "middle"
        assert data["pickups"][2]["position"] == "neck"

    def test_calculate_24fret_sss(self):
        """24-fret SSS adjusts neck pickup position."""
        response = client.post(
            "/api/instruments/guitar/pickup-calculator/calculate",
            json={
                "scale_length_mm": 647.7,
                "fret_count": 24,
                "configuration": "SSS",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["fret_count"] == 24
        assert data["fret_24_position_mm"] is not None
        # Neck pickup should be closer to bridge for 24-fret
        neck_pickup = data["pickups"][2]
        assert "24-fret" in neck_pickup["notes"]

    def test_calculate_hh_layout(self):
        """POST /calculate returns valid HH layout."""
        response = client.post(
            "/api/instruments/guitar/pickup-calculator/calculate",
            json={
                "scale_length_mm": 628.65,  # Gibson 24.75"
                "fret_count": 22,
                "configuration": "HH",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["configuration"] == "HH"
        assert len(data["pickups"]) == 2
        assert data["pickups"][0]["pickup_type"] == "humbucker"
        assert data["pickups"][1]["pickup_type"] == "humbucker"

    def test_calculate_hss_layout(self):
        """POST /calculate returns valid HSS layout."""
        response = client.post(
            "/api/instruments/guitar/pickup-calculator/calculate",
            json={
                "scale_length_mm": 647.7,
                "fret_count": 22,
                "configuration": "HSS",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["configuration"] == "HSS"
        assert len(data["pickups"]) == 3
        assert data["pickups"][0]["pickup_type"] == "humbucker"  # Bridge
        assert data["pickups"][1]["pickup_type"] == "single_coil"  # Middle
        assert data["pickups"][2]["pickup_type"] == "single_coil"  # Neck

    def test_list_configurations(self):
        """GET /configurations returns available configs."""
        response = client.get(
            "/api/instruments/guitar/pickup-calculator/configurations"
        )
        assert response.status_code == 200
        data = response.json()
        assert "configurations" in data
        config_ids = [c["id"] for c in data["configurations"]]
        assert "SSS" in config_ids
        assert "HH" in config_ids
        assert "HSS" in config_ids

    def test_list_scale_lengths(self):
        """GET /scale-lengths returns presets."""
        response = client.get(
            "/api/instruments/guitar/pickup-calculator/scale-lengths"
        )
        assert response.status_code == 200
        data = response.json()
        assert "scale_lengths" in data
        preset_ids = [p["id"] for p in data["scale_lengths"]]
        assert "fender_25.5" in preset_ids
        assert "gibson_24.75" in preset_ids

    def test_24fret_strat_preset(self):
        """GET /presets/24fret-strat returns pre-calculated layout."""
        response = client.get(
            "/api/instruments/guitar/pickup-calculator/presets/24fret-strat"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["scale_length_mm"] == 647.7
        assert data["fret_count"] == 24
        assert data["configuration"] == "SSS"
        assert len(data["pickups"]) == 3
