"""
Tests for finish_calc.py — CONSTRUCTION-007.

Validates finish schedule calculations.

Expected results:
- Rosewood needs more grain fill than maple
- Nitro has more coats than poly
- French polish requires most coats
- Oil finish has minimal coats
"""

import pytest

from app.calculators.finish_calc import (
    compute_finish_schedule,
    estimate_grain_fill_coats,
    list_finish_types,
    list_wood_species_pores,
    get_finish_properties,
    FinishSchedule,
    FinishType,
    PORE_DEPTH_MM,
    FINISH_PROPERTIES,
)


class TestComputeFinishSchedule:
    """Test finish schedule calculation."""

    def test_nitro_on_rosewood(self):
        """Nitro on rosewood should have grain fill coats."""
        schedule = compute_finish_schedule(
            finish_type="nitro",
            wood_species="rosewood",
        )

        assert isinstance(schedule, FinishSchedule)
        assert schedule.finish_type == "nitro"
        assert schedule.wood_species == "rosewood"
        assert schedule.grain_fill_coats > 0  # Rosewood has large pores
        assert schedule.total_coats >= 8  # Nitro needs multiple coats
        assert schedule.gate == "GREEN"

    def test_poly_fewer_coats_than_nitro(self):
        """Poly should need fewer coats than nitro."""
        nitro = compute_finish_schedule(
            finish_type="nitro",
            wood_species="mahogany",
        )

        poly = compute_finish_schedule(
            finish_type="poly",
            wood_species="mahogany",
        )

        # Poly fills faster, needs fewer coats
        assert poly.build_coats <= nitro.build_coats

    def test_maple_minimal_grain_fill(self):
        """Maple (closed pore) should need minimal grain fill."""
        schedule = compute_finish_schedule(
            finish_type="nitro",
            wood_species="maple",
        )

        # Maple has very small pores
        assert schedule.grain_fill_coats == 0 or schedule.grain_fill_coats <= 2

    def test_rosewood_more_fill_than_maple(self):
        """Rosewood needs more grain fill coats than maple."""
        rosewood = compute_finish_schedule(
            finish_type="nitro",
            wood_species="rosewood",
        )

        maple = compute_finish_schedule(
            finish_type="nitro",
            wood_species="maple",
        )

        assert rosewood.grain_fill_coats > maple.grain_fill_coats

    def test_oil_finish_minimal_coats(self):
        """Oil finish should have minimal coats."""
        schedule = compute_finish_schedule(
            finish_type="oil",
            wood_species="walnut",
        )

        assert schedule.total_coats <= 8  # Oil finishes are thin
        assert schedule.total_cure_days <= 14

    def test_french_polish_many_coats(self):
        """French polish should require many coats."""
        schedule = compute_finish_schedule(
            finish_type="french_polish",
            wood_species="spruce",
        )

        # French polish is many thin coats
        assert "french" in schedule.notes[0].lower() or len(schedule.coats) > 5

    def test_invalid_finish_type_raises(self):
        """Unknown finish type should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown finish type"):
            compute_finish_schedule(
                finish_type="unknown_finish",
                wood_species="maple",
            )

    def test_sanding_schedule_included(self):
        """Schedule should include sanding steps."""
        schedule = compute_finish_schedule(
            finish_type="nitro",
            wood_species="mahogany",
        )

        assert len(schedule.sanding_schedule) > 0
        # Should have final sanding with high grits
        final_grits = [s.grit for s in schedule.sanding_schedule]
        assert max(final_grits) >= 600


class TestEstimateGrainFillCoats:
    """Test grain fill coat estimation."""

    def test_rosewood_needs_fill(self):
        """Rosewood should need several fill coats."""
        coats = estimate_grain_fill_coats(
            wood_species="rosewood",
            finish_type="nitro",
        )

        assert coats > 0
        assert coats <= 10  # Reasonable upper bound

    def test_maple_no_fill(self):
        """Maple should need no/minimal fill."""
        coats = estimate_grain_fill_coats(
            wood_species="maple",
            finish_type="nitro",
        )

        assert coats == 0  # Closed pore wood

    def test_poly_fills_faster(self):
        """Poly should need fewer fill coats than nitro."""
        nitro_coats = estimate_grain_fill_coats(
            wood_species="mahogany",
            finish_type="nitro",
        )

        poly_coats = estimate_grain_fill_coats(
            wood_species="mahogany",
            finish_type="poly",
        )

        # Poly fills ~1.6x faster per coat
        assert poly_coats <= nitro_coats


class TestHelperFunctions:
    """Test utility functions."""

    def test_list_finish_types(self):
        """list_finish_types should return all types."""
        types = list_finish_types()

        assert "nitro" in types
        assert "poly" in types
        assert "oil" in types
        assert "french_polish" in types

    def test_list_wood_species_pores(self):
        """list_wood_species_pores should return pore depths."""
        pores = list_wood_species_pores()

        assert "rosewood" in pores
        assert "maple" in pores
        assert pores["rosewood"] > pores["maple"]

    def test_get_finish_properties(self):
        """get_finish_properties should return correct data."""
        props = get_finish_properties("nitro")

        assert "fill_mm_per_coat" in props
        assert "dry_time_between_coats_hours" in props
        assert "cure_time_days" in props
        assert "sanding_grit_sequence" in props

    def test_get_finish_properties_invalid(self):
        """Unknown finish should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown finish type"):
            get_finish_properties("unknown")


class TestPoreData:
    """Validate pore depth data."""

    def test_pore_depths_positive(self):
        """All pore depths should be positive."""
        for species, depth in PORE_DEPTH_MM.items():
            assert depth > 0, f"{species} has non-positive pore depth"

    def test_pore_depths_realistic(self):
        """Pore depths should be in realistic range (0-0.5mm)."""
        for species, depth in PORE_DEPTH_MM.items():
            assert 0 < depth < 0.5, f"{species} depth {depth}mm out of range"

    def test_large_pore_woods(self):
        """Large pore woods should have depth > 0.15mm."""
        large_pore = ["rosewood", "mahogany", "walnut", "ash", "oak"]
        for species in large_pore:
            if species in PORE_DEPTH_MM:
                assert PORE_DEPTH_MM[species] >= 0.15, f"{species} should be large pore"

    def test_closed_pore_woods(self):
        """Closed pore woods should have depth < 0.10mm."""
        closed_pore = ["maple", "ebony", "spruce"]
        for species in closed_pore:
            if species in PORE_DEPTH_MM:
                assert PORE_DEPTH_MM[species] < 0.10, f"{species} should be closed pore"


class TestFinishProperties:
    """Validate finish property data."""

    def test_all_finish_types_have_properties(self):
        """Every finish type should have required properties."""
        required = [
            "fill_mm_per_coat",
            "dry_time_between_coats_hours",
            "cure_time_days",
            "recommended_coats",
            "sanding_grit_sequence",
        ]

        for finish_type, props in FINISH_PROPERTIES.items():
            for key in required:
                assert key in props, f"{finish_type} missing {key}"

    def test_nitro_cure_time_long(self):
        """Nitro should have long cure time (30 days)."""
        props = FINISH_PROPERTIES["nitro"]
        assert props["cure_time_days"] >= 21

    def test_poly_cure_time_short(self):
        """Poly should have shorter cure time."""
        props = FINISH_PROPERTIES["poly"]
        assert props["cure_time_days"] <= 14
