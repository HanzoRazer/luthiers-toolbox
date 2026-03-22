"""
Tests for inverse brace sizing calculator - ACOUSTIC-004.

6 test cases:
1. Heavier load increases required EI
2. Tighter deflection limit increases required EI
3. Spruce achieves target (ACHIEVABLE gate)
4. Height formula correctness (rectangular profile)
5. ACHIEVABLE gate (height <= 10mm)
6. NOT_ACHIEVABLE gate (height > 14mm)
"""
import pytest
import math

from app.calculators.bracing_calc import (
    BraceSizingTarget,
    RequiredBraceSpec,
    compute_required_EI,
    compute_brace_dimensions_for_EI,
    solve_brace_sizing,
)
from app.calculators import _bracing_physics as physics


# Standard target for testing - realistic values for achievable bracing
# With parabolic braces, most stiffness comes from the plate.
# For height ~9mm (ACHIEVABLE), brace EI per brace should be ~1.8 N*m²
STANDARD_TARGET = BraceSizingTarget(
    max_deflection_mm=5.0,  # Looser limit typical for classical guitars
    applied_load_n=300.0,  # Moderate saddle force
    plate_length_mm=500.0,  # Typical dreadnought body
    bridge_position_fraction=0.63,
    existing_plate_EI_Nm2=180.0,  # Stiff plate provides most of the stiffness
)


class TestHeavierLoadIncreasesEI:
    """Test 1: Heavier load increases required EI."""

    def test_heavier_load_requires_more_ei(self):
        """Heavier applied load requires higher EI to meet deflection target."""
        target_light = BraceSizingTarget(
            max_deflection_mm=1.5,
            applied_load_n=300.0,  # Light load
            plate_length_mm=500.0,
        )

        target_heavy = BraceSizingTarget(
            max_deflection_mm=1.5,
            applied_load_n=600.0,  # Heavy load
            plate_length_mm=500.0,
        )

        ei_light = compute_required_EI(target_light)
        ei_heavy = compute_required_EI(target_heavy)

        assert ei_heavy > ei_light
        # Doubling load should double required EI (linear relationship)
        assert abs(ei_heavy / ei_light - 2.0) < 0.01


class TestTighterLimitIncreasesEI:
    """Test 2: Tighter deflection limit increases required EI."""

    def test_tighter_limit_requires_more_ei(self):
        """Smaller deflection limit requires higher EI."""
        target_loose = BraceSizingTarget(
            max_deflection_mm=2.0,  # Loose limit
            applied_load_n=400.0,
            plate_length_mm=500.0,
        )

        target_tight = BraceSizingTarget(
            max_deflection_mm=1.0,  # Tight limit
            applied_load_n=400.0,
            plate_length_mm=500.0,
        )

        ei_loose = compute_required_EI(target_loose)
        ei_tight = compute_required_EI(target_tight)

        assert ei_tight > ei_loose
        # Halving deflection limit should double required EI
        assert abs(ei_tight / ei_loose - 2.0) < 0.01


class TestSpruceAchievesTarget:
    """Test 3: Spruce achieves target with reasonable dimensions."""

    def test_spruce_achieves_target(self):
        """Sitka spruce can achieve typical deflection targets."""
        result = solve_brace_sizing(
            target=STANDARD_TARGET,
            wood_species="sitka_spruce",
            brace_width_mm=5.5,
            profile_type="parabolic",
            brace_count=2,
        )

        # Should be achievable with typical brace heights
        assert result.gate in ("ACHIEVABLE", "MARGINAL")
        assert result.suggested_height_mm > 0
        assert result.suggested_height_mm < 15.0  # Practical limit


class TestHeightFormulaRectangular:
    """Test 4: Height formula correctness for rectangular profile."""

    def test_height_formula_rectangular(self):
        """Verify rectangular brace height formula: h = cbrt(12 * EI / (E * w))."""
        # Use a known EI value
        required_EI_Nm2 = 100.0  # 100 N*m^2 per brace
        width_mm = 5.5
        species = "sitka_spruce"

        result = compute_brace_dimensions_for_EI(
            required_brace_EI_Nm2=required_EI_Nm2,
            wood_species=species,
            brace_width_mm=width_mm,
            profile_type="rectangular",
        )

        # Manual calculation
        E_MPa = physics.MATERIAL_MOE_MPA[species]  # 9500 MPa
        EI_Nmm2 = required_EI_Nm2 * 1e6  # Convert N*m^2 to N*mm^2
        I_mm4 = EI_Nmm2 / E_MPa
        h_cubed = 12.0 * I_mm4 / width_mm
        expected_height = h_cubed ** (1.0 / 3.0)

        assert abs(result.suggested_height_mm - expected_height) < 0.01


class TestAchievableGate:
    """Test 5: ACHIEVABLE gate when height <= 10mm."""

    def test_achievable_gate_under_10mm(self):
        """Gate is ACHIEVABLE when brace height is <= 10mm."""
        # Use small EI to get small height
        # For rectangular: h = cbrt(12 * EI / (E * w))
        # E = 9500 MPa, w = 5.5mm
        # For h = 10mm: EI = E * w * h^3 / 12 / 1e6 = 9500 * 5.5 * 1000 / 12 / 1e6 ~ 4.35 N*m^2
        result = compute_brace_dimensions_for_EI(
            required_brace_EI_Nm2=3.0,  # Small EI (will give h ~ 8.6mm)
            wood_species="sitka_spruce",
            brace_width_mm=5.5,
            profile_type="rectangular",
        )

        # Should be achievable with height under 10mm
        assert result.suggested_height_mm <= 10.0
        assert result.gate == "ACHIEVABLE"


class TestNotAchievableGate:
    """Test 6: NOT_ACHIEVABLE gate when height > 14mm."""

    def test_not_achievable_gate_over_14mm(self):
        """Gate is NOT_ACHIEVABLE when brace height exceeds 14mm."""
        # Use very large EI to force large height
        result = compute_brace_dimensions_for_EI(
            required_brace_EI_Nm2=1000.0,  # Very large EI
            wood_species="sitka_spruce",
            brace_width_mm=5.5,
            profile_type="rectangular",
        )

        # Should exceed 14mm
        assert result.suggested_height_mm > 14.0
        assert result.gate == "NOT_ACHIEVABLE"


# =============================================================================
# API ENDPOINT SMOKE TEST
# =============================================================================


class TestBraceSizingEndpoint:
    """Endpoint smoke test for POST /api/instrument/brace-sizing."""

    def test_brace_sizing_endpoint_returns_200(self, client):
        """POST /api/instrument/brace-sizing returns 200 with valid payload."""
        response = client.post(
            "/api/instrument/brace-sizing",
            json={
                "max_deflection_mm": 1.5,
                "applied_load_n": 400.0,
                "plate_length_mm": 500.0,
                "bridge_position_fraction": 0.63,
                "existing_plate_EI_Nm2": 50.0,
                "wood_species": "sitka_spruce",
                "brace_width_mm": 5.5,
                "profile_type": "parabolic",
                "brace_count": 2,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "required_EI_Nm2" in data
        assert "required_brace_EI_Nm2" in data
        assert "suggested_width_mm" in data
        assert "suggested_height_mm" in data
        assert "wood_species" in data
        assert "profile_type" in data
        assert "gate" in data
        assert data["gate"] in ("ACHIEVABLE", "MARGINAL", "NOT_ACHIEVABLE")
        assert "notes" in data

    def test_brace_sizing_endpoint_defaults(self, client):
        """Endpoint works with minimal required fields."""
        response = client.post(
            "/api/instrument/brace-sizing",
            json={
                "max_deflection_mm": 1.5,
                "applied_load_n": 400.0,
                "plate_length_mm": 500.0,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["suggested_height_mm"] > 0
        assert data["wood_species"] == "sitka_spruce"  # Default

    def test_brace_sizing_endpoint_invalid_deflection(self, client):
        """Endpoint rejects zero or negative deflection limit."""
        response = client.post(
            "/api/instrument/brace-sizing",
            json={
                "max_deflection_mm": 0.0,  # Invalid
                "applied_load_n": 400.0,
                "plate_length_mm": 500.0,
            },
        )

        # FastAPI returns 422 for validation errors
        assert response.status_code == 422
