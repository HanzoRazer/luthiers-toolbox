"""
Tests for expert symptom-based workflow evaluation (Phase 7).

Tests evaluate_expert_symptoms() function and the expert endpoint.
"""

import pytest
from fastapi.testclient import TestClient

from app.instrument_geometry.neck.setup_workflow import (
    DiagnosticGate,
    PlayerSymptom,
    evaluate_expert_symptoms,
)
from app.main import app


client = TestClient(app)


# ─── Unit Tests: evaluate_expert_symptoms() ────────────────────────────────────


class TestEvaluateExpertSymptomsUnit:
    """Unit tests for evaluate_expert_symptoms function."""

    def test_rule1_open_string_buzz_nut_low(self):
        """Open string buzz + nut too low → RED, confidence >= 0.85."""
        result = evaluate_expert_symptoms(
            symptoms=[PlayerSymptom.BUZZ_OPEN_STRINGS],
            relief_gate=DiagnosticGate.GREEN,
            relief_diagnostic_ids=["relief_ok"],
            action_gate=DiagnosticGate.GREEN,
            action_diagnostic_ids=[],
            nut_gate=DiagnosticGate.RED,
            nut_diagnostic_ids=["nut_slot_s1_too_low_severe"],
        )

        assert result.overall_gate == DiagnosticGate.RED
        assert len(result.diagnostics) == 1
        diag = result.diagnostics[0]
        assert diag.id == "expert_open_string_buzz_nut"
        assert diag.symptom == PlayerSymptom.BUZZ_OPEN_STRINGS
        assert diag.confidence >= 0.85
        assert "nut" in diag.message.lower()

    def test_rule2_low_fret_buzz_relief_low(self):
        """Low fret buzz + relief too low → RED."""
        result = evaluate_expert_symptoms(
            symptoms=[PlayerSymptom.BUZZ_LOW_FRETS],
            relief_gate=DiagnosticGate.RED,
            relief_diagnostic_ids=["relief_too_low_severe"],
            action_gate=DiagnosticGate.GREEN,
            action_diagnostic_ids=[],
            nut_gate=DiagnosticGate.GREEN,
            nut_diagnostic_ids=[],
        )

        assert result.overall_gate == DiagnosticGate.RED
        diag = result.diagnostics[0]
        assert diag.id == "expert_low_fret_buzz_relief"
        assert diag.confidence >= 0.8
        assert "relief" in diag.message.lower()

    def test_rule3_middle_fret_buzz_relief_low(self):
        """Middle fret buzz + relief too low → RED/YELLOW."""
        result = evaluate_expert_symptoms(
            symptoms=[PlayerSymptom.BUZZ_MIDDLE_FRETS],
            relief_gate=DiagnosticGate.RED,
            relief_diagnostic_ids=["relief_too_low_severe"],
            action_gate=DiagnosticGate.GREEN,
            action_diagnostic_ids=[],
            nut_gate=DiagnosticGate.GREEN,
            nut_diagnostic_ids=[],
        )

        diag = result.diagnostics[0]
        assert diag.id == "expert_middle_fret_buzz_interaction"
        assert diag.gate == DiagnosticGate.RED

    def test_rule3_middle_fret_buzz_action_low(self):
        """Middle fret buzz + action too low → triggers rule."""
        result = evaluate_expert_symptoms(
            symptoms=[PlayerSymptom.BUZZ_MIDDLE_FRETS],
            relief_gate=DiagnosticGate.GREEN,
            relief_diagnostic_ids=["relief_ok"],
            action_gate=DiagnosticGate.YELLOW,
            action_diagnostic_ids=["action_treble_too_low"],
            nut_gate=DiagnosticGate.GREEN,
            nut_diagnostic_ids=[],
        )

        diag = result.diagnostics[0]
        assert diag.id == "expert_middle_fret_buzz_interaction"
        assert diag.gate == DiagnosticGate.YELLOW

    def test_rule4_upper_fret_buzz_action_low(self):
        """Upper fret buzz + action too low → triggers rule."""
        result = evaluate_expert_symptoms(
            symptoms=[PlayerSymptom.BUZZ_UPPER_FRETS],
            relief_gate=DiagnosticGate.GREEN,
            relief_diagnostic_ids=[],
            action_gate=DiagnosticGate.RED,
            action_diagnostic_ids=["action_treble_too_low_severe"],
            nut_gate=DiagnosticGate.GREEN,
            nut_diagnostic_ids=[],
        )

        diag = result.diagnostics[0]
        assert diag.id == "expert_upper_fret_buzz_action"
        assert diag.gate == DiagnosticGate.RED
        assert "saddle" in diag.message.lower() or "action" in diag.message.lower()

    def test_rule5_first_position_hard_nut_high(self):
        """First position hard + nut too high → RED, confidence >= 0.85."""
        result = evaluate_expert_symptoms(
            symptoms=[PlayerSymptom.FIRST_POSITION_HARD],
            relief_gate=DiagnosticGate.GREEN,
            relief_diagnostic_ids=[],
            action_gate=DiagnosticGate.GREEN,
            action_diagnostic_ids=[],
            nut_gate=DiagnosticGate.RED,
            nut_diagnostic_ids=["nut_slot_s1_too_high_severe"],
        )

        diag = result.diagnostics[0]
        assert diag.id == "expert_first_position_hard_nut"
        assert diag.gate == DiagnosticGate.RED
        assert diag.confidence >= 0.85

    def test_rule6_first_position_sharp_nut_high(self):
        """First position sharp + nut too high → triggers rule."""
        result = evaluate_expert_symptoms(
            symptoms=[PlayerSymptom.FIRST_POSITION_SHARP],
            relief_gate=DiagnosticGate.GREEN,
            relief_diagnostic_ids=[],
            action_gate=DiagnosticGate.GREEN,
            action_diagnostic_ids=[],
            nut_gate=DiagnosticGate.YELLOW,
            nut_diagnostic_ids=["nut_slot_s2_too_high"],
        )

        diag = result.diagnostics[0]
        assert diag.id == "expert_first_position_sharp_nut"
        assert "sharp" in diag.message.lower() or "stretch" in diag.message.lower()

    def test_rule7_feels_stiff_action_high(self):
        """Feels stiff + high action → YELLOW."""
        result = evaluate_expert_symptoms(
            symptoms=[PlayerSymptom.FEELS_STIFF],
            relief_gate=DiagnosticGate.GREEN,
            relief_diagnostic_ids=[],
            action_gate=DiagnosticGate.RED,
            action_diagnostic_ids=["action_treble_too_high_severe"],
            nut_gate=DiagnosticGate.GREEN,
            nut_diagnostic_ids=[],
        )

        diag = result.diagnostics[0]
        assert diag.id == "expert_feels_stiff_action_nut"
        assert diag.gate == DiagnosticGate.YELLOW
        assert diag.confidence >= 0.6

    def test_rule7_feels_stiff_nut_high(self):
        """Feels stiff + high nut → YELLOW."""
        result = evaluate_expert_symptoms(
            symptoms=[PlayerSymptom.FEELS_STIFF],
            relief_gate=DiagnosticGate.GREEN,
            relief_diagnostic_ids=[],
            action_gate=DiagnosticGate.GREEN,
            action_diagnostic_ids=[],
            nut_gate=DiagnosticGate.YELLOW,
            nut_diagnostic_ids=["nut_slot_s1_too_high"],
        )

        diag = result.diagnostics[0]
        assert diag.id == "expert_feels_stiff_action_nut"

    def test_rule8_feels_slinky_action_low(self):
        """Feels slinky + low action → YELLOW."""
        result = evaluate_expert_symptoms(
            symptoms=[PlayerSymptom.FEELS_SLINKY],
            relief_gate=DiagnosticGate.GREEN,
            relief_diagnostic_ids=[],
            action_gate=DiagnosticGate.YELLOW,
            action_diagnostic_ids=["action_bass_too_low"],
            nut_gate=DiagnosticGate.GREEN,
            nut_diagnostic_ids=[],
        )

        diag = result.diagnostics[0]
        assert diag.id == "expert_feels_slinky_action"
        assert diag.gate == DiagnosticGate.YELLOW
        assert diag.confidence >= 0.5

    def test_fallback_no_matching_measurement(self):
        """Symptom with no matching measurement → YELLOW fallback, confidence 0.4."""
        result = evaluate_expert_symptoms(
            symptoms=[PlayerSymptom.BUZZ_LOW_FRETS],
            relief_gate=DiagnosticGate.GREEN,
            relief_diagnostic_ids=["relief_ok"],
            action_gate=DiagnosticGate.GREEN,
            action_diagnostic_ids=[],
            nut_gate=DiagnosticGate.GREEN,
            nut_diagnostic_ids=[],
        )

        assert result.overall_gate == DiagnosticGate.YELLOW
        diag = result.diagnostics[0]
        assert "fallback" in diag.id
        assert diag.gate == DiagnosticGate.YELLOW
        assert diag.confidence == 0.4
        assert "not strongly" in diag.message.lower()

    def test_multiple_symptoms_multiple_diagnostics(self):
        """Multiple symptoms → one diagnostic per symptom."""
        result = evaluate_expert_symptoms(
            symptoms=[PlayerSymptom.BUZZ_LOW_FRETS, PlayerSymptom.FIRST_POSITION_HARD],
            relief_gate=DiagnosticGate.RED,
            relief_diagnostic_ids=["relief_too_low_severe"],
            action_gate=DiagnosticGate.GREEN,
            action_diagnostic_ids=[],
            nut_gate=DiagnosticGate.RED,
            nut_diagnostic_ids=["nut_slot_s1_too_high_severe"],
        )

        assert len(result.diagnostics) == 2
        symptoms_found = {d.symptom for d in result.diagnostics}
        assert PlayerSymptom.BUZZ_LOW_FRETS in symptoms_found
        assert PlayerSymptom.FIRST_POSITION_HARD in symptoms_found

    def test_diagnostics_sorted_by_severity_then_confidence(self):
        """Diagnostics should be sorted RED > YELLOW > GREEN, then by confidence."""
        result = evaluate_expert_symptoms(
            symptoms=[PlayerSymptom.FEELS_STIFF, PlayerSymptom.BUZZ_LOW_FRETS],
            relief_gate=DiagnosticGate.RED,
            relief_diagnostic_ids=["relief_too_low_severe"],
            action_gate=DiagnosticGate.RED,
            action_diagnostic_ids=["action_treble_too_high_severe"],
            nut_gate=DiagnosticGate.GREEN,
            nut_diagnostic_ids=[],
        )

        # buzz_low_frets should be RED, feels_stiff should be YELLOW
        assert result.diagnostics[0].gate == DiagnosticGate.RED
        assert result.diagnostics[1].gate == DiagnosticGate.YELLOW

    def test_overall_gate_worst_case(self):
        """Overall gate should be worst-case across all diagnostics."""
        result = evaluate_expert_symptoms(
            symptoms=[PlayerSymptom.FEELS_SLINKY, PlayerSymptom.BUZZ_LOW_FRETS],
            relief_gate=DiagnosticGate.RED,
            relief_diagnostic_ids=["relief_too_low_severe"],
            action_gate=DiagnosticGate.YELLOW,
            action_diagnostic_ids=["action_bass_too_low"],
            nut_gate=DiagnosticGate.GREEN,
            nut_diagnostic_ids=[],
        )

        # buzz_low_frets should be RED, feels_slinky should be YELLOW
        assert result.overall_gate == DiagnosticGate.RED

    def test_fretted_notes_buzz_general(self):
        """Fretted notes buzz → general diagnosis when relief/action low."""
        result = evaluate_expert_symptoms(
            symptoms=[PlayerSymptom.FRETTED_NOTES_BUZZ],
            relief_gate=DiagnosticGate.YELLOW,
            relief_diagnostic_ids=["relief_too_low"],
            action_gate=DiagnosticGate.GREEN,
            action_diagnostic_ids=[],
            nut_gate=DiagnosticGate.GREEN,
            nut_diagnostic_ids=[],
        )

        diag = result.diagnostics[0]
        assert diag.id == "expert_fretted_buzz_general"
        assert diag.symptom == PlayerSymptom.FRETTED_NOTES_BUZZ


# ─── Endpoint Tests ──────────────────────────────────────────────────────────


class TestExpertEndpoint:
    """Integration tests for the expert workflow endpoint."""

    def test_endpoint_returns_200_with_valid_input(self):
        """POST with valid symptoms and gates returns 200."""
        response = client.post(
            "/api/instrument/setup/workflow/expert/evaluate",
            json={
                "symptoms": ["buzz_low_frets"],
                "relief_gate": "red",
                "relief_diagnostic_ids": ["relief_too_low_severe"],
                "action_gate": "green",
                "action_diagnostic_ids": [],
                "nut_gate": "green",
                "nut_diagnostic_ids": [],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["overall_gate"] == "red"
        assert len(data["diagnostics"]) == 1
        assert data["diagnostics"][0]["symptom"] == "buzz_low_frets"

    def test_endpoint_multiple_symptoms(self):
        """POST with multiple symptoms returns multiple diagnostics."""
        response = client.post(
            "/api/instrument/setup/workflow/expert/evaluate",
            json={
                "symptoms": ["buzz_low_frets", "first_position_hard"],
                "relief_gate": "red",
                "relief_diagnostic_ids": ["relief_too_low_severe"],
                "action_gate": "green",
                "action_diagnostic_ids": [],
                "nut_gate": "red",
                "nut_diagnostic_ids": ["nut_slot_s1_too_high_severe"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["diagnostics"]) == 2

    def test_endpoint_fallback_scenario(self):
        """POST with symptom and no matching measurement returns fallback."""
        response = client.post(
            "/api/instrument/setup/workflow/expert/evaluate",
            json={
                "symptoms": ["buzz_upper_frets"],
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
        assert data["overall_gate"] == "yellow"
        assert "fallback" in data["diagnostics"][0]["id"]

    def test_endpoint_requires_symptoms(self):
        """POST without symptoms returns 422."""
        response = client.post(
            "/api/instrument/setup/workflow/expert/evaluate",
            json={
                "symptoms": [],
                "relief_gate": "green",
                "action_gate": "green",
                "nut_gate": "green",
            },
        )

        assert response.status_code == 422

    def test_endpoint_validates_symptom_values(self):
        """POST with invalid symptom value returns 422."""
        response = client.post(
            "/api/instrument/setup/workflow/expert/evaluate",
            json={
                "symptoms": ["invalid_symptom"],
                "relief_gate": "green",
                "action_gate": "green",
                "nut_gate": "green",
            },
        )

        assert response.status_code == 422

    def test_endpoint_validates_gate_values(self):
        """POST with invalid gate value returns 422."""
        response = client.post(
            "/api/instrument/setup/workflow/expert/evaluate",
            json={
                "symptoms": ["buzz_low_frets"],
                "relief_gate": "invalid",
                "action_gate": "green",
                "nut_gate": "green",
            },
        )

        assert response.status_code == 422

    def test_endpoint_includes_confidence(self):
        """Response diagnostics include confidence scores."""
        response = client.post(
            "/api/instrument/setup/workflow/expert/evaluate",
            json={
                "symptoms": ["first_position_hard"],
                "relief_gate": "green",
                "relief_diagnostic_ids": [],
                "action_gate": "green",
                "action_diagnostic_ids": [],
                "nut_gate": "red",
                "nut_diagnostic_ids": ["nut_slot_s1_too_high_severe"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        diag = data["diagnostics"][0]
        assert "confidence" in diag
        assert 0 <= diag["confidence"] <= 1
