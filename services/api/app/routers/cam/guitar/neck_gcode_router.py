"""Neck G-code router (project-driven).

Extracted from ``body_gcode_router`` for a structural reason, not a cosmetic one:
**a neck manufacturing route does not belong in a body G-code router.**

The route path, request contract and manufacturing behaviour are unchanged. The
generator-readiness gate remains the first manufacturing decision, and the neck
route remains REVIEW_REQUIRED, so it continues to fail closed.

This router is NOT the separately tracked neck path that carries the standing
rapids-at-cutting-depth finding; that one lives in ``cam_workspace_router`` and
is deliberately left alone.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ....auth.deps import get_current_principal
from ....auth.principal import Principal
from ....db.session import get_db
from app.core.safety import safety_critical

from ._gcode_common import (
    _generate_timestamp,
    _get_project_or_404,
    _make_nc_response,
    _parse_design_state_or_422,
    _readiness_gate,
)

router = APIRouter()


@router.post("/{model_id}/neck/gcode", response_class=StreamingResponse)
@safety_critical
def generate_neck_gcode(
    model_id: str,
    project_id: str = Query(..., description="Project UUID"),
    preset: str = Query(None, description="Neck preset: gibson_50s, fender_vintage, etc."),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """
    Generate neck G-code from project.

    Uses NeckDimensions.from_project() to get dimensions,
    then generates neck carving G-code.

    Works for any model_id - neck dimensions come from project.spec.

    Returns .nc file as streaming download.
    """

    _readiness_gate("neck")
    project = _get_project_or_404(project_id, principal, db)
    design_state = _parse_design_state_or_422(project)

    try:
        from ....generators.neck_headstock_config import NeckDimensions, NECK_PRESETS

        # Use preset or from_project()
        if preset and preset in NECK_PRESETS:
            dims = NECK_PRESETS[preset]
        else:
            dims = NeckDimensions.from_project(design_state)

        # Generate basic neck G-code
        gcode_lines = []
        gcode_lines.append(f"(Neck G-code - {model_id})")
        gcode_lines.append(f"(Project: {project.name})")
        gcode_lines.append(f"(Scale: {dims.scale_length_in:.2f}\")")
        gcode_lines.append(f"(Nut width: {dims.nut_width_in:.4f}\")")
        gcode_lines.append(f"(Headstock angle: {dims.headstock_angle_deg}°)")
        gcode_lines.append("")
        gcode_lines.append("G20 (inches)")
        gcode_lines.append("G90 (absolute)")
        gcode_lines.append("G17 (XY plane)")
        gcode_lines.append("")

        # Truss rod channel
        gcode_lines.append("(=== TRUSS ROD CHANNEL ===)")
        gcode_lines.append("M3 S18000")
        gcode_lines.append("G4 P2")
        gcode_lines.append(f"G0 Z0.5")
        gcode_lines.append(f"G0 X0 Y0")

        # Simple truss rod pocket - centerline
        tr_width = dims.truss_rod_width_in
        tr_depth = dims.truss_rod_depth_in
        tr_length = dims.truss_rod_length_in

        gcode_lines.append(f"G0 X{-tr_width/2:.4f} Y0")
        gcode_lines.append(f"G1 Z{-tr_depth:.4f} F20")
        gcode_lines.append(f"G1 X{tr_width/2:.4f} F60")
        gcode_lines.append(f"G1 Y{tr_length:.4f}")
        gcode_lines.append(f"G1 X{-tr_width/2:.4f}")
        gcode_lines.append(f"G1 Y0")
        gcode_lines.append("G0 Z0.5")
        gcode_lines.append("")

        # Headstock angle (if angled)
        if dims.headstock_angle_deg > 0:
            gcode_lines.append("(=== HEADSTOCK ANGLE CUT ===)")
            gcode_lines.append(f"(Angle: {dims.headstock_angle_deg}° - requires angled fixture or 5-axis)")
            gcode_lines.append(f"(Headstock thickness: {dims.headstock_thickness_in:.3f}\")")
            gcode_lines.append("")

        gcode_lines.append("(=== NECK PROFILE ===)")
        gcode_lines.append("(Profile carving requires 4th axis or ball-end 3D surfacing)")
        gcode_lines.append(f"(Depth at 1st fret: {dims.depth_at_1st_in:.3f}\")")
        gcode_lines.append(f"(Depth at 12th fret: {dims.depth_at_12th_in:.3f}\")")
        gcode_lines.append("")

        gcode_lines.append("M5 (spindle stop)")
        gcode_lines.append("G0 Z1.0")
        gcode_lines.append("M30 (program end)")

        gcode = "\n".join(gcode_lines)

        filename = f"{model_id}_neck_{_generate_timestamp()}.nc"
        return _make_nc_response(gcode, filename)

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Neck generator module not available: {e}"
        )
