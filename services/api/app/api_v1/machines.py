"""
Machines API v1

Machine profiles and setup:

1. GET  /machines/profiles - List machine profiles
2. GET  /machines/profiles/{id} - Get profile details
3. POST /machines/probe/surface - Surface probing routine
4. POST /machines/probe/corner - Corner finding routine
5. GET  /machines/dialects - List G-code dialects
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/machines", tags=["Machines"])


# =============================================================================
# SCHEMAS
# =============================================================================

class V1Response(BaseModel):
    """Standard v1 response wrapper."""
    ok: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    hint: Optional[str] = None


class ProbeRequest(BaseModel):
    """Request probing routine generation."""
    machine_id: str = Field(..., description="Machine profile ID")
    probe_type: str = Field(..., description="Probe type: touch, tool_setter, laser")
    feed_rate: float = Field(100.0, description="Probing feed rate mm/min")
    retract_mm: float = Field(2.0, description="Retract distance after contact")


class SurfaceProbeRequest(ProbeRequest):
    """Surface probing parameters."""
    grid_x: int = Field(3, description="Grid points in X")
    grid_y: int = Field(3, description="Grid points in Y")
    x_min: float = Field(0.0, description="Start X")
    x_max: float = Field(100.0, description="End X")
    y_min: float = Field(0.0, description="Start Y")
    y_max: float = Field(100.0, description="End Y")


class CornerProbeRequest(ProbeRequest):
    """Corner finding parameters."""
    corner: str = Field("front_left", description="Corner: front_left, front_right, back_left, back_right")
    approach_x: float = Field(10.0, description="Approach distance X")
    approach_y: float = Field(10.0, description="Approach distance Y")


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/profiles")
def list_machine_profiles() -> V1Response:
    """
    List available machine profiles.

    Profiles contain travel limits, spindle specs, and defaults.
    """
    profiles = [
        {
            "id": "shapeoko_3",
            "name": "Shapeoko 3",
            "type": "router",
            "travel_x_mm": 425,
            "travel_y_mm": 425,
            "travel_z_mm": 75,
            "spindle_rpm_max": 30000,
            "dialect": "grbl",
        },
        {
            "id": "x_carve_1000",
            "name": "X-Carve 1000mm",
            "type": "router",
            "travel_x_mm": 750,
            "travel_y_mm": 750,
            "travel_z_mm": 65,
            "spindle_rpm_max": 30000,
            "dialect": "grbl",
        },
        {
            "id": "haas_vf2",
            "name": "Haas VF-2",
            "type": "mill",
            "travel_x_mm": 762,
            "travel_y_mm": 406,
            "travel_z_mm": 508,
            "spindle_rpm_max": 8100,
            "dialect": "haas",
        },
        {
            "id": "linuxcnc_custom",
            "name": "LinuxCNC Custom",
            "type": "router",
            "travel_x_mm": 600,
            "travel_y_mm": 400,
            "travel_z_mm": 100,
            "spindle_rpm_max": 24000,
            "dialect": "linuxcnc",
        },
    ]

    return V1Response(
        ok=True,
        data={
            "profiles": profiles,
            "total": len(profiles),
        },
    )


@router.get("/profiles/{profile_id}")
def get_machine_profile(profile_id: str) -> V1Response:
    """
    Get detailed machine profile.

    Includes travel limits, spindle specs, tooling, and CAM defaults.
    """
    # Example profile structure
    return V1Response(
        ok=True,
        data={
            "id": profile_id,
            "name": "Shapeoko 3",
            "type": "router",
            "travel": {
                "x_mm": 425,
                "y_mm": 425,
                "z_mm": 75,
            },
            "spindle": {
                "rpm_min": 10000,
                "rpm_max": 30000,
                "type": "router",
            },
            "rapids": {
                "xy_mm_min": 5000,
                "z_mm_min": 2000,
            },
            "defaults": {
                "safe_z_mm": 5.0,
                "feed_xy_mm_min": 1200,
                "feed_z_mm_min": 300,
                "stepdown_mm": 2.0,
            },
            "dialect": "grbl",
            "features": ["probe", "tool_change_manual"],
        },
    )


@router.post("/probe/surface")
def generate_surface_probe(req: SurfaceProbeRequest) -> V1Response:
    """
    Generate G-code for surface probing grid.

    Creates a grid of probe points for workpiece surface mapping.
    """
    points = []
    step_x = (req.x_max - req.x_min) / (req.grid_x - 1) if req.grid_x > 1 else 0
    step_y = (req.y_max - req.y_min) / (req.grid_y - 1) if req.grid_y > 1 else 0

    for j in range(req.grid_y):
        for i in range(req.grid_x):
            x = req.x_min + (i * step_x)
            y = req.y_min + (j * step_y)
            points.append({"x": round(x, 3), "y": round(y, 3)})

    # Generate G-code
    lines = [
        "; Surface Probing Routine",
        f"; Grid: {req.grid_x}x{req.grid_y}, Points: {len(points)}",
        "",
        "G21 ; mm",
        "G90 ; absolute",
        f"G0 Z10 ; safe height",
        "",
    ]

    for idx, pt in enumerate(points):
        lines.append(f"; Point {idx + 1}")
        lines.append(f"G0 X{pt['x']} Y{pt['y']}")
        lines.append(f"G38.2 Z-20 F{req.feed_rate} ; probe down")
        lines.append(f"G0 Z{req.retract_mm} ; retract")
        lines.append("")

    lines.append("G0 Z10 ; return to safe height")
    lines.append("M30 ; end program")

    return V1Response(
        ok=True,
        data={
            "machine_id": req.machine_id,
            "probe_type": req.probe_type,
            "grid": {"x": req.grid_x, "y": req.grid_y},
            "points": points,
            "total_points": len(points),
            "gcode": "\n".join(lines),
            "estimated_time_s": len(points) * 5,
        },
    )


@router.post("/probe/corner")
def generate_corner_probe(req: CornerProbeRequest) -> V1Response:
    """
    Generate G-code for corner finding.

    Probes X and Y edges to establish workpiece origin.
    """
    # Generate corner finding routine
    lines = [
        "; Corner Finding Routine",
        f"; Corner: {req.corner}",
        "",
        "G21 ; mm",
        "G90 ; absolute",
        "G0 Z10 ; safe height",
        "",
        "; Probe X edge",
        f"G38.2 X{-req.approach_x if 'left' in req.corner else req.approach_x} F{req.feed_rate}",
        f"G0 X{req.retract_mm if 'left' in req.corner else -req.retract_mm}",
        "",
        "; Probe Y edge",
        f"G38.2 Y{-req.approach_y if 'front' in req.corner else req.approach_y} F{req.feed_rate}",
        f"G0 Y{req.retract_mm if 'front' in req.corner else -req.retract_mm}",
        "",
        "G0 Z10 ; return to safe height",
        "M30 ; end program",
    ]

    return V1Response(
        ok=True,
        data={
            "machine_id": req.machine_id,
            "corner": req.corner,
            "gcode": "\n".join(lines),
            "hint": "Run this routine with probe connected, then set work offset",
        },
    )


@router.get("/dialects")
def list_dialects() -> V1Response:
    """
    List supported G-code dialects (post-processors).

    Each dialect formats G-code for a specific controller.
    """
    dialects = [
        {
            "id": "grbl",
            "name": "GRBL 1.1+",
            "description": "Arduino-based CNC controllers",
            "features": ["probing", "spindle_pwm"],
            "line_numbers": False,
        },
        {
            "id": "linuxcnc",
            "name": "LinuxCNC / EMC2",
            "description": "Linux-based motion controller",
            "features": ["probing", "tool_change", "subroutines"],
            "line_numbers": True,
        },
        {
            "id": "mach3",
            "name": "Mach3 / Mach4",
            "description": "Windows-based CNC control",
            "features": ["probing", "tool_change"],
            "line_numbers": True,
        },
        {
            "id": "haas",
            "name": "Haas NGC",
            "description": "Haas industrial mills",
            "features": ["probing", "tool_change", "coolant"],
            "line_numbers": True,
        },
        {
            "id": "fanuc",
            "name": "FANUC",
            "description": "FANUC industrial CNC",
            "features": ["probing", "tool_change", "coolant", "subprograms"],
            "line_numbers": True,
        },
    ]

    return V1Response(
        ok=True,
        data={
            "dialects": dialects,
            "default": "grbl",
            "total": len(dialects),
        },
    )
