"""
Tests for bridge_calc.py — GEOMETRY-004.

Validates bridge geometry calculations for various body styles.

Expected results:
- Dreadnought: spacing=54mm, length=170mm, width=32mm
- OM/000: spacing=52mm, length=165mm, width=30mm
- Classical: spacing=58mm, tie block (no pins)
- Archtop: spacing=52mm, tune-o-matic style
"""

import pytest

from app.calculators.bridge_calc import (
    compute_bridge_spec,
    compute_pin_positions,
    list_body_styles,
    get_bridge_defaults,
    BridgeSpec,
    PinPositions,
    BRIDGE_SPECS,
)


class TestComputeBridgeSpec:
    """Test bridge specification calculation."""

    def test_dreadnought_dimensions(self):
        """Dreadnought bridge should have standard dimensions."""
        spec = compute_bridge_spec(
            body_style="dreadnought",
            scale_length_mm=645.16,  # 25.4"
        )

        assert isinstance(spec, BridgeSpec)
        assert spec.body_style == "dreadnought"
        assert spec.string_spacing_mm == 54.0
        assert spec.bridge_length_mm == 170.0
        assert spec.bridge_width_mm == 32.0
        assert spec.saddle_slot_width_mm == 3.2
        assert spec.gate == "GREEN"

    def test_om_000_dimensions(self):
        """OM/000 bridge should have narrower dimensions."""
        spec = compute_bridge_spec(
            body_style="om_000",
            scale_length_mm=632.46,  # 24.9"
        )

        assert spec.string_spacing_mm == 52.0
        assert spec.bridge_length_mm == 165.0
        assert spec.bridge_width_mm == 30.0
        assert spec.gate == "GREEN"

    def test_classical_no_pins(self):
        """Classical bridge should have tie block, no pins."""
        spec = compute_bridge_spec(
            body_style="classical",
            scale_length_mm=650.0,
        )

        assert spec.string_spacing_mm == 58.0
        assert spec.pin_spacing_mm == 0.0  # No pins
        assert "tie block" in spec.notes[0].lower()
        assert spec.bridge_plate_length_mm == 0.0  # No bridge plate

    def test_archtop_tune_o_matic(self):
        """Archtop should have tune-o-matic style."""
        spec = compute_bridge_spec(
            body_style="archtop",
            scale_length_mm=628.65,  # 24.75"
        )

        assert spec.bridge_length_mm == 95.0  # Shorter
        assert spec.saddle_slot_width_mm == 0.0  # No slot
        assert "tune-o-matic" in spec.notes[0].lower()

    def test_custom_spacing_override(self):
        """Custom spacing should override default."""
        spec = compute_bridge_spec(
            body_style="dreadnought",
            scale_length_mm=645.16,
            custom_spacing_mm=56.0,
        )

        assert spec.string_spacing_mm == 56.0
        assert spec.pin_spacing_mm == 56.0  # Pins match spacing

    def test_invalid_body_style_raises(self):
        """Unknown body style should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown body style"):
            compute_bridge_spec(
                body_style="ukulele",
                scale_length_mm=400.0,
            )

    def test_unusual_scale_length_yellow_gate(self):
        """Unusual scale length should trigger YELLOW gate."""
        spec = compute_bridge_spec(
            body_style="dreadnought",
            scale_length_mm=350.0,  # Too short
        )

        assert spec.gate == "YELLOW"
        assert any("unusual scale" in note.lower() for note in spec.notes)


class TestComputePinPositions:
    """Test bridge pin position calculation."""

    def test_six_string_positions(self):
        """Six strings should be evenly distributed."""
        result = compute_pin_positions(
            string_spacing_mm=54.0,
            string_count=6,
        )

        assert isinstance(result, PinPositions)
        assert len(result.positions_mm) == 6
        assert result.total_span_mm == 54.0

        # Check symmetry around center
        assert result.positions_mm[0] == -27.0  # Bass E
        assert result.positions_mm[5] == 27.0   # Treble e

        # Check inter-string spacing (54mm / 5 = 10.8mm)
        spacing = result.positions_mm[1] - result.positions_mm[0]
        assert abs(spacing - 10.8) < 0.01

    def test_pin_positions_with_offset(self):
        """Pin positions should be offset from center."""
        result = compute_pin_positions(
            string_spacing_mm=54.0,
            string_count=6,
            bridge_center_x=100.0,
        )

        # Center should be at 100mm
        assert result.positions_mm[0] == 73.0   # 100 - 27
        assert result.positions_mm[5] == 127.0  # 100 + 27

    def test_single_string(self):
        """Single string should be at center."""
        result = compute_pin_positions(
            string_spacing_mm=54.0,
            string_count=1,
        )

        assert len(result.positions_mm) == 1
        assert result.positions_mm[0] == 0.0
        assert result.total_span_mm == 0.0

    def test_zero_strings(self):
        """Zero strings should return empty list."""
        result = compute_pin_positions(
            string_spacing_mm=54.0,
            string_count=0,
        )

        assert len(result.positions_mm) == 0
        assert result.total_span_mm == 0.0


class TestHelperFunctions:
    """Test utility functions."""

    def test_list_body_styles(self):
        """list_body_styles should return all supported styles."""
        styles = list_body_styles()

        assert "dreadnought" in styles
        assert "om_000" in styles
        assert "parlor" in styles
        assert "classical" in styles
        assert "archtop" in styles
        assert "jumbo" in styles

    def test_get_bridge_defaults_valid(self):
        """get_bridge_defaults should return spec dict."""
        defaults = get_bridge_defaults("dreadnought")

        assert defaults["string_spacing_mm"] == 54.0
        assert defaults["bridge_length_mm"] == 170.0
        assert defaults["material"] == "ebony"

    def test_get_bridge_defaults_invalid(self):
        """get_bridge_defaults should raise for unknown style."""
        with pytest.raises(ValueError, match="Unknown body style"):
            get_bridge_defaults("unknown_style")


class TestBridgeSpecDataclass:
    """Test BridgeSpec dataclass methods."""

    def test_to_dict(self):
        """to_dict should return complete dictionary."""
        spec = compute_bridge_spec(
            body_style="dreadnought",
            scale_length_mm=645.16,
        )

        d = spec.to_dict()

        assert isinstance(d, dict)
        assert d["body_style"] == "dreadnought"
        assert d["string_spacing_mm"] == 54.0
        assert d["gate"] == "GREEN"
        assert "notes" in d
