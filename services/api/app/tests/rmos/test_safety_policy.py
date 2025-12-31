"""
Unit tests for RMOS Safety Policy module.

Tests SafetyPolicy.extract_safety_decision and SafetyPolicy.should_block
with various payload shapes and edge cases.
"""
import pytest
from app.rmos.policies import RiskLevel, SafetyDecision, SafetyPolicy


class TestRiskLevel:
    """Tests for RiskLevel enum."""

    def test_risk_level_values(self):
        """Verify all expected risk levels exist."""
        assert RiskLevel.GREEN.value == "GREEN"
        assert RiskLevel.YELLOW.value == "YELLOW"
        assert RiskLevel.RED.value == "RED"
        assert RiskLevel.UNKNOWN.value == "UNKNOWN"
        assert RiskLevel.ERROR.value == "ERROR"

    def test_risk_level_is_string_enum(self):
        """RiskLevel should be usable as string."""
        assert RiskLevel.GREEN == "GREEN"
        assert str(RiskLevel.RED) == "RED"


class TestSafetyDecision:
    """Tests for SafetyDecision dataclass."""

    def test_decision_is_immutable(self):
        """SafetyDecision should be frozen."""
        decision = SafetyDecision(risk_level=RiskLevel.GREEN)
        with pytest.raises(Exception):  # FrozenInstanceError
            decision.risk_level = RiskLevel.RED

    def test_risk_level_str(self):
        """risk_level_str() returns string value."""
        decision = SafetyDecision(risk_level=RiskLevel.YELLOW, score=85.0)
        assert decision.risk_level_str() == "YELLOW"

    def test_to_dict(self):
        """to_dict() returns serializable dict."""
        decision = SafetyDecision(
            risk_level=RiskLevel.RED,
            score=25.0,
            block_reason="Too dangerous",
            warnings=["High chipload", "Tool deflection risk"],
        )
        d = decision.to_dict()
        assert d["risk_level"] == "RED"
        assert d["score"] == 25.0
        assert d["block_reason"] == "Too dangerous"
        assert d["warnings"] == ["High chipload", "Tool deflection risk"]


class TestExtractSafetyDecision:
    """Tests for SafetyPolicy.extract_safety_decision."""

    def test_flat_payload(self):
        """Extract from flat payload with risk_level at top level."""
        feasibility = {
            "risk_level": "GREEN",
            "score": 95.0,
            "warnings": ["Minor concern"],
        }
        decision = SafetyPolicy.extract_safety_decision(feasibility)
        assert decision.risk_level == RiskLevel.GREEN
        assert decision.score == 95.0
        assert decision.warnings == ["Minor concern"]

    def test_nested_safety_payload(self):
        """Extract from nested safety block (common RMOS pattern)."""
        feasibility = {
            "mode": "saw",
            "tool_id": "saw:crosscut",
            "safety": {
                "risk_level": "YELLOW",
                "score": 70.0,
                "block_reason": None,
                "warnings": ["Moderate chipload"],
            },
        }
        decision = SafetyPolicy.extract_safety_decision(feasibility)
        assert decision.risk_level == RiskLevel.YELLOW
        assert decision.score == 70.0

    def test_nested_decision_payload(self):
        """Extract from nested decision block."""
        feasibility = {
            "decision": {
                "risk_level": "RED",
                "score": 20.0,
                "block_reason": "Safety limit exceeded",
            },
        }
        decision = SafetyPolicy.extract_safety_decision(feasibility)
        assert decision.risk_level == RiskLevel.RED
        assert decision.block_reason == "Safety limit exceeded"

    def test_missing_risk_level_returns_unknown(self):
        """Missing risk_level should return UNKNOWN."""
        feasibility = {"score": 50.0, "warnings": []}
        decision = SafetyPolicy.extract_safety_decision(feasibility)
        assert decision.risk_level == RiskLevel.UNKNOWN
        assert "Missing risk_level" in decision.warnings[0]

    def test_invalid_risk_level_returns_unknown(self):
        """Invalid risk_level string should normalize to UNKNOWN."""
        feasibility = {"risk_level": "INVALID_LEVEL"}
        decision = SafetyPolicy.extract_safety_decision(feasibility)
        assert decision.risk_level == RiskLevel.UNKNOWN

    def test_none_feasibility_returns_unknown(self):
        """None feasibility should return UNKNOWN."""
        decision = SafetyPolicy.extract_safety_decision(None)
        assert decision.risk_level == RiskLevel.UNKNOWN
        assert "missing or not a dict" in decision.block_reason.lower()

    def test_non_dict_feasibility_returns_unknown(self):
        """Non-dict feasibility should return UNKNOWN."""
        decision = SafetyPolicy.extract_safety_decision("not a dict")
        assert decision.risk_level == RiskLevel.UNKNOWN

    def test_empty_dict_returns_unknown(self):
        """Empty dict should return UNKNOWN."""
        decision = SafetyPolicy.extract_safety_decision({})
        assert decision.risk_level == RiskLevel.UNKNOWN

    def test_case_insensitive_risk_level(self):
        """Risk level should be case-insensitive."""
        for variant in ["green", "Green", "GREEN", "gReEn"]:
            decision = SafetyPolicy.extract_safety_decision({"risk_level": variant})
            assert decision.risk_level == RiskLevel.GREEN

    def test_whitespace_in_risk_level(self):
        """Whitespace in risk_level should be stripped."""
        decision = SafetyPolicy.extract_safety_decision({"risk_level": "  RED  "})
        assert decision.risk_level == RiskLevel.RED

    def test_warnings_normalized_to_list(self):
        """Single warning string should be converted to list."""
        feasibility = {"risk_level": "GREEN", "warnings": "Single warning"}
        decision = SafetyPolicy.extract_safety_decision(feasibility)
        assert decision.warnings == ["Single warning"]

    def test_none_warnings_returns_empty_list(self):
        """None warnings should return empty list."""
        feasibility = {"risk_level": "GREEN", "warnings": None}
        decision = SafetyPolicy.extract_safety_decision(feasibility)
        assert decision.warnings == []

    def test_score_conversion(self):
        """Score should be safely converted to float."""
        feasibility = {"risk_level": "GREEN", "score": "85.5"}
        decision = SafetyPolicy.extract_safety_decision(feasibility)
        assert decision.score == 85.5

    def test_invalid_score_returns_none(self):
        """Invalid score should return None, not raise."""
        feasibility = {"risk_level": "GREEN", "score": "not_a_number"}
        decision = SafetyPolicy.extract_safety_decision(feasibility)
        assert decision.score is None


class TestShouldBlock:
    """Tests for SafetyPolicy.should_block."""

    def test_red_blocks(self):
        """RED should block when BLOCK_ON_RED is True."""
        assert SafetyPolicy.should_block(RiskLevel.RED) is True
        assert SafetyPolicy.should_block("RED") is True

    def test_unknown_blocks(self):
        """UNKNOWN should block when TREAT_UNKNOWN_AS_RED is True."""
        assert SafetyPolicy.should_block(RiskLevel.UNKNOWN) is True
        assert SafetyPolicy.should_block("UNKNOWN") is True

    def test_error_blocks(self):
        """ERROR should block when TREAT_UNKNOWN_AS_RED is True."""
        assert SafetyPolicy.should_block(RiskLevel.ERROR) is True
        assert SafetyPolicy.should_block("ERROR") is True

    def test_green_does_not_block(self):
        """GREEN should never block."""
        assert SafetyPolicy.should_block(RiskLevel.GREEN) is False
        assert SafetyPolicy.should_block("GREEN") is False

    def test_yellow_does_not_block(self):
        """YELLOW should not block (proceed with warning)."""
        assert SafetyPolicy.should_block(RiskLevel.YELLOW) is False
        assert SafetyPolicy.should_block("YELLOW") is False

    def test_none_blocks(self):
        """None risk level should block (treated as UNKNOWN)."""
        assert SafetyPolicy.should_block(None) is True

    def test_invalid_string_blocks(self):
        """Invalid risk level string should block (treated as UNKNOWN)."""
        assert SafetyPolicy.should_block("BOGUS") is True

    def test_case_insensitive(self):
        """Risk level matching should be case-insensitive."""
        assert SafetyPolicy.should_block("red") is True
        assert SafetyPolicy.should_block("green") is False


class TestIntegration:
    """Integration tests combining extract + should_block."""

    def test_green_payload_does_not_block(self):
        """Full flow: GREEN payload should not block."""
        feasibility = {
            "safety": {"risk_level": "GREEN", "score": 90.0}
        }
        decision = SafetyPolicy.extract_safety_decision(feasibility)
        assert SafetyPolicy.should_block(decision.risk_level) is False

    def test_red_payload_blocks(self):
        """Full flow: RED payload should block."""
        feasibility = {
            "safety": {"risk_level": "RED", "score": 10.0, "block_reason": "Danger"}
        }
        decision = SafetyPolicy.extract_safety_decision(feasibility)
        assert SafetyPolicy.should_block(decision.risk_level) is True

    def test_missing_feasibility_blocks(self):
        """Full flow: Missing feasibility should block."""
        decision = SafetyPolicy.extract_safety_decision(None)
        assert SafetyPolicy.should_block(decision.risk_level) is True

    def test_malformed_payload_blocks(self):
        """Full flow: Malformed payload should block (fail-safe)."""
        feasibility = {"some": "random", "data": 123}
        decision = SafetyPolicy.extract_safety_decision(feasibility)
        assert decision.risk_level == RiskLevel.UNKNOWN
        assert SafetyPolicy.should_block(decision.risk_level) is True
