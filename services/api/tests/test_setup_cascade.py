"""
Tests for instrument setup cascade calculator (CONSTRUCTION-002).
"""

import pytest

from app.calculators.setup_cascade import (
    SetupState,
    SetupIssue,
    SetupCascadeResult,
    evaluate_setup,
    suggest_adjustments,
)


def _green_state() -> SetupState:
    """All parameters in GREEN ranges. Geometry chosen so derived neck angle is GREEN."""
    return SetupState(
        neck_angle_deg=1.8,
        truss_rod_relief_mm=0.25,
        action_at_nut_mm=0.45,
        action_at_12th_treble_mm=1.9,
        action_at_12th_bass_mm=2.4,
        saddle_height_mm=12.0,
        saddle_projection_mm=2.5,
        fretboard_height_at_joint_mm=5.0,  # 12+2.5-5 = 9.5mm diff → ~1.46° GREEN
        scale_length_mm=628.65,
    )


class TestAllGreenSetup:
    """All GREEN setup → no issues or only minor."""

    def test_all_green_returns_green_overall(self):
        result = evaluate_setup(_green_state())
        assert result.overall_gate == "GREEN"
        assert "within recommended" in result.summary.lower()

    def test_all_green_suggestions_empty_or_minimal(self):
        result = evaluate_setup(_green_state())
        suggestions = suggest_adjustments(result)
        assert len(suggestions) == 0 or result.overall_gate == "GREEN"


class TestLowAction:
    """Low action → YELLOW with fix suggestion."""

    def test_low_treble_12th_yellow(self):
        state = SetupState(
            action_at_12th_treble_mm=1.0,
            action_at_12th_bass_mm=2.0,
            truss_rod_relief_mm=0.25,
            action_at_nut_mm=0.5,
            saddle_projection_mm=2.5,
        )
        result = evaluate_setup(state)
        assert result.overall_gate in ("YELLOW", "RED")
        treble_issues = [i for i in result.issues if i.parameter == "action_at_12th_treble_mm"]
        assert len(treble_issues) >= 1
        assert any("saddle" in i.fix.lower() or "action" in i.fix.lower() for i in treble_issues)

    def test_low_action_suggestion_returned(self):
        state = SetupState(action_at_12th_treble_mm=1.0, action_at_12th_bass_mm=1.5)
        result = evaluate_setup(state)
        suggestions = suggest_adjustments(result)
        assert len(suggestions) >= 1


class TestBadNeckAngleCascades:
    """Bad neck angle → RED cascades to saddle/geometry issue."""

    def test_flat_neck_angle_red(self):
        state = SetupState(neck_angle_deg=0.3, saddle_projection_mm=2.5)
        result = evaluate_setup(state)
        # Either neck_angle issue is RED or overall is RED
        neck_issues = [i for i in result.issues if i.parameter == "neck_angle_deg"]
        assert result.overall_gate == "RED" or (neck_issues and neck_issues[0].gate == "RED")

    def test_steep_neck_angle_red(self):
        state = SetupState(neck_angle_deg=6.0)
        result = evaluate_setup(state)
        assert result.overall_gate == "RED" or any(
            i.parameter == "neck_angle_deg" and i.gate == "RED" for i in result.issues
        )


class TestReliefOutOfRange:
    """Relief out of range → YELLOW or RED."""

    def test_relief_too_low_yellow_or_red(self):
        state = SetupState(truss_rod_relief_mm=0.08)
        result = evaluate_setup(state)
        relief_issues = [i for i in result.issues if i.parameter == "truss_rod_relief_mm"]
        assert len(relief_issues) >= 1
        assert relief_issues[0].gate in ("YELLOW", "RED")

    def test_relief_too_high_yellow_or_red(self):
        state = SetupState(truss_rod_relief_mm=0.5)
        result = evaluate_setup(state)
        relief_issues = [i for i in result.issues if i.parameter == "truss_rod_relief_mm"]
        assert len(relief_issues) >= 1


class TestSuggestAdjustments:
    """suggest_adjustments returns plain-language list."""

    def test_red_first_then_yellow(self):
        state = SetupState(
            truss_rod_relief_mm=0.05,  # RED
            action_at_12th_treble_mm=2.4,  # YELLOW
        )
        result = evaluate_setup(state)
        suggestions = suggest_adjustments(result)
        assert len(suggestions) >= 1
        # RED fixes should appear before or with YELLOW
        red_issues = [i.fix for i in result.issues if i.gate == "RED"]
        for fix in red_issues:
            assert fix in suggestions

    def test_suggestions_match_issue_fixes(self):
        state = SetupState(saddle_projection_mm=0.8)  # RED
        result = evaluate_setup(state)
        suggestions = suggest_adjustments(result)
        assert len(result.issues) >= 1
        assert len(suggestions) >= 1
        assert all(isinstance(s, str) for s in suggestions)


class TestSaddleProjection:
    """Saddle projection gate."""

    def test_saddle_too_low_red(self):
        state = SetupState(saddle_projection_mm=1.0)
        result = evaluate_setup(state)
        saddle_issues = [i for i in result.issues if i.parameter == "saddle_projection_mm"]
        assert len(saddle_issues) >= 1
        assert saddle_issues[0].gate in ("YELLOW", "RED")

    def test_saddle_in_green_no_issue(self):
        state = _green_state()
        result = evaluate_setup(state)
        saddle_issues = [i for i in result.issues if i.parameter == "saddle_projection_mm"]
        assert len(saddle_issues) == 0


class TestNutAction:
    """Nut action gate."""

    def test_nut_too_high_yellow_or_red(self):
        state = SetupState(action_at_nut_mm=1.0)
        result = evaluate_setup(state)
        nut_issues = [i for i in result.issues if i.parameter == "action_at_nut_mm"]
        assert len(nut_issues) >= 1


class TestSetupCascadeResultStructure:
    """Result has required fields."""

    def test_result_has_state_issues_overall_summary(self):
        result = evaluate_setup(SetupState())
        assert hasattr(result, "state")
        assert hasattr(result, "issues")
        assert result.overall_gate in ("GREEN", "YELLOW", "RED")
        assert isinstance(result.summary, str)
        assert len(result.summary) > 0


class TestSetupEvaluateEndpoint:
    """POST /api/instrument/setup/evaluate."""

    def test_setup_evaluate_returns_200_and_structure(self, client):
        response = client.post(
            "/api/instrument/setup/evaluate",
            json={
                "neck_angle_deg": 1.5,
                "truss_rod_relief_mm": 0.25,
                "action_at_nut_mm": 0.5,
                "action_at_12th_treble_mm": 1.9,
                "action_at_12th_bass_mm": 2.4,
                "saddle_projection_mm": 2.5,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "state" in data
        assert "issues" in data
        assert "overall_gate" in data
        assert data["overall_gate"] in ("GREEN", "YELLOW", "RED")
        assert "summary" in data
        assert "suggestions" in data
