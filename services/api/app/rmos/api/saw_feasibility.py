"""Saw production-engine adapter.

Not a second evaluator. It builds the ``ScorerDesignSpec`` the shared
``feasibility_scorer`` consumes and dispatches through ``_score_via_scorer``,
which routes ``saw:`` tools to ``SawEngine.check_feasibility`` and the CNC Saw
Labs calculators.

Extracted from ``rmos_feasibility_router`` so the saw plumbing repair does not
push that module over the 500-line file-size gate (same reason the profiling
adapter lives beside it). The scorer adapter and ``ScorerDesignSpec`` are still
owned by the router and shared with the rosette lane, so they are imported
lazily at call time to avoid an import cycle with the router that registers
this engine.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from ..feasibility_authority import error_feasibility, unavailable_feasibility

logger = logging.getLogger(__name__)

# The safety-critical process facts every Saw calculator reads: rim speed and
# blade dynamics need diameter and RPM; bite load and heat need feed rate, RPM
# and tooth count; cutting force and deflection need feed rate, diameter, RPM,
# stock thickness and machine power. If any is absent the request does not
# describe a real cut, so the evaluator returns UNKNOWN rather than scoring on a
# hardcoded conversion default. These are request keys (the contract a caller
# supplies), not the SawContext field names.
_SAW_REQUIRED_KEYS = (
    "rpm",
    "feed_rate_mm_min",
    "tool_diameter_mm",
    "tooth_count",
    "stock_thickness_mm",
    "spindle_power_watts",
)


def compute_saw_feasibility(
    *,
    mode: str = "saw",
    tool_id: Optional[str] = None,
    req: Dict[str, Any],
    context: Optional[str] = None,
) -> Dict[str, Any]:
    """Saw feasibility via the CNC Saw Labs calculators (through SawEngine).

    Every fact in ``_SAW_REQUIRED_KEYS`` must be present; if any is absent the
    result is a blocking UNKNOWN. The calculators are not run on substituted
    values, because a default-scored verdict is not a truthful statement about
    the cut that was requested. An evaluation failure - including an
    out-of-range fact the SawContext rejects - is a blocking ERROR, never a
    manufacturing-preserving YELLOW.
    """
    # Owned by the router and shared with the rosette lane; imported here to
    # avoid an import cycle with the module that registers this engine.
    from .rmos_feasibility_router import (
        _ENGINE_FAILURES,
        ScorerDesignSpec,
        _score_via_scorer,
    )

    tool_id = str(tool_id or req.get("tool_id") or "saw:unknown")

    missing = [k for k in _SAW_REQUIRED_KEYS if req.get(k) is None]
    if missing:
        return unavailable_feasibility(
            mode=mode,
            tool_id=tool_id,
            context=context,
            detail=f"saw process facts absent: {', '.join(missing)}",
        )

    try:
        design = ScorerDesignSpec(
            outer_diameter_mm=req.get("outer_diameter_mm", 100.0),
            inner_diameter_mm=req.get("inner_diameter_mm", 20.0),
            ring_count=req.get("ring_count", 1),
            pattern_type=req.get("pattern_type", "crosscut"),
            depth_mm=req.get("depth_mm"),
            # Guarded present above; passed through without a friendly default.
            stock_thickness_mm=req.get("stock_thickness_mm"),
            # Cut length feeds only the time estimate, not any safety score, so
            # it is not gated; plumbed truthfully when the caller supplies it.
            cut_length_mm=req.get("cut_length_mm"),
        )
        return _score_via_scorer(
            mode=mode,
            tool_id=tool_id,
            context=context,
            design=design,
            req=req,
            default_material="hardwood",
        )
    except _ENGINE_FAILURES as e:
        logger.error("Saw feasibility engine error for tool %s: %s", tool_id, e, exc_info=True)
        return error_feasibility(mode=mode, tool_id=tool_id, context=context, error=e)
