"""Profiling production-engine adapter.

Not a second evaluator. Dispatches to
``app.cam.profiling.feasibility.compute_profile_feasibility`` and maps
that scorer's low/medium/high/blocked vocabulary onto GREEN/YELLOW/RED
so ``SafetyPolicy`` can consume it.

Extracted from ``rmos_feasibility_router`` so registering the existing
evaluator does not push that module over the 500-line file-size gate.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from ..feasibility_authority import error_feasibility, unavailable_feasibility

logger = logging.getLogger(__name__)

# Same fail-closed set as rmos_feasibility_router._ENGINE_FAILURES.
_ENGINE_FAILURES = (
    ImportError,
    ValueError,
    TypeError,
    AttributeError,
    KeyError,
    ZeroDivisionError,
    OSError,
)

_PROFILE_REQUIRED_KEYS = (
    "tool_diameter_mm",
    "cut_depth_mm",
    "stepdown_mm",
    "feed_rate_mm_min",
    "plunge_rate_mm_min",
    "safe_z_mm",
    "retract_z_mm",
    "contour_point_count",
    "tab_count",
    "tab_height_mm",
    "use_tabs",
    "finishing_pass",
    "finishing_allowance_mm",
)


def compute_profiling_feasibility(
    *,
    mode: str = "profiling",
    tool_id: Optional[str] = None,
    req: Dict[str, Any],
    context: Optional[str] = None,
) -> Dict[str, Any]:
    """Dispatch to ``compute_profile_feasibility`` — not a second evaluator.

    RMOS-PROFILING-CONVERGE-001. Feasible-with-warnings stays YELLOW
    (allowed); issues stay RED. No physics change.
    """
    tool_id = str(tool_id or req.get("tool_id") or "profiling:unknown")
    missing = [k for k in _PROFILE_REQUIRED_KEYS if req.get(k) is None]
    if missing:
        return unavailable_feasibility(
            mode=mode,
            tool_id=tool_id,
            context=context,
            detail=f"profiling parameters absent: {', '.join(missing)}",
        )

    try:
        from app.cam.profiling.feasibility import compute_profile_feasibility

        result = compute_profile_feasibility(
            tool_diameter_mm=float(req["tool_diameter_mm"]),
            cut_depth_mm=float(req["cut_depth_mm"]),
            stepdown_mm=float(req["stepdown_mm"]),
            feed_rate_mm_min=float(req["feed_rate_mm_min"]),
            plunge_rate_mm_min=float(req["plunge_rate_mm_min"]),
            safe_z_mm=float(req["safe_z_mm"]),
            retract_z_mm=float(req["retract_z_mm"]),
            contour_point_count=int(req["contour_point_count"]),
            tab_count=int(req["tab_count"]),
            tab_height_mm=float(req["tab_height_mm"]),
            use_tabs=bool(req["use_tabs"]),
            finishing_pass=bool(req["finishing_pass"]),
            finishing_allowance_mm=float(req["finishing_allowance_mm"]),
        )
        if not result.feasible:
            risk_level = "RED"
            block_reason = "; ".join(result.issues) or "Blocked by profile feasibility"
        elif result.risk_level == "low":
            risk_level = "GREEN"
            block_reason = None
        else:
            risk_level = "YELLOW"
            block_reason = None
        return {
            "mode": mode,
            "tool_id": tool_id,
            "safety": {
                "risk_level": risk_level,
                "score": None,
                "block_reason": block_reason,
                "warnings": list(result.warnings),
                "details": {
                    "context": context,
                    "engine": "compute_profile_feasibility",
                    "evaluator_risk_level": result.risk_level,
                    "issues": list(result.issues),
                    "summary": result.summary,
                },
            },
        }
    except _ENGINE_FAILURES as e:
        logger.error("Profiling feasibility engine error for tool %s: %s", tool_id, e, exc_info=True)
        return error_feasibility(mode=mode, tool_id=tool_id, context=context, error=e)
