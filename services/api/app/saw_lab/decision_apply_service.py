"""
Decision Apply Service

Applies approved tuning decisions to machining contexts.
Used by /api/saw/batch/plan/choose when operator opts in to apply_recommended_patch.
Used by saw_lab_toolpaths_from_decision_service for toolpath generation.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple


def apply_decision_to_context(
    *,
    base_context: Dict[str, Any],
    applied_context_patch: Optional[Dict[str, Any]] = None,
    applied_multipliers: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Apply a tuning decision's patch and multipliers to a base context.
    
    Returns (tuned_context, apply_stamp) tuple:
      - tuned_context: New context dict with patched values and multipliers applied
      - apply_stamp: Audit record of what was applied (for traceability)
    
    Never mutates the input. Returns a shallow copy with updated values.
    
    Precedence:
      1. Start with base_context
      2. Overlay applied_context_patch (if present)
      3. Apply multipliers to numeric fields (rpm, feed, doc)
    
    Args:
        base_context: The machining context (feed_rate, spindle_rpm, doc_mm, etc.)
        applied_context_patch: Dict of values to overlay (optional)
        applied_multipliers: Dict with rpm, feed, doc multipliers (optional)
    
    Returns:
        Tuple of (tuned_context, apply_stamp)
    """
    result = dict(base_context)
    
    patch_applied = False
    multipliers_applied = False
    applied_keys: list = []
    
    # Step 1: Overlay patch values
    if applied_context_patch:
        for k, v in applied_context_patch.items():
            result[k] = v
            applied_keys.append(k)
        patch_applied = True
    
    # Step 2: Apply multipliers
    if applied_multipliers:
        rpm_mul = float(applied_multipliers.get("rpm", applied_multipliers.get("rpm_mul", 1.0)))
        feed_mul = float(applied_multipliers.get("feed", applied_multipliers.get("feed_mul", 1.0)))
        doc_mul = float(applied_multipliers.get("doc", applied_multipliers.get("doc_mul", 1.0)))
        
        # Apply to common field names
        for rpm_key in ("spindle_rpm", "rpm", "max_rpm"):
            if rpm_key in result and rpm_mul != 1.0:
                result[rpm_key] = float(result[rpm_key]) * rpm_mul
                multipliers_applied = True
        
        for feed_key in ("feed_rate", "feed_rate_mmpm", "feed_rate_mm_per_min"):
            if feed_key in result and feed_mul != 1.0:
                result[feed_key] = float(result[feed_key]) * feed_mul
                multipliers_applied = True
        
        for doc_key in ("doc_mm", "depth_of_cut_mm", "doc"):
            if doc_key in result and doc_mul != 1.0:
                result[doc_key] = float(result[doc_key]) * doc_mul
                multipliers_applied = True
    
    apply_stamp = {
        "patch_applied": patch_applied,
        "multipliers_applied": multipliers_applied,
        "applied_keys": applied_keys,
        "applied_multipliers": applied_multipliers or {},
    }
    
    return result, apply_stamp


def apply_decision_payload_to_context(
    base_context: Dict[str, Any],
    decision_payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Legacy helper: Apply a tuning decision's delta multipliers to a base context.
    
    Returns a new context dict with modified feed_rate_mmpm, spindle_rpm, doc_mm.
    Never mutates the input. Returns a shallow copy with updated values.
    
    Args:
        base_context: The machining context (feed_rate_mmpm, spindle_rpm, doc_mm, etc.)
        decision_payload: The tuning decision payload with delta.rpm_mul, delta.feed_mul, delta.doc_mul
    
    Returns:
        New context dict with adjusted parameters.
    """
    delta = decision_payload.get("delta", {})
    multipliers = {
        "rpm_mul": delta.get("rpm_mul", 1.0),
        "feed_mul": delta.get("feed_mul", 1.0),
        "doc_mul": delta.get("doc_mul", 1.0),
    }
    tuned, _ = apply_decision_to_context(
        base_context=base_context,
        applied_multipliers=multipliers,
    )
    return tuned


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
