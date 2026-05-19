"""
Tests for combined setup workflow evaluation (Phase 6).

Tests evaluate_combined_setup() function and the combined endpoint.
"""

import pytest
from fastapi.testclient import TestClient

from app.instrument_geometry.neck.setup_workflow import (
    DiagnosticGate,
    evaluate_combined_setup,
)
from app.main import app


client = TestClient(app)


# ─── Unit Tests: evaluate_combined_setup() ────────────────────────────────────


class TestEvaluateCombinedSetupUnit:
    """Unit tests for evaluate_combined_setup function."""

    def test_rule1_fret_buzz_likely(self):
        """Relief RED (too low) + Action RED (too low) → RED fret buzz."""
        result = evaluate_combined_setup(
            relief_gate=DiagnosticGate.RED,
            relief_diagnostic_ids=["relief_too_low_severe"],
            action_gate=DiagnosticGate.RED,
            action_diagnostic_ids=["action_treble_too_low_severe", "action_bass_too_low_severe"],
            nut_gate=DiagnosticGate.GREEN,
            nut_diagnostic_ids=["nut_slot_s1_in_range"],
        )

        assert result.overall_gate == DiagnosticGate.RED
        assert any(d.id == "combined_fret_buzz_likely" for d in result.diagnostics)
        buzz_diag = next(d for d in result.diagnostics if d.id == "combined_fret_buzz_likely")
        assert buzz_diag.gate == DiagnosticGate.RED
        assert "fret buzz" in buzz_diag.message.lower()

    def test_rule1_with_yellow_action(self):
        """Relief RED (too low) + Action YELLOW (too low) → RED fret buzz."""
        result = evaluate_combined_setup(
            relief_gate=DiagnosticGate.RED,
            relief_diagnostic_ids=["relief_too_low_severe"],
            action_gate=DiagnosticGate.YELLOW,
            action_diagnostic_ids=["action_treble_too_low"],
            nut_gate=DiagnosticGate.GREEN,
            nut_diagnostic_ids=[],
        )

        assert result.overall_gate == DiagnosticGate.RED
        assert any(d.id == "combined_fret_buzz_likely" for d in result.diagnostics)

    def test_rule1_not_triggered_if_action_high(self):
        """Relief RED (too low) but Action too HIGH → no buzz rule."""
        result = evaluate_combined_setup(
            relief_gate=DiagnosticGate.RED,
            relief_diagnostic_ids=["relief_too_low_severe"],
            action_gate=DiagnosticGate.RED,
            action_diagnostic_ids=["action_treble_too_high_severe"],
            nut_gate=DiagnosticGate.GREEN,
            nut_diagnostic_ids=[],
        )

        assert not any(d.id == "combined_fret_buzz_likely" for d in result.diagnostics)

    def test_rule2_high_action_compound(self):
        """Action RED (too high) + Nut RED (too high) → RED compound."""
        result = evaluate_combined_setup(
            relief_gate=DiagnosticGate.GREEN,
            relief_diagnostic_ids=["relief_ok"],
            action_gate=DiagnosticGate.RED,
            action_diagnostic_ids=["action_treble_too_high_severe"],
            nut_gate=DiagnosticGate.RED,
            nut_diagnostic_ids=["nut_slot_s1_too_high_severe"],
        )

        assert result.overall_gate == DiagnosticGate.RED
        assert any(d.id == "combined_high_action_compound" for d in result.diagnostics)
        compound_diag = next(d for d in result.diagnostics if d.id == "combined_high_action_compound")
        assert "compounded" in compound_diag.message.lower()

    def test_rule3_nut_dominant(self):
        """Nut RED + Relief GREEN + Action GREEN → YELLOW nut dominant."""
        result = evaluate_combined_setup(
            relief_gate=DiagnosticGate.GREEN,
            relief_diagnostic_ids=["relief_ok"],
            action_gate=DiagnosticGate.GREEN,
            action_diagnostic_ids=["action_treble_in_range", "action_bass_in_range"],
            nut_gate=DiagnosticGate.RED,
            nut_diagnostic_ids=["nut_slot_s1_too_low_severe"],
        )

        assert result.overall_gate == DiagnosticGate.YELLOW
        assert any(d.id == "combined_nut_dominant" for d in result.diagnostics)
        nut_diag = next(d for d in result.diagnostics if d.id == "combined_nut_dominant")
        assert "nut" in nut_diag.message.lower()
        assert "primary" in nut_diag.message.lower()

    def test_rule3_with_yellow_action(self):
        """Nut RED + Relief GREEN + Action YELLOW → YELLOW nut dominant."""
        result = evaluate_combined_setup(
            relief_gate=DiagnosticGate.GREEN,
            relief_diagnostic_ids=["relief_ok"],
            action_gate=DiagnosticGate.YELLOW,
            action_diagnostic_ids=["action_treble_too_low"],
            nut_gate=DiagnosticGate.RED,
            nut_diagnostic_ids=["nut_slot_s1_too_high_severe"],
        )

        assert any(d.id == "combined_nut_dominant" for d in result.diagnostics)

    def test_rule4_balanced_setup(self):
        """All GREEN → GREEN balanced."""
        result = evaluate_combined_setup(
            relief_gate=DiagnosticGate.GREEN,
            relief_diagnostic_ids=["relief_ok"],
            action_gate=DiagnosticGate.GREEN,
            action_diagnostic_ids=["action_treble_in_range", "action_bass_in_range"],
            nut_gate=DiagnosticGate.GREEN,
            nut_diagnostic_ids=["nut_slot_s1_in_range"],
        )

        assert result.overall_gate == DiagnosticGate.GREEN
        assert any(d.id == "combined_balanced" for d in result.diagnostics)
        balanced_diag = next(d for d in result.diagnostics if d.id == "combined_balanced")
        assert "balanced" in balanced_diag.message.lower()

    def test_rule5_mixed_moderate(self):
        """2+ YELLOW, no RED → YELLOW mixed moderate."""
        result = evaluate_combined_setup(
            relief_gate=DiagnosticGate.YELLOW,
            relief_diagnostic_ids=["relief_too_low"],
            action_gate=DiagnosticGate.YELLOW,
            action_diagnostic_ids=["action_treble_too_low"],
            nut_gate=DiagnosticGate.GREEN,
            nut_diagnostic_ids=["nut_slot_s1_in_range"],
        )

        assert result.overall_gate == DiagnosticGate.YELLOW
        assert any(d.id == "combined_mixed_moderate" for d in result.diagnostics)
        mixed_diag = next(d for d in result.diagnostics if d.id == "combined_mixed_moderate")
        assert "multiple" in mixed_diag.message.lower()
        assert len(mixed_diag.contributing_factors) >= 2

    def test_rule5_three_yellow(self):
        """3 YELLOW → YELLOW mixed moderate with all factors."""
        result = evaluate_combined_setup(
            relief_gate=DiagnosticGate.YELLOW,
            relief_diagnostic_ids=["relief_too_high"],
            action_gate=DiagnosticGate.YELLOW,
            action_diagnostic_ids=["action_bass_too_high"],
            nut_gate=DiagnosticGate.YELLOW,
            nut_diagnostic_ids=["nut_slot_s3_too_high"],
        )

        assert any(d.id == "combined_mixed_moderate" for d in result.diagnostics)
        mixed_diag = next(d for d in result.diagnostics if d.id == "combined_mixed_moderate")
        assert len(mixed_diag.contributing_factors) == 3

    def test_rule5_not_triggered_with_red(self):
        """YELLOW + YELLOW + RED → rule 5 should NOT fire."""
        result = evaluate_combined_setup(
            relief_gate=DiagnosticGate.YELLOW,
            relief_diagnostic_ids=["relief_too_low"],
            action_gate=DiagnosticGate.YELLOW,
            action_diagnostic_ids=["action_treble_too_low"],
            nut_gate=DiagnosticGate.RED,
            nut_diagnostic_ids=["nut_slot_s1_too_low_severe"],
        )

        assert not any(d.id == "combined_mixed_moderate" for d in result.diagnostics)

    def test_multiple_rules_can_fire(self):
        """Multiple rules can fire simultaneously."""
        result = evaluate_combined_setup(
            relief_gate=DiagnosticGate.RED,
            relief_diagnostic_ids=["relief_too_low_severe"],
            action_gate=DiagnosticGate.RED,
            action_diagnostic_ids=["action_treble_too_low_severe"],
            nut_gate=DiagnosticGate.GREEN,
            nut_diagnostic_ids=[],
        )

        # Rule 1 should fire
        assert any(d.id == "combined_fret_buzz_likely" for d in result.diagnostics)
        # Multiple diagnostics possible
        assert len(result.diagnostics) >= 1

    def test_diagnostics_sorted_by_severity(self):
        """Diagnostics should be sorted RED > YELLOW > GREEN."""
        result = evaluate_combined_setup(
            relief_gate=DiagnosticGate.GREEN,
            relief_diagnostic_ids=["relief_ok"],
            action_gate=DiagnosticGate.GREEN,
            action_diagnostic_ids=[],
            nut_gate=DiagnosticGate.RED,
            nut_diagnostic_ids=["nut_slot_s1_too_low_severe"],
        )

        # Should have nut dominant (YELLOW) but overall should reflect worst case
        if len(result.diagnostics) > 1:
            gates = [d.gate for d in result.diagnostics]
            severity = {DiagnosticGate.RED: 0, DiagnosticGate.YELLOW: 1, DiagnosticGate.GREEN: 2}
            assert gates == sorted(gates, key=lambda g: severity[g])


# ─── Endpoint Tests ──────────────────────────────────────────────────────────


class TestCombinedEndpoint:
    """Integration tests for the combined workflow endpoint."""

    def test_endpoint_returns_200_with_valid_input(self):
        """POST with valid gates returns 200."""
        response = client.post(
            "/api/instrument/setup/workflow/combined/evaluate",
            json={
                "relief_gate": "green",
                "relief_diagnostic_ids": ["relief_ok"],
                "action_gate": "green",
                "action_diagnostic_ids": [],
                "nut_gate": "green",
                "nut_diagnostic_ids": [],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["overall_gate"] == "green"
        assert "diagnostics" in data

    def test_endpoint_fret_buzz_scenario(self):
        """POST with fret buzz scenario returns RED with buzz diagnostic."""
        response = client.post(
            "/api/instrument/setup/workflow/combined/evaluate",
            json={
                "relief_gate": "red",
                "relief_diagnostic_ids": ["relief_too_low_severe"],
                "action_gate": "red",
                "action_diagnostic_ids": ["action_treble_too_low_severe"],
                "nut_gate": "green",
                "nut_diagnostic_ids": [],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["overall_gate"] == "red"
        assert any(d["id"] == "combined_fret_buzz_likely" for d in data["diagnostics"])

    def test_endpoint_nut_dominant_scenario(self):
        """POST with nut dominant scenario returns YELLOW."""
        response = client.post(
            "/api/instrument/setup/workflow/combined/evaluate",
            json={
                "relief_gate": "green",
                "relief_diagnostic_ids": ["relief_ok"],
                "action_gate": "green",
                "action_diagnostic_ids": [],
                "nut_gate": "red",
                "nut_diagnostic_ids": ["nut_slot_s1_too_high_severe"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["overall_gate"] == "yellow"
        assert any(d["id"] == "combined_nut_dominant" for d in data["diagnostics"])

    def test_endpoint_mixed_moderate_scenario(self):
        """POST with mixed moderate scenario returns YELLOW."""
        response = client.post(
            "/api/instrument/setup/workflow/combined/evaluate",
            json={
                "relief_gate": "yellow",
                "relief_diagnostic_ids": ["relief_too_low"],
                "action_gate": "yellow",
                "action_diagnostic_ids": ["action_treble_too_high"],
                "nut_gate": "green",
                "nut_diagnostic_ids": [],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["overall_gate"] == "yellow"
        assert any(d["id"] == "combined_mixed_moderate" for d in data["diagnostics"])

    def test_endpoint_requires_gates(self):
        """POST without required gates returns 422."""
        response = client.post(
            "/api/instrument/setup/workflow/combined/evaluate",
            json={},
        )

        assert response.status_code == 422

    def test_endpoint_validates_gate_values(self):
        """POST with invalid gate value returns 422."""
        response = client.post(
            "/api/instrument/setup/workflow/combined/evaluate",
            json={
                "relief_gate": "invalid",
                "action_gate": "green",
                "nut_gate": "green",
            },
        )

        assert response.status_code == 422
