"""
RMOS Toolpaths Router - Canonical Toolpath Generation Endpoint

Implements:
- SERVER_SIDE_FEASIBILITY_ENFORCEMENT_CONTRACT_v1.md
- RUN_ARTIFACT_PERSISTENCE_CONTRACT_v1.md

GOVERNANCE INVARIANTS:
1. Client feasibility is ALWAYS ignored and recomputed server-side
2. RED/UNKNOWN risk levels result in HTTP 409 (blocked)
3. EVERY request creates a run artifact (OK, BLOCKED, or ERROR)
4. All outputs are SHA256 hashed for provenance
"""

from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from typing import Any, Dict, Optional

from app.rmos.runs import (
    RunArtifact,
    persist_run,
    create_run_id,
    sha256_of_obj,
    sha256_of_text,
)
from .rmos_feasibility_router import compute_feasibility_internal, resolve_mode

router = APIRouter()

# Safety policy (hardcoded production invariants per governance contract)
BLOCK_ON_RED = True
TREAT_UNKNOWN_AS_RED = True


@router.post("/toolpaths")
def rmos_toolpaths(req: Dict[str, Any]) -> Dict[str, Any]:
    """
    POST /api/rmos/toolpaths

    Generate toolpaths with mandatory server-side feasibility enforcement.

    Flow:
    1. Recompute feasibility server-side (NEVER trust client)
    2. Evaluate safety decision
    3. Block if RED/UNKNOWN (HTTP 409)
    4. Generate toolpaths if safe
    5. Persist run artifact for audit trail
    """
    tool_id = str(req.get("tool_id") or "")
    if not tool_id:
        raise HTTPException(status_code=400, detail={"error": "MISSING_TOOL_ID"})

    mode = resolve_mode(tool_id)
    now = datetime.now(timezone.utc).isoformat()

    # 1) Recompute feasibility server-side (MANDATORY per governance)
    feasibility = compute_feasibility_internal(tool_id=tool_id, req=req, context="toolpaths")

    # 2) Derive safety decision
    decision = extract_safety_decision(feasibility)
    risk_level = (decision.get("risk_level") or "UNKNOWN").upper()

    # 3) Always compute feasibility hash
    feas_hash = sha256_of_obj(feasibility)

    # 4) Block if policy requires (BLOCKED artifact)
    if should_block(mode=mode, risk_level=risk_level):
        run_id = create_run_id()

        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id=tool_id,
            workflow_mode=mode,
            event_type="toolpaths",
            status="BLOCKED",
            feasibility=feasibility,
            request_hash=feas_hash,
            notes=f"Blocked by safety policy: {risk_level}",
        )
        persist_run(artifact)

        raise HTTPException(
            status_code=409,
            detail={
                "error": "SAFETY_BLOCKED",
                "message": "Toolpath generation blocked by server-side safety policy.",
                "run_id": run_id,
                "decision": decision,
                "authoritative_feasibility": feasibility,
            },
        )

    # 5) Generate toolpaths (OK artifact) or persist ERROR artifact
    try:
        toolpaths_payload = dispatch_toolpaths(mode=mode, req=req, feasibility=feasibility)

        # Hash all outputs
        toolpaths_hash = sha256_of_obj(toolpaths_payload)
        gcode_hash: Optional[str] = None

        gcode = toolpaths_payload.get("gcode_text") or toolpaths_payload.get("gcode")
        if isinstance(gcode, str):
            gcode_hash = sha256_of_text(gcode)

        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id=tool_id,
            workflow_mode=mode,
            event_type="toolpaths",
            status="OK",
            feasibility=feasibility,
            request_hash=feas_hash,
            toolpaths_hash=toolpaths_hash,
            gcode_hash=gcode_hash,
        )
        persist_run(artifact)

        # Return payload + audit linkage
        toolpaths_payload["_run_id"] = run_id
        toolpaths_payload["_hashes"] = {
            "feasibility_sha256": feas_hash,
            "toolpaths_sha256": toolpaths_hash,
            "gcode_sha256": gcode_hash,
        }
        return toolpaths_payload

    except HTTPException:
        raise
    except Exception as e:
        # ERROR artifact
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id=tool_id,
            workflow_mode=mode,
            event_type="toolpaths",
            status="ERROR",
            feasibility=feasibility,
            request_hash=feas_hash,
            errors=[f"{type(e).__name__}: {str(e)}"],
        )
        persist_run(artifact)

        raise HTTPException(
            status_code=500,
            detail={
                "error": "TOOLPATHS_ERROR",
                "run_id": run_id,
                "message": str(e),
            },
        )


# -----------------------------
# Policy helpers
# -----------------------------

def should_block(*, mode: str, risk_level: str) -> bool:
    """
    Determine if toolpath generation should be blocked based on risk level.

    Per governance contract:
    - RED always blocks (if BLOCK_ON_RED)
    - UNKNOWN blocks (if TREAT_UNKNOWN_AS_RED)
    """
    if risk_level == "RED" and BLOCK_ON_RED:
        return True
    if risk_level == "UNKNOWN" and TREAT_UNKNOWN_AS_RED:
        return True
    return False


def extract_safety_decision(feasibility: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract normalized safety decision from feasibility payload.

    Handles various payload shapes:
    - Direct: { "risk_level": "GREEN", ... }
    - Nested: { "safety": { "risk_level": "GREEN", ... } }
    """
    # Direct shape
    if isinstance(feasibility.get("risk_level"), str):
        return {
            "risk_level": feasibility.get("risk_level"),
            "score": feasibility.get("score"),
            "block_reason": feasibility.get("block_reason"),
            "warnings": feasibility.get("warnings", []),
        }

    # Nested shape (preferred)
    safety = feasibility.get("safety")
    if isinstance(safety, dict):
        return {
            "risk_level": safety.get("risk_level", "UNKNOWN"),
            "score": safety.get("score"),
            "block_reason": safety.get("block_reason"),
            "warnings": safety.get("warnings", []),
        }

    # Fallback
    return {
        "risk_level": "UNKNOWN",
        "score": None,
        "block_reason": "Could not extract safety decision from feasibility",
        "warnings": ["Missing safety decision in feasibility payload"],
    }


# -----------------------------
# Toolpath dispatchers (TODO: replace with real engines)
# -----------------------------

def dispatch_toolpaths(*, mode: str, req: Dict[str, Any], feasibility: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dispatch to appropriate toolpath builder based on mode.

    GOVERNANCE REQUIREMENT: Must accept authoritative feasibility (not client-provided).
    """
    if mode == "saw":
        return build_saw_toolpaths(req=req, feasibility=feasibility)

    if mode == "rosette":
        return build_rosette_toolpaths(req=req, feasibility=feasibility)

    raise HTTPException(status_code=400, detail={"error": "UNKNOWN_MODE", "mode": mode})


def build_saw_toolpaths(*, req: Dict[str, Any], feasibility: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build saw toolpaths.

    TODO: Wire to real CNC Saw Labs toolpath generator.
    """
    # Placeholder G-code
    gcode = """G90
G21
; SAW TOOLPATH PLACEHOLDER
; Generated by RMOS Toolpaths Router
; Authoritative feasibility hash embedded in run artifact
M2
"""
    return {
        "mode": "saw",
        "gcode_text": gcode,
        "opplan": {"kind": "saw_opplan", "version": 1, "note": "placeholder"},
    }


def build_rosette_toolpaths(*, req: Dict[str, Any], feasibility: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build rosette toolpaths.

    TODO: Wire to real rosette CAM engine.
    """
    gcode = """G90
G21
; ROSETTE TOOLPATH PLACEHOLDER
; Generated by RMOS Toolpaths Router
M2
"""
    return {
        "mode": "rosette",
        "gcode_text": gcode,
        "opplan": {"kind": "rosette_opplan", "version": 1, "note": "placeholder"},
    }
