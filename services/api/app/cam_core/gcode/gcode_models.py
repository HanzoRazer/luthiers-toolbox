"""
G-code Data Models for CAM Core

Pydantic schemas used by cam_core/gcode/saw_gcode_generator.py.
Reconstructed from type annotations in the generator (CP-S57).

Models:
    Point2D             — (x, y) coordinate alias
    SawToolpath         — A single cutting path with 2-D point list
    DepthPass           — One depth level in a multi-pass operation
    SawGCodeRequest     — Full request for saw G-code generation
    SawGCodeResult      — Generated G-code plus metadata
"""
from __future__ import annotations

from typing import List, Literal, Tuple

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------

# Point2D is a plain tuple alias — kept as a type alias rather than a model
# so existing code that passes (x, y) tuples works without wrapping.
Point2D = Tuple[float, float]


# ---------------------------------------------------------------------------
# Toolpath and depth planning
# ---------------------------------------------------------------------------

class SawToolpath(BaseModel):
    """A single 2-D cutting path for a saw operation."""

    points: List[Point2D] = Field(
        ...,
        description="Ordered list of (x, y) coordinates in mm.",
    )
    is_closed: bool = Field(
        False,
        description=(
            "If True the generator will append a closing segment back to "
            "points[0] at the end of each pass."
        ),
    )

    class Config:
        json_schema_extra = {
            "example": {
                "points": [[0.0, 0.0], [100.0, 0.0], [100.0, 50.0], [0.0, 50.0]],
                "is_closed": True,
            }
        }


class DepthPass(BaseModel):
    """A single depth level computed by plan_depth_passes()."""

    depth_mm: float = Field(
        ...,
        description="Z depth for this pass in mm. Negative = below surface (Z=0).",
    )


# ---------------------------------------------------------------------------
# Request / Response
# ---------------------------------------------------------------------------

class SawGCodeRequest(BaseModel):
    """Complete request payload for generate_saw_gcode()."""

    # Operation identity
    op_type: Literal["slice", "batch", "contour"] = Field(
        "slice",
        description="Operation type — affects header comment and validation.",
    )
    program_id: str = Field(
        "0001",
        description="G-code program number (emitted as O{id}).",
    )
    program_comment: str = Field(
        "SAW OPERATION",
        description="Free-text comment inserted in the program header.",
    )

    # Toolpaths
    toolpaths: List[SawToolpath] = Field(
        ...,
        description="One or more cutting paths to execute at each depth pass.",
    )
    closed_paths_only: bool = Field(
        False,
        description=(
            "When True, raises ValueError if any toolpath is open. "
            "Use for operations that require closed contours."
        ),
    )

    # Depth planning
    total_depth_mm: float = Field(
        ...,
        gt=0,
        description="Total cutting depth (positive value, mm).",
    )
    doc_per_pass_mm: float = Field(
        1.0,
        gt=0,
        description="Maximum depth-of-cut per pass (mm). Controls number of passes.",
    )

    # Feed rates (input always in IPM regardless of machine_units)
    feed_ipm: float = Field(
        60.0,
        gt=0,
        description="Cutting feed rate in inches per minute.",
    )
    plunge_ipm: float = Field(
        20.0,
        gt=0,
        description="Plunge (Z) feed rate in inches per minute.",
    )

    # Machine configuration
    machine_units: Literal["mm", "inch"] = Field(
        "mm",
        description="Output unit mode. 'mm' emits G21; 'inch' emits G20 and skips IPM→mm/min conversion.",
    )
    safe_z_mm: float = Field(
        5.0,
        description="Safe Z height for rapid moves (mm, above workpiece surface).",
    )
    surface_z_mm: float = Field(
        0.0,
        description="Z coordinate of the workpiece surface (mm). Typically 0.",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "op_type": "slice",
                "toolpaths": [
                    {"points": [[0, 0], [100, 0]], "is_closed": False}
                ],
                "total_depth_mm": 3.0,
                "doc_per_pass_mm": 1.0,
                "feed_ipm": 60,
                "plunge_ipm": 20,
            }
        }


class SawGCodeResult(BaseModel):
    """Output from generate_saw_gcode()."""

    gcode: str = Field(
        ...,
        description="Complete G-code program as a single string.",
    )
    op_type: str = Field(
        ...,
        description="Echo of SawGCodeRequest.op_type.",
    )
    depth_passes: List[DepthPass] = Field(
        ...,
        description="Depth pass schedule that was executed.",
    )
    total_length_mm: float = Field(
        ...,
        description=(
            "Estimated total cutting path length in mm "
            "(sum across all passes and toolpaths)."
        ),
    )
