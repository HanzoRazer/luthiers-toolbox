"""
Tests for action workflow evaluation (Phase 4).

Tests evaluate_action() function and the action endpoint.
"""

import pytest
from fastapi.testclient import TestClient

from app.instrument_geometry.neck.setup_workflow import (
    DiagnosticGate,
    evaluate_action,
    DEFAULT_TREBLE_ACTION_TARGET_MIN_MM,
    DEFAULT_TREBLE_ACTION_TARGET_MAX_MM,
    DEFAULT_BASS_ACTION_TARGET_MIN_MM,
    DEFAULT_BASS_ACTION_TARGET_MAX_MM,
)
from app.main import app


client = TestClient(app)


# ─── Unit Tests: evaluate_action() ───────────────────────────────────────────


class TestEvaluateActionUnit:
    """Unit tests for evaluate_action function."""

    def test_both_in_range_returns_green(self):
        """Treble 1.5mm and bass 2.0mm should both be GREEN."""
        result = evaluate_action(treble_action_mm=1.5, bass_action_mm=2.0)

        assert result.overall_gate == DiagnosticGate.GREEN
        assert result.diagnostics[0].gate == DiagnosticGate.GREEN
        assert result.diagnostics[1].gate == DiagnosticGate.GREEN
        assert result.current_step == "action"

    def test_treble_slightly_low_returns_yellow(self):
        """Treble 1.1mm (below 1.25 but within 0.25 tolerance) should be YELLOW."""
        result = evaluate_action(treble_action_mm=1.1, bass_action_mm=2.0)

        assert result.overall_gate == DiagnosticGate.YELLOW
        assert result.diagnostics[0].gate == DiagnosticGate.YELLOW
        assert result.diagnostics[1].gate == DiagnosticGate.GREEN
        assert "treble" in result.diagnostics[0].id

    def test_treble_too_low_returns_red(self):
        """Treble 0.9mm (below 1.25 - 0.25 = 1.0) should be RED."""
        result = evaluate_action(treble_action_mm=0.9, bass_action_mm=2.0)

        assert result.overall_gate == DiagnosticGate.RED
        assert result.diagnostics[0].gate == DiagnosticGate.RED
        assert result.diagnostics[1].gate == DiagnosticGate.GREEN

    def test_treble_slightly_high_returns_yellow(self):
        """Treble 1.9mm (above 1.75 but within 0.25 tolerance) should be YELLOW."""
        result = evaluate_action(treble_action_mm=1.9, bass_action_mm=2.0)

        assert result.overall_gate == DiagnosticGate.YELLOW
        assert result.diagnostics[0].gate == DiagnosticGate.YELLOW
        assert result.diagnostics[1].gate == DiagnosticGate.GREEN

    def test_treble_too_high_returns_red(self):
        """Treble 2.2mm (above 1.75 + 0.25 = 2.0) should be RED."""
        result = evaluate_action(treble_action_mm=2.2, bass_action_mm=2.0)

        assert result.overall_gate == DiagnosticGate.RED
        assert result.diagnostics[0].gate == DiagnosticGate.RED
        assert result.diagnostics[1].gate == DiagnosticGate.GREEN

    def test_bass_slightly_low_returns_yellow(self):
        """Bass 1.6mm (below 1.75 but within 0.25 tolerance) should be YELLOW."""
        result = evaluate_action(treble_action_mm=1.5, bass_action_mm=1.6)

        assert result.overall_gate == DiagnosticGate.YELLOW
        assert result.diagnostics[0].gate == DiagnosticGate.GREEN
        assert result.diagnostics[1].gate == DiagnosticGate.YELLOW

    def test_bass_too_low_returns_red(self):
        """Bass 1.4mm (below 1.75 - 0.25 = 1.5) should be RED."""
        result = evaluate_action(treble_action_mm=1.5, bass_action_mm=1.4)

        assert result.overall_gate == DiagnosticGate.RED
        assert result.diagnostics[0].gate == DiagnosticGate.GREEN
        assert result.diagnostics[1].gate == DiagnosticGate.RED

    def test_worst_case_gate_wins(self):
        """When treble is RED and bass is YELLOW, overall should be RED."""
        result = evaluate_action(treble_action_mm=0.9, bass_action_mm=1.6)

        assert result.overall_gate == DiagnosticGate.RED
        assert result.diagnostics[0].gate == DiagnosticGate.RED
        assert result.diagnostics[1].gate == DiagnosticGate.YELLOW

    def test_diagnostics_contain_causes_and_actions(self):
        """Non-GREEN diagnostics should have probable_causes and recommended_actions."""
        result = evaluate_action(treble_action_mm=0.9, bass_action_mm=2.0)

        treble_diag = result.diagnostics[0]
        assert treble_diag.gate == DiagnosticGate.RED
        assert len(treble_diag.probable_causes) > 0
        assert len(treble_diag.recommended_actions) > 0

    def test_green_diagnostics_have_no_causes(self):
        """GREEN diagnostics should have empty probable_causes and recommended_actions."""
        result = evaluate_action(treble_action_mm=1.5, bass_action_mm=2.0)

        for diag in result.diagnostics:
            assert diag.gate == DiagnosticGate.GREEN
            assert diag.probable_causes == []
            assert diag.recommended_actions == []


# ─── Endpoint Tests ──────────────────────────────────────────────────────────


class TestActionEndpoint:
    """Integration tests for the action workflow endpoint."""

    def test_endpoint_returns_200_with_valid_input(self):
        """POST with valid treble/bass values returns 200."""
        response = client.post(
            "/api/instrument/setup/workflow/action/evaluate",
            json={"treble_action_mm": 1.5, "bass_action_mm": 2.0},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["current_step"] == "action"
        assert data["overall_gate"] == "green"
        assert len(data["diagnostics"]) == 2

    def test_endpoint_accepts_custom_targets(self):
        """POST with custom target values should use those thresholds."""
        response = client.post(
            "/api/instrument/setup/workflow/action/evaluate",
            json={
                "treble_action_mm": 1.5,
                "bass_action_mm": 2.0,
                "treble_target_min_mm": 1.4,
                "treble_target_max_mm": 1.6,
                "bass_target_min_mm": 1.9,
                "bass_target_max_mm": 2.1,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["overall_gate"] == "green"

    def test_endpoint_returns_yellow_for_borderline(self):
        """POST with borderline values returns YELLOW."""
        response = client.post(
            "/api/instrument/setup/workflow/action/evaluate",
            json={"treble_action_mm": 1.1, "bass_action_mm": 2.0},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["overall_gate"] == "yellow"

    def test_endpoint_returns_red_for_severe(self):
        """POST with out-of-range values returns RED."""
        response = client.post(
            "/api/instrument/setup/workflow/action/evaluate",
            json={"treble_action_mm": 0.9, "bass_action_mm": 2.0},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["overall_gate"] == "red"

    def test_endpoint_requires_treble_action(self):
        """POST without treble_action_mm returns 422."""
        response = client.post(
            "/api/instrument/setup/workflow/action/evaluate",
            json={"bass_action_mm": 2.0},
        )

        assert response.status_code == 422

    def test_endpoint_requires_bass_action(self):
        """POST without bass_action_mm returns 422."""
        response = client.post(
            "/api/instrument/setup/workflow/action/evaluate",
            json={"treble_action_mm": 1.5},
        )

        assert response.status_code == 422
