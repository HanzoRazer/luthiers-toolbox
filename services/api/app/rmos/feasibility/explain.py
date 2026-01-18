"""
Phase 3 — Explanation Derivation

Derives human-readable explanations from rule IDs without executing any logic.
All explanations are deterministic, registry-backed, and rule-referenced.

Usage:
    from app.rmos.feasibility.explain import explain_decision
    explanation = explain_decision(run_artifact)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict

from .rule_registry import FEASIBILITY_RULES, RuleMetadata


class TriggeredRuleExplanation(TypedDict):
    """A single rule explanation derived from the registry."""
    rule_id: str
    level: str
    summary: str
    description: str
    operator_hint: str


class DecisionExplanation(TypedDict):
    """
    Complete explanation of a feasibility decision.
    
    This structure is deterministic, registry-backed, and contains
    no AI-generated or interpreted content.
    """
    risk_level: str
    summary: str
    triggered_rules: List[TriggeredRuleExplanation]
    override_reason: Optional[str]


def explain_rules(rule_ids: List[str]) -> List[TriggeredRuleExplanation]:
    """
    Look up rule IDs in the registry and return structured explanations.
    
    Args:
        rule_ids: List of rule IDs (e.g., ["F001", "F011"])
    
    Returns:
        List of TriggeredRuleExplanation with full metadata from registry.
        Unknown rule IDs are included with a fallback message.
    """
    explanations: List[TriggeredRuleExplanation] = []
    
    for rule_id in rule_ids:
        meta = FEASIBILITY_RULES.get(rule_id)
        if meta:
            explanations.append(TriggeredRuleExplanation(
                rule_id=rule_id,
                level=meta["level"],
                summary=meta["summary"],
                description=meta["description"],
                operator_hint=meta["operator_hint"],
            ))
        else:
            # Unknown rule ID — include with fallback
            explanations.append(TriggeredRuleExplanation(
                rule_id=rule_id,
                level="UNKNOWN",
                summary=f"Unknown rule: {rule_id}",
                description="This rule is not in the registry. It may be deprecated or from a newer engine version.",
                operator_hint="Contact support if this rule affects your workflow.",
            ))
    
    return explanations


def derive_summary(risk_level: str, triggered_count: int) -> str:
    """
    Generate a deterministic summary based on risk level and rule count.
    No AI. No interpretation. Just a template.
    """
    if risk_level == "GREEN":
        return "All checks passed"
    elif risk_level == "YELLOW":
        return f"Manual review required ({triggered_count} warning{'s' if triggered_count != 1 else ''})"
    elif risk_level == "RED":
        return f"Blocked ({triggered_count} critical issue{'s' if triggered_count != 1 else ''})"
    else:
        return "Status unknown"


def explain_decision(
    run_artifact: Optional[Dict[str, Any]] = None,
    *,
    feasibility: Optional[Dict[str, Any]] = None,
    decision: Optional[Dict[str, Any]] = None,
    override_reason: Optional[str] = None,
) -> DecisionExplanation:
    """
    Derive a complete explanation from a RunArtifact or its components.
    
    This function:
    - Extracts rule IDs from feasibility.rules_triggered
    - Looks up each rule in the authoritative registry
    - Returns a deterministic, human-readable explanation
    
    Args:
        run_artifact: Full RunArtifact dict (optional)
        feasibility: Feasibility dict (if run_artifact not provided)
        decision: Decision dict (if run_artifact not provided)
        override_reason: Override reason if present
    
    Returns:
        DecisionExplanation with all information needed for UI display.
    """
    # Extract components from run_artifact if provided
    if run_artifact:
        feasibility = feasibility or run_artifact.get("feasibility") or {}
        decision = decision or run_artifact.get("decision") or {}
        if not override_reason:
            details = decision.get("details") or {}
            override_reason = details.get("override_reason")
    
    feasibility = feasibility or {}
    decision = decision or {}
    
    # Get risk level (decision is authoritative, fallback to feasibility)
    risk_level = (
        decision.get("risk_level")
        or feasibility.get("risk_level")
        or "UNKNOWN"
    )
    if hasattr(risk_level, "value"):
        risk_level = risk_level.value
    
    # Get triggered rules
    rules_triggered: List[str] = feasibility.get("rules_triggered") or []
    
    # Derive explanations from registry
    triggered_explanations = explain_rules(rules_triggered)
    
    # Generate summary
    summary = derive_summary(risk_level, len(rules_triggered))
    
    return DecisionExplanation(
        risk_level=risk_level,
        summary=summary,
        triggered_rules=triggered_explanations,
        override_reason=override_reason,
    )


def explain_to_dict(explanation: DecisionExplanation) -> Dict[str, Any]:
    """Convert DecisionExplanation to a plain dict for JSON serialization."""
    return {
        "risk_level": explanation["risk_level"],
        "summary": explanation["summary"],
        "triggered_rules": [dict(r) for r in explanation["triggered_rules"]],
        "override_reason": explanation["override_reason"],
    }
