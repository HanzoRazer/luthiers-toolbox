"""
Minimal coverage tests for app.rmos.feasibility.explain.

Target: bring explain.py from 28% to >60% coverage.
"""

import pytest

from app.rmos.feasibility.explain import (
    explain_rules,
    derive_summary,
    explain_decision,
    explain_to_dict,
)


class TestExplainRules:
    """Test explain_rules function."""

    def test_known_rule_id(self):
        result = explain_rules(["F001"])
        assert result is not None
        assert len(result) == 1
        assert result[0]["rule_id"] == "F001"
        assert result[0]["level"] != "UNKNOWN"

    def test_unknown_rule_id(self):
        result = explain_rules(["FAKE_RULE_999"])
        assert result is not None
        assert len(result) == 1
        assert result[0]["rule_id"] == "FAKE_RULE_999"
        assert result[0]["level"] == "UNKNOWN"
        assert "Unknown rule" in result[0]["summary"]

    def test_multiple_rules(self):
        result = explain_rules(["F001", "F002", "UNKNOWN_X"])
        assert len(result) == 3

    def test_empty_rules(self):
        result = explain_rules([])
        assert result == []


class TestDeriveSummary:
    """Test derive_summary function."""

    def test_green_summary(self):
        summary = derive_summary("GREEN", 0)
        assert summary is not None
        assert "passed" in summary.lower()

    def test_yellow_summary_single(self):
        summary = derive_summary("YELLOW", 1)
        assert summary is not None
        assert "warning" in summary.lower()
        assert "1" in summary

    def test_yellow_summary_plural(self):
        summary = derive_summary("YELLOW", 3)
        assert "warnings" in summary

    def test_red_summary_single(self):
        summary = derive_summary("RED", 1)
        assert summary is not None
        assert "blocked" in summary.lower()

    def test_red_summary_plural(self):
        summary = derive_summary("RED", 5)
        assert "issues" in summary

    def test_unknown_summary(self):
        summary = derive_summary("INVALID", 0)
        assert "unknown" in summary.lower()


class TestExplainDecision:
    """Test explain_decision function."""

    def test_with_run_artifact(self):
        run_artifact = {
            "feasibility": {
                "risk_level": "YELLOW",
                "rules_triggered": ["F001"],
            },
            "decision": {
                "risk_level": "YELLOW",
            },
        }
        result = explain_decision(run_artifact)
        assert result is not None
        assert result["risk_level"] == "YELLOW"
        assert len(result["triggered_rules"]) == 1

    def test_with_components(self):
        result = explain_decision(
            feasibility={"risk_level": "RED", "rules_triggered": ["F001", "F002"]},
            decision={"risk_level": "RED"},
        )
        assert result["risk_level"] == "RED"
        assert len(result["triggered_rules"]) == 2

    def test_with_override_reason(self):
        result = explain_decision(
            feasibility={"risk_level": "YELLOW", "rules_triggered": []},
            override_reason="Operator approved",
        )
        assert result["override_reason"] == "Operator approved"

    def test_override_from_decision_details(self):
        result = explain_decision(
            run_artifact={
                "feasibility": {"rules_triggered": []},
                "decision": {
                    "risk_level": "GREEN",
                    "details": {"override_reason": "From details"},
                },
            }
        )
        assert result["override_reason"] == "From details"

    def test_empty_input(self):
        result = explain_decision()
        assert result is not None
        assert result["risk_level"] == "UNKNOWN"
        assert result["triggered_rules"] == []

    def test_risk_level_with_value_attr(self):
        """Test handling of enum-like risk_level with .value attribute."""
        class FakeEnum:
            value = "GREEN"

        result = explain_decision(
            feasibility={"risk_level": FakeEnum(), "rules_triggered": []},
        )
        assert result["risk_level"] == "GREEN"


class TestExplainToDict:
    """Test explain_to_dict function."""

    def test_converts_to_dict(self):
        explanation = explain_decision(
            feasibility={"risk_level": "GREEN", "rules_triggered": []},
        )
        result = explain_to_dict(explanation)
        assert isinstance(result, dict)
        assert result["risk_level"] == "GREEN"
        assert "triggered_rules" in result
        assert isinstance(result["triggered_rules"], list)
