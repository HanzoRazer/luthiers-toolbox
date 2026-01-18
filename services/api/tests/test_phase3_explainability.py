"""
Phase 3 — Explainability Tests

Tests that:
1. Rule registry contains all rule IDs
2. RuleHit now includes rule_id
3. FeasibilityResult includes rules_triggered
4. explain_decision derives correct explanations
"""

from __future__ import annotations

import pytest


class TestRuleRegistry:
    """Test rule_registry.py is authoritative and complete."""

    def test_registry_has_all_red_rules(self):
        from app.rmos.feasibility.rule_registry import FEASIBILITY_RULES

        red_rules = ["F001", "F002", "F003", "F004", "F005", "F006", "F007"]
        for rule_id in red_rules:
            assert rule_id in FEASIBILITY_RULES, f"Missing RED rule: {rule_id}"
            assert FEASIBILITY_RULES[rule_id]["level"] == "RED"

    def test_registry_has_all_yellow_rules(self):
        from app.rmos.feasibility.rule_registry import FEASIBILITY_RULES

        yellow_rules = ["F010", "F011", "F012", "F013"]
        for rule_id in yellow_rules:
            assert rule_id in FEASIBILITY_RULES, f"Missing YELLOW rule: {rule_id}"
            assert FEASIBILITY_RULES[rule_id]["level"] == "YELLOW"

    def test_registry_entries_have_required_fields(self):
        from app.rmos.feasibility.rule_registry import FEASIBILITY_RULES

        required_fields = ["level", "summary", "description", "operator_hint"]
        for rule_id, meta in FEASIBILITY_RULES.items():
            for field in required_fields:
                assert field in meta, f"Rule {rule_id} missing field: {field}"
                assert isinstance(meta[field], str), f"Rule {rule_id}.{field} must be string"
                assert len(meta[field]) > 0, f"Rule {rule_id}.{field} must not be empty"


class TestRuleHitWithId:
    """Test RuleHit now includes rule_id."""

    def test_rule_hit_has_rule_id(self):
        from app.rmos.feasibility.rules import RuleHit

        hit = RuleHit("F001", "RED", "test message")
        assert hit.rule_id == "F001"
        assert hit.level == "RED"
        assert hit.message == "test message"

    def test_all_rules_return_rule_ids(self):
        from app.rmos.feasibility.rules import all_rules
        from app.rmos.feasibility.schemas import FeasibilityInput

        # Create input that triggers multiple rules
        fi = FeasibilityInput(
            tool_d=0,  # F001: invalid
            stepover=0.5,
            stepdown=1.0,
            z_rough=-3.0,
            feed_xy=300,
            feed_z=300,
            rapid=1000,
            safe_z=5,
            strategy="offset",
            layer_name="0",
            climb=True,
            smoothing=0,
            margin=0,
        )
        hits = all_rules(fi)

        assert len(hits) > 0, "Should have at least one rule hit"
        for hit in hits:
            assert hit.rule_id, f"Hit missing rule_id: {hit}"
            assert hit.rule_id.startswith("F"), f"Rule ID should start with F: {hit.rule_id}"


class TestFeasibilityResultWithRulesTriggered:
    """Test FeasibilityResult includes rules_triggered."""

    def test_result_has_rules_triggered_field(self):
        from app.rmos.feasibility import compute_feasibility
        from app.rmos.feasibility.schemas import FeasibilityInput

        fi = FeasibilityInput(
            tool_d=6.0,
            stepover=0.5,
            stepdown=1.0,
            z_rough=-3.0,
            feed_xy=300,
            feed_z=500,  # F011: feed_z > feed_xy
            rapid=1000,
            safe_z=5,
            strategy="offset",
            layer_name="0",
            climb=True,
            smoothing=0,
            margin=0,
        )
        result = compute_feasibility(fi)

        assert hasattr(result, "rules_triggered")
        assert isinstance(result.rules_triggered, list)
        assert "F011" in result.rules_triggered

    def test_green_result_has_empty_rules_triggered(self):
        from app.rmos.feasibility import compute_feasibility
        from app.rmos.feasibility.schemas import FeasibilityInput, RiskLevel

        fi = FeasibilityInput(
            tool_d=6.0,
            stepover=0.5,
            stepdown=1.0,
            z_rough=-3.0,
            feed_xy=500,
            feed_z=300,
            rapid=1000,
            safe_z=5,
            strategy="offset",
            layer_name="0",
            climb=True,
            smoothing=0,
            margin=0,
        )
        result = compute_feasibility(fi)

        assert result.risk_level == RiskLevel.GREEN
        assert result.rules_triggered == []


class TestExplainDecision:
    """Test explain_decision derives correct explanations."""

    def test_explain_with_rules_triggered(self):
        from app.rmos.feasibility.explain import explain_decision

        feasibility = {
            "risk_level": "YELLOW",
            "rules_triggered": ["F011"],
        }
        decision = {
            "risk_level": "YELLOW",
        }

        explanation = explain_decision(feasibility=feasibility, decision=decision)

        assert explanation["risk_level"] == "YELLOW"
        assert len(explanation["triggered_rules"]) == 1
        assert explanation["triggered_rules"][0]["rule_id"] == "F011"
        assert explanation["triggered_rules"][0]["summary"] == "Plunge feed exceeds lateral feed"
        assert "operator_hint" in explanation["triggered_rules"][0]

    def test_explain_from_run_artifact(self):
        from app.rmos.feasibility.explain import explain_decision

        run_artifact = {
            "feasibility": {
                "risk_level": "RED",
                "rules_triggered": ["F001", "F004"],
            },
            "decision": {
                "risk_level": "RED",
                "details": {
                    "override_reason": "Operator approved after review",
                },
            },
        }

        explanation = explain_decision(run_artifact)

        assert explanation["risk_level"] == "RED"
        assert len(explanation["triggered_rules"]) == 2
        assert explanation["override_reason"] == "Operator approved after review"

    def test_explain_unknown_rule_id(self):
        from app.rmos.feasibility.explain import explain_decision

        feasibility = {
            "risk_level": "YELLOW",
            "rules_triggered": ["F999"],  # Unknown rule
        }

        explanation = explain_decision(feasibility=feasibility)

        assert len(explanation["triggered_rules"]) == 1
        assert explanation["triggered_rules"][0]["rule_id"] == "F999"
        assert explanation["triggered_rules"][0]["level"] == "UNKNOWN"
        assert "Unknown rule" in explanation["triggered_rules"][0]["summary"]

    def test_derive_summary_deterministic(self):
        from app.rmos.feasibility.explain import derive_summary

        assert derive_summary("GREEN", 0) == "All checks passed"
        assert derive_summary("YELLOW", 1) == "Manual review required (1 warning)"
        assert derive_summary("YELLOW", 2) == "Manual review required (2 warnings)"
        assert derive_summary("RED", 1) == "Blocked (1 critical issue)"
        assert derive_summary("RED", 3) == "Blocked (3 critical issues)"


class TestExplainRules:
    """Test explain_rules function."""

    def test_explain_multiple_rules(self):
        from app.rmos.feasibility.explain import explain_rules

        explanations = explain_rules(["F001", "F011"])

        assert len(explanations) == 2
        assert explanations[0]["rule_id"] == "F001"
        assert explanations[0]["level"] == "RED"
        assert explanations[1]["rule_id"] == "F011"
        assert explanations[1]["level"] == "YELLOW"

    def test_explain_empty_list(self):
        from app.rmos.feasibility.explain import explain_rules

        explanations = explain_rules([])
        assert explanations == []
