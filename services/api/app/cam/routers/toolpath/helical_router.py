"""
CAM Helical Router

LANE: OPERATION (for /helical_entry endpoint)
LANE: UTILITY (for /helical_health endpoint)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md
Execution Class: B (Deterministic) - generates G-code from explicit parameters

Helical Z-ramping for plunge entry.

Migrated from: routers/cam_helical_v161_router.py

Architecture Layer: ROUTER (Layer 6)
See: docs/governance/ARCHITECTURE_INVARIANTS.md

GOVERNANCE INVARIANTS:
1. Client feasibility is ALWAYS ignored and recomputed server-side
2. RED/UNKNOWN risk levels result in HTTP 409 (blocked)
3. EVERY request creates a run artifact (OK, BLOCKED, or ERROR)
4. All outputs are SHA256 hashed for provenance

ARTIFACT KINDS:
- helical_gcode_execution (OK/ERROR) - from /helical_entry
- helical_gcode_blocked (BLOCKED) - from /helical_entry when safety policy blocks

Features:
- Helical plunge entry (prevents tool breakage in hardwood)
- G2/G3 arc-based spiral descent
- CW/CCW direction support
- IJ mode (relative center offsets) and R mode (arc radius)
- Post-processor presets (GRBL, Mach3, Haas, Marlin)
- Configurable pitch, feed rates, and arc segmentation
- Safe rapid to clearance plane
- Dwell command support (post-aware G4 P/S)

Endpoints:
    POST /helical_entry    - Generate helical plunge G-code
    GET  /helical_health   - Health check
"""

from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator

from ...helical_core import (
    helical_plunge,
    helical_preview_points,
    helical_stats,
    helical_validate,
)
from ....utils.post_presets import get_dwell_command, get_post_preset

# Import run artifact persistence (OPERATION lane requirement)
from datetime import datetime, timezone
from ....rmos.runs import (
    RunArtifact,
    persist_run,
    create_run_id,
    sha256_of_obj,
    sha256_of_text,
)

# Import feasibility functions (Phase 2: server-side enforcement)
from ....rmos.api.rmos_feasibility_router import compute_feasibility_internal
from ....rmos.policies import SafetyPolicy

router = APIRouter()


class HelicalReq(BaseModel):
    # Geometry
    cx: float = Field(..., description="Arc center X (mm)")
    cy: float = Field(..., description="Arc center Y (mm)")
    radius_mm: float = Field(..., gt=0, description="Helix radius (mm)")
    direction: Literal["CW", "CCW"] = Field("CCW", description="Arc direction")
    # Z & feed
    plane_z_mm: float = Field(5.0, description="Clearance plane Z (mm)")
    start_z_mm: float = Field(0.0, description="Z where helix begins descending (mm)")
    z_target_mm: float = Field(..., description="Target Z (mm, negative for plunge)")
    pitch_mm_per_rev: float = Field(1.5, gt=0, description="Z change per full 360° (absolute magnitude)")
    feed_xy_mm_min: float = Field(600.0, gt=0, description="XY feed (mm/min) during arc")
    feed_z_mm_min: Optional[float] = Field(None, description="Optional Z feed limit (mm/min). If set, we will cap effective helix speed.")
    # Output style
    ij_mode: bool = Field(True, description="Emit I,J relative center. If false, uses R where possible.")
    absolute: bool = Field(True, description="Use G90 absolute coords for X,Y,Z")
    units_mm: bool = Field(True, description="True=metric (G21), False=inches (G20)")
    # Safety & extras
    safe_rapid: bool = Field(True, description="Emit G0 to clearance plane before starting")
    dwell_ms: int = Field(0, ge=0, description="Optional dwell (ms) after helix completes")
    # Limits
    max_arc_degrees: float = Field(360.0, gt=0, le=360.0, description="Split arcs to this maximum sweep each segment")
    # Post-processor preset
    post_preset: Optional[str] = Field(None, description="Optional controller preset: GRBL | Mach3 | Haas | Marlin")
    # Safety validation parameters (optional)
    tool_diameter_mm: Optional[float] = Field(None, gt=0, description="Tool diameter for safety checks (mm)")
    material: Optional[str] = Field(None, description="Material type: hardwood | softwood | plywood | mdf | acrylic | aluminum")
    spindle_rpm: Optional[int] = Field(None, gt=0, description="Spindle speed for chipload validation (RPM)")

    @model_validator(mode='before')
    @classmethod
    def migrate_old_field_names(cls, data: Any) -> Any:
        """
        Backward compatibility: Accept old field names from tests and migrate to new names.

        Old → New mappings:
        - entry_x → cx
        - entry_y → cy
        - helix_radius → radius_mm
        - target_depth → z_target_mm
        - pitch → pitch_mm_per_rev
        - feed_xy → feed_xy_mm_min
        - feed_z → feed_z_mm_min
        - direction: lowercase → uppercase (cw → CW, ccw → CCW)
        """
        if isinstance(data, dict):
            # Map old field names to new ones
            if 'entry_x' in data:
                data['cx'] = data.pop('entry_x')
            if 'entry_y' in data:
                data['cy'] = data.pop('entry_y')
            if 'helix_radius' in data:
                data['radius_mm'] = data.pop('helix_radius')
            if 'target_depth' in data:
                data['z_target_mm'] = data.pop('target_depth')
            if 'pitch' in data and 'pitch_mm_per_rev' not in data:
                data['pitch_mm_per_rev'] = data.pop('pitch')
            if 'feed_xy' in data:
                data['feed_xy_mm_min'] = data.pop('feed_xy')
            if 'feed_z' in data:
                data['feed_z_mm_min'] = data.pop('feed_z')
            # Normalize direction to uppercase
            if 'direction' in data and isinstance(data['direction'], str):
                data['direction'] = data['direction'].upper()
        return data

    @field_validator("z_target_mm")
    @classmethod
    def check_depth(cls, v: Any) -> float:
        if not isinstance(v, (int, float)):
            raise ValueError("z_target_mm must be a number")
        return float(v)


def _fmt(n: float) -> str:
    # 3 decimals is typical for mm mode; adapt as needed
    formatted = f"{n:.4f}"
    return formatted.rstrip('0').rstrip('.') if '.' in formatted else formatted


def helical_gcode(req: HelicalReq) -> Dict[str, Any]:
    # Get post-processor preset (defaults to GRBL if not specified)
    preset = get_post_preset(req.post_preset)

    # Override ij_mode if preset requires R-mode
    effective_ij_mode = not preset.use_r_mode if req.post_preset else req.ij_mode

    # CRITICAL: Run safety validation BEFORE generating toolpath
    warnings = helical_validate(
        radius_mm=req.radius_mm,
        pitch_mm_per_rev=req.pitch_mm_per_rev,
        feed_xy_mm_min=req.feed_xy_mm_min,
        tool_diameter_mm=req.tool_diameter_mm,
        material=req.material,
        spindle_rpm=req.spindle_rpm,
    )

    # Generate toolpath using core module
    moves = helical_plunge(
        cx=req.cx,
        cy=req.cy,
        radius_mm=req.radius_mm,
        direction=req.direction,
        start_z_mm=req.start_z_mm,
        z_target_mm=req.z_target_mm,
        pitch_mm_per_rev=req.pitch_mm_per_rev,
        feed_xy_mm_min=req.feed_xy_mm_min,
        max_arc_degrees=req.max_arc_degrees,
        ij_mode=effective_ij_mode,
    )

    # Calculate statistics using core module
    stats = helical_stats(
        moves=moves,
        radius_mm=req.radius_mm,
        pitch_mm_per_rev=req.pitch_mm_per_rev,
        start_z_mm=req.start_z_mm,
        z_target_mm=req.z_target_mm,
        feed_xy_mm_min=req.feed_xy_mm_min,
        tool_diameter_mm=req.tool_diameter_mm,
        spindle_rpm=req.spindle_rpm,
    )

    # Generate preview points for visualization
    preview = helical_preview_points(
        cx=req.cx,
        cy=req.cy,
        radius_mm=req.radius_mm,
        direction=req.direction,
        start_z_mm=req.start_z_mm,
        z_target_mm=req.z_target_mm,
        pitch_mm_per_rev=req.pitch_mm_per_rev,
        points_per_rev=16,  # 16 points per revolution for smooth preview
    )

    # Convert moves to G-code
    lines = []
    units = "G21" if req.units_mm else "G20"
    preset_name = preset.name if req.post_preset else "default"

    # Header
    lines.append(f"({req.direction} Helical Z-Ramp, r={_fmt(req.radius_mm)} pitch={_fmt(req.pitch_mm_per_rev)} startZ={_fmt(req.start_z_mm)} targetZ={_fmt(req.z_target_mm)})")
    lines.append(f"(Post preset: {preset_name})")
    if warnings:
        lines.append(f"(WARNINGS: {len(warnings)} safety checks flagged - review before running)")
    lines.append(units)
    lines.append("G90" if req.absolute else "G91")
    lines.append("G17")  # XY plane

    # Safe rapid to clearance
    sx = req.cx + req.radius_mm
    sy = req.cy
    if req.safe_rapid:
        lines.append(f"G0 Z{_fmt(req.plane_z_mm)}")
    lines.append(f"G0 X{_fmt(sx)} Y{_fmt(sy)}")

    # Plunge to start Z
    if req.plane_z_mm != req.start_z_mm:
        lines.append(f"G1 Z{_fmt(req.start_z_mm)} F{_fmt(req.feed_z_mm_min or req.feed_xy_mm_min)}")

    # Emit helical moves
    for move in moves:
        parts = [move["code"]]
        if "x" in move:
            parts.append(f"X{_fmt(move['x'])}")
        if "y" in move:
            parts.append(f"Y{_fmt(move['y'])}")
        if "z" in move:
            parts.append(f"Z{_fmt(move['z'])}")
        if "i" in move:
            parts.append(f"I{_fmt(move['i'])}")
        if "j" in move:
            parts.append(f"J{_fmt(move['j'])}")
        if "r" in move:
            parts.append(f"R{_fmt(move['r'])}")
        if "f" in move:
            parts.append(f"F{_fmt(move['f'])}")
        lines.append(" ".join(parts))

    # Optional dwell
    if req.dwell_ms and req.dwell_ms > 0:
        dwell_cmd = get_dwell_command(req.dwell_ms, preset)
        if dwell_cmd:
            lines.append(dwell_cmd)

    # Exit to clearance plane
    lines.append(f"G0 Z{_fmt(req.plane_z_mm)}")

    program = "\n".join(lines)

    # Add warning count and preview points to stats
    stats["post_preset"] = preset_name
    stats["arc_mode"] = "R" if not effective_ij_mode else "IJ"
    stats["warning_count"] = len(warnings)

    return {
        "ok": True,
        "gcode": program,
        "stats": stats,
        "warnings": warnings,
        "preview_points": preview,
    }


@router.post("/helical_entry")
def helical_entry(req: HelicalReq) -> Dict[str, Any]:
    """
    Generate helical plunge G-code.

    LANE: OPERATION - Creates helical_gcode_execution artifact.
    """
    now = datetime.now(timezone.utc).isoformat()
    request_hash = sha256_of_obj(req.model_dump())

    # --- Server-side feasibility enforcement (ADR-003 / OPERATION lane) ---
    feasibility = compute_feasibility_internal(
        tool_id="helical:gcode",
        req=req,
        context="helical_gcode",
    )
    decision = SafetyPolicy.extract_safety_decision(feasibility)
    risk_level = decision.risk_level_str()
    feas_hash = sha256_of_obj(feasibility)

    if SafetyPolicy.should_block(decision.risk_level):
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id="helical:gcode",
            workflow_mode="helical",
            event_type="helical_gcode_blocked",
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
                "message": "Helical G-code generation blocked due to unresolved feasibility concerns.",
                "run_id": run_id,
                "decision": decision.to_dict(),
                "authoritative_feasibility": feasibility,
            },
        )

    # Basic sanity checks with artifact persistence
    def error_artifact(msg: str):
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id="helical:gcode",
            workflow_mode="helical",
            event_type="helical_gcode_execution",
            status="ERROR",
            feasibility=feasibility,
            request_hash=request_hash,
            errors=[msg],
        )
        persist_run(artifact)
        raise HTTPException(status_code=400, detail={"error": "VALIDATION_ERROR", "run_id": run_id, "message": msg})

    if req.radius_mm <= 0:
        error_artifact("radius_mm must be > 0")
    if req.max_arc_degrees <= 0 or req.max_arc_degrees > 360:
        error_artifact("max_arc_degrees must be (0,360]")
    if req.pitch_mm_per_rev <= 0:
        error_artifact("pitch must be > 0")
    if req.start_z_mm == req.z_target_mm:
        error_artifact("start_z_mm equals z_target_mm; nothing to do")

    try:
        result = helical_gcode(req)

        # Hash G-code for provenance
        gcode_hash = sha256_of_text(result.get("gcode", ""))

        # Create OK artifact
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id="helical:gcode",
            workflow_mode="helical",
            event_type="helical_gcode_execution",
            status="OK",
            feasibility=feasibility,
            request_hash=request_hash,
            gcode_hash=gcode_hash,
        )
        persist_run(artifact)

        # Add audit linkage to response
        result["_run_id"] = run_id
        result["_hashes"] = {
            "request_sha256": request_hash,
            "gcode_sha256": gcode_hash,
        }
        return result

    except HTTPException:
        raise
    except Exception as e:
        run_id = create_run_id()
        artifact = RunArtifact(
            run_id=run_id,
            created_at_utc=now,
            tool_id="helical:gcode",
            workflow_mode="helical",
            event_type="helical_gcode_execution",
            status="ERROR",
            feasibility=feasibility,
            request_hash=request_hash,
            errors=[f"{type(e).__name__}: {str(e)}"],
        )
        persist_run(artifact)
        raise HTTPException(
            status_code=500,
            detail={"error": "HELICAL_GCODE_ERROR", "run_id": run_id, "message": str(e)},
        )


@router.get("/helical_health")
def helical_health() -> Dict[str, Any]:
    return {"ok": True, "status": "ok", "service": "helical_v161", "module": "helical_v161", "version": "16.1"}
