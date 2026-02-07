"""
RMOS Toolpaths Router - Canonical Toolpath Generation Endpoint

LANE: OPERATION
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md
Execution Class: B (Deterministic) for saw/rosette modes

Implements:
- OPERATION_EXECUTION_GOVERNANCE_v1.md (Appendix D: Execution Classes)
- SERVER_SIDE_FEASIBILITY_ENFORCEMENT_CONTRACT_v1.md
- RUN_ARTIFACT_PERSISTENCE_CONTRACT_v1.md

GOVERNANCE INVARIANTS:
1. Client feasibility is ALWAYS ignored and recomputed server-side
2. RED/UNKNOWN risk levels result in HTTP 409 (blocked)
3. EVERY request creates a run artifact (OK, BLOCKED, or ERROR)
4. All outputs are SHA256 hashed for provenance

ARTIFACT KINDS:
- rmos_toolpaths_execution (OK/ERROR)
- rmos_toolpaths_blocked (BLOCKED)
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
            event_type="rmos_toolpaths_blocked",  # OPERATION lane artifact kind
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
            event_type="rmos_toolpaths_execution",  # OPERATION lane artifact kind
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
    except Exception as e:  # WP-1: governance catch-all — creates ERROR RunArtifact for audit trail
        # ERROR artifact
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id=tool_id,
            workflow_mode=mode,
            event_type="rmos_toolpaths_execution",  # OPERATION lane artifact kind
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
# Toolpath dispatchers (wired to real engines)
# -----------------------------

def dispatch_toolpaths(*, mode: str, req: Dict[str, Any], feasibility: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dispatch to appropriate toolpath builder based on mode.

    GOVERNANCE REQUIREMENT: Must accept authoritative feasibility (not client-provided).
    
    Wired to real engines via generate_toolpaths_server_side.
    """
    try:
        from ..toolpaths import generate_toolpaths_server_side
        
        # Extract design and context from request
        design = {
            "outer_diameter_mm": req.get("outer_diameter_mm", 100.0),
            "inner_diameter_mm": req.get("inner_diameter_mm", 20.0),
            "ring_count": req.get("ring_count", 1),
            "pattern_type": req.get("pattern_type", "radial"),
            "depth_mm": req.get("depth_mm", -3.0),
            "stock_thickness_mm": req.get("stock_thickness_mm", 25.0),
            "petal_count": req.get("petal_count"),
            # Saw-specific
            "kerf_width_mm": req.get("kerf_width_mm", 2.0),
            "num_cuts": req.get("num_cuts", 1),
            "spacing_mm": req.get("spacing_mm", 5.0),
            "length_mm": req.get("length_mm", 50.0),
            "cuts": req.get("cuts", []),
        }
        
        context = {
            "tool_id": req.get("tool_id"),
            "material_id": req.get("material_id"),
            "machine_id": req.get("machine_id"),
            "feed_rate": req.get("feed_rate_mm_min", 500.0),
            "spindle_rpm": req.get("rpm", 3000),
        }
        
        # Call canonical toolpath generator
        result = generate_toolpaths_server_side(
            mode=mode,
            design=design,
            context=context,
            feasibility=feasibility,
            post_processor_id=req.get("post_processor_id"),
            options=req.get("options"),
        )
        
        return result
        
    except ImportError as e:
        # Fallback if toolpaths module has issues
        if mode == "saw":
            return build_saw_toolpaths(req=req, feasibility=feasibility)
        elif mode == "rosette":
            return build_rosette_toolpaths(req=req, feasibility=feasibility)
        else:
            raise HTTPException(status_code=400, detail={"error": "UNKNOWN_MODE", "mode": mode})
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": "TOOLPATH_ERROR", "message": str(e)})


def build_saw_toolpaths(*, req: Dict[str, Any], feasibility: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback saw toolpath generator (used if toolpaths module import fails).
    
    Real toolpaths are generated via generate_toolpaths_server_side().
    """
    # Placeholder G-code
    gcode = """G90
G21
; SAW TOOLPATH FALLBACK
; Generated by RMOS Toolpaths Router
; Primary toolpath generator unavailable
M2
"""
    return {
        "mode": "saw",
        "gcode_text": gcode,
        "opplan": {"kind": "saw_opplan", "version": 1, "note": "fallback_mode"},
    }


def build_rosette_toolpaths(*, req: Dict[str, Any], feasibility: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback rosette toolpath generator (used if toolpaths module import fails).
    
    Real toolpaths are generated via generate_toolpaths_server_side().
    """
    gcode = """G90
G21
; ROSETTE TOOLPATH FALLBACK
; Generated by RMOS Toolpaths Router
; Primary toolpath generator unavailable
M2
"""
    return {
        "mode": "rosette",
        "gcode_text": gcode,
        "opplan": {"kind": "rosette_opplan", "version": 1, "note": "fallback_mode"},
    }
