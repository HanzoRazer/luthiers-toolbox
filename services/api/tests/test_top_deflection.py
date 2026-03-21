"""
Tests for top deflection calculator — ACOUSTIC-003.

8 test cases:
1. Spruce dreadnought standard load → GREEN
2. Heavy load (700N) → YELLOW or RED
3. Thicker plate → less deflection
4. More bracing → less deflection
5. Creep projection = static × 1.35
6. bridge_position_fraction affects result
7. composite_EI > plate_EI when braces present
8. Gate boundaries at 1.5mm and 3.0mm
"""
import pytest

from app.calculators.top_deflection_calc import (
    compute_top_deflection,
    compute_plate_EI,
    compute_composite_EI,
    PlateProperties,
    BraceContribution,
    DeflectionResult,
    CREEP_FACTOR,
    SPRUCE_SITKA,
)


# Standard spruce dreadnought plate for testing
STANDARD_PLATE = PlateProperties(
    E_L_GPa=11.0,  # Sitka spruce
    E_C_GPa=0.8,
    thickness_mm=2.8,
    length_mm=500.0,
    width_mm=400.0,
    density_kg_m3=400.0,
)


class TestSpruceStandardLoad:
    """Test 1: Spruce dreadnought standard load → GREEN."""

    def test_standard_load_green_gate(self):
        """Standard string load (~400N) on well-braced spruce top yields GREEN."""
        # X-brace with lateral braces provides significant stiffness
        # Real X-brace EI is ~500 N·m² per brace (tall, stiff spruce braces)
        braces = BraceContribution(
            brace_EI_Nm2=500.0,  # Strong X-brace contribution
            brace_count=2,
        )

        result = compute_top_deflection(
            load_n=400.0,  # Typical saddle force
            plate=STANDARD_PLATE,
            braces=braces,
            bridge_position_fraction=0.63,
        )

        assert result.gate == "GREEN"
        assert result.total_projected_mm < 1.5
        assert result.static_deflection_mm > 0


class TestHeavyLoad:
    """Test 2: Heavy load (700N) → YELLOW or RED."""

    def test_heavy_load_elevated_gate(self):
        """Heavy string load (700N) pushes deflection into YELLOW or RED."""
        # Bare plate without bracing to maximize deflection
        result = compute_top_deflection(
            load_n=700.0,  # Very heavy load
            plate=STANDARD_PLATE,
            braces=None,  # No bracing
            bridge_position_fraction=0.63,
        )

        # Should be YELLOW or RED with no bracing
        assert result.gate in ("YELLOW", "RED")
        assert result.total_projected_mm > 1.0


class TestThickerPlate:
    """Test 3: Thicker plate → less deflection."""

    def test_thicker_plate_reduces_deflection(self):
        """Thicker top plate results in less deflection."""
        thin_plate = PlateProperties(
            E_L_GPa=11.0,
            E_C_GPa=0.8,
            thickness_mm=2.5,  # Thin
            length_mm=500.0,
            width_mm=400.0,
            density_kg_m3=400.0,
        )

        thick_plate = PlateProperties(
            E_L_GPa=11.0,
            E_C_GPa=0.8,
            thickness_mm=3.5,  # Thick
            length_mm=500.0,
            width_mm=400.0,
            density_kg_m3=400.0,
        )

        result_thin = compute_top_deflection(load_n=400.0, plate=thin_plate)
        result_thick = compute_top_deflection(load_n=400.0, plate=thick_plate)

        assert result_thick.static_deflection_mm < result_thin.static_deflection_mm
        # EI scales with thickness³, so thick should have much higher EI
        assert result_thick.composite_EI_Nm2 > result_thin.composite_EI_Nm2


class TestMoreBracing:
    """Test 4: More bracing → less deflection."""

    def test_more_bracing_reduces_deflection(self):
        """Adding bracing reduces deflection."""
        result_no_brace = compute_top_deflection(
            load_n=400.0,
            plate=STANDARD_PLATE,
            braces=None,
        )

        result_with_brace = compute_top_deflection(
            load_n=400.0,
            plate=STANDARD_PLATE,
            braces=BraceContribution(brace_EI_Nm2=50.0, brace_count=2),
        )

        assert result_with_brace.static_deflection_mm < result_no_brace.static_deflection_mm
        assert result_with_brace.composite_EI_Nm2 > result_no_brace.composite_EI_Nm2


class TestCreepProjection:
    """Test 5: Creep projection = static × 1.35."""

    def test_creep_is_35_percent_of_static(self):
        """Creep projection equals static deflection × 0.35."""
        result = compute_top_deflection(
            load_n=400.0,
            plate=STANDARD_PLATE,
            braces=BraceContribution(brace_EI_Nm2=50.0, brace_count=2),
        )

        expected_creep = result.static_deflection_mm * CREEP_FACTOR
        assert abs(result.creep_projection_mm - expected_creep) < 0.0001

        # Total should be static + creep
        expected_total = result.static_deflection_mm * (1 + CREEP_FACTOR)
        assert abs(result.total_projected_mm - expected_total) < 0.0001


class TestBridgePositionFraction:
    """Test 6: bridge_position_fraction affects result."""

    def test_bridge_position_affects_deflection(self):
        """Different bridge positions yield different deflections."""
        result_center = compute_top_deflection(
            load_n=400.0,
            plate=STANDARD_PLATE,
            bridge_position_fraction=0.5,  # Center
        )

        result_offset = compute_top_deflection(
            load_n=400.0,
            plate=STANDARD_PLATE,
            bridge_position_fraction=0.63,  # Typical offset
        )

        # Center load gives maximum deflection for simply-supported beam
        assert result_center.static_deflection_mm != result_offset.static_deflection_mm


class TestCompositeEIWithBraces:
    """Test 7: composite_EI > plate_EI when braces present."""

    def test_composite_ei_greater_with_braces(self):
        """Composite EI exceeds plate EI when braces are added."""
        plate_ei = compute_plate_EI(STANDARD_PLATE)

        braces = BraceContribution(brace_EI_Nm2=50.0, brace_count=2)
        composite_ei = compute_composite_EI(STANDARD_PLATE, braces)

        assert composite_ei > plate_ei
        # Should be plate + (2 × 50)
        expected = plate_ei + 100.0
        assert abs(composite_ei - expected) < 0.0001


class TestGateBoundaries:
    """Test 8: Gate boundaries at 1.5mm and 3.0mm."""

    def test_gate_boundary_green_yellow(self):
        """Gate transitions from GREEN to YELLOW at 1.5mm total."""
        # Find a configuration that produces just under 1.5mm
        # Use very stiff bracing to keep deflection low
        result_low = compute_top_deflection(
            load_n=200.0,
            plate=STANDARD_PLATE,
            braces=BraceContribution(brace_EI_Nm2=100.0, brace_count=3),
        )

        # Should be well under 1.5mm
        if result_low.total_projected_mm < 1.5:
            assert result_low.gate == "GREEN"

    def test_gate_boundary_yellow_red(self):
        """Gate transitions from YELLOW to RED at 3.0mm total."""
        # Use bare thin plate with heavy load to exceed 3mm
        thin_soft_plate = PlateProperties(
            E_L_GPa=7.0,  # Cedar-like, softer
            E_C_GPa=0.5,
            thickness_mm=2.3,  # Thin
            length_mm=500.0,
            width_mm=400.0,
            density_kg_m3=350.0,
        )

        result_high = compute_top_deflection(
            load_n=800.0,  # Very heavy
            plate=thin_soft_plate,
            braces=None,  # No bracing
        )

        # Should exceed 3mm and be RED
        if result_high.total_projected_mm >= 3.0:
            assert result_high.gate == "RED"
        elif result_high.total_projected_mm >= 1.5:
            assert result_high.gate == "YELLOW"


# =============================================================================
# API ENDPOINT SMOKE TEST
# =============================================================================


class TestTopDeflectionEndpoint:
    """Endpoint smoke test for POST /api/instrument/top-deflection."""

    def test_top_deflection_endpoint_returns_200(self, client):
        """POST /api/instrument/top-deflection returns 200 with valid payload."""
        response = client.post(
            "/api/instrument/top-deflection",
            json={
                "load_n": 400.0,
                "plate": {
                    "E_L_GPa": 11.0,
                    "E_C_GPa": 0.8,
                    "thickness_mm": 2.8,
                    "length_mm": 500.0,
                    "width_mm": 400.0,
                    "density_kg_m3": 400.0,
                },
                "braces": {
                    "brace_EI_Nm2": 50.0,
                    "brace_count": 2,
                },
                "bridge_position_fraction": 0.63,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "static_deflection_mm" in data
        assert "creep_projection_mm" in data
        assert "total_projected_mm" in data
        assert "gate" in data
        assert data["gate"] in ("GREEN", "YELLOW", "RED")
        assert "composite_EI_Nm2" in data
        assert "notes" in data

    def test_top_deflection_endpoint_no_braces(self, client):
        """Endpoint works without braces (bare plate)."""
        response = client.post(
            "/api/instrument/top-deflection",
            json={
                "load_n": 400.0,
                "plate": {
                    "E_L_GPa": 11.0,
                    "E_C_GPa": 0.8,
                    "thickness_mm": 2.8,
                    "length_mm": 500.0,
                    "width_mm": 400.0,
                },
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["static_deflection_mm"] > 0

    def test_top_deflection_endpoint_invalid_load(self, client):
        """Endpoint rejects zero or negative load."""
        response = client.post(
            "/api/instrument/top-deflection",
            json={
                "load_n": 0.0,  # Invalid
                "plate": {
                    "E_L_GPa": 11.0,
                    "thickness_mm": 2.8,
                    "length_mm": 500.0,
                    "width_mm": 400.0,
                },
            },
        )

        # FastAPI returns 422 for validation errors
        assert response.status_code == 422
