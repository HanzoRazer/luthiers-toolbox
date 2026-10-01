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

from pydantic import ValidationError

from ..feasibility_authority import error_feasibility, unavailable_feasibility

logger = logging.getLogger(__name__)

# Every field the seven Saw calculators read (saw_lab/calculators/*.py), expressed
# as request keys the caller supplies. If any is absent the request does not describe
# a real cut, so the evaluator returns a blocking UNKNOWN rather than scoring on a
# hardcoded conversion default. These are deliberately the full calculator-consumed
# contract, not a subset (see SAC-041). Explicit zero is a value, not "missing"
# (Frozen #7); out-of-range values fail model validation as a blocking ERROR.
_SAW_REQUIRED_NUMERIC = (
    "blade_diameter_mm", "blade_kerf_mm", "blade_thickness_mm", "tooth_count",
    "rpm", "arbor_size_mm", "stock_thickness_mm", "feed_rate_mm_min",
    "blade_youngs_modulus_gpa",
    # explicit Saw design facts the kickback / cutting-force / deflection / heat
    # calculators consume (miter/bevel/cut_type and dado width/depth):
    "cut_length_mm", "miter_angle_deg", "bevel_angle_deg", "dado_width_mm",
    "dado_depth_mm", "repeat_count",
)
_SAW_REQUIRED_STR = ("material_id", "cut_type")
_SAW_REQUIRED_BOOL = ("use_dust_collection",)


def _is_number(v: Any) -> bool:
    """A real numeric fact — not a bool masquerading as a number (SAC-011)."""
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _validate_and_normalize(req: Dict[str, Any]) -> tuple:
    """Partition the required Saw facts into (normalized_req, missing, invalid).

    Machine power may arrive as ``machine_power_kw`` or as ``spindle_power_watts``
    (converted to kW exactly once, SAC-005). Missing = key absent or ``None``;
    invalid = present but wrong type (non-numeric, boolean-for-number, empty string).
    Range violations are left to model validation (blocking ERROR), not defaulted.
    """
    r = dict(req)
    missing: list = []
    invalid: list = []
    # Machine power: one canonical kW input, or one documented watts->kW conversion.
    if r.get("machine_power_kw") is None:
        watts = r.get("spindle_power_watts")
        if watts is None:
            missing.append("machine_power_kw")
        elif not _is_number(watts):
            invalid.append("spindle_power_watts")
        else:
            r["machine_power_kw"] = float(watts) / 1000.0  # single documented conversion
    elif not _is_number(r["machine_power_kw"]):
        invalid.append("machine_power_kw")
    for k in _SAW_REQUIRED_NUMERIC:
        v = r.get(k)
        if v is None:
            missing.append(k)
        elif not _is_number(v):
            invalid.append(k)
    for k in _SAW_REQUIRED_STR:
        v = r.get(k)
        if v is None:
            missing.append(k)
        elif not isinstance(v, str) or not v.strip():
            invalid.append(k)
    for k in _SAW_REQUIRED_BOOL:
        v = r.get(k)
        if v is None:
            missing.append(k)
        elif not isinstance(v, bool):
            invalid.append(k)
    return r, missing, invalid


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
        SawScorerDesignSpec,
        _score_via_scorer,
    )

    tool_id = str(tool_id or req.get("tool_id") or "saw:unknown")

    r, missing, invalid = _validate_and_normalize(req)
    if missing:
        return unavailable_feasibility(
            mode=mode,
            tool_id=tool_id,
            context=context,
            detail=f"saw process facts absent: {', '.join(sorted(missing))}",
        )
    if invalid:
        # Present-but-not-a-truthful-number (non-numeric, boolean-for-number, empty
        # string) is a blocking ERROR, never a default-scored verdict.
        return error_feasibility(
            mode=mode,
            tool_id=tool_id,
            context=context,
            detail=f"saw process facts invalid (non-numeric / boolean / empty): {', '.join(sorted(invalid))}",
        )

    try:
        # Explicit Saw design facts — NO Rosette aliases. Out-of-range values fail
        # here (ValidationError) and become a blocking ERROR below.
        design = SawScorerDesignSpec(
            cut_length_mm=r["cut_length_mm"],
            cut_type=r["cut_type"],
            miter_angle_deg=r["miter_angle_deg"],
            bevel_angle_deg=r["bevel_angle_deg"],
            dado_width_mm=r["dado_width_mm"],
            dado_depth_mm=r["dado_depth_mm"],
            repeat_count=int(r["repeat_count"]),
        )
        return _score_via_scorer(
            mode=mode,
            tool_id=tool_id,
            context=context,
            design=design,
            req=r,
            # material_id is guarded present above; this sentinel is never used but
            # must not be a plausible real material (SAC-013 guards substitution).
            default_material="__require_explicit_material__",
        )
    except (ValidationError,) + tuple(_ENGINE_FAILURES) as e:
        logger.error("Saw feasibility engine error for tool %s: %s", tool_id, e, exc_info=True)
        return error_feasibility(mode=mode, tool_id=tool_id, context=context, error=e)
