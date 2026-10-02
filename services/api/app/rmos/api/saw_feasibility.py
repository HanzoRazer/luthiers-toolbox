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
# Downstream models store these as ints (SawContext.max_rpm / tooth_count,
# SawDesign.repeat_count). A non-integral float is not that fact; truncating it
# with int() would score a substituted value. Integral floats (3450.0) are the
# same value and stay valid.
_SAW_INTEGRAL = frozenset({"rpm", "tooth_count", "repeat_count"})
_SAW_REQUIRED_STR = ("material_id", "cut_type")
_SAW_REQUIRED_BOOL = ("use_dust_collection",)


def _is_number(v: Any) -> bool:
    """A real numeric fact — not a bool masquerading as a number (SAC-011)."""
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _record(missing: list, invalid: list, key: str, kind: Optional[str]) -> None:
    if kind == "missing":
        missing.append(key)
    elif kind == "invalid":
        invalid.append(key)


def _number_kind(key: str, value: Any) -> Optional[str]:
    """'missing' / 'invalid' / None (acceptable).

    A non-integral float for an integer fact (rpm, tooth_count, repeat_count)
    is invalid: truncating 3450.7 to 3450 would score a substituted value.
    """
    if value is None:
        return "missing"
    if not _is_number(value):
        return "invalid"
    if key in _SAW_INTEGRAL and not float(value).is_integer():
        return "invalid"
    return None


def _text_kind(value: Any) -> Optional[str]:
    if value is None:
        return "missing"
    if not isinstance(value, str) or not value.strip():
        return "invalid"
    return None


def _bool_kind(value: Any) -> Optional[str]:
    if value is None:
        return "missing"
    if not isinstance(value, bool):
        return "invalid"
    return None


def _normalize_machine_power(req: Dict[str, Any], missing: list, invalid: list) -> None:
    """One canonical kW input, or one documented watts->kW conversion (SAC-005)."""
    if req.get("machine_power_kw") is None:
        watts = req.get("spindle_power_watts")
        if watts is None:
            missing.append("machine_power_kw")
        elif not _is_number(watts):
            invalid.append("spindle_power_watts")
        else:
            req["machine_power_kw"] = float(watts) / 1000.0
    elif not _is_number(req["machine_power_kw"]):
        invalid.append("machine_power_kw")


def _validate_and_normalize(req: Dict[str, Any]) -> tuple:
    """Partition the required Saw facts into (normalized_req, missing, invalid).

    Missing = key absent or ``None``. Invalid = present but wrong type
    (non-numeric, boolean-for-number, empty string, or a non-integral value
    for an integer fact). Range violations are left to model validation
    (blocking ERROR), not defaulted.
    """
    r = dict(req)
    missing: list = []
    invalid: list = []
    _normalize_machine_power(r, missing, invalid)
    for key in _SAW_REQUIRED_NUMERIC:
        _record(missing, invalid, key, _number_kind(key, r.get(key)))
    for key in _SAW_REQUIRED_STR:
        _record(missing, invalid, key, _text_kind(r.get(key)))
    for key in _SAW_REQUIRED_BOOL:
        _record(missing, invalid, key, _bool_kind(r.get(key)))
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
            detail=f"saw process facts invalid (non-numeric / boolean / empty / non-integral): {', '.join(sorted(invalid))}",
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
            repeat_count=r["repeat_count"],
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
