"""
Saw Safety Gate Unit Tests

Tests saw-specific field normalization (risk_bucket -> risk_level).
"""
import pytest
from app.rmos.policies import compute_saw_safety_decision, SafetyPolicy, RiskLevel


class TestSawSafetyGate:
    """Test compute_saw_safety_decision() saw-specific handling."""

    def test_saw_gate_normalizes_risk_bucket_flat(self):
        """Saw gate normalizes top-level risk_bucket to risk_level."""
        feasibility = {"risk_bucket": "RED", "score": 0.15}
        d = compute_saw_safety_decision(feasibility)
        assert d.risk_level == RiskLevel.RED
        assert SafetyPolicy.should_block(d.risk_level) is True

    def test_saw_gate_normalizes_nested_risk_bucket(self):
        """Saw gate normalizes nested safety.risk_bucket to risk_level."""
        feasibility = {"safety": {"risk_bucket": "RED", "score": 0.2}}
        d = compute_saw_safety_decision(feasibility)
        assert d.risk_level == RiskLevel.RED

    def test_saw_gate_passes_through_standard_risk_level(self):
        """Saw gate passes through standard risk_level unchanged."""
        feasibility = {"safety": {"risk_level": "YELLOW", "score": 0.6}}
        d = compute_saw_safety_decision(feasibility)
        assert d.risk_level == RiskLevel.YELLOW
        assert SafetyPolicy.should_block(d.risk_level) is False

    def test_saw_gate_missing_payload_returns_unknown(self):
        """Missing payload returns UNKNOWN."""
        d = compute_saw_safety_decision(None)
        assert d.risk_level == RiskLevel.UNKNOWN
        assert SafetyPolicy.should_block(d.risk_level) is True

    def test_saw_gate_empty_dict_returns_unknown(self):
        """Empty dict returns UNKNOWN."""
        d = compute_saw_safety_decision({})
        assert d.risk_level == RiskLevel.UNKNOWN

    def test_saw_gate_returns_safety_decision(self):
        """Saw gate returns SafetyDecision dataclass."""
        feasibility = {"risk_level": "GREEN"}
        d = compute_saw_safety_decision(feasibility)
        # Should have to_dict method
        assert hasattr(d, "to_dict")
        assert hasattr(d, "risk_level")
        assert d.to_dict()["risk_level"] == "GREEN"
