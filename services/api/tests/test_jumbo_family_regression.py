"""
Regression test for jumbo family geometry fix.

Bug: Jumbo spec had "family": "dreadnought" which caused BodyContourSolver
to use dreadnought ratios instead of jumbo-specific ratios.

Fix: Changed jumbo family to "jumbo" and added FAMILY_DEFAULTS["jumbo"]
with canonical dimensions (432mm lower bout, 530mm body length).

This test ensures jumbo dimensions are generated correctly and don't
regress to dreadnought dimensions.

Related:
- vectorizer-sandbox PR #18 (same fix applied there)
- luthiers-toolbox fix/jumbo-family-geometry-bug branch
"""

import pytest


class TestJumboFamilyRegression:
    """Regression tests for jumbo family geometry bug."""

    def test_jumbo_spec_has_correct_family(self):
        """Jumbo spec must declare family='jumbo', not 'dreadnought'."""
        from app.instrument_geometry.body.ibg.instrument_body_generator import (
            INSTRUMENT_SPECS,
        )

        assert "jumbo" in INSTRUMENT_SPECS
        assert INSTRUMENT_SPECS["jumbo"]["family"] == "jumbo"

    def test_jumbo_family_defaults_exist(self):
        """FAMILY_DEFAULTS must have a 'jumbo' entry."""
        from app.instrument_geometry.body.ibg.body_contour_solver import (
            FAMILY_DEFAULTS,
        )

        assert "jumbo" in FAMILY_DEFAULTS

    def test_jumbo_defaults_have_correct_dimensions(self):
        """Jumbo defaults must have canonical jumbo dimensions."""
        from app.instrument_geometry.body.ibg.body_contour_solver import (
            FAMILY_DEFAULTS,
        )

        jumbo = FAMILY_DEFAULTS["jumbo"]

        assert jumbo["lower_bout_mm"] == 432.0
        assert jumbo["upper_bout_mm"] == 305.0
        assert jumbo["waist_mm"] == 254.0
        assert jumbo["body_length_mm"] == 530.0

    def test_jumbo_defaults_distinct_from_dreadnought(self):
        """Jumbo dimensions must be distinct from dreadnought."""
        from app.instrument_geometry.body.ibg.body_contour_solver import (
            FAMILY_DEFAULTS,
        )

        jumbo = FAMILY_DEFAULTS["jumbo"]
        dread = FAMILY_DEFAULTS["dreadnought"]

        assert jumbo["lower_bout_mm"] > dread["lower_bout_mm"]
        assert jumbo["body_length_mm"] > dread["body_length_mm"]

    def test_jumbo_generator_uses_correct_family(self):
        """InstrumentBodyGenerator for jumbo must use jumbo family."""
        from app.instrument_geometry.body.ibg import InstrumentBodyGenerator

        gen = InstrumentBodyGenerator("jumbo")
        assert gen.family == "jumbo"

    def test_jumbo_generated_dimensions_within_tolerance(self):
        """Generated jumbo body must have dimensions within 5% of expected."""
        from app.instrument_geometry.body.ibg import InstrumentBodyGenerator

        gen = InstrumentBodyGenerator("jumbo")
        model = gen.generate_from_defaults()

        expected_lower_bout = 432.0
        expected_body_length = 530.0

        tolerance = 0.05

        lower_bout_error = abs(model.lower_bout_width_mm - expected_lower_bout) / expected_lower_bout
        body_length_error = abs(model.body_length_mm - expected_body_length) / expected_body_length

        assert lower_bout_error <= tolerance, (
            f"Lower bout {model.lower_bout_width_mm}mm exceeds 5% tolerance "
            f"from expected {expected_lower_bout}mm"
        )
        assert body_length_error <= tolerance, (
            f"Body length {model.body_length_mm}mm exceeds 5% tolerance "
            f"from expected {expected_body_length}mm"
        )

    def test_jumbo_not_generating_dreadnought_dimensions(self):
        """Jumbo must NOT produce dreadnought-scale dimensions."""
        from app.instrument_geometry.body.ibg import InstrumentBodyGenerator

        gen = InstrumentBodyGenerator("jumbo")
        model = gen.generate_from_defaults()

        dreadnought_lower_bout = 381.0

        assert model.lower_bout_width_mm > dreadnought_lower_bout + 20, (
            f"Jumbo lower bout {model.lower_bout_width_mm}mm is too close to "
            f"dreadnought {dreadnought_lower_bout}mm — regression to wrong family?"
        )
