# tests/test_strat_variants_smoke.py

"""
Smoke tests for Stratocaster model variants.

GAP-08: Verifies fret count is no longer hardcoded.
"""

import pytest

from app.instrument_geometry.guitars.strat import (
    get_spec,
    get_model_info,
    list_variants,
    MODEL_INFO,
)


class TestStratVariants:
    """Tests for Strat variant support."""

    def test_list_variants_returns_three(self):
        """Three variants should be available."""
        variants = list_variants()
        assert "vintage" in variants
        assert "modern" in variants
        assert "24fret" in variants

    def test_vintage_has_21_frets(self):
        """Vintage Strat has 21 frets."""
        spec = get_spec("vintage")
        assert spec.fret_count == 21

    def test_modern_has_22_frets(self):
        """Modern Strat has 22 frets."""
        spec = get_spec("modern")
        assert spec.fret_count == 22

    def test_24fret_has_24_frets(self):
        """24-fret Strat has 24 frets."""
        spec = get_spec("24fret")
        assert spec.fret_count == 24

    def test_default_is_modern(self):
        """Default get_spec() returns modern (22 frets)."""
        spec = get_spec()
        assert spec.fret_count == 22

    def test_model_info_backward_compatible(self):
        """MODEL_INFO constant still works (backward compat)."""
        assert MODEL_INFO["fret_count"] == 22
        assert MODEL_INFO["scale_length_mm"] == 648.0


class TestStratSpecDetails:
    """Tests for spec details by variant."""

    def test_vintage_single_radius(self):
        """Vintage has single radius (7.25\")."""
        spec = get_spec("vintage")
        # Single radius: base == end
        assert spec.base_radius_mm == pytest.approx(184.15, abs=1.0)

    def test_modern_compound_radius(self):
        """Modern has compound radius (9.5\" to 12\")."""
        spec = get_spec("modern")
        assert spec.base_radius_mm == pytest.approx(241.3, abs=1.0)
        assert spec.end_radius_mm == pytest.approx(304.8, abs=1.0)

    def test_24fret_flatter_radius(self):
        """24-fret has flatter compound radius (12\" to 16\")."""
        spec = get_spec("24fret")
        assert spec.base_radius_mm == pytest.approx(304.8, abs=1.0)
        assert spec.end_radius_mm == pytest.approx(406.4, abs=1.0)

    def test_all_variants_same_scale_length(self):
        """All variants have 648mm (25.5\") scale."""
        for variant in list_variants():
            spec = get_spec(variant)
            assert spec.scale_length_mm == 648.0


class TestModelInfo:
    """Tests for get_model_info()."""

    def test_model_info_includes_variant(self):
        """get_model_info includes variant name."""
        info = get_model_info("24fret")
        assert info["variant"] == "24fret"
        assert "24fret" in info["id"]

    def test_model_info_fret_count_varies(self):
        """Different variants have different fret counts."""
        assert get_model_info("vintage")["fret_count"] == 21
        assert get_model_info("modern")["fret_count"] == 22
        assert get_model_info("24fret")["fret_count"] == 24
