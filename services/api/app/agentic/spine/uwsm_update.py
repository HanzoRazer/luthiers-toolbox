"""
UWSM Update Engine — Updates user working style model based on feedback.

The User Working Style Model (UWSM) is a set of dimensions that describe
how the user prefers to interact with the agentic system:

Dimensions:
- guidance_density: How much detail in suggestions (very_low -> very_high)
- initiative_tolerance: Who leads (user_led, shared_control, system_led)
- cognitive_load_sensitivity: How easily overwhelmed (low -> very_high)
- expertise_proxy: Inferred skill level (novice, intermediate, expert)
- comparison_preference: How to show comparisons (side_by_side, overlay, sequential)
- visual_density_tolerance: UI density preference (sparse, moderate, dense)
- exploration_vs_confirmation: Workflow style (exploration, balanced, confirmation)

Updates are triggered by:
- Explicit feedback ("helpful" or "too_much")
- Implicit signals (undo patterns, idle time)
"""

from __future__ import annotations

from typing import Dict, Any
from copy import deepcopy


# Ordered levels for dimensions that have progression
GUIDANCE_LEVELS = ["very_low", "low", "medium", "high", "very_high"]
COGNITIVE_LOAD_LEVELS = ["low", "medium", "high", "very_high"]


def default_uwsm() -> Dict[str, Any]:
    """Return the default UWSM configuration."""
    return {
        "dimensions": {
            "guidance_density": {"value": "medium"},
            "initiative_tolerance": {"value": "shared_control"},
            "cognitive_load_sensitivity": {"value": "medium"},
            "expertise_proxy": {"value": "intermediate"},
            "comparison_preference": {"value": "side_by_side"},
            "visual_density_tolerance": {"value": "moderate"},
            "exploration_vs_confirmation": {"value": "balanced"},
        }
    }


def _nudge_level(current: str, levels: list, direction: int) -> str:
    """Move current value up or down in the level list."""
    if current not in levels:
        return current
    idx = levels.index(current)
    new_idx = max(0, min(len(levels) - 1, idx + direction))
    return levels[new_idx]


def update_uwsm(
    uwsm: Dict[str, Any],
    feedback: str,
    directive_action: str = "",
) -> Dict[str, Any]:
    """
    Update UWSM based on feedback.
    
    Args:
        uwsm: Current UWSM state
        feedback: "helpful" or "too_much"
        directive_action: The action that was shown when feedback was given
    
    Returns:
        Updated UWSM (new copy, not mutated)
    """
    updated = deepcopy(uwsm)
    dims = updated.get("dimensions", {})
    
    if feedback == "too_much":
        # User felt overwhelmed: increase cognitive load sensitivity
        current = dims.get("cognitive_load_sensitivity", {}).get("value", "medium")
        new_value = _nudge_level(current, COGNITIVE_LOAD_LEVELS, +1)
        dims.setdefault("cognitive_load_sensitivity", {})["value"] = new_value
        
        # Also reduce guidance density slightly
        current_guidance = dims.get("guidance_density", {}).get("value", "medium")
        new_guidance = _nudge_level(current_guidance, GUIDANCE_LEVELS, -1)
        dims.setdefault("guidance_density", {})["value"] = new_guidance
    
    elif feedback == "helpful":
        # User found it helpful: slight positive reinforcement
        # (Don't change much - helpful is the expected baseline)
        pass
    
    updated["dimensions"] = dims
    return updated
