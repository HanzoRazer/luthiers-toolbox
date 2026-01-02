# RMOS Safety Policies
from .safety_policy import RiskLevel, SafetyDecision, SafetyPolicy
from .saw_safety_gate import compute_saw_safety_decision


def extract_safety_decision(feasibility):
    """Compat wrapper: returns dict shape expected by legacy routers."""
    d = SafetyPolicy.extract_safety_decision(feasibility)
    return d.to_dict() if hasattr(d, "to_dict") else {
        "risk_level": getattr(d.risk_level, "value", str(d.risk_level)),
        "score": getattr(d, "score", None),
        "block_reason": getattr(d, "block_reason", None),
        "warnings": getattr(d, "warnings", []) or [],
    }


def should_block(*, mode: str, risk_level: str) -> bool:
    """Compat wrapper: mode kept for signature compatibility."""
    return SafetyPolicy.should_block(risk_level)


__all__ = [
    "RiskLevel",
    "SafetyDecision",
    "SafetyPolicy",
    "compute_saw_safety_decision",
    "extract_safety_decision",
    "should_block",
]
