"""
RMOS Feasibility Engine — Phase 3 Explainability

This module provides:
- compute_feasibility(): Evaluate feasibility with rule-referenced output
- explain_decision(): Derive human-readable explanations from registry
- FEASIBILITY_RULES: Authoritative rule registry (no logic, just metadata)
"""

from .engine import compute_feasibility
from .schemas import FeasibilityInput, FeasibilityResult, RiskLevel
from .explain import explain_decision, explain_rules, DecisionExplanation
from .rule_registry import FEASIBILITY_RULES, get_rule, get_all_rule_ids

__all__ = [
    # Engine
    "compute_feasibility",
    # Schemas
    "FeasibilityInput",
    "FeasibilityResult",
    "RiskLevel",
    # Phase 3: Explainability
    "explain_decision",
    "explain_rules",
    "DecisionExplanation",
    "FEASIBILITY_RULES",
    "get_rule",
    "get_all_rule_ids",
]
