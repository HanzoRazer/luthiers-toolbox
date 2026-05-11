"""
Drilling Preview Router — Governed Preview Endpoint

Provides governed preview for drilling operations without G-code generation.

GOVERNED PREVIEW STATUS: GOVERNED PREVIEW (5E)
Gate Semantics: Overlap→RED, near-touch→YELLOW, valid→GREEN
Coordinate System: Workpiece-relative, Z-zero at top of stock

Route: POST /api/cam/drilling/preview

Dev Order: 5E (2026-05-09)
Reference: nut_slot_cam.py, fret_slots_router.py (5C/5D)

Note: This route does NOT use RMOS persistence. Preview only.
G-code generation routes with RMOS are in drill_pattern_router.py.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field


router = APIRouter(tags=["cam", "drilling"])


# --- Governed Preview Standard Types ---

class CamGate(str, Enum):
    """CAM safety gate classification."""
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class CamIssue(BaseModel):
    """Structured issue for governed preview."""
    code: str
    severity: Literal["green", "yellow", "red"]
    message: str
    field: Optional[str] = None


class CoordinateSystem(BaseModel):
    """Coordinate system metadata for governed preview."""
    units: str = "mm"
    origin: str
    x_axis: str
    y_axis: str
    z_axis: str
    z_zero: str
    handedness: str = "right_handed"
    frame: str = "local_workpiece"
    notes: Optional[str] = None
    coordinate_confidence: Optional[str] = None


class PreviewMetadata(BaseModel):
    """Generator metadata for governed preview."""
    generator_id: str
    generator_version: Optional[str] = None
    preview_only: bool = True
    machine_ready: bool = False
    risk_class: str = "A"
    generated_at: str
    operation_category: Optional[str] = None


# Drilling coordinate system constant
DRILLING_COORDINATE_SYSTEM = CoordinateSystem(
    units="mm",
    origin="workpiece_origin",
    x_axis="left_to_right",
    y_axis="front_to_back",
    z_axis="tool_depth",
    z_zero="top_of_stock",
    handedness="right_handed",
    frame="local_workpiece",
    notes="X/Y define hole center position on workpiece surface. "
          "Z depth is positive value representing depth into material.",
    coordinate_confidence="documented_from_current_code",
)


# --- Request/Response Models ---

class DrillHoleInput(BaseModel):
    """Single drill hole specification."""
    x_mm: float = Field(..., description="X position of hole center")
    y_mm: float = Field(..., description="Y position of hole center")
    diameter_mm: float = Field(..., gt=0, description="Hole diameter")
    depth_mm: float = Field(..., gt=0, description="Hole depth")
    label: Optional[str] = None


class DrillingPreviewRequest(BaseModel):
    """Request for drilling preview."""
    holes: List[DrillHoleInput] = Field(..., min_length=1)
    stock_thickness_mm: Optional[float] = Field(None, gt=0, description="Stock thickness for depth validation")
    stock_width_mm: Optional[float] = Field(None, gt=0, description="Stock width (X dimension)")
    stock_height_mm: Optional[float] = Field(None, gt=0, description="Stock height (Y dimension)")
    min_edge_distance_mm: float = Field(3.0, ge=0, description="Minimum distance from hole edge to stock edge")


class DrillHoleOut(BaseModel):
    """Hole data for preview response."""
    x_mm: float
    y_mm: float
    diameter_mm: float
    depth_mm: float
    label: Optional[str] = None
    radius_mm: float


class DrillingPreviewResponse(BaseModel):
    """
    Response for drilling preview.

    GOVERNED PREVIEW fields (5E normalization):
    - operation, status, gate, units: standard envelope
    - coordinate_system: spatial reference metadata
    - canonical_toolpath: wrapper for holes data
    - preview_geometry: frontend-friendly hole geometry
    - warnings, errors, issues: structured validation output
    - metadata: generator provenance
    - statistics: drilling metrics

    No legacy fields needed (this is a new route).
    """
    # Governed Preview Standard Fields
    operation: str = "drilling_preview"
    status: str = "preview"
    gate: CamGate = CamGate.GREEN
    units: str = "mm"
    coordinate_system: CoordinateSystem = Field(default_factory=lambda: DRILLING_COORDINATE_SYSTEM)
    canonical_toolpath: Dict[str, Any]
    preview_geometry: Dict[str, Any]
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    issues: List[CamIssue] = Field(default_factory=list)
    statistics: Dict[str, Any]
    metadata: PreviewMetadata


# --- Gate Evaluation ---

class GateEvaluation:
    """Accumulates gate evaluation results."""

    def __init__(self):
        self.gate = CamGate.GREEN
        self.warnings: List[str] = []
        self.errors: List[str] = []
        self.issues: List[CamIssue] = []

    def add_error(self, code: str, message: str, field: Optional[str] = None) -> None:
        """Add RED error."""
        self.errors.append(message)
        self.issues.append(CamIssue(code=code, severity="red", message=message, field=field))
        self.gate = CamGate.RED

    def add_warning(self, code: str, message: str, field: Optional[str] = None) -> None:
        """Add YELLOW warning."""
        self.warnings.append(message)
        self.issues.append(CamIssue(code=code, severity="yellow", message=message, field=field))
        if self.gate != CamGate.RED:
            self.gate = CamGate.YELLOW


def _distance(h1: DrillHoleInput, h2: DrillHoleInput) -> float:
    """Calculate center-to-center distance between two holes."""
    return math.sqrt((h2.x_mm - h1.x_mm) ** 2 + (h2.y_mm - h1.y_mm) ** 2)


def _evaluate_drilling_gate(
    holes: List[DrillHoleInput],
    stock_thickness_mm: Optional[float],
    stock_width_mm: Optional[float],
    stock_height_mm: Optional[float],
    min_edge_distance_mm: float,
) -> GateEvaluation:
    """
    Evaluate drilling preview gate conditions.

    RED conditions:
    - Overlapping holes (center_distance < sum_of_radii)
    - Negative or zero dimensions
    - Depth exceeds stock thickness

    YELLOW conditions:
    - Near-touching holes (sum_of_radii <= distance < sum_of_radii + 1mm)
    - Hole near stock edge
    - Deep holes (depth > 3x diameter)
    - Small diameter (< 1mm)
    """
    eval_result = GateEvaluation()

    # Validate individual holes
    for i, hole in enumerate(holes):
        hole_id = hole.label or f"hole_{i+1}"

        # Check for invalid dimensions (should be caught by Pydantic, but double-check)
        if hole.diameter_mm <= 0:
            eval_result.add_error(
                "INVALID_DIAMETER",
                f"{hole_id}: diameter must be positive (got {hole.diameter_mm}mm)",
                f"holes[{i}].diameter_mm",
            )

        if hole.depth_mm <= 0:
            eval_result.add_error(
                "INVALID_DEPTH",
                f"{hole_id}: depth must be positive (got {hole.depth_mm}mm)",
                f"holes[{i}].depth_mm",
            )

        # Check depth vs stock thickness
        if stock_thickness_mm is not None and hole.depth_mm >= stock_thickness_mm:
            eval_result.add_error(
                "DEPTH_EXCEEDS_STOCK",
                f"{hole_id}: depth ({hole.depth_mm}mm) >= stock thickness ({stock_thickness_mm}mm)",
                f"holes[{i}].depth_mm",
            )

        # Check stock bounds
        radius = hole.diameter_mm / 2.0
        if stock_width_mm is not None:
            if hole.x_mm - radius < 0:
                eval_result.add_error(
                    "OUT_OF_BOUNDS_X",
                    f"{hole_id}: hole extends past left edge (x={hole.x_mm}mm, radius={radius}mm)",
                    f"holes[{i}].x_mm",
                )
            elif hole.x_mm + radius > stock_width_mm:
                eval_result.add_error(
                    "OUT_OF_BOUNDS_X",
                    f"{hole_id}: hole extends past right edge",
                    f"holes[{i}].x_mm",
                )
            elif hole.x_mm - radius < min_edge_distance_mm:
                eval_result.add_warning(
                    "NEAR_EDGE_X",
                    f"{hole_id}: hole edge is {hole.x_mm - radius:.1f}mm from left edge (min: {min_edge_distance_mm}mm)",
                    f"holes[{i}].x_mm",
                )
            elif hole.x_mm + radius > stock_width_mm - min_edge_distance_mm:
                eval_result.add_warning(
                    "NEAR_EDGE_X",
                    f"{hole_id}: hole edge is {stock_width_mm - hole.x_mm - radius:.1f}mm from right edge",
                    f"holes[{i}].x_mm",
                )

        if stock_height_mm is not None:
            if hole.y_mm - radius < 0:
                eval_result.add_error(
                    "OUT_OF_BOUNDS_Y",
                    f"{hole_id}: hole extends past front edge (y={hole.y_mm}mm, radius={radius}mm)",
                    f"holes[{i}].y_mm",
                )
            elif hole.y_mm + radius > stock_height_mm:
                eval_result.add_error(
                    "OUT_OF_BOUNDS_Y",
                    f"{hole_id}: hole extends past back edge",
                    f"holes[{i}].y_mm",
                )
            elif hole.y_mm - radius < min_edge_distance_mm:
                eval_result.add_warning(
                    "NEAR_EDGE_Y",
                    f"{hole_id}: hole edge is {hole.y_mm - radius:.1f}mm from front edge",
                    f"holes[{i}].y_mm",
                )
            elif hole.y_mm + radius > stock_height_mm - min_edge_distance_mm:
                eval_result.add_warning(
                    "NEAR_EDGE_Y",
                    f"{hole_id}: hole edge is {stock_height_mm - hole.y_mm - radius:.1f}mm from back edge",
                    f"holes[{i}].y_mm",
                )

        # Check for deep holes (depth > 3x diameter)
        if hole.depth_mm > 3 * hole.diameter_mm:
            ratio = hole.depth_mm / hole.diameter_mm
            eval_result.add_warning(
                "DEEP_HOLE",
                f"{hole_id}: depth/diameter ratio is {ratio:.1f} (>3), consider peck drilling",
                f"holes[{i}].depth_mm",
            )

        # Check for small diameter
        if hole.diameter_mm < 1.0:
            eval_result.add_warning(
                "SMALL_DIAMETER",
                f"{hole_id}: diameter ({hole.diameter_mm}mm) < 1mm, may require specialty tooling",
                f"holes[{i}].diameter_mm",
            )

    # Check hole-to-hole relationships
    for i in range(len(holes)):
        for j in range(i + 1, len(holes)):
            h1, h2 = holes[i], holes[j]
            dist = _distance(h1, h2)
            sum_radii = (h1.diameter_mm + h2.diameter_mm) / 2.0

            h1_id = h1.label or f"hole_{i+1}"
            h2_id = h2.label or f"hole_{j+1}"

            if dist < sum_radii:
                # Overlapping holes - RED
                eval_result.add_error(
                    "OVERLAPPING_HOLES",
                    f"{h1_id} and {h2_id} overlap (distance={dist:.2f}mm, sum_radii={sum_radii:.2f}mm)",
                )
            elif dist < sum_radii + 1.0:
                # Near-touching holes - YELLOW
                gap = dist - sum_radii
                eval_result.add_warning(
                    "NEAR_TOUCHING_HOLES",
                    f"{h1_id} and {h2_id} are very close (gap={gap:.2f}mm)",
                )

    return eval_result


def _compute_statistics(holes: List[DrillHoleInput]) -> Dict[str, Any]:
    """Compute drilling statistics."""
    if not holes:
        return {
            "operation_count": 0,
            "move_count": 0,
            "warning_count": 0,
            "error_count": 0,
            "hole_count": 0,
        }

    diameters = [h.diameter_mm for h in holes]
    depths = [h.depth_mm for h in holes]

    # Calculate spacing between holes
    spacings = []
    for i in range(len(holes)):
        for j in range(i + 1, len(holes)):
            spacings.append(_distance(holes[i], holes[j]))

    # Calculate bounds
    x_coords = [h.x_mm for h in holes]
    y_coords = [h.y_mm for h in holes]
    max_radius = max(h.diameter_mm / 2 for h in holes)

    return {
        "operation_count": len(holes),
        "move_count": len(holes) * 3,  # rapid + plunge + retract per hole
        "warning_count": 0,  # Updated by caller
        "error_count": 0,  # Updated by caller
        "hole_count": len(holes),
        "min_diameter_mm": round(min(diameters), 3),
        "max_diameter_mm": round(max(diameters), 3),
        "min_depth_mm": round(min(depths), 3),
        "max_depth_mm": round(max(depths), 3),
        "total_depth_mm": round(sum(depths), 3),
        "min_hole_spacing_mm": round(min(spacings), 3) if spacings else None,
        "max_hole_spacing_mm": round(max(spacings), 3) if spacings else None,
        "bounds": {
            "x_min": round(min(x_coords) - max_radius, 3),
            "x_max": round(max(x_coords) + max_radius, 3),
            "y_min": round(min(y_coords) - max_radius, 3),
            "y_max": round(max(y_coords) + max_radius, 3),
        },
    }


# --- Core Preview Function ---

def generate_drilling_preview(req: DrillingPreviewRequest) -> DrillingPreviewResponse:
    """
    Generate governed drilling preview from request.

    Pure function that can be called by lifecycle orchestrator or route.
    No G-code generation. No RMOS persistence.

    Args:
        req: Drilling preview request

    Returns:
        DrillingPreviewResponse with gate evaluation
    """
    # Evaluate gate conditions
    gate_eval = _evaluate_drilling_gate(
        holes=req.holes,
        stock_thickness_mm=req.stock_thickness_mm,
        stock_width_mm=req.stock_width_mm,
        stock_height_mm=req.stock_height_mm,
        min_edge_distance_mm=req.min_edge_distance_mm,
    )

    # Build hole output
    holes_out = [
        DrillHoleOut(
            x_mm=h.x_mm,
            y_mm=h.y_mm,
            diameter_mm=h.diameter_mm,
            depth_mm=h.depth_mm,
            label=h.label,
            radius_mm=h.diameter_mm / 2.0,
        )
        for h in req.holes
    ]

    # Compute statistics
    statistics = _compute_statistics(req.holes)
    statistics["warning_count"] = len(gate_eval.warnings)
    statistics["error_count"] = len(gate_eval.errors)

    # Build canonical toolpath
    canonical_toolpath = {
        "holes": [h.model_dump() for h in holes_out],
        "hole_count": len(holes_out),
    }

    # Build preview geometry (frontend-friendly format)
    preview_geometry = {
        "holes": [
            {
                "x": h.x_mm,
                "y": h.y_mm,
                "diameter_mm": h.diameter_mm,
                "radius_mm": h.radius_mm,
            }
            for h in holes_out
        ],
    }

    # Add stock bounds to preview geometry if provided
    if req.stock_width_mm is not None and req.stock_height_mm is not None:
        preview_geometry["stock_bounds"] = {
            "width_mm": req.stock_width_mm,
            "height_mm": req.stock_height_mm,
            "thickness_mm": req.stock_thickness_mm,
        }

    # Build metadata
    metadata = PreviewMetadata(
        generator_id="drilling_preview",
        generator_version="1.0.0",
        preview_only=True,
        machine_ready=False,
        risk_class="A",
        generated_at=datetime.now(timezone.utc).isoformat(),
        operation_category="drilling",
    )

    return DrillingPreviewResponse(
        operation="drilling_preview",
        status="preview",
        gate=gate_eval.gate,
        units="mm",
        coordinate_system=DRILLING_COORDINATE_SYSTEM,
        canonical_toolpath=canonical_toolpath,
        preview_geometry=preview_geometry,
        warnings=gate_eval.warnings,
        errors=gate_eval.errors,
        issues=gate_eval.issues,
        statistics=statistics,
        metadata=metadata,
    )


# --- Endpoint ---

@router.post("/preview")
def preview_drilling(req: DrillingPreviewRequest) -> DrillingPreviewResponse:
    """
    Preview drilling operation geometry and validate parameters.

    GOVERNED PREVIEW endpoint (5E).
    Returns governed preview response with gate evaluation.

    No G-code generation. No RMOS persistence.
    """
    return generate_drilling_preview(req)
