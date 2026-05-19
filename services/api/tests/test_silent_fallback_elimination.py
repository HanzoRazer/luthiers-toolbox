"""
Tests for Sprint M2: Silent Fallback Elimination.

Verifies that calculators raise ValueError on unknown inputs
instead of silently falling back to defaults.
"""

import pytest


class TestSoundholeExtendedLoudFailure:
    """estimate_plate_air_coupling must raise on unknown species."""

    def test_unknown_species_raises_valueerror(self):
        from app.calculators.soundhole_extended import estimate_plate_air_coupling

        with pytest.raises(ValueError, match="Unknown species"):
            estimate_plate_air_coupling(
                species_key="unobtanium",
                thickness_mm=2.8,
                plate_length_mm=500.0,
                plate_width_mm=400.0,
                f_H_hz=100.0,
            )

    def test_known_species_succeeds(self):
        from app.calculators.soundhole_extended import estimate_plate_air_coupling

        result = estimate_plate_air_coupling(
            species_key="sitka_spruce",
            thickness_mm=2.8,
            plate_length_mm=500.0,
            plate_width_mm=400.0,
            f_H_hz=100.0,
        )
        assert result.status in ("clear", "moderate", "strong")


class TestBackBraceCalcLoudFailure:
    """seam_stress_estimate must raise on unknown material."""

    def test_unknown_material_raises_valueerror(self):
        from app.calculators.back_brace_calc import seam_stress_estimate

        with pytest.raises(ValueError, match="Unknown back material"):
            seam_stress_estimate(
                back_half_width_mm=200.0,
                back_material="unobtanium",
                rh_swing_pct=20.0,
            )

    def test_known_material_succeeds(self):
        from app.calculators.back_brace_calc import seam_stress_estimate

        result = seam_stress_estimate(
            back_half_width_mm=200.0,
            back_material="mahogany",
            rh_swing_pct=20.0,
        )
        assert "delta_total_mm" in result


class TestFinishCalcLoudFailure:
    """finish_calc must raise on unknown wood species."""

    def test_compute_finish_schedule_unknown_species_raises(self):
        from app.calculators.finish_calc import compute_finish_schedule

        with pytest.raises(ValueError, match="Unknown wood species"):
            compute_finish_schedule(
                finish_type="nitro",
                wood_species="unobtanium",
            )

    def test_estimate_grain_fill_coats_unknown_species_raises(self):
        from app.calculators.finish_calc import estimate_grain_fill_coats

        with pytest.raises(ValueError, match="Unknown wood species"):
            estimate_grain_fill_coats(
                wood_species="unobtanium",
                finish_type="nitro",
            )

    def test_known_species_succeeds(self):
        from app.calculators.finish_calc import compute_finish_schedule

        result = compute_finish_schedule(
            finish_type="nitro",
            wood_species="mahogany",
        )
        assert result.total_coats > 0


class TestBindingMaterialsLoudFailure:
    """get_minimum_bend_radius must raise on unknown material."""

    def test_unknown_material_raises_valueerror(self):
        from app.calculators.binding_materials import get_minimum_bend_radius

        with pytest.raises(ValueError, match="Unknown binding material"):
            get_minimum_bend_radius("unobtanium")

    def test_known_material_by_enum_succeeds(self):
        from app.calculators.binding_materials import (
            get_minimum_bend_radius,
            BindingMaterial,
        )

        radius = get_minimum_bend_radius(BindingMaterial.CELLULOID)
        assert radius == 6.0

    def test_known_material_by_string_succeeds(self):
        from app.calculators.binding_materials import get_minimum_bend_radius

        radius = get_minimum_bend_radius("celluloid")
        assert radius == 6.0


class TestHeadstockBreakAngleLoudFailure:
    """get_nut_friction must raise on unknown material."""

    def test_unknown_nut_material_raises_valueerror(self):
        from app.calculators.headstock_break_angle_calc import get_nut_friction

        with pytest.raises(ValueError, match="Unknown nut/tree material"):
            get_nut_friction("unobtanium")

    def test_known_material_succeeds(self):
        from app.calculators.headstock_break_angle_calc import get_nut_friction

        mu = get_nut_friction("bone_dry")
        assert mu == 0.10
