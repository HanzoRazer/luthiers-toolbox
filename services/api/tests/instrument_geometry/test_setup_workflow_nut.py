"""
Tests for nut slot workflow evaluation (Phase 5).

Tests evaluate_nut_slots() function and the nut endpoint.
"""

import pytest
from fastapi.testclient import TestClient

from app.instrument_geometry.neck.setup_workflow import (
    DiagnosticGate,
    evaluate_nut_slots,
    DEFAULT_NUT_TREBLE_TARGET_MIN_MM,
    DEFAULT_NUT_TREBLE_TARGET_MAX_MM,
    DEFAULT_NUT_BASS_TARGET_MIN_MM,
    DEFAULT_NUT_BASS_TARGET_MAX_MM,
)
from app.main import app


client = TestClient(app)


# ─── Unit Tests: evaluate_nut_slots() ────────────────────────────────────────


class TestEvaluateNutSlotsUnit:
    """Unit tests for evaluate_nut_slots function."""

    def test_all_in_range_returns_green(self):
        """All strings in range should return GREEN overall."""
        result = evaluate_nut_slots([0.25, 0.25, 0.25, 0.30, 0.30, 0.30])

        assert result.overall_gate == DiagnosticGate.GREEN
        assert result.current_step == "nut"
        assert len(result.diagnostics) == 6
        for diag in result.diagnostics:
            assert diag.gate == DiagnosticGate.GREEN

    def test_string1_slightly_low_returns_yellow(self):
        """String 1 at 0.18mm (below 0.20 but within 0.05 tolerance) should be YELLOW."""
        result = evaluate_nut_slots([0.18, 0.25, 0.25, 0.30, 0.30, 0.30])

        assert result.overall_gate == DiagnosticGate.YELLOW
        assert result.diagnostics[0].gate == DiagnosticGate.YELLOW
        assert "too_low" in result.diagnostics[0].id

    def test_string1_too_low_returns_red(self):
        """String 1 at 0.10mm (below 0.20 - 0.05 = 0.15) should be RED."""
        result = evaluate_nut_slots([0.10, 0.25, 0.25, 0.30, 0.30, 0.30])

        assert result.overall_gate == DiagnosticGate.RED
        assert result.diagnostics[0].gate == DiagnosticGate.RED
        assert "too_low_severe" in result.diagnostics[0].id

    def test_string1_slightly_high_returns_yellow(self):
        """String 1 at 0.35mm (above 0.30 but within 0.05 tolerance) should be YELLOW."""
        result = evaluate_nut_slots([0.35, 0.25, 0.25, 0.30, 0.30, 0.30])

        assert result.overall_gate == DiagnosticGate.YELLOW
        assert result.diagnostics[0].gate == DiagnosticGate.YELLOW
        assert "too_high" in result.diagnostics[0].id

    def test_string1_too_high_returns_red(self):
        """String 1 at 0.45mm (above 0.30 + 0.05 = 0.35) should be RED."""
        result = evaluate_nut_slots([0.45, 0.25, 0.25, 0.30, 0.30, 0.30])

        assert result.overall_gate == DiagnosticGate.RED
        assert result.diagnostics[0].gate == DiagnosticGate.RED
        assert "too_high_severe" in result.diagnostics[0].id

    def test_bass_string_uses_bass_targets(self):
        """String 4 (bass) should use bass target range 0.25-0.40mm."""
        # 0.30mm is in range for bass (0.25-0.40) but would be at edge for treble (0.20-0.30)
        result = evaluate_nut_slots([0.25, 0.25, 0.25, 0.30, 0.30, 0.30])

        # String 4 (index 3) should be GREEN
        assert result.diagnostics[3].gate == DiagnosticGate.GREEN
        assert result.diagnostics[3].target_min == DEFAULT_NUT_BASS_TARGET_MIN_MM
        assert result.diagnostics[3].target_max == DEFAULT_NUT_BASS_TARGET_MAX_MM

    def test_treble_string_uses_treble_targets(self):
        """String 1 (treble) should use treble target range 0.20-0.30mm."""
        result = evaluate_nut_slots([0.25, 0.25, 0.25, 0.30, 0.30, 0.30])

        # String 1 (index 0) should be GREEN
        assert result.diagnostics[0].gate == DiagnosticGate.GREEN
        assert result.diagnostics[0].target_min == DEFAULT_NUT_TREBLE_TARGET_MIN_MM
        assert result.diagnostics[0].target_max == DEFAULT_NUT_TREBLE_TARGET_MAX_MM

    def test_worst_case_gate_wins(self):
        """Overall gate should be worst-case: RED > YELLOW > GREEN."""
        # String 1 RED, String 2 YELLOW, rest GREEN
        result = evaluate_nut_slots([0.10, 0.18, 0.25, 0.30, 0.30, 0.30])

        assert result.overall_gate == DiagnosticGate.RED
        assert result.diagnostics[0].gate == DiagnosticGate.RED
        assert result.diagnostics[1].gate == DiagnosticGate.YELLOW

    def test_diagnostics_contain_causes_and_actions(self):
        """Non-GREEN diagnostics should have probable_causes and recommended_actions."""
        result = evaluate_nut_slots([0.10, 0.25, 0.25, 0.30, 0.30, 0.30])

        diag = result.diagnostics[0]
        assert diag.gate == DiagnosticGate.RED
        assert len(diag.probable_causes) > 0
        assert len(diag.recommended_actions) > 0

    def test_green_diagnostics_have_no_causes(self):
        """GREEN diagnostics should have empty probable_causes and recommended_actions."""
        result = evaluate_nut_slots([0.25, 0.25, 0.25, 0.30, 0.30, 0.30])

        for diag in result.diagnostics:
            assert diag.gate == DiagnosticGate.GREEN
            assert diag.probable_causes == []
            assert diag.recommended_actions == []

    def test_wrong_string_count_raises_error(self):
        """Providing wrong number of clearances should raise ValueError."""
        with pytest.raises(ValueError, match="Expected 6"):
            evaluate_nut_slots([0.25, 0.25, 0.25])

    def test_custom_targets_are_used(self):
        """Custom target values should be used instead of defaults."""
        result = evaluate_nut_slots(
            clearances_mm=[0.15, 0.15, 0.15, 0.20, 0.20, 0.20],
            treble_target_min_mm=0.10,
            treble_target_max_mm=0.20,
            bass_target_min_mm=0.15,
            bass_target_max_mm=0.25,
        )

        assert result.overall_gate == DiagnosticGate.GREEN
        assert result.diagnostics[0].target_min == 0.10
        assert result.diagnostics[0].target_max == 0.20
        assert result.diagnostics[3].target_min == 0.15
        assert result.diagnostics[3].target_max == 0.25


# ─── Endpoint Tests ──────────────────────────────────────────────────────────


class TestNutEndpoint:
    """Integration tests for the nut workflow endpoint."""

    def test_endpoint_returns_200_with_valid_input(self):
        """POST with valid clearances returns 200."""
        response = client.post(
            "/api/instrument/setup/workflow/nut/evaluate",
            json={"clearances_mm": [0.25, 0.25, 0.25, 0.30, 0.30, 0.30]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["current_step"] == "nut"
        assert data["overall_gate"] == "green"
        assert len(data["diagnostics"]) == 6

    def test_endpoint_accepts_custom_targets(self):
        """POST with custom target values should use those thresholds."""
        response = client.post(
            "/api/instrument/setup/workflow/nut/evaluate",
            json={
                "clearances_mm": [0.15, 0.15, 0.15, 0.20, 0.20, 0.20],
                "treble_target_min_mm": 0.10,
                "treble_target_max_mm": 0.20,
                "bass_target_min_mm": 0.15,
                "bass_target_max_mm": 0.25,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["overall_gate"] == "green"

    def test_endpoint_returns_yellow_for_borderline(self):
        """POST with borderline values returns YELLOW."""
        response = client.post(
            "/api/instrument/setup/workflow/nut/evaluate",
            json={"clearances_mm": [0.18, 0.25, 0.25, 0.30, 0.30, 0.30]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["overall_gate"] == "yellow"

    def test_endpoint_returns_red_for_severe(self):
        """POST with out-of-range values returns RED."""
        response = client.post(
            "/api/instrument/setup/workflow/nut/evaluate",
            json={"clearances_mm": [0.10, 0.25, 0.25, 0.30, 0.30, 0.30]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["overall_gate"] == "red"

    def test_endpoint_requires_clearances(self):
        """POST without clearances_mm returns 422."""
        response = client.post(
            "/api/instrument/setup/workflow/nut/evaluate",
            json={},
        )

        assert response.status_code == 422

    def test_endpoint_validates_clearance_count(self):
        """POST with wrong number of clearances returns 422."""
        response = client.post(
            "/api/instrument/setup/workflow/nut/evaluate",
            json={"clearances_mm": [0.25, 0.25, 0.25]},
        )

        assert response.status_code == 422

    def test_endpoint_validates_negative_clearance(self):
        """POST with negative clearance returns 422."""
        response = client.post(
            "/api/instrument/setup/workflow/nut/evaluate",
            json={"clearances_mm": [-0.10, 0.25, 0.25, 0.30, 0.30, 0.30]},
        )

        assert response.status_code == 422
