"""
Tests for Scale Validation Gate

Regression tests for known scale extraction failures:
- Cuatro at 2.5× (524×951mm extracted, expected ~260×375mm)
- Explorer at 0.7× (302×419mm extracted, expected ~480×475mm)

These tests ensure the gate catches real failures that previously
shipped incorrect DXF files.

Author: Production Shop
Date: 2026-04-14
"""

import pytest

from app.services.scale_validation import (
    validate_scale_before_export,
    get_body_bounds,
    compute_scale_correction,
    GENERIC_BOUNDS_MM,
    _reset_cache,
)


class TestScaleValidationGate:
    """Core validation gate tests."""

    def setup_method(self):
        """Reset cache before each test."""
        _reset_cache()

    # ─────────────────────────────────────────────────────────────────────────
    # REGRESSION TESTS — These are the documented failure cases
    # ─────────────────────────────────────────────────────────────────────────

    def test_cuatro_2_5x_scale_error_blocked(self):
        """
        REGRESSION: Cuatro extracted at 2.5× scale should be blocked.

        Documented failure: 524×951mm extracted, spec says ~260×375mm.
        This is a 2.5× scale error that would produce wrong CAM output.
        """
        # The actual bad extraction values from the bug report
        violation = validate_scale_before_export(
            width_mm=524,
            height_mm=951,
            spec_name="cuatro",
        )

        assert violation is not None
        assert "951" in violation or "524" in violation
        assert "cuatro" in violation

    def test_explorer_0_7x_scale_error_blocked(self):
        """
        REGRESSION: Explorer extracted at 0.7× scale should be blocked.

        Documented failure: 302×419mm extracted, spec says ~480×475mm.
        This is a 35% undersized error — SILENT failure without the gate.
        """
        # The actual bad extraction values from the bug report
        violation = validate_scale_before_export(
            width_mm=302,
            height_mm=419,
            spec_name="gibson_explorer",
        )

        assert violation is not None
        # Width error should be caught (302 vs expected ~480)
        assert "302" in violation or "Width" in violation
        assert "gibson_explorer" in violation

    # ─────────────────────────────────────────────────────────────────────────
    # VALID EXTRACTION TESTS — These should pass
    # ─────────────────────────────────────────────────────────────────────────

    def test_valid_explorer_passes(self):
        """Valid Explorer extraction should pass."""
        # Within ±20% of expected 480×475mm
        violation = validate_scale_before_export(
            width_mm=480,
            height_mm=475,
            spec_name="gibson_explorer",
        )
        assert violation is None

    def test_valid_cuatro_passes(self):
        """Valid cuatro extraction should pass."""
        # Within ±20% of expected 260×375mm
        violation = validate_scale_before_export(
            width_mm=260,
            height_mm=375,
            spec_name="cuatro",
        )
        assert violation is None

    def test_valid_dreadnought_passes(self):
        """Valid dreadnought extraction should pass."""
        # Dreadnought: body_length=520, lower_bout=381
        violation = validate_scale_before_export(
            width_mm=380,
            height_mm=520,
            spec_name="dreadnought",
        )
        assert violation is None

    def test_valid_stratocaster_passes(self):
        """Valid Stratocaster extraction should pass."""
        # Strat: body_length=406, lower_bout=408
        violation = validate_scale_before_export(
            width_mm=400,
            height_mm=410,
            spec_name="stratocaster",
        )
        assert violation is None

    # ─────────────────────────────────────────────────────────────────────────
    # GENERIC BOUNDS TESTS
    # ─────────────────────────────────────────────────────────────────────────

    def test_unknown_spec_uses_generic_bounds(self):
        """Unknown spec_name falls back to generic bounds."""
        bounds = get_body_bounds("nonexistent_guitar")
        assert bounds == GENERIC_BOUNDS_MM

    def test_no_spec_uses_generic_bounds(self):
        """No spec_name falls back to generic bounds."""
        bounds = get_body_bounds(None)
        assert bounds == GENERIC_BOUNDS_MM

    def test_generic_bounds_catch_extreme_oversized(self):
        """Generic bounds should catch obviously oversized extractions."""
        # 1000mm height is way outside generic bounds (200-900)
        violation = validate_scale_before_export(
            width_mm=400,
            height_mm=1000,
            spec_name=None,
        )
        assert violation is not None
        assert "1000" in violation

    def test_generic_bounds_catch_extreme_undersized(self):
        """Generic bounds should catch obviously undersized extractions."""
        # 100mm width is below generic minimum (150)
        violation = validate_scale_before_export(
            width_mm=100,
            height_mm=400,
            spec_name=None,
        )
        assert violation is not None
        assert "100" in violation

    def test_generic_bounds_allow_reasonable_unknown(self):
        """Generic bounds should allow reasonable dimensions for unknown specs."""
        # 350×500mm is reasonable for many guitars
        violation = validate_scale_before_export(
            width_mm=350,
            height_mm=500,
            spec_name=None,
        )
        assert violation is None

    # ─────────────────────────────────────────────────────────────────────────
    # SCALE CORRECTION SUGGESTION TESTS
    # ─────────────────────────────────────────────────────────────────────────

    def test_correction_factor_for_2_5x_error(self):
        """Correction factor for 2.5× error should be ~0.4."""
        correction, explanation = compute_scale_correction(
            width_mm=524,
            height_mm=951,
            spec_name="cuatro",
        )

        # Expected: 260/524 ≈ 0.5, 375/951 ≈ 0.39, average ≈ 0.45
        assert 0.3 < correction < 0.6
        assert "cuatro" not in explanation or "260" in explanation or "375" in explanation

    def test_correction_factor_for_undersized_error(self):
        """Correction factor for undersized error should be >1."""
        correction, explanation = compute_scale_correction(
            width_mm=302,
            height_mm=419,
            spec_name="gibson_explorer",
        )

        # Expected: 480/302 ≈ 1.6, 475/419 ≈ 1.13, average ≈ 1.37
        assert correction > 1.0
        assert "302" in explanation or "419" in explanation


class TestBoundsLoading:
    """Tests for spec bounds loading."""

    def setup_method(self):
        _reset_cache()

    def test_known_specs_have_tight_bounds(self):
        """Known specs should have tighter bounds than generic."""
        dread_bounds = get_body_bounds("dreadnought")
        generic_bounds = GENERIC_BOUNDS_MM

        # Dreadnought bounds should be tighter than generic
        w_min_d, w_max_d, h_min_d, h_max_d = dread_bounds
        w_min_g, w_max_g, h_min_g, h_max_g = generic_bounds

        assert w_max_d - w_min_d < w_max_g - w_min_g
        assert h_max_d - h_min_d < h_max_g - h_min_g

    def test_explorer_bounds_reasonable(self):
        """Explorer bounds should be in expected range."""
        w_min, w_max, h_min, h_max = get_body_bounds("gibson_explorer")

        # Explorer: body_length=460, lower_bout_width=475 (from gibson_explorer.json)
        # With ±20% tolerance: width 380-570, height 368-552
        assert 370 < w_min < 390  # ~380
        assert 560 < w_max < 580  # ~570
        assert 360 < h_min < 380  # ~368
        assert 545 < h_max < 560  # ~552

    def test_cuatro_bounds_reasonable(self):
        """Cuatro bounds should be in expected range."""
        w_min, w_max, h_min, h_max = get_body_bounds("cuatro")

        # Cuatro: body_length=375, lower_bout=260
        # With ±20% tolerance: width 208-312, height 300-450
        assert 200 < w_min < 220
        assert 300 < w_max < 320
        assert 290 < h_min < 310
        assert 440 < h_max < 460
