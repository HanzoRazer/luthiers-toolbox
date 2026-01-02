"""
Safety Policy Unit Tests

Locks the contract for SafetyPolicy before applying across routers.
Tests all 3 feasibility payload shapes + compat wrappers.
"""
import pytest
from app.rmos.policies import SafetyPolicy, RiskLevel, extract_safety_decision, should_block


class TestSafetyPolicyExtraction:
    """Test SafetyPolicy.extract_safety_decision() with all payload shapes."""

    def test_extract_nested_safety(self):
        """Shape 3 (primary): nested safety block."""
        feasibility = {
            "safety": {
                "risk_level": "RED",
                "score": 0.1,
                "warnings": ["tool wear detected"],
                "block_reason": "excessive chipload",
            }
        }
        d = SafetyPolicy.extract_safety_decision(feasibility)
        assert d.risk_level == RiskLevel.RED
        assert d.score == 0.1
        assert d.block_reason == "excessive chipload"
        assert "tool wear detected" in d.warnings
        assert SafetyPolicy.should_block(d.risk_level) is True

    def test_extract_flat(self):
        """Shape 1: flat payload with risk_level at top level."""
        feasibility = {"risk_level": "GREEN", "score": 0.9, "warnings": []}
        d = SafetyPolicy.extract_safety_decision(feasibility)
        assert d.risk_level == RiskLevel.GREEN
        assert d.score == 0.9
        assert SafetyPolicy.should_block(d.risk_level) is False

    def test_extract_nested_decision(self):
        """Shape 2: nested decision block."""
        feasibility = {"decision": {"risk_level": "UNKNOWN", "warnings": ["missing data"]}}
        d = SafetyPolicy.extract_safety_decision(feasibility)
        assert d.risk_level == RiskLevel.UNKNOWN
        assert SafetyPolicy.should_block(d.risk_level) is True  # UNKNOWN treated as RED

    def test_extract_yellow_does_not_block(self):
        """YELLOW risk level should not block."""
        feasibility = {"risk_level": "YELLOW", "score": 0.6}
        d = SafetyPolicy.extract_safety_decision(feasibility)
        assert d.risk_level == RiskLevel.YELLOW
        assert SafetyPolicy.should_block(d.risk_level) is False

    def test_extract_missing_payload_returns_unknown(self):
        """Missing/None payload returns UNKNOWN (which blocks)."""
        d = SafetyPolicy.extract_safety_decision(None)
        assert d.risk_level == RiskLevel.UNKNOWN
        assert SafetyPolicy.should_block(d.risk_level) is True

    def test_extract_empty_dict_returns_unknown(self):
        """Empty dict returns UNKNOWN (which blocks)."""
        d = SafetyPolicy.extract_safety_decision({})
        assert d.risk_level == RiskLevel.UNKNOWN
        assert SafetyPolicy.should_block(d.risk_level) is True

    def test_extract_error_level_blocks(self):
        """ERROR risk level should block (treated as UNKNOWN)."""
        feasibility = {"risk_level": "ERROR"}
        d = SafetyPolicy.extract_safety_decision(feasibility)
        assert d.risk_level == RiskLevel.ERROR
        assert SafetyPolicy.should_block(d.risk_level) is True


class TestSafetyPolicyShouldBlock:
    """Test SafetyPolicy.should_block() with various inputs."""

    def test_block_on_red_enum(self):
        assert SafetyPolicy.should_block(RiskLevel.RED) is True

    def test_block_on_red_string(self):
        assert SafetyPolicy.should_block("RED") is True

    def test_block_on_unknown_enum(self):
        assert SafetyPolicy.should_block(RiskLevel.UNKNOWN) is True

    def test_block_on_unknown_string(self):
        assert SafetyPolicy.should_block("UNKNOWN") is True

    def test_no_block_on_green(self):
        assert SafetyPolicy.should_block(RiskLevel.GREEN) is False
        assert SafetyPolicy.should_block("GREEN") is False

    def test_no_block_on_yellow(self):
        assert SafetyPolicy.should_block(RiskLevel.YELLOW) is False
        assert SafetyPolicy.should_block("yellow") is False  # case insensitive

    def test_block_on_none_returns_true(self):
        """None input should be treated as UNKNOWN (blocks)."""
        assert SafetyPolicy.should_block(None) is True

    def test_block_on_empty_string_returns_true(self):
        """Empty string should be treated as UNKNOWN (blocks)."""
        assert SafetyPolicy.should_block("") is True


class TestCompatWrappers:
    """Test backward-compatible wrapper functions."""

    def test_extract_safety_decision_returns_dict(self):
        """Compat wrapper returns dict, not SafetyDecision."""
        feasibility = {"safety": {"risk_level": "RED", "score": 0.2}}
        decision = extract_safety_decision(feasibility)
        assert isinstance(decision, dict)
        assert decision["risk_level"] == "RED"
        assert decision["score"] == 0.2

    def test_should_block_with_mode_param(self):
        """Compat wrapper accepts mode param for signature compatibility."""
        assert should_block(mode="saw", risk_level="RED") is True
        assert should_block(mode="router_3axis", risk_level="GREEN") is False
        assert should_block(mode="vcarve", risk_level="UNKNOWN") is True

    def test_round_trip_compat(self):
        """Extract + should_block compat wrappers work together."""
        feasibility = {"safety": {"risk_level": "RED"}}
        decision = extract_safety_decision(feasibility)
        assert should_block(mode="saw", risk_level=decision["risk_level"]) is True

    def test_compat_with_nested_decision(self):
        """Compat wrappers handle nested decision shape."""
        feasibility = {"decision": {"risk_level": "YELLOW", "score": 0.7}}
        decision = extract_safety_decision(feasibility)
        assert decision["risk_level"] == "YELLOW"
        assert should_block(mode="drilling", risk_level=decision["risk_level"]) is False
