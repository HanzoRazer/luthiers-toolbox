from __future__ import annotations

import os
from typing import Any, Dict, Optional, Tuple

from app.services.saw_lab_learned_overrides_resolver import resolve_learned_multipliers


def is_apply_accepted_overrides_enabled() -> bool:
    """
    Second-stage feature flag:
      - when TRUE, callers may choose to apply ACCEPTed learned multipliers to a context
      - default OFF (safe-by-default)

    Env var:
      SAW_LAB_APPLY_ACCEPTED_OVERRIDES=true/false
    """
    v = os.getenv("SAW_LAB_APPLY_ACCEPTED_OVERRIDES", "false").strip().lower()
    return v in ("1", "true", "yes", "y", "on")


def _num(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except (ValueError, TypeError):  # WP-1: narrowed from except Exception
        return None


def apply_multipliers_to_context(
    *,
    context: Dict[str, Any],
    multipliers: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Apply resolved multipliers to a *copy* of the provided context.
    We only touch keys that are present + numeric.

    Context keys supported (kept intentionally minimal):
      - spindle_rpm
      - feed_rate
      - doc_mm
    """
    ctx = dict(context or {})
    res = dict(multipliers or {})

    rpm_mult = _num(res.get("spindle_rpm_mult")) or 1.0
    feed_mult = _num(res.get("feed_rate_mult")) or 1.0
    doc_mult = _num(res.get("doc_mult")) or 1.0

    before = {
        "spindle_rpm": ctx.get("spindle_rpm"),
        "feed_rate": ctx.get("feed_rate"),
        "doc_mm": ctx.get("doc_mm"),
    }

    rpm = _num(ctx.get("spindle_rpm"))
    if rpm is not None:
        ctx["spindle_rpm"] = max(1.0, rpm * rpm_mult)

    feed = _num(ctx.get("feed_rate"))
    if feed is not None:
        ctx["feed_rate"] = max(0.01, feed * feed_mult)

    doc = _num(ctx.get("doc_mm"))
    if doc is not None:
        ctx["doc_mm"] = max(0.001, doc * doc_mult)

    after = {
        "spindle_rpm": ctx.get("spindle_rpm"),
        "feed_rate": ctx.get("feed_rate"),
        "doc_mm": ctx.get("doc_mm"),
    }

    stamp = {
        "applied": True,
        "multipliers": {"spindle_rpm_mult": rpm_mult, "feed_rate_mult": feed_mult, "doc_mult": doc_mult},
        "before": before,
        "after": after,
    }
    return ctx, stamp


def tune_context_from_accepted_learning(
    *,
    context: Dict[str, Any],
    tool_id: Optional[str] = None,
    material_id: Optional[str] = None,
    thickness_mm: Optional[float] = None,
    limit_events: int = 200,
) -> Dict[str, Any]:
    """
    Safe "apply preview":
      - resolves ACCEPTed multipliers (read-path)
      - applies to context (pure function on a copy)

    This does NOT persist anything and does NOT run toolpaths.
    """
    resolved = resolve_learned_multipliers(
        tool_id=tool_id,
        material_id=material_id,
        thickness_mm=thickness_mm,
        limit_events=limit_events,
    )
    tuned, stamp = apply_multipliers_to_context(context=context, multipliers=resolved.get("resolved") or {})
    return {
        "apply_enabled": is_apply_accepted_overrides_enabled(),
        "resolved": resolved,
        "tuning_stamp": stamp,
        "tuned_context": tuned,
    }


def maybe_apply_accepted_learning_to_context(
    *,
    context: Dict[str, Any],
    tool_id: Optional[str] = None,
    material_id: Optional[str] = None,
    thickness_mm: Optional[float] = None,
    limit_events: int = 200,
) -> Dict[str, Any]:
    """
    Helper for execution paths:
      - If apply flag OFF: returns original context and a stamp that says applied=False
      - If apply flag ON: returns tuned context + stamp
    """
    if not is_apply_accepted_overrides_enabled():
        return {
            "apply_enabled": False,
            "resolved": {"source_count": 0, "sources": [], "resolved": {"spindle_rpm_mult": 1.0, "feed_rate_mult": 1.0, "doc_mult": 1.0}},
            "tuning_stamp": {"applied": False, "multipliers": {"spindle_rpm_mult": 1.0, "feed_rate_mult": 1.0, "doc_mult": 1.0}, "before": {}, "after": {}},
            "tuned_context": dict(context or {}),
        }
    return tune_context_from_accepted_learning(
        context=context,
        tool_id=tool_id,
        material_id=material_id,
        thickness_mm=thickness_mm,
        limit_events=limit_events,
    )
