"""
Tests for Feasibility Explanation Derivation (Phase 3).

These tests verify the human-readable explanation generation from rule IDs.
"""
import pytest

from app.rmos.feasibility.explain import (
    explain_rules,
    derive_summary,
    explain_decision,
    explain_to_dict,
    TriggeredRuleExplanation,
    DecisionExplanation,
)


class TestExplainRules:
    """Tests for explain_rules function."""

    def test_known_rule_returns_full_metadata(self):
        """Known rules should return full registry metadata."""
        explanations = explain_rules(["F001"])
        assert len(explanations) == 1
        exp = explanations[0]
        assert exp["rule_id"] == "F001"
        assert exp["level"] in ("RED", "YELLOW", "GREEN")
        assert exp["summary"]  # Non-empty
        assert exp["description"]  # Non-empty
        assert exp["operator_hint"]  # Non-empty

    def test_unknown_rule_returns_fallback(self):
        """Unknown rules should return fallback explanation."""
        explanations = explain_rules(["UNKNOWN_RULE_XYZ"])
        assert len(explanations) == 1
        exp = explanations[0]
        assert exp["rule_id"] == "UNKNOWN_RULE_XYZ"
        assert exp["level"] == "UNKNOWN"
        assert "Unknown rule" in exp["summary"]
        assert "not in the registry" in exp["description"]

    def test_multiple_rules(self):
        """Multiple rules should all be explained."""
        explanations = explain_rules(["F001", "F002", "FAKE"])
        assert len(explanations) == 3
        # F001 and F002 should be known
        assert explanations[0]["rule_id"] == "F001"
        assert explanations[1]["rule_id"] == "F002"
        # FAKE should be unknown
        assert explanations[2]["level"] == "UNKNOWN"

    def test_empty_list(self):
        """Empty list should return empty list."""
        explanations = explain_rules([])
        assert explanations == []


class TestDeriveSummary:
    """Tests for derive_summary function."""

    def test_green_summary(self):
        summary = derive_summary("GREEN", 0)
        assert summary == "All checks passed"

    def test_yellow_singular(self):
        summary = derive_summary("YELLOW", 1)
        assert "1 warning" in summary
        assert "warnings" not in summary  # Should be singular

    def test_yellow_plural(self):
        summary = derive_summary("YELLOW", 3)
        assert "3 warnings" in summary

    def test_red_singular(self):
        summary = derive_summary("RED", 1)
        assert "1 critical issue" in summary
        assert "issues" not in summary  # Should be singular

    def test_red_plural(self):
        summary = derive_summary("RED", 2)
        assert "2 critical issues" in summary

    def test_unknown_level(self):
        summary = derive_summary("PURPLE", 5)
        assert summary == "Status unknown"


class TestExplainDecision:
    """Tests for explain_decision function."""

    def test_from_run_artifact(self):
        """Should extract components from run_artifact."""
        run_artifact = {
            "feasibility": {
                "risk_level": "YELLOW",
                "rules_triggered": ["F010", "F011"],
            },
            "decision": {
                "risk_level": "YELLOW",
                "details": {"override_reason": None},
            },
        }
        explanation = explain_decision(run_artifact)
        assert explanation["risk_level"] == "YELLOW"
        assert len(explanation["triggered_rules"]) == 2
        assert "warning" in explanation["summary"].lower()

    def test_from_components(self):
        """Should work with individual components."""
        explanation = explain_decision(
            feasibility={"risk_level": "RED", "rules_triggered": ["F001"]},
            decision={"risk_level": "RED"},
        )
        assert explanation["risk_level"] == "RED"
        assert len(explanation["triggered_rules"]) == 1
        assert "Blocked" in explanation["summary"]

    def test_override_reason_from_decision_details(self):
        """Should extract override_reason from decision.details."""
        run_artifact = {
            "feasibility": {"risk_level": "YELLOW", "rules_triggered": ["F010"]},
            "decision": {
                "risk_level": "GREEN",
                "details": {"override_reason": "Operator approved after inspection"},
            },
        }
        explanation = explain_decision(run_artifact)
        assert explanation["override_reason"] == "Operator approved after inspection"

    def test_override_reason_direct(self):
        """Should accept override_reason as direct parameter."""
        explanation = explain_decision(
            feasibility={"risk_level": "YELLOW", "rules_triggered": ["F010"]},
            override_reason="Manual override",
        )
        assert explanation["override_reason"] == "Manual override"

    def test_empty_input_returns_defaults(self):
        """Empty input should return sensible defaults."""
        explanation = explain_decision()
        assert explanation["risk_level"] == "UNKNOWN"
        assert explanation["triggered_rules"] == []
        assert explanation["override_reason"] is None

    def test_risk_level_enum_value_handling(self):
        """Should handle risk_level with .value attribute (enums)."""
        class MockEnum:
            value = "GREEN"

        explanation = explain_decision(
            feasibility={"risk_level": MockEnum(), "rules_triggered": []},
        )
        assert explanation["risk_level"] == "GREEN"

    def test_decision_risk_level_takes_precedence(self):
        """Decision risk_level should take precedence over feasibility."""
        explanation = explain_decision(
            feasibility={"risk_level": "RED", "rules_triggered": ["F001"]},
            decision={"risk_level": "GREEN"},  # Override
        )
        assert explanation["risk_level"] == "GREEN"


class TestExplainToDict:
    """Tests for explain_to_dict function."""

    def test_converts_to_plain_dict(self):
        explanation: DecisionExplanation = {
            "risk_level": "YELLOW",
            "summary": "Test summary",
            "triggered_rules": [
                {
                    "rule_id": "F010",
                    "level": "YELLOW",
                    "summary": "Rule summary",
                    "description": "Rule description",
                    "operator_hint": "Do something",
                }
            ],
            "override_reason": None,
        }
        d = explain_to_dict(explanation)
        assert isinstance(d, dict)
        assert d["risk_level"] == "YELLOW"
        assert d["summary"] == "Test summary"
        assert len(d["triggered_rules"]) == 1
        assert isinstance(d["triggered_rules"][0], dict)
        assert d["override_reason"] is None
