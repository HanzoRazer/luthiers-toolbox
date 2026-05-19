"""
Endpoint tests for aperture_geometry response augmentation.

Verifies that spiral geometry endpoints include the new aperture_geometry
field without breaking existing response structure.

Dev Order 3: Non-breaking API augmentation
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestSpiralGeometryApertureAugmentation:
    """Tests for aperture_geometry field in spiral geometry response."""

    def test_upper_has_aperture_geometry(self):
        """Spiral geometry endpoint returns upper.aperture_geometry."""
        response = client.post(
            "/api/instrument/soundhole/spiral/geometry",
            json={
                "upper": {
                    "center_x_mm": -88.0,
                    "center_y_mm": -62.0,
                    "start_radius_mm": 10.0,
                    "growth_rate_k": 0.18,
                    "turns": 1.1,
                    "slot_width_mm": 14.0,
                    "rotation_deg": 270.0,
                },
                "lower": {
                    "center_x_mm": 78.0,
                    "center_y_mm": 112.0,
                    "start_radius_mm": 10.0,
                    "growth_rate_k": 0.18,
                    "turns": 1.1,
                    "slot_width_mm": 14.0,
                    "rotation_deg": 90.0,
                },
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "upper" in data
        assert "aperture_geometry" in data["upper"]

    def test_lower_has_aperture_geometry(self):
        """Spiral geometry endpoint returns lower.aperture_geometry."""
        response = client.post(
            "/api/instrument/soundhole/spiral/geometry",
            json={
                "upper": {
                    "center_x_mm": -88.0,
                    "center_y_mm": -62.0,
                    "start_radius_mm": 10.0,
                    "growth_rate_k": 0.18,
                    "turns": 1.1,
                    "slot_width_mm": 14.0,
                    "rotation_deg": 270.0,
                },
                "lower": {
                    "center_x_mm": 78.0,
                    "center_y_mm": 112.0,
                    "start_radius_mm": 10.0,
                    "growth_rate_k": 0.18,
                    "turns": 1.1,
                    "slot_width_mm": 14.0,
                    "rotation_deg": 90.0,
                },
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "lower" in data
        assert "aperture_geometry" in data["lower"]

    def test_aperture_type_is_spiral(self):
        """aperture_geometry.aperture_type == 'spiral'."""
        response = client.post(
            "/api/instrument/soundhole/spiral/geometry",
            json={
                "upper": {
                    "center_x_mm": -88.0,
                    "center_y_mm": -62.0,
                    "start_radius_mm": 10.0,
                    "growth_rate_k": 0.18,
                    "turns": 1.1,
                    "slot_width_mm": 14.0,
                    "rotation_deg": 270.0,
                },
                "lower": {
                    "center_x_mm": 78.0,
                    "center_y_mm": 112.0,
                    "start_radius_mm": 10.0,
                    "growth_rate_k": 0.18,
                    "turns": 1.1,
                    "slot_width_mm": 14.0,
                    "rotation_deg": 90.0,
                },
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["upper"]["aperture_geometry"]["aperture_type"] == "spiral"
        assert data["lower"]["aperture_geometry"]["aperture_type"] == "spiral"

    def test_aperture_geometry_matches_legacy_fields(self):
        """aperture_geometry values match legacy area_mm2, perimeter_mm, total_length_mm."""
        response = client.post(
            "/api/instrument/soundhole/spiral/geometry",
            json={
                "upper": {
                    "center_x_mm": -88.0,
                    "center_y_mm": -62.0,
                    "start_radius_mm": 10.0,
                    "growth_rate_k": 0.18,
                    "turns": 1.1,
                    "slot_width_mm": 14.0,
                    "rotation_deg": 270.0,
                },
                "lower": {
                    "center_x_mm": 78.0,
                    "center_y_mm": 112.0,
                    "start_radius_mm": 10.0,
                    "growth_rate_k": 0.18,
                    "turns": 1.1,
                    "slot_width_mm": 14.0,
                    "rotation_deg": 90.0,
                },
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Upper spiral
        upper = data["upper"]
        upper_ag = upper["aperture_geometry"]
        assert upper_ag["area_mm2"] == upper["area_mm2"]
        assert upper_ag["perimeter_mm"] == upper["perimeter_mm"]
        assert upper_ag["path_length_mm"] == upper["total_length_mm"]
        assert upper_ag["pa_ratio_mm_inv"] == upper["pa_ratio_mm_inv"]

        # Lower spiral
        lower = data["lower"]
        lower_ag = lower["aperture_geometry"]
        assert lower_ag["area_mm2"] == lower["area_mm2"]
        assert lower_ag["perimeter_mm"] == lower["perimeter_mm"]
        assert lower_ag["path_length_mm"] == lower["total_length_mm"]
        assert lower_ag["pa_ratio_mm_inv"] == lower["pa_ratio_mm_inv"]

    def test_aperture_geometry_has_equivalent_diameter(self):
        """aperture_geometry includes computed equivalent_diameter_mm."""
        response = client.post(
            "/api/instrument/soundhole/spiral/geometry",
            json={
                "upper": {
                    "center_x_mm": -88.0,
                    "center_y_mm": -62.0,
                    "start_radius_mm": 10.0,
                    "growth_rate_k": 0.18,
                    "turns": 1.1,
                    "slot_width_mm": 14.0,
                    "rotation_deg": 270.0,
                },
                "lower": {
                    "center_x_mm": 78.0,
                    "center_y_mm": 112.0,
                    "start_radius_mm": 10.0,
                    "growth_rate_k": 0.18,
                    "turns": 1.1,
                    "slot_width_mm": 14.0,
                    "rotation_deg": 90.0,
                },
            },
        )

        assert response.status_code == 200
        data = response.json()

        # equivalent_diameter should be computed from area
        upper_ag = data["upper"]["aperture_geometry"]
        assert "equivalent_diameter_mm" in upper_ag
        assert upper_ag["equivalent_diameter_mm"] > 0

        # Verify formula: d = 2 * sqrt(area / pi)
        import math
        expected_d = 2.0 * math.sqrt(upper_ag["area_mm2"] / math.pi)
        assert abs(upper_ag["equivalent_diameter_mm"] - expected_d) < 0.01

    def test_aperture_geometry_has_characteristic_width(self):
        """aperture_geometry includes slot_width as characteristic_width_mm."""
        response = client.post(
            "/api/instrument/soundhole/spiral/geometry",
            json={
                "upper": {
                    "center_x_mm": -88.0,
                    "center_y_mm": -62.0,
                    "start_radius_mm": 10.0,
                    "growth_rate_k": 0.18,
                    "turns": 1.1,
                    "slot_width_mm": 14.0,
                    "rotation_deg": 270.0,
                },
                "lower": {
                    "center_x_mm": 78.0,
                    "center_y_mm": 112.0,
                    "start_radius_mm": 10.0,
                    "growth_rate_k": 0.18,
                    "turns": 1.1,
                    "slot_width_mm": 16.0,  # Different width
                    "rotation_deg": 90.0,
                },
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["upper"]["aperture_geometry"]["characteristic_width_mm"] == 14.0
        assert data["lower"]["aperture_geometry"]["characteristic_width_mm"] == 16.0


class TestLegacyFieldsPreserved:
    """Tests that existing legacy fields are still present."""

    def test_legacy_upper_fields_present(self):
        """Upper spiral still has all legacy fields."""
        response = client.post(
            "/api/instrument/soundhole/spiral/geometry",
            json={
                "upper": {
                    "center_x_mm": -88.0,
                    "center_y_mm": -62.0,
                    "start_radius_mm": 10.0,
                    "growth_rate_k": 0.18,
                    "turns": 1.1,
                    "slot_width_mm": 14.0,
                    "rotation_deg": 270.0,
                },
                "lower": {
                    "center_x_mm": 78.0,
                    "center_y_mm": 112.0,
                    "start_radius_mm": 10.0,
                    "growth_rate_k": 0.18,
                    "turns": 1.1,
                    "slot_width_mm": 14.0,
                    "rotation_deg": 90.0,
                },
            },
        )

        assert response.status_code == 200
        upper = response.json()["upper"]

        # All legacy fields must still be present
        assert "centerline" in upper
        assert "outer_wall" in upper
        assert "inner_wall" in upper
        assert "area_mm2" in upper
        assert "perimeter_mm" in upper
        assert "pa_ratio_mm_inv" in upper
        assert "end_radius_mm" in upper
        assert "total_length_mm" in upper

    def test_legacy_dual_level_fields_present(self):
        """Dual-spiral level fields still present."""
        response = client.post(
            "/api/instrument/soundhole/spiral/geometry",
            json={
                "upper": {
                    "center_x_mm": -88.0,
                    "center_y_mm": -62.0,
                    "start_radius_mm": 10.0,
                    "growth_rate_k": 0.18,
                    "turns": 1.1,
                    "slot_width_mm": 14.0,
                    "rotation_deg": 270.0,
                },
                "lower": {
                    "center_x_mm": 78.0,
                    "center_y_mm": 112.0,
                    "start_radius_mm": 10.0,
                    "growth_rate_k": 0.18,
                    "turns": 1.1,
                    "slot_width_mm": 14.0,
                    "rotation_deg": 90.0,
                },
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Dual-level legacy fields
        assert "total_area_mm2" in data
        assert "round_ref_area_mm2" in data
        assert "area_ratio_pct" in data
        assert "pa_threshold_upper" in data
        assert "pa_threshold_lower" in data
        assert "williams_2019_note" in data
        assert "acoustic_verdict" in data
