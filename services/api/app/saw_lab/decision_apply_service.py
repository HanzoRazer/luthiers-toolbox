"""
Decision Apply Service

Applies approved tuning decisions to machining contexts.
Used by /api/saw/batch/plan/choose when operator opts in to apply_recommended_patch.
"""
from __future__ import annotations

from typing import Any, Dict, Optional


def apply_decision_to_context(
    base_context: Dict[str, Any],
    decision_payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Apply a tuning decision's multipliers to a base context.
    
    Returns a new context dict with modified feed_rate_mmpm, spindle_rpm, doc_mm.
    Never mutates the input. Returns a shallow copy with updated values.
    
    Args:
        base_context: The machining context (feed_rate_mmpm, spindle_rpm, doc_mm, etc.)
        decision_payload: The tuning decision payload with delta.rpm_mul, delta.feed_mul, delta.doc_mul
    
    Returns:
        New context dict with adjusted parameters.
    """
    delta = decision_payload.get("delta", {})
    rpm_mul = delta.get("rpm_mul", 1.0)
    feed_mul = delta.get("feed_mul", 1.0)
    doc_mul = delta.get("doc_mul", 1.0)
    
    result = dict(base_context)
    
    if "spindle_rpm" in result and rpm_mul != 1.0:
        result["spindle_rpm"] = result["spindle_rpm"] * rpm_mul
    
    if "feed_rate_mmpm" in result and feed_mul != 1.0:
        result["feed_rate_mmpm"] = result["feed_rate_mmpm"] * feed_mul
    
    if "doc_mm" in result and doc_mul != 1.0:
        result["doc_mm"] = result["doc_mm"] * doc_mul
    
    return result


def get_multipliers_from_decision(decision_payload: Dict[str, Any]) -> Dict[str, float]:
    """
    Extract multipliers from a tuning decision payload.
    
    Returns:
        Dict with rpm_mul, feed_mul, doc_mul (defaults to 1.0 if missing)
    """
    delta = decision_payload.get("delta", {})
    return {
        "rpm_mul": delta.get("rpm_mul", 1.0),
        "feed_mul": delta.get("feed_mul", 1.0),
        "doc_mul": delta.get("doc_mul", 1.0),
    }
