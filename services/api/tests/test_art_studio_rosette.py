# tests/test_art_studio_rosette.py

"""
Tests for Rosette Calculator Facade.

Tests the core rosette channel calculation logic via the calculator facade
(app.calculators.rosette_calc). The HTTP API was consolidated to
/api/art/rosette/* in January 2026 with a different schema.
"""

import pytest


class TestRosetteCalculator:
    """Tests for rosette calculator façade."""

    def test_calculate_rosette_channel_basic(self):
        """Test basic rosette channel calculation."""
        from app.calculators.rosette_calc import (
            RosetteCalcInput,
            PurflingBand,
            calculate_rosette_channel,
        )

        input_data = RosetteCalcInput(
            soundhole_diameter_mm=100.0,
            central_band_mm=3.0,
            inner_purfling=[PurflingBand(material="bwb", width_mm=1.5)],
            outer_purfling=[PurflingBand(material="bwb", width_mm=1.5)],
            channel_depth_mm=1.5,
        )

        result = calculate_rosette_channel(input_data)

        assert result.soundhole_diameter_mm == 100.0
        assert result.soundhole_radius_mm == 50.0
        assert result.channel_width_mm > 0
        assert result.channel_depth_mm == 1.5
        assert result.channel_inner_radius_mm <= result.soundhole_radius_mm
        assert result.channel_outer_radius_mm > result.soundhole_radius_mm

    def test_calculate_rosette_with_multiple_purfling(self):
        """Test rosette with multiple purfling bands."""
        from app.calculators.rosette_calc import (
            RosetteCalcInput,
            PurflingBand,
            calculate_rosette_channel,
        )

        input_data = RosetteCalcInput(
            soundhole_diameter_mm=85.0,
            central_band_mm=12.0,
            inner_purfling=[
                PurflingBand(material="bwb", width_mm=1.5),
                PurflingBand(material="maple", width_mm=0.5),
            ],
            outer_purfling=[
                PurflingBand(material="maple", width_mm=0.5),
                PurflingBand(material="bwb", width_mm=1.5),
            ],
            channel_depth_mm=2.0,
        )

        result = calculate_rosette_channel(input_data)

        assert result.soundhole_diameter_mm == 85.0
        assert result.channel_width_mm > 12.0  # At least central band width
        assert result.stack.central_band_width_mm >= 0

    def test_presets_available(self):
        """Test that presets are available."""
        from app.calculators.rosette_calc import list_presets, get_preset

        presets = list_presets()
        assert len(presets) >= 3
        assert "classical_simple" in presets
        assert "steel_string_standard" in presets

        # Get a specific preset
        preset = get_preset("steel_string_standard")
        assert preset is not None
        assert preset.soundhole_diameter_mm == 100.0
