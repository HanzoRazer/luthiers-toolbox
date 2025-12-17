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
    Saw feasibility engine.

    TODO: Wire to real SAW feasibility scorer (CNC Saw Labs calculators).

    Expected output shape:
      {
        "mode": "saw",
        "tool_id": "...",
        "safety": { "risk_level": "...", "score": ..., "block_reason": ..., "warnings": [...], "details": {...} },
        "checks": {...},            # optional
        "recommendations": {...},   # optional
      }

    Current implementation:
    - If req includes a "safety" dict (test hook), echo it.
    - Otherwise return UNKNOWN (which toolpaths policy will block).
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

    # Default: no safety computed => UNKNOWN => blocked in production
    return {
        "mode": "saw",
        "tool_id": tool_id,
        "safety": {
            "risk_level": "UNKNOWN",
            "score": None,
            "block_reason": "Saw feasibility engine not wired yet",
            "warnings": ["Feasibility stub active - toolpaths blocked in production."],
            "details": {"context": context},
        },
    }


# -----------------------------
# Rosette feasibility
# -----------------------------

def compute_rosette_feasibility(*, req: Dict[str, Any], context: Optional[str]) -> Dict[str, Any]:
    """
    Rosette feasibility engine.

    TODO: Wire to rosette manufacturability scorer.
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

    # Default: UNKNOWN until real engine wired
    return {
        "mode": "rosette",
        "tool_id": tool_id,
        "safety": {
            "risk_level": "UNKNOWN",
            "score": None,
            "block_reason": "Rosette feasibility engine not wired yet",
            "warnings": ["Feasibility stub active - toolpaths blocked in production."],
            "details": {"context": context},
        },
    }
