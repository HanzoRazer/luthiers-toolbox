"""
Unit tests for Saw Safety Gate wrapper.

Tests compute_saw_safety_decision with saw-specific field name variations.
"""
import pytest
from enum import Enum
from app.rmos.policies import RiskLevel, SafetyPolicy
from app.rmos.policies.saw_safety_gate import compute_saw_safety_decision


class MockRiskBucket(str, Enum):
    """Mock RiskBucket enum to simulate FeasibilityResult."""
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"


class TestSawSafetyGate:
    """Tests for compute_saw_safety_decision."""

    def test_standard_safety_nested_payload(self):
        """Handle standard safety nested payload."""
        feasibility = {
            "mode": "saw",
            "tool_id": "saw:crosscut",
            "safety": {
                "risk_level": "GREEN",
                "score": 85.0,
                "warnings": ["Minor chipload concern"],
            },
        }
        decision = compute_saw_safety_decision(feasibility)
        assert decision.risk_level == RiskLevel.GREEN
        assert decision.score == 85.0

    def test_risk_bucket_top_level(self):
        """Handle saw-specific risk_bucket at top level."""
        feasibility = {
            "risk_bucket": "RED",
            "score": 20.0,
        }
        decision = compute_saw_safety_decision(feasibility)
        assert decision.risk_level == RiskLevel.RED
        assert decision.score == 20.0

    def test_risk_bucket_enum_with_value(self):
        """Handle risk_bucket as enum with .value attribute."""
        feasibility = {
            "risk_bucket": MockRiskBucket.YELLOW,
            "score": 60.0,
        }
        decision = compute_saw_safety_decision(feasibility)
        assert decision.risk_level == RiskLevel.YELLOW

    def test_risk_bucket_nested_in_safety(self):
        """Handle risk_bucket nested in safety block."""
        feasibility = {
            "mode": "saw",
            "safety": {
                "risk_bucket": "RED",
                "score": 15.0,
            },
        }
        decision = compute_saw_safety_decision(feasibility)
        assert decision.risk_level == RiskLevel.RED

    def test_risk_bucket_enum_nested(self):
        """Handle risk_bucket enum nested in safety block."""
        feasibility = {
            "safety": {
                "risk_bucket": MockRiskBucket.GREEN,
                "score": 95.0,
            },
        }
        decision = compute_saw_safety_decision(feasibility)
        assert decision.risk_level == RiskLevel.GREEN

    def test_risk_level_takes_precedence_over_risk_bucket(self):
        """When both present, risk_level should take precedence."""
        feasibility = {
            "risk_level": "GREEN",
            "risk_bucket": "RED",  # Should be ignored
        }
        decision = compute_saw_safety_decision(feasibility)
        assert decision.risk_level == RiskLevel.GREEN

    def test_missing_payload_returns_unknown(self):
        """Missing payload returns UNKNOWN."""
        decision = compute_saw_safety_decision(None)
        assert decision.risk_level == RiskLevel.UNKNOWN
        assert "missing" in decision.block_reason.lower()

    def test_empty_payload_returns_unknown(self):
        """Empty payload returns UNKNOWN."""
        decision = compute_saw_safety_decision({})
        assert decision.risk_level == RiskLevel.UNKNOWN

    def test_non_dict_returns_unknown(self):
        """Non-dict payload returns UNKNOWN."""
        decision = compute_saw_safety_decision("not a dict")
        assert decision.risk_level == RiskLevel.UNKNOWN


class TestSawIntegration:
    """Integration tests for saw safety gate with policy."""

    def test_feasibility_result_style_payload(self):
        """Test payload matching FeasibilityResult from feasibility_scorer."""
        # This mimics what compute_saw_feasibility returns
        feasibility = {
            "mode": "saw",
            "tool_id": "saw:crosscut",
            "safety": {
                "risk_level": "YELLOW",
                "score": 65.0,
                "block_reason": None,
                "warnings": ["Chipload at upper limit"],
                "details": {
                    "efficiency": 0.75,
                    "estimated_cut_time_seconds": 45.0,
                },
            },
        }
        decision = compute_saw_safety_decision(feasibility)
        assert decision.risk_level == RiskLevel.YELLOW
        assert decision.score == 65.0
        assert not SafetyPolicy.should_block(decision.risk_level)

    def test_red_saw_feasibility_blocks(self):
        """RED saw feasibility should block."""
        feasibility = {
            "mode": "saw",
            "safety": {
                "risk_level": "RED",
                "score": 10.0,
                "block_reason": "Spindle overload detected",
            },
        }
        decision = compute_saw_safety_decision(feasibility)
        assert decision.risk_level == RiskLevel.RED
        assert SafetyPolicy.should_block(decision.risk_level) is True

    def test_legacy_risk_bucket_blocks_on_red(self):
        """Legacy risk_bucket=RED should block."""
        feasibility = {"risk_bucket": "RED"}
        decision = compute_saw_safety_decision(feasibility)
        assert SafetyPolicy.should_block(decision.risk_level) is True
