"""
Tests for Bridge Saddle Compensation Calculator.

Tests both Design Mode (estimate from specs) and Setup Mode (adjust from measurements).
"""
import math
import pytest
from fastapi.testclient import TestClient

from app.calculators.saddle_compensation import (
    StringSpec,
    DesignCalculatorInput,
    DesignCalculatorResult,
    StringMeasurementInput,
    SetupCalculatorInput,
    SetupCalculatorResult,
    estimate_string_compensation_mm,
    fit_straight_saddle,
    build_design_report,
    compute_saddle_adjustment,
    build_setup_result,
    REFERENCE_SCALE_MM,
)


# =============================================================================
# Fixtures - Gibson 24.75" with light gauge strings
# =============================================================================

GIBSON_SCALE_MM = 628.65  # 24.75" in mm
FENDER_SCALE_MM = 647.7   # 25.5" in mm


@pytest.fixture
def gibson_light_gauge_strings() -> list:
    """Gibson Les Paul with light gauge strings (10-46)."""
    # Standard 6-string layout, typical string spread ~52mm
    return [
        StringSpec(name="E6", gauge_in=0.046, tension_lb=17.5, is_wound=True, x_mm=0.0),
        StringSpec(name="A5", gauge_in=0.036, tension_lb=18.4, is_wound=True, x_mm=10.4),
        StringSpec(name="D4", gauge_in=0.026, tension_lb=18.4, is_wound=True, x_mm=20.8),
        StringSpec(name="G3", gauge_in=0.017, tension_lb=16.6, is_wound=False, x_mm=31.2),
        StringSpec(name="B2", gauge_in=0.013, tension_lb=15.4, is_wound=False, x_mm=41.6),
        StringSpec(name="E1", gauge_in=0.010, tension_lb=16.2, is_wound=False, x_mm=52.0),
    ]


@pytest.fixture
def design_input_gibson(gibson_light_gauge_strings) -> DesignCalculatorInput:
    """Design mode input for Gibson with standard action."""
    return DesignCalculatorInput(
        scale_length_mm=GIBSON_SCALE_MM,
        action_12th_treble_mm=1.6,  # ~1/16" typical electric
        action_12th_bass_mm=2.0,    # slightly higher on bass side
        strings=gibson_light_gauge_strings,
    )


# =============================================================================
# Tests for estimate_string_compensation_mm
# =============================================================================

class TestEstimateStringCompensation:
    """Tests for individual string compensation estimation."""

    def test_wound_string_has_higher_compensation(self):
        """Wound strings should have higher compensation than plain."""
        # Same gauge, different wound status
        comp_wound = estimate_string_compensation_mm(
            gauge_in=0.017, tension_lb=16.0, is_wound=True,
            action_mm=1.8, scale_length_mm=GIBSON_SCALE_MM
        )
        comp_plain = estimate_string_compensation_mm(
            gauge_in=0.017, tension_lb=16.0, is_wound=False,
            action_mm=1.8, scale_length_mm=GIBSON_SCALE_MM
        )
        assert comp_wound > comp_plain
        # Wound bonus is 0.55mm
        assert abs((comp_wound - comp_plain) - 0.55) < 0.01

    def test_heavier_gauge_has_higher_compensation(self):
        """Heavier gauge strings need more compensation."""
        comp_heavy = estimate_string_compensation_mm(
            gauge_in=0.046, tension_lb=17.0, is_wound=True,
            action_mm=2.0, scale_length_mm=GIBSON_SCALE_MM
        )
        comp_light = estimate_string_compensation_mm(
            gauge_in=0.026, tension_lb=17.0, is_wound=True,
            action_mm=2.0, scale_length_mm=GIBSON_SCALE_MM
        )
        assert comp_heavy > comp_light

    def test_higher_action_increases_compensation(self):
        """Higher action at 12th fret increases compensation."""
        comp_high = estimate_string_compensation_mm(
            gauge_in=0.013, tension_lb=15.0, is_wound=False,
            action_mm=2.5, scale_length_mm=GIBSON_SCALE_MM
        )
        comp_low = estimate_string_compensation_mm(
            gauge_in=0.013, tension_lb=15.0, is_wound=False,
            action_mm=1.5, scale_length_mm=GIBSON_SCALE_MM
        )
        assert comp_high > comp_low

    def test_lower_tension_increases_compensation(self):
        """Lower tension strings need more compensation."""
        comp_low_tension = estimate_string_compensation_mm(
            gauge_in=0.010, tension_lb=12.0, is_wound=False,
            action_mm=1.6, scale_length_mm=GIBSON_SCALE_MM
        )
        comp_high_tension = estimate_string_compensation_mm(
            gauge_in=0.010, tension_lb=20.0, is_wound=False,
            action_mm=1.6, scale_length_mm=GIBSON_SCALE_MM
        )
        assert comp_low_tension > comp_high_tension

    def test_compensation_in_reasonable_range(self):
        """Compensation should be in typical range (1-4mm for most strings)."""
        # Typical wound bass string
        comp = estimate_string_compensation_mm(
            gauge_in=0.046, tension_lb=17.5, is_wound=True,
            action_mm=2.0, scale_length_mm=GIBSON_SCALE_MM
        )
        assert 1.0 < comp < 5.0

        # Typical plain high E
        comp_e1 = estimate_string_compensation_mm(
            gauge_in=0.010, tension_lb=16.0, is_wound=False,
            action_mm=1.6, scale_length_mm=GIBSON_SCALE_MM
        )
        assert 0.5 < comp_e1 < 3.0


# =============================================================================
# Tests for fit_straight_saddle
# =============================================================================

class TestFitStraightSaddle:
    """Tests for least squares saddle fitting."""

    def test_perfect_line_has_r_squared_one(self):
        """Perfect linear data should have R-squared = 1."""
        x = [0, 10, 20, 30, 40, 50]
        y = [2.0, 2.2, 2.4, 2.6, 2.8, 3.0]  # Perfect line

        fit = fit_straight_saddle(x, y)

        assert abs(fit.r_squared - 1.0) < 0.001
        assert abs(fit.slope - 0.02) < 0.001

    def test_residuals_sum_to_zero(self):
        """Residuals from least squares fit should sum to approximately zero."""
        x = [0, 10, 20, 30, 40, 50]
        y = [2.5, 2.3, 2.6, 2.4, 2.7, 2.1]  # Scattered data

        fit = fit_straight_saddle(x, y)

        # Calculate residuals
        residuals = [yi - (fit.slope * xi + fit.intercept_mm) for xi, yi in zip(x, y)]

        # Sum should be very close to zero
        assert abs(sum(residuals)) < 0.0001

    def test_slant_angle_positive_for_increasing_comp(self):
        """Positive slope (treble needs more comp) gives positive angle."""
        x = [0, 52]  # bass to treble
        y = [2.0, 3.0]  # increasing compensation

        fit = fit_straight_saddle(x, y)

        assert fit.slope > 0
        assert fit.slant_angle_deg > 0

    def test_slant_angle_negative_for_decreasing_comp(self):
        """Negative slope (bass needs more comp) gives negative angle."""
        x = [0, 52]
        y = [3.0, 2.0]  # decreasing compensation

        fit = fit_straight_saddle(x, y)

        assert fit.slope < 0
        assert fit.slant_angle_deg < 0

    def test_single_string_returns_zero_slope(self):
        """Single string should have zero slope."""
        fit = fit_straight_saddle([25], [2.5])

        assert fit.slope == 0.0
        assert fit.slant_angle_deg == 0.0
        assert fit.intercept_mm == 2.5


# =============================================================================
# Tests for build_design_report (Integration)
# =============================================================================

class TestBuildDesignReport:
    """Integration tests for complete design mode calculation."""

    def test_gibson_light_gauge_angle_reasonable(self, design_input_gibson):
        """Gibson 24.75" with light gauge should produce reasonable saddle angle (1-4°)."""
        result = build_design_report(design_input_gibson)

        angle = abs(result.saddle_fit.slant_angle_deg)
        # Typical range for electric guitars is 1-4°
        assert 1.0 <= angle <= 5.0, f"Expected angle 1-5°, got {angle}°"

    def test_all_strings_have_results(self, design_input_gibson):
        """Should return result for each input string."""
        result = build_design_report(design_input_gibson)

        assert len(result.string_results) == 6
        names = [s.name for s in result.string_results]
        assert "E6" in names
        assert "E1" in names

    def test_residuals_reasonable(self, design_input_gibson):
        """Crown residuals should be small for standard setup."""
        result = build_design_report(design_input_gibson)

        # Max residual typically < 0.5mm for standard strings
        assert result.max_residual_mm < 1.0

    def test_bass_string_has_more_compensation(self, design_input_gibson):
        """Bass strings should generally have more compensation."""
        result = build_design_report(design_input_gibson)

        e6_result = next(s for s in result.string_results if s.name == "E6")
        e1_result = next(s for s in result.string_results if s.name == "E1")

        # Heavy wound bass needs more compensation than plain treble
        assert e6_result.compensation_mm > e1_result.compensation_mm

    def test_recommendation_generated(self, design_input_gibson):
        """Should generate a human-readable recommendation."""
        result = build_design_report(design_input_gibson)

        assert result.recommendation
        assert len(result.recommendation) > 10


# =============================================================================
# Tests for compute_saddle_adjustment (Setup Mode)
# =============================================================================

class TestComputeSaddleAdjustment:
    """Tests for cents-to-mm conversion."""

    def test_positive_cents_gives_positive_delta(self):
        """Sharp note (+5 cents) should require positive adjustment (move back)."""
        delta = compute_saddle_adjustment(GIBSON_SCALE_MM, cents_error=5.0)

        assert delta > 0, "Sharp note should need saddle moved back"

    def test_negative_cents_gives_negative_delta(self):
        """Flat note (-5 cents) should require negative adjustment (move forward)."""
        delta = compute_saddle_adjustment(GIBSON_SCALE_MM, cents_error=-5.0)

        assert delta < 0, "Flat note should need saddle moved forward"

    def test_zero_cents_gives_zero_delta(self):
        """Perfect intonation should require no adjustment."""
        delta = compute_saddle_adjustment(GIBSON_SCALE_MM, cents_error=0.0)

        assert abs(delta) < 0.0001

    def test_5_cents_adjustment_reasonable(self):
        """5 cents error should give adjustment in reasonable range."""
        delta_5_cents = compute_saddle_adjustment(GIBSON_SCALE_MM, cents_error=5.0)

        # 5 cents on a 628mm scale should be roughly 1.8mm
        # Formula: 628 * (2^(5/1200) - 1) ≈ 1.814mm
        expected = GIBSON_SCALE_MM * (2 ** (5 / 1200) - 1)
        assert abs(delta_5_cents - expected) < 0.001

    def test_larger_scale_gives_larger_adjustment(self):
        """Longer scale length should require larger adjustment for same cents error."""
        delta_gibson = compute_saddle_adjustment(GIBSON_SCALE_MM, cents_error=5.0)
        delta_fender = compute_saddle_adjustment(FENDER_SCALE_MM, cents_error=5.0)

        assert delta_fender > delta_gibson


# =============================================================================
# Tests for build_setup_result (Setup Mode Integration)
# =============================================================================

class TestBuildSetupResult:
    """Integration tests for setup mode calculation."""

    def test_sharp_strings_need_more_compensation(self):
        """Sharp strings should get positive delta_L."""
        inp = SetupCalculatorInput(
            scale_length_mm=GIBSON_SCALE_MM,
            strings=[
                StringMeasurementInput(
                    name="E1", x_mm=52, current_comp_mm=2.0, cents_error=5.0
                ),
            ]
        )
        result = build_setup_result(inp)

        assert result.string_results[0].delta_L_mm > 0
        assert result.string_results[0].new_comp_mm > 2.0

    def test_flat_strings_need_less_compensation(self):
        """Flat strings should get negative delta_L."""
        inp = SetupCalculatorInput(
            scale_length_mm=GIBSON_SCALE_MM,
            strings=[
                StringMeasurementInput(
                    name="E1", x_mm=52, current_comp_mm=2.5, cents_error=-5.0
                ),
            ]
        )
        result = build_setup_result(inp)

        assert result.string_results[0].delta_L_mm < 0
        assert result.string_results[0].new_comp_mm < 2.5

    def test_multiple_strings_processed(self):
        """Should process all input strings."""
        inp = SetupCalculatorInput(
            scale_length_mm=GIBSON_SCALE_MM,
            strings=[
                StringMeasurementInput(name="E6", x_mm=0, current_comp_mm=2.5, cents_error=3.0),
                StringMeasurementInput(name="A5", x_mm=10, current_comp_mm=2.3, cents_error=-2.0),
                StringMeasurementInput(name="E1", x_mm=52, current_comp_mm=1.8, cents_error=0.0),
            ]
        )
        result = build_setup_result(inp)

        assert len(result.string_results) == 3
        assert result.avg_adjustment_mm > 0
        assert result.max_adjustment_mm > 0

    def test_recommendation_generated(self):
        """Should generate a human-readable recommendation."""
        inp = SetupCalculatorInput(
            scale_length_mm=GIBSON_SCALE_MM,
            strings=[
                StringMeasurementInput(name="E1", x_mm=52, current_comp_mm=2.0, cents_error=2.0),
            ]
        )
        result = build_setup_result(inp)

        assert result.recommendation
        assert len(result.recommendation) > 10


# =============================================================================
# Router Endpoint Tests
# =============================================================================

class TestSaddleCompensationEndpoints:
    """Tests for API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from app.main import app
        return TestClient(app)

    def test_compensation_endpoint_exists(self, client):
        """POST /api/instrument/bridge/compensation should exist."""
        response = client.post(
            "/api/instrument/bridge/compensation",
            json={
                "scale_length_mm": 628.65,
                "action_12th_treble_mm": 1.6,
                "action_12th_bass_mm": 2.0,
                "strings": [
                    {"name": "E6", "gauge_in": 0.046, "tension_lb": 17.5, "is_wound": True, "x_mm": 0},
                    {"name": "E1", "gauge_in": 0.010, "tension_lb": 16.2, "is_wound": False, "x_mm": 52},
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "saddle_fit" in data
        assert "slant_angle_deg" in data["saddle_fit"]

    def test_setup_endpoint_exists(self, client):
        """POST /api/instrument/bridge/setup should exist."""
        response = client.post(
            "/api/instrument/bridge/setup",
            json={
                "scale_length_mm": 628.65,
                "strings": [
                    {"name": "E1", "x_mm": 52, "current_comp_mm": 2.0, "cents_error": 5.0},
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "string_results" in data
        assert data["string_results"][0]["delta_L_mm"] > 0

    def test_compensation_endpoint_validation(self, client):
        """Should reject invalid input."""
        response = client.post(
            "/api/instrument/bridge/compensation",
            json={
                "scale_length_mm": -100,  # Invalid
                "action_12th_treble_mm": 1.6,
                "action_12th_bass_mm": 2.0,
                "strings": []  # Empty
            }
        )
        assert response.status_code == 422  # Validation error

    def test_setup_endpoint_validation(self, client):
        """Should reject invalid input."""
        response = client.post(
            "/api/instrument/bridge/setup",
            json={
                "scale_length_mm": 628.65,
                "strings": []  # Empty
            }
        )
        assert response.status_code == 422  # Validation error
