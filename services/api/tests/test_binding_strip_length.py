"""
Tests for BIND-GAP-04: Binding strip length calculator.

Validates:
1. Basic perimeter-based calculation
2. Installation method variations
3. Miter corner waste allowance
4. Outline-based calculation with auto-corner detection
5. Order length rounding
6. API endpoint integration
"""

import pytest
from fastapi.testclient import TestClient

from app.calculators.binding_geometry import (
    InstallationMethod,
    BindingMaterial,
    BindingStripEstimate,
    calculate_binding_strip_length,
    calculate_binding_strip_from_outline,
)
from app.main import app


client = TestClient(app)


class TestStripLengthCalculation:
    """Test core strip length calculation logic."""

    def test_single_continuous_basic(self):
        """Single continuous strip for typical acoustic body."""
        # Typical OM perimeter ~1000mm
        estimate = calculate_binding_strip_length(
            perimeter_mm=1000.0,
            installation_method=InstallationMethod.SINGLE_CONTINUOUS,
            num_joints=1,
            include_top=True,
            include_back=True,
        )

        # Single continuous strip wraps the perimeter once
        assert estimate.perimeter_mm == 1000.0
        assert estimate.minimum_length_mm == 1000.0

        # Recommended includes overlap + handling waste
        assert estimate.recommended_length_mm > estimate.minimum_length_mm

        # Order length rounded to 50mm
        assert estimate.order_length_mm % 50 == 0
        assert estimate.order_length_mm >= estimate.recommended_length_mm

    def test_top_and_back_method(self):
        """Top and back as separate strips (halves of perimeter)."""
        estimate = calculate_binding_strip_length(
            perimeter_mm=1000.0,
            installation_method=InstallationMethod.TOP_AND_BACK,
            include_top=True,
            include_back=True,
        )

        # Should have 2 sections (top_edge and back_edge)
        assert len(estimate.sections) == 2
        assert estimate.sections[0]["name"] == "top_edge"
        assert estimate.sections[1]["name"] == "back_edge"
        # Each section is half perimeter
        assert estimate.sections[0]["length_mm"] == 500.0
        assert estimate.sections[1]["length_mm"] == 500.0

    def test_traditional_acoustic(self):
        """Traditional acoustic with top rim and back rim."""
        estimate = calculate_binding_strip_length(
            perimeter_mm=1000.0,
            installation_method=InstallationMethod.TRADITIONAL_ACOUSTIC,
            include_top=True,
            include_back=True,
        )

        # Should have 2 sections (top_rim and back_rim, no sides)
        assert len(estimate.sections) == 2
        assert estimate.sections[0]["name"] == "top_rim"
        assert estimate.sections[1]["name"] == "back_rim"

    def test_miter_waste_added(self):
        """Miter corners add waste allowance."""
        no_miters = calculate_binding_strip_length(
            perimeter_mm=1000.0,
            installation_method=InstallationMethod.SINGLE_CONTINUOUS,
            num_miter_corners=0,
        )

        with_miters = calculate_binding_strip_length(
            perimeter_mm=1000.0,
            installation_method=InstallationMethod.SINGLE_CONTINUOUS,
            num_miter_corners=4,
        )

        # More miter corners = more waste
        assert with_miters.miter_waste_mm > no_miters.miter_waste_mm
        assert with_miters.recommended_length_mm > no_miters.recommended_length_mm

    def test_handling_waste_percentage(self):
        """Handling waste scales with length."""
        low_waste = calculate_binding_strip_length(
            perimeter_mm=1000.0,
            installation_method=InstallationMethod.SINGLE_CONTINUOUS,
            handling_waste_percent=2.0,
        )

        high_waste = calculate_binding_strip_length(
            perimeter_mm=1000.0,
            installation_method=InstallationMethod.SINGLE_CONTINUOUS,
            handling_waste_percent=10.0,
        )

        assert high_waste.handling_waste_mm > low_waste.handling_waste_mm

    def test_top_only(self):
        """Top binding only (no back)."""
        estimate = calculate_binding_strip_length(
            perimeter_mm=1000.0,
            installation_method=InstallationMethod.SINGLE_CONTINUOUS,
            include_top=True,
            include_back=False,
        )

        # Minimum should be ~1 perimeter (just top)
        assert estimate.minimum_length_mm == pytest.approx(1000.0, rel=0.01)

    def test_includes_sides(self):
        """Include side binding (laminated sides) - requires TRADITIONAL_ACOUSTIC method."""
        without_sides = calculate_binding_strip_length(
            perimeter_mm=1000.0,
            installation_method=InstallationMethod.TRADITIONAL_ACOUSTIC,
            include_top=True,
            include_back=True,
            include_sides=False,
        )

        with_sides = calculate_binding_strip_length(
            perimeter_mm=1000.0,
            installation_method=InstallationMethod.TRADITIONAL_ACOUSTIC,
            include_top=True,
            include_back=True,
            include_sides=True,
            side_depth_mm=100.0,
        )

        # With sides adds side strip sections
        assert with_sides.minimum_length_mm > without_sides.minimum_length_mm
        assert len(with_sides.sections) > len(without_sides.sections)


class TestOutlineBasedCalculation:
    """Test outline-based strip length calculation."""

    def test_square_outline_detects_corners(self):
        """Square outline auto-detects 4 miter corners."""
        # Simple square 100×100mm
        square = [
            (0.0, 0.0),
            (100.0, 0.0),
            (100.0, 100.0),
            (0.0, 100.0),
            (0.0, 0.0),  # close
        ]

        estimate = calculate_binding_strip_from_outline(
            outline_points=square,
            installation_method=InstallationMethod.SINGLE_CONTINUOUS,
        )

        # Perimeter = 400mm
        assert estimate.perimeter_mm == pytest.approx(400.0, rel=0.01)

        # Should detect 4 corners (90° turns)
        assert estimate.miter_waste_mm > 0

    def test_circle_outline_no_corners(self):
        """Circle/smooth outline has no miter corners."""
        import math

        # Generate circle points
        n_points = 36
        radius = 100.0
        circle = [
            (radius * math.cos(2 * math.pi * i / n_points),
             radius * math.sin(2 * math.pi * i / n_points))
            for i in range(n_points + 1)
        ]

        estimate = calculate_binding_strip_from_outline(
            outline_points=circle,
            installation_method=InstallationMethod.SINGLE_CONTINUOUS,
        )

        # Perimeter ~628mm (2πr)
        expected_perimeter = 2 * math.pi * radius
        assert estimate.perimeter_mm == pytest.approx(expected_perimeter, rel=0.05)

        # No sharp corners
        assert estimate.miter_waste_mm == 0.0


class TestStripLengthEndpoint:
    """Test /api/binding/strip-length endpoint."""

    def test_endpoint_with_perimeter(self):
        """Endpoint accepts perimeter_mm input."""
        response = client.post("/api/binding/strip-length", json={
            "perimeter_mm": 1000.0,
            "installation_method": "single_continuous",
            "include_top": True,
            "include_back": True,
        })

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["perimeter_mm"] == 1000.0
        assert data["order_length_mm"] > 0
        assert data["order_length_mm"] % 50 == 0

    def test_endpoint_with_body_style(self):
        """Endpoint accepts body_style input."""
        response = client.post("/api/binding/strip-length", json={
            "body_style": "om",
            "installation_method": "single_continuous",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["perimeter_mm"] > 0

    def test_endpoint_rejects_both_inputs(self):
        """Endpoint rejects both body_style AND perimeter_mm."""
        response = client.post("/api/binding/strip-length", json={
            "body_style": "om",
            "perimeter_mm": 1000.0,
        })

        assert response.status_code == 400

    def test_endpoint_rejects_neither_input(self):
        """Endpoint requires body_style OR perimeter_mm."""
        response = client.post("/api/binding/strip-length", json={
            "installation_method": "single_continuous",
        })

        assert response.status_code == 400

    def test_endpoint_invalid_method(self):
        """Endpoint rejects invalid installation method."""
        response = client.post("/api/binding/strip-length", json={
            "perimeter_mm": 1000.0,
            "installation_method": "invalid_method",
        })

        assert response.status_code == 400
        assert "available_methods" in response.json()["detail"]

    def test_endpoint_top_and_back(self):
        """Endpoint handles top_and_back method."""
        response = client.post("/api/binding/strip-length", json={
            "perimeter_mm": 1000.0,
            "installation_method": "top_and_back",
        })

        assert response.status_code == 200
        data = response.json()
        assert len(data["sections"]) == 2
