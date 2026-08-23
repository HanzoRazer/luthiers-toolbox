"""
RMOS Feasibility Router - Canonical Feasibility Endpoint

Implements the SERVER_SIDE_FEASIBILITY_ENFORCEMENT_CONTRACT_v1.md governance contract.

This is the SINGLE SOURCE OF TRUTH for feasibility computation.
Both /api/rmos/feasibility (public API) and /api/rmos/toolpaths (internal)
MUST use this same engine.

RMOS-CONVERGE-001A - canonical feasibility authority cutover
------------------------------------------------------------
There is exactly one authority boundary, at ``compute_feasibility_internal``:

* every request is passed through ``sanitize_feasibility_input`` before an
  engine sees it, so a client cannot assert ``feasibility`` / ``safety`` /
  ``decision`` / ``risk_level`` / ``export_allowed`` (D1);
* no engine echoes a caller-supplied safety block - every result is
  constructed by the server (D2);
* engines are resolved from an explicit table with **no default**. A mode
  with no substantive evaluator returns ``FEASIBILITY_ENGINE_UNAVAILABLE`` /
  ``UNKNOWN``, never GREEN (D3/D4);
* an evaluator that raises returns ``FEASIBILITY_ENGINE_ERROR`` / ``ERROR``,
  not a manufacturing-preserving YELLOW.

``UNKNOWN`` and ``ERROR`` are blocking under ``SafetyPolicy``'s default
posture.

**A lane with no substantive evaluator is blocked by design.** Owner ruling,
2026-08-23 (RMOS-CONVERGE-001A): a manufacturing lane is not production-ready
merely because it previously returned GREEN, and availability does not
outrank manufacturing authority. ``RMOS_TREAT_UNKNOWN_AS_RED=false`` is
**not** the sanctioned operational workaround for these lanes - using it that
way reintroduces exactly the authority defect this boundary exists to remove.
The way to reopen a blocked lane is to give it a real evaluator and register
it in ``_PRODUCTION_FEASIBILITY_ENGINES``.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Callable, Dict, Optional

from app.safety import safety_critical

from ..feasibility_authority import (
    error_feasibility,
    sanitize_feasibility_input,
    unavailable_feasibility,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Exceptions an adapter/engine may raise that mean "could not evaluate".
# They are reported as ERROR (blocking), never downgraded to keep
# manufacturing running.
_ENGINE_FAILURES = (
    ImportError,
    ValueError,
    TypeError,
    AttributeError,
    KeyError,
    ZeroDivisionError,
    OSError,
)


@router.post("/feasibility")
def rmos_feasibility(req: Dict[str, Any]) -> Dict[str, Any]:
    """
    POST /api/rmos/feasibility

    Canonical feasibility endpoint. Computes manufacturability assessment
    for the given tool/material/machine context.

    Returns safety decision with risk_level (GREEN/YELLOW/RED/UNKNOWN/ERROR).
    """
    tool_id = str(req.get("tool_id") or "")
    if not tool_id:
        raise HTTPException(status_code=400, detail={"error": "MISSING_TOOL_ID"})

    return compute_feasibility_internal(tool_id=tool_id, req=req, context="api")


@safety_critical
def compute_feasibility_internal(
    *,
    tool_id: str,
    req: Dict[str, Any],
    context: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Canonical feasibility entrypoint - the single server-authority boundary.

    - Used by /api/rmos/feasibility (API)
    - Used internally by the canonical CAM/toolpath routers (server-side recompute)

    GOVERNANCE INVARIANT: this function never trusts client-provided
    feasibility. Authority-shaped client keys are stripped here, and the
    result is always constructed server-side from an authoritative engine.
    """
    mode = resolve_mode(tool_id)

    clean_req, rejected = sanitize_feasibility_input(req)
    if rejected:
        logger.warning(
            "Rejected client-supplied authority keys %s on feasibility request "
            "(tool_id=%s mode=%s context=%s)",
            rejected, tool_id, mode, context,
        )

    engine = resolve_feasibility_engine(mode)
    if engine is None:
        # No substantive evaluator. Inability to evaluate is not permission
        # to manufacture - fail closed with a machine-readable reason.
        return unavailable_feasibility(mode=mode, tool_id=tool_id, context=context)

    return engine(mode=mode, tool_id=tool_id, req=clean_req, context=context)


# -----------------------------
# Mode resolution
# -----------------------------

def resolve_mode(tool_id: str) -> str:
    """Resolve tool_id to processing mode."""
    if tool_id.startswith("saw:"):
        return "saw"
    if tool_id.startswith("rosette:"):
        return "rosette"
    if tool_id.startswith("vcarve:"):
        return "vcarve"
    if tool_id.startswith("roughing:"):
        return "roughing"
    if tool_id.startswith("drilling:"):
        return "drilling"
    if tool_id.startswith("drill_pattern:"):
        return "drill_pattern"
    if tool_id.startswith("biarc:"):
        return "biarc"
    if tool_id.startswith("relief:"):
        return "relief"
    if tool_id.startswith("adaptive:"):
        return "adaptive"
    if tool_id.startswith("helical:"):
        return "helical"
    return "unknown"


def resolve_feasibility_engine(mode: str) -> Optional[Callable[..., Dict[str, Any]]]:
    """
    Resolve the substantive feasibility engine for a mode, or ``None``.

    Engine absence is explicit and is the caller's problem to handle. There
    is deliberately no default engine: a ``dict.get(mode, some_stub)`` here
    is what allowed unevaluated CAM modes to be authorized GREEN.
    """
    return _PRODUCTION_FEASIBILITY_ENGINES.get(mode)


# -----------------------------
# Design spec consumed by feasibility_scorer
# -----------------------------

class ScorerDesignSpec(BaseModel):
    """
    The design contract ``feasibility_scorer.score_design_feasibility``
    actually consumes.

    This is not a new design schema: it names the attributes the scorer and
    its calculators read - ``outer_diameter_mm``, ``inner_diameter_mm``,
    ``ring_count``, ``pattern_type``, and the ``hasattr``-guarded
    ``depth_mm``.

    ``art_studio.schemas.RosetteParamSpec`` is a different, ``extra="forbid"``
    contract built around ``ring_params``; it rejects these fields and
    carries no ``ring_count``, so binding the scorer to it made every
    saw/rosette evaluation raise and fail open to YELLOW.
    """

    outer_diameter_mm: float = 100.0
    inner_diameter_mm: float = 20.0
    ring_count: int = 3
    pattern_type: str = "radial"
    depth_mm: Optional[float] = None
    stock_thickness_mm: Optional[float] = None
    petal_count: Optional[int] = None


def _score_via_scorer(
    *,
    mode: str,
    tool_id: str,
    context: Optional[str],
    design: ScorerDesignSpec,
    req: Dict[str, Any],
    default_material: str,
) -> Dict[str, Any]:
    """
    Shared adapter onto ``feasibility_scorer.score_design_feasibility``.

    Raises on evaluation failure; the caller converts that into an explicit
    blocking ERROR result.
    """
    from ..feasibility_scorer import score_design_feasibility
    from ..api_contracts import RmosContext

    rmos_ctx = RmosContext(
        tool_id=tool_id,
        material_id=req.get("material_id", default_material),
        machine_id=req.get("machine_id"),
        rpm=req.get("rpm"),
        feed_rate_mm_min=req.get("feed_rate_mm_min"),
        spindle_power_watts=req.get("spindle_power_watts"),
        tool_diameter_mm=req.get("tool_diameter_mm"),
    )

    result = score_design_feasibility(design, rmos_ctx)

    risk_level = (
        result.risk_bucket.value
        if hasattr(result.risk_bucket, "value")
        else str(result.risk_bucket)
    )

    block_reason = None
    if risk_level == "RED":
        block_reason = "Safety risk too high for automatic execution"
    elif risk_level in ("UNKNOWN", "ERROR"):
        block_reason = "Could not determine safety level"

    return {
        "mode": mode,
        "tool_id": tool_id,
        "safety": {
            "risk_level": risk_level,
            "score": result.score,
            "block_reason": block_reason,
            "warnings": result.warnings,
            "details": {
                "context": context,
                "engine": "feasibility_scorer",
                "efficiency": result.efficiency,
                "estimated_cut_time_seconds": result.estimated_cut_time_seconds,
                "calculator_results": result.calculator_results,
            },
        },
    }


# -----------------------------
# Saw feasibility
# -----------------------------

def compute_saw_feasibility(
    *,
    mode: str = "saw",
    tool_id: Optional[str] = None,
    req: Dict[str, Any],
    context: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Saw feasibility engine using CNC Saw Labs calculators via SawEngine.

    Output shape:
      {
        "mode": "saw",
        "tool_id": "...",
        "safety": { "risk_level": ..., "score": ..., "block_reason": ..., "warnings": [...], "details": {...} },
      }

    An evaluation failure is reported as blocking ERROR. It is not
    downgraded to YELLOW: an engine that could not run has not established
    that the cut is survivable.
    """
    tool_id = str(tool_id or req.get("tool_id") or "saw:unknown")

    try:
        design = ScorerDesignSpec(
            outer_diameter_mm=req.get("outer_diameter_mm", 100.0),
            inner_diameter_mm=req.get("inner_diameter_mm", 20.0),
            ring_count=req.get("ring_count", 1),
            pattern_type=req.get("pattern_type", "crosscut"),
            depth_mm=req.get("depth_mm"),
            stock_thickness_mm=req.get("stock_thickness_mm", 25.0),
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


# -----------------------------
# Rosette feasibility
# -----------------------------

def compute_rosette_feasibility(
    *,
    mode: str = "rosette",
    tool_id: Optional[str] = None,
    req: Dict[str, Any],
    context: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Rosette feasibility engine using the RMOS manufacturability scorer.

    An evaluation failure is reported as blocking ERROR (see
    ``compute_saw_feasibility``).
    """
    tool_id = str(tool_id or req.get("tool_id") or "rosette:unknown")

    try:
        design = ScorerDesignSpec(
            outer_diameter_mm=req.get("outer_diameter_mm", 100.0),
            inner_diameter_mm=req.get("inner_diameter_mm", 20.0),
            ring_count=req.get("ring_count", 3),
            pattern_type=req.get("pattern_type", "radial"),
            depth_mm=req.get("depth_mm"),
            petal_count=req.get("petal_count"),
        )
        return _score_via_scorer(
            mode=mode,
            tool_id=tool_id,
            context=context,
            design=design,
            req=req,
            default_material="spruce",
        )
    except _ENGINE_FAILURES as e:
        logger.error("Rosette feasibility engine error for tool %s: %s", tool_id, e, exc_info=True)
        return error_feasibility(mode=mode, tool_id=tool_id, context=context, error=e)


# -----------------------------
# Adaptive pocketing feasibility
# -----------------------------

# Every field the rule engine needs that the adaptive plan request carries
# directly. If any is absent the input contract does not match and we say so
# rather than substituting a value.
_ADAPTIVE_REQUIRED_KEYS = (
    "tool_d",
    "stepover",
    "stepdown",
    "z_rough",
    "feed_xy",
    "safe_z",
    "strategy",
    "climb",
    "smoothing",
    "margin",
)


def compute_adaptive_feasibility(
    *,
    mode: str = "adaptive",
    tool_id: Optional[str] = None,
    req: Dict[str, Any],
    context: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Adaptive pocketing feasibility via the RMOS rule engine
    (``app.rmos.feasibility.engine.compute_feasibility``).

    The adaptive plan request (``PlanIn``) carries the rule engine's CAM
    parameters field-for-field, so this is a dispatch to an existing
    evaluator, not a new one. Two ``FeasibilityInput`` fields have no source
    in the plan request and are recorded as derived in the result details:

    * ``layer_name`` - descriptive only; no rule reads it.
    * ``feed_z`` - the plan request carries no plunge feed, so rule F011
      (feed_z > feed_xy) has no data and is inert. It is set equal to
      ``feed_xy`` so the rule neither fires on nor is suppressed by an
      invented value.
    """
    tool_id = str(tool_id or req.get("tool_id") or "adaptive:unknown")

    missing = [k for k in _ADAPTIVE_REQUIRED_KEYS if req.get(k) is None]
    if missing:
        return unavailable_feasibility(
            mode=mode,
            tool_id=tool_id,
            context=context,
            detail=f"adaptive plan parameters absent: {', '.join(missing)}",
        )

    try:
        from ..feasibility.engine import compute_feasibility
        from ..feasibility.schemas import FeasibilityInput

        loops = req.get("loops") or []
        feed_xy = float(req["feed_xy"])

        fi = FeasibilityInput(
            pipeline_id="adaptive_pocket_v1",
            post_id="GRBL",
            units=str(req.get("units") or "mm"),
            tool_d=float(req["tool_d"]),
            stepover=float(req["stepover"]),
            stepdown=float(req["stepdown"]),
            z_rough=float(req["z_rough"]),
            feed_xy=feed_xy,
            feed_z=feed_xy,
            rapid=float(req.get("machine_rapid") or 0.0),
            safe_z=float(req["safe_z"]),
            strategy=str(req["strategy"]),
            layer_name="adaptive_pocket",
            climb=bool(req["climb"]),
            smoothing=float(req["smoothing"]),
            margin=float(req["margin"]),
            # Genuine derivations: the plan request's loops are closed
            # polygons by contract, so their count is the loop hint.
            has_closed_paths=bool(loops),
            loop_count_hint=len(loops),
        )

        result = compute_feasibility(fi)
        risk_level = result.risk_level.value

        block_reason = None
        if result.blocking:
            block_reason = "; ".join(result.blocking_reasons) or "Blocked by feasibility rules"

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
                    "engine": result.engine_version,
                    "rules_triggered": list(result.rules_triggered),
                    "constraints": list(result.constraints),
                    "blocking_reasons": list(result.blocking_reasons),
                    "derived_inputs": {
                        "layer_name": "descriptive only; no rule reads it",
                        "feed_z": "absent from plan request; set to feed_xy so rule F011 is inert",
                        "loop_count_hint": "len(loops) from the plan request",
                    },
                },
            },
        }
    except _ENGINE_FAILURES as e:
        logger.error("Adaptive feasibility engine error for tool %s: %s", tool_id, e, exc_info=True)
        return error_feasibility(mode=mode, tool_id=tool_id, context=context, error=e)


# -----------------------------
# Production engine table
# -----------------------------
#
# Explicit and total: a mode absent from this table has no substantive
# evaluator and is failed closed by compute_feasibility_internal. Adding a
# mode here is a claim that a real engine evaluates it - do not add a mode to
# make a test or a lane green.
_PRODUCTION_FEASIBILITY_ENGINES: Dict[str, Callable[..., Dict[str, Any]]] = {
    "saw": compute_saw_feasibility,
    "rosette": compute_rosette_feasibility,
    "adaptive": compute_adaptive_feasibility,
}
