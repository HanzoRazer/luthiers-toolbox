"""
Phase 3 — Feasibility Rule Registry (Authoritative)

This file contains NO LOGIC. It is a static registry of rule metadata.
Each rule ID maps to:
- level: RED or YELLOW
- summary: One-line human-readable explanation
- description: Full explanation of what the rule checks
- operator_hint: Actionable guidance for the operator

The explanation comes from the registry, not from runtime logic.
"""

from __future__ import annotations

from typing import Dict, TypedDict


class RuleMetadata(TypedDict):
    level: str  # "RED" or "YELLOW"
    summary: str
    description: str
    operator_hint: str


# =============================================================================
# RULE REGISTRY — Authoritative source of truth for explainability
# =============================================================================

FEASIBILITY_RULES: Dict[str, RuleMetadata] = {
    # =========================================================================
    # RED rules (blocking)
    # =========================================================================
    "F001": {
        "level": "RED",
        "summary": "Invalid tool diameter",
        "description": "tool_d must be greater than zero for material removal.",
        "operator_hint": "Set tool_d to a positive value matching your endmill diameter.",
    },
    "F002": {
        "level": "RED",
        "summary": "Invalid stepover ratio",
        "description": "stepover must be between 0 (exclusive) and 0.95 (inclusive).",
        "operator_hint": "Set stepover to a value like 0.4 (40% of tool diameter).",
    },
    "F003": {
        "level": "RED",
        "summary": "Invalid stepdown",
        "description": "stepdown must be greater than zero to define depth per pass.",
        "operator_hint": "Set stepdown to a positive value (e.g., 1.0mm per pass).",
    },
    "F004": {
        "level": "RED",
        "summary": "Invalid cutting depth",
        "description": "z_rough must be negative to indicate material removal below surface.",
        "operator_hint": "Set z_rough to a negative value representing total depth (e.g., -3.0).",
    },
    "F005": {
        "level": "RED",
        "summary": "Invalid safe Z height",
        "description": "safe_z must be greater than zero to ensure clearance above workpiece.",
        "operator_hint": "Set safe_z to a positive value (e.g., 5.0mm above stock).",
    },
    "F006": {
        "level": "RED",
        "summary": "No closed geometry",
        "description": "DXF contains no closed paths on the selected layer.",
        "operator_hint": "Ensure your DXF has closed polylines or circles on the target layer.",
    },
    "F007": {
        "level": "RED",
        "summary": "No closed loops detected",
        "description": "Preflight analysis found zero closed loops in the DXF.",
        "operator_hint": "Check that geometry is properly closed and on the correct layer.",
    },
    # =========================================================================
    # YELLOW rules (warnings)
    # =========================================================================
    "F010": {
        "level": "YELLOW",
        "summary": "Tool larger than smallest feature",
        "description": "tool_d exceeds the smallest feature dimension; fine details may be unreachable.",
        "operator_hint": "Use a smaller tool or accept that some features may be skipped.",
    },
    "F011": {
        "level": "YELLOW",
        "summary": "Plunge feed exceeds lateral feed",
        "description": "feed_z is higher than feed_xy, which may stress the tool during plunges.",
        "operator_hint": "Reduce feed_z to be less than or equal to feed_xy.",
    },
    "F012": {
        "level": "YELLOW",
        "summary": "Large stepdown",
        "description": "stepdown exceeds recommended maximum; deeper cuts increase tool stress.",
        "operator_hint": "Reduce stepdown to 3.0mm or less for safer machining.",
    },
    "F013": {
        "level": "YELLOW",
        "summary": "High loop count",
        "description": "The geometry contains many loops, which may result in long machining time.",
        "operator_hint": "Consider simplifying geometry or accepting longer runtime.",
    },
}


def get_rule(rule_id: str) -> RuleMetadata | None:
    """Look up rule metadata by ID. Returns None if unknown."""
    return FEASIBILITY_RULES.get(rule_id)


def get_all_rule_ids() -> list[str]:
    """Return all registered rule IDs."""
    return list(FEASIBILITY_RULES.keys())
