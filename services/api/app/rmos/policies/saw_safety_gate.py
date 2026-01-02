"""
Saw Safety Gate - Saw-specific feasibility decision wrapper

This module provides a thin wrapper around SafetyPolicy for saw operations,
handling saw-specific field name variations (e.g., risk_bucket vs risk_level).

Per OPERATION_EXECUTION_GOVERNANCE_v1.md, Saw Lab operations are Class B
(Deterministic) but still require the same safety gate semantics.

Usage:
    from app.rmos.policies import compute_saw_safety_decision, SafetyPolicy

    decision = compute_saw_safety_decision(feasibility)
    if SafetyPolicy.should_block(decision.risk_level):
        # Block with HTTP 409
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from .safety_policy import SafetyDecision, SafetyPolicy, RiskLevel


def compute_saw_safety_decision(feasibility: Optional[Dict[str, Any]]) -> SafetyDecision:
    """
    Extract safety decision from saw feasibility payload.

    Handles saw-specific field name variations:
    - risk_bucket (from FeasibilityResult) -> risk_level
    - Nested in safety.risk_level or safety.risk_bucket

    Falls back to SafetyPolicy.extract_safety_decision for standard handling.

    Args:
        feasibility: Saw feasibility payload from compute_saw_feasibility()

    Returns:
        SafetyDecision with normalized risk_level
    """
    if not isinstance(feasibility, dict):
        return SafetyDecision(
            risk_level=RiskLevel.UNKNOWN,
            block_reason="Saw feasibility payload missing or not a dict",
            warnings=["Missing saw feasibility payload"],
        )

    # Normalize saw-specific field names before delegating
    normalized = _normalize_saw_feasibility(feasibility)
    return SafetyPolicy.extract_safety_decision(normalized)


def _normalize_saw_feasibility(feasibility: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize saw-specific field names to standard policy format.

    Handles:
    - Top-level risk_bucket -> risk_level
    - Nested safety.risk_bucket -> safety.risk_level
    - FeasibilityResult.risk_bucket enum values
    """
    result = dict(feasibility)

    # Handle top-level risk_bucket -> risk_level
    if "risk_bucket" in result and "risk_level" not in result:
        rb = result["risk_bucket"]
        # Handle enum with .value attribute
        if hasattr(rb, "value"):
            result["risk_level"] = rb.value
        else:
            result["risk_level"] = str(rb)

    # Handle nested safety block
    if "safety" in result and isinstance(result["safety"], dict):
        safety = dict(result["safety"])
        if "risk_bucket" in safety and "risk_level" not in safety:
            rb = safety["risk_bucket"]
            if hasattr(rb, "value"):
                safety["risk_level"] = rb.value
            else:
                safety["risk_level"] = str(rb)
        result["safety"] = safety

    return result
