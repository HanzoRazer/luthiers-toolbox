"""
Pydantic schemas for geometry_router.py

Extracted as part of Phase 9 god-object decomposition.
Contains 7 schema classes for geometry import/export/parity endpoints.
"""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class Segment(BaseModel):
    """
    Geometry segment (line or arc).

    Segment Types:
    - line: Requires x1, y1, x2, y2
    - arc: Requires cx, cy, r, start, end, cw

    Coordinates:
    - All values in current units (mm or inch)
    - Angles in degrees (0-360)
    """
    type: Literal["line", "arc"]  # MUST be explicit type
    x1: Optional[float] = None    # Line start X
    y1: Optional[float] = None    # Line start Y
    x2: Optional[float] = None    # Line end X
    y2: Optional[float] = None    # Line end Y
    cx: Optional[float] = None    # Arc center X
    cy: Optional[float] = None    # Arc center Y
    r: Optional[float] = None     # Arc radius
    start: Optional[float] = None  # Arc start angle (degrees)
    end: Optional[float] = None    # Arc end angle (degrees)
    cw: Optional[bool] = None      # Arc clockwise flag


class GeometryIn(BaseModel):
    """
    Canonical geometry format for import/export.

    Fields:
    - units: 'mm' or 'inch' (MUST be explicit)
    - paths: List of Segment objects

    Validation:
    - Path count must be <= MAX_SEGMENTS
    - Coordinates must be within safe bounds
    """
    units: Literal["mm", "inch"] = "mm"
    paths: List[Segment]


class ParityRequest(BaseModel):
    """Request for geometry/toolpath parity validation."""
    geometry: GeometryIn
    gcode: str
    tolerance_mm: float = 0.05


class ExportRequest(BaseModel):
    """Request for geometry export to DXF/SVG."""
    geometry: GeometryIn
    post_id: Optional[str] = None  # GRBL/Mach4/LinuxCNC/PathPilot/MASSO
    job_name: Optional[str] = Field(
        default=None,
        description="Filename stem for DXF/SVG (safe chars only)"
    )


class SimulationGateFields(BaseModel):
    """
    Mixin fields for simulation gate enforcement.

    SAFETY: G-code export requires simulation verification OR explicit override.
    See: docs/DESIGN_REVIEW_2026-02-22.md Priority #3
    """
    simulation_passed: Optional[bool] = Field(
        default=None,
        description="True if G-code was simulated without critical issues"
    )
    simulation_hash: Optional[str] = Field(
        default=None,
        description="SHA256 of simulation result for verification"
    )
    simulation_override: Optional[bool] = Field(
        default=False,
        description="Explicitly bypass simulation gate (requires reason)"
    )
    simulation_override_reason: Optional[str] = Field(
        default=None,
        description="Required reason when simulation_override=True"
    )


class GcodeExportIn(SimulationGateFields):
    """
    Request for G-code export with post-processor headers/footers.

    SAFETY GATE: For governed exports, requires one of:
    - simulation_passed=True with valid simulation_hash
    - simulation_override=True with simulation_override_reason

    The gate is enforced when RMOS_REQUIRE_SIMULATION=1 (default).
    """
    gcode: str
    units: Optional[str] = "mm"
    post_id: Optional[str] = None
    job_name: Optional[str] = Field(
        default=None,
        description="Filename stem for NC file (safe chars only)"
    )


class ExportBundleIn(BaseModel):
    """Request for CAM bundle export (DXF + SVG + G-code + manifest)."""
    geometry: GeometryIn
    gcode: str
    post_id: Optional[str] = None
    target_units: Optional[str] = None  # if provided, geometry is scaled server-side
    job_name: Optional[str] = Field(
        default=None,
        description="Filename stem for bundle files (safe chars only)"
    )


class ExportBundleMultiIn(BaseModel):
    """Request for multi-post CAM bundle export."""
    geometry: GeometryIn
    gcode: str
    post_ids: List[str]  # e.g. ["GRBL","Mach4","LinuxCNC","PathPilot","MASSO"]
    target_units: Optional[str] = None  # if provided, geometry is scaled server-side
    job_name: Optional[str] = Field(
        default=None,
        description="Filename stem for bundle files (safe chars only)"
    )
