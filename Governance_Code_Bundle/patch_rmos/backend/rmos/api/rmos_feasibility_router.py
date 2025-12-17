from __future__ import annotations

from fastapi import APIRouter, HTTPException
from typing import Any, Dict, Optional

router = APIRouter()


@router.post("/api/rmos/feasibility")
def rmos_feasibility(req: Dict[str, Any]) -> Dict[str, Any]:
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

    IMPORTANT: This function should NOT trust client-provided feasibility.
    It should compute feasibility from req + authoritative registry/presets when wired.
    """
    mode = resolve_mode(tool_id)

    # NEVER trust any nested feasibility from client
    clean_req = dict(req)
    clean_req.pop("feasibility", None)

    if mode == "saw":
        return compute_saw_feasibility(req=clean_req, context=context)

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
    if tool_id.startswith("saw:"):
        return "saw"
    return "unknown"


# -----------------------------
# Saw feasibility (stub)
# -----------------------------

def compute_saw_feasibility(*, req: Dict[str, Any], context: Optional[str]) -> Dict[str, Any]:
    """
    STUB feasibility engine for saw.
    Replace this with the real SAW feasibility scorer once available.

    Expected output shape (minimum):
      {
        "mode": "saw",
        "tool_id": "...",
        "safety": { "risk_level": "...", "score": ..., "block_reason": ..., "warnings": [...], "details": {...} },
        "checks": {...},            # optional
        "recommendations": {...},   # optional
      }

    For now:
    - If req includes a "safety" dict (test hook), echo it.
    - Otherwise return UNKNOWN (which toolpaths policy will block).
    """
    tool_id = str(req.get("tool_id") or "saw:unknown")

    safety = req.get("safety")
    if isinstance(safety, dict):
        # minimal normalization
        return {
            "mode": "saw",
            "tool_id": tool_id,
            "safety": safety,
            "meta": {"context": context, "note": "echoed safety from request (test hook)"},
        }

    return {
        "mode": "saw",
        "tool_id": tool_id,
        "safety": {
            "risk_level": "UNKNOWN",
            "score": None,
            "block_reason": "Saw feasibility engine not wired yet",
            "warnings": ["Feasibility stub active — toolpaths should be blocked in production."],
            "details": {"context": context},
        },
    }
