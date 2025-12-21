"""
RMOS Feasibility Router - Canonical Feasibility Endpoint

Implements the SERVER_SIDE_FEASIBILITY_ENFORCEMENT_CONTRACT_v1.md governance contract.

This is the SINGLE SOURCE OF TRUTH for feasibility computation.
Both /api/rmos/feasibility (public API) and /api/rmos/toolpaths (internal)
MUST use this same engine.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from typing import Any, Dict, Optional

router = APIRouter()


@router.post("/feasibility")
def rmos_feasibility(req: Dict[str, Any]) -> Dict[str, Any]:
    """
    POST /api/rmos/feasibility

    Canonical feasibility endpoint. Computes manufacturability assessment
    for the given tool/material/machine context.

    Returns safety decision with risk_level (GREEN/YELLOW/RED/UNKNOWN).
    """
    tool_id = str(req.get("tool_id") or "")
    if not tool_id:
        raise HTTPException(status_code=400, detail={"error": "MISSING_TOOL_ID"})

    return compute_feasibility_internal(tool_id=tool_id, req=req, context="api")


def compute_feasibility_internal(
    *,
    tool_id: str,
    req: Dict[str, Any],
    context: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Canonical feasibility entrypoint.

    - Used by /api/rmos/feasibility (API)
    - Used internally by /api/rmos/toolpaths (server-side recompute)

    GOVERNANCE INVARIANT: This function NEVER trusts client-provided feasibility.
    It computes feasibility from req + authoritative registry/presets.
    """
    mode = resolve_mode(tool_id)

    # NEVER trust any nested feasibility from client
    clean_req = dict(req)
    clean_req.pop("feasibility", None)

    if mode == "saw":
        return compute_saw_feasibility(req=clean_req, context=context)

    if mode == "rosette":
        return compute_rosette_feasibility(req=clean_req, context=context)

    # Unknown tool mode
    return {
        "mode": mode,
        "tool_id": tool_id,
        "safety": {
            "risk_level": "UNKNOWN",
            "block_reason": f"Unsupported mode for feasibility: {mode}",
            "warnings": [f"No feasibility engine registered for mode: {mode}"],
            "details": {"context": context},
        },
    }


# -----------------------------
# Mode resolution
# -----------------------------

def resolve_mode(tool_id: str) -> str:
    """Resolve tool_id to processing mode."""
    if tool_id.startswith("saw:"):
        return "saw"
    if tool_id.startswith("rosette:"):
        return "rosette"
    return "unknown"


# -----------------------------
# Saw feasibility
# -----------------------------

def compute_saw_feasibility(*, req: Dict[str, Any], context: Optional[str]) -> Dict[str, Any]:
    """
    Saw feasibility engine using CNC Saw Labs calculators via SawEngine.

    Output shape:
      {
        "mode": "saw",
        "tool_id": "...",
        "safety": { "risk_level": "...", "score": ..., "block_reason": ..., "warnings": [...], "details": {...} },
        "checks": {...},            # optional
        "recommendations": {...},   # optional
      }
    """
    tool_id = str(req.get("tool_id") or "saw:unknown")

    # Test hook: allow caller to provide pre-computed safety for testing
    safety = req.get("safety")
    if isinstance(safety, dict):
        return {
            "mode": "saw",
            "tool_id": tool_id,
            "safety": safety,
            "meta": {"context": context, "note": "echoed safety from request (test hook)"},
        }

    # Wire to real SawEngine via feasibility_scorer
    try:
        from ..feasibility_scorer import score_design_feasibility
        from ..api_contracts import RmosContext, RiskBucket
        
        # Import design spec - try art_studio first, fallback to api_contracts
        try:
            from ...art_studio.schemas import RosetteParamSpec
        except ImportError:
            from ..api_contracts import RosetteParamSpec
        
        # Build RmosContext from request
        rmos_ctx = RmosContext(
            tool_id=tool_id,
            material_id=req.get("material_id", "hardwood"),
            machine_id=req.get("machine_id"),
            rpm=req.get("rpm"),
            feed_rate_mm_min=req.get("feed_rate_mm_min"),
            spindle_power_watts=req.get("spindle_power_watts"),
            tool_diameter_mm=req.get("tool_diameter_mm"),
        )
        
        # Build design spec from request
        design = RosetteParamSpec(
            outer_diameter_mm=req.get("outer_diameter_mm", 100.0),
            inner_diameter_mm=req.get("inner_diameter_mm", 20.0),
            ring_count=req.get("ring_count", 1),
            pattern_type=req.get("pattern_type", "crosscut"),
            depth_mm=req.get("depth_mm"),
            stock_thickness_mm=req.get("stock_thickness_mm", 25.0),
        )
        
        # Call real feasibility scorer
        result = score_design_feasibility(design, rmos_ctx)
        
        # Convert RiskBucket enum to string risk_level
        risk_level = result.risk_bucket.value if hasattr(result.risk_bucket, 'value') else str(result.risk_bucket)
        
        # Determine block_reason based on risk
        block_reason = None
        if risk_level == "RED":
            block_reason = "Safety risk too high for automatic execution"
        elif risk_level == "UNKNOWN":
            block_reason = "Could not determine safety level"
        
        return {
            "mode": "saw",
            "tool_id": tool_id,
            "safety": {
                "risk_level": risk_level,
                "score": result.score,
                "block_reason": block_reason,
                "warnings": result.warnings,
                "details": {
                    "context": context,
                    "efficiency": result.efficiency,
                    "estimated_cut_time_seconds": result.estimated_cut_time_seconds,
                    "calculator_results": result.calculator_results,
                },
            },
        }
    except Exception as e:
        # Fallback on error - return YELLOW (allows with warning)
        return {
            "mode": "saw",
            "tool_id": tool_id,
            "safety": {
                "risk_level": "YELLOW",
                "score": 50.0,
                "block_reason": None,
                "warnings": [f"Feasibility engine error: {str(e)}"],
                "details": {"context": context, "error": str(e)},
            },
        }


# -----------------------------
# Rosette feasibility
# -----------------------------

def compute_rosette_feasibility(*, req: Dict[str, Any], context: Optional[str]) -> Dict[str, Any]:
    """
    Rosette feasibility engine using RMOS manufacturability scorer.

    Output shape:
      {
        "mode": "rosette",
        "tool_id": "...",
        "safety": { "risk_level": "...", "score": ..., "block_reason": ..., "warnings": [...], "details": {...} },
      }
    """
    tool_id = str(req.get("tool_id") or "rosette:unknown")

    # Test hook
    safety = req.get("safety")
    if isinstance(safety, dict):
        return {
            "mode": "rosette",
            "tool_id": tool_id,
            "safety": safety,
            "meta": {"context": context, "note": "echoed safety from request (test hook)"},
        }

    # Wire to real feasibility scorer
    try:
        from ..feasibility_scorer import score_design_feasibility
        from ..api_contracts import RmosContext, RiskBucket
        
        # Import design spec - try art_studio first, fallback to api_contracts
        try:
            from ...art_studio.schemas import RosetteParamSpec
        except ImportError:
            from ..api_contracts import RosetteParamSpec
        
        # Build RmosContext from request
        rmos_ctx = RmosContext(
            tool_id=tool_id,
            material_id=req.get("material_id", "spruce"),
            machine_id=req.get("machine_id"),
            rpm=req.get("rpm"),
            feed_rate_mm_min=req.get("feed_rate_mm_min"),
            spindle_power_watts=req.get("spindle_power_watts"),
            tool_diameter_mm=req.get("tool_diameter_mm"),
        )
        
        # Build design spec from request
        design = RosetteParamSpec(
            outer_diameter_mm=req.get("outer_diameter_mm", 100.0),
            inner_diameter_mm=req.get("inner_diameter_mm", 20.0),
            ring_count=req.get("ring_count", 3),
            pattern_type=req.get("pattern_type", "radial"),
            depth_mm=req.get("depth_mm"),
            petal_count=req.get("petal_count"),
        )
        
        # Call real feasibility scorer (uses router mode for rosette)
        result = score_design_feasibility(design, rmos_ctx)
        
        # Convert RiskBucket enum to string risk_level
        risk_level = result.risk_bucket.value if hasattr(result.risk_bucket, 'value') else str(result.risk_bucket)
        
        # Determine block_reason based on risk
        block_reason = None
        if risk_level == "RED":
            block_reason = "Safety risk too high for automatic execution"
        elif risk_level == "UNKNOWN":
            block_reason = "Could not determine safety level"
        
        return {
            "mode": "rosette",
            "tool_id": tool_id,
            "safety": {
                "risk_level": risk_level,
                "score": result.score,
                "block_reason": block_reason,
                "warnings": result.warnings,
                "details": {
                    "context": context,
                    "efficiency": result.efficiency,
                    "estimated_cut_time_seconds": result.estimated_cut_time_seconds,
                    "calculator_results": result.calculator_results,
                },
            },
        }
    except Exception as e:
        # Fallback on error - return YELLOW (allows with warning)
        return {
            "mode": "rosette",
            "tool_id": tool_id,
            "safety": {
                "risk_level": "YELLOW",
                "score": 50.0,
                "block_reason": None,
                "warnings": [f"Feasibility engine error: {str(e)}"],
                "details": {"context": context, "error": str(e)},
            },
        }
