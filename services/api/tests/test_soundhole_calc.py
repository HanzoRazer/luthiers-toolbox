"""
Tests for GEOMETRY-002: Soundhole Placement and Sizing Calculator.
"""

import pytest
from app.calculators.soundhole_calc import (
    SoundholeSpec,
    compute_soundhole_spec,
    check_soundhole_position,
    list_body_styles,
    get_standard_diameter,
    STANDARD_DIAMETERS_MM,
)


class TestComputeSoundholeSpec:
    """Tests for compute_soundhole_spec function."""

    def test_dreadnought_standard_diameter(self):
        """Dreadnought should use 100mm standard diameter."""
        spec = compute_soundhole_spec(
            body_style="dreadnought",
            body_length_mm=500.0,
        )
        assert spec.diameter_mm == 100.0
        assert spec.body_style == "dreadnought"
        assert spec.gate == "GREEN"

    def test_om_000_standard_diameter(self):
        """OM/000 should use 98mm standard diameter."""
        spec = compute_soundhole_spec(
            body_style="om_000",
            body_length_mm=485.0,
        )
        assert spec.diameter_mm == 98.0
        assert spec.body_style == "om_000"
        assert spec.gate == "GREEN"

    def test_parlor_standard_diameter(self):
        """Parlor should use 85mm standard diameter."""
        spec = compute_soundhole_spec(
            body_style="parlor",
            body_length_mm=440.0,
        )
        assert spec.diameter_mm == 85.0
        assert spec.body_style == "parlor"
        assert spec.gate == "GREEN"

    def test_classical_standard_diameter(self):
        """Classical should use 85mm standard diameter."""
        spec = compute_soundhole_spec(
            body_style="classical",
            body_length_mm=490.0,
        )
        assert spec.diameter_mm == 85.0
        assert spec.body_style == "classical"
        assert spec.gate == "GREEN"

    def test_custom_diameter_override(self):
        """Custom diameter should override standard."""
        spec = compute_soundhole_spec(
            body_style="dreadnought",
            body_length_mm=500.0,
            custom_diameter_mm=95.0,
        )
        assert spec.diameter_mm == 95.0
        # Custom 95mm differs from standard 100mm by 5mm, should trigger note
        assert spec.gate == "GREEN"  # 5mm deviation is acceptable


class TestCheckSoundholePosition:
    """Tests for check_soundhole_position function."""

    def test_standard_position_returns_green(self):
        """Standard position (50% of body length) should return GREEN."""
        # Position at 50% of 500mm body = 250mm
        gate = check_soundhole_position(
            diameter_mm=100.0,
            position_mm=250.0,
            body_length_mm=500.0,
        )
        assert gate == "GREEN"

    def test_marginal_position_returns_yellow(self):
        """Position at 43% should return YELLOW (outside 45-55% but inside 40-60%)."""
        # Position at 43% of 500mm body = 215mm
        gate = check_soundhole_position(
            diameter_mm=100.0,
            position_mm=215.0,
            body_length_mm=500.0,
        )
        assert gate == "YELLOW"

    def test_invalid_position_returns_red(self):
        """Position at 35% should return RED (outside 40-60%)."""
        # Position at 35% of 500mm body = 175mm
        gate = check_soundhole_position(
            diameter_mm=100.0,
            position_mm=175.0,
            body_length_mm=500.0,
        )
        assert gate == "RED"


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_list_body_styles_excludes_archtop(self):
        """list_body_styles should not include archtop."""
        styles = list_body_styles()
        assert "archtop" not in styles
        assert "dreadnought" in styles
        assert "om_000" in styles

    def test_get_standard_diameter_known_style(self):
        """get_standard_diameter should return correct value for known style."""
        assert get_standard_diameter("dreadnought") == 100.0
        assert get_standard_diameter("om_000") == 98.0
        assert get_standard_diameter("parlor") == 85.0

    def test_get_standard_diameter_unknown_style(self):
        """get_standard_diameter should return None for unknown style."""
        assert get_standard_diameter("unknown_style") is None


class TestArchtopSpecialCase:
    """Tests for archtop body style (uses f-holes)."""

    def test_archtop_returns_yellow_gate(self):
        """Archtop should return YELLOW with f-hole recommendation."""
        spec = compute_soundhole_spec(
            body_style="archtop",
            body_length_mm=500.0,
        )
        assert spec.gate == "YELLOW"
        assert spec.diameter_mm == 0.0
        assert any("f-hole" in note.lower() for note in spec.notes)
