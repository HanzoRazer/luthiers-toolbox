"""
Nut Slot CAM Preview Generator

CAM Dev Order 1: Toolpath JSON preview for nut slot cutting.
Software proof-of-concept only — not for shop use.

Coordinate system:
  - Origin: left face of nut (bass side at high X)
  - X axis: string-to-string direction along nut
  - Y axis: slot length direction
  - Z-zero: top of stock
  - Units: mm

Gate logic:
  - GREEN: all parameters within safe bounds
  - YELLOW: marginal parameters (warnings)
  - RED: unsafe parameters (blocks export)

No G-code output. No machine-specific postprocessing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# Gate Enum
# -----------------------------------------------------------------------------

class CamGate(str, Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


# -----------------------------------------------------------------------------
# Request Model
# -----------------------------------------------------------------------------

class NutSlotPreviewRequest(BaseModel):
    """Request for nut slot CAM preview."""

    nut_width_mm: float = Field(..., gt=0, description="Total nut width in mm")
    num_strings: int = Field(..., ge=1, le=12, description="Number of strings (1-12)")
    edge_offset_bass_mm: float = Field(..., ge=0, description="Offset from bass edge to first string")
    edge_offset_treble_mm: float = Field(..., ge=0, description="Offset from treble edge to last string")
    string_positions_x_mm: Optional[List[float]] = Field(
        None, description="Explicit X positions for each string (overrides calculated)"
    )
    slot_length_mm: float = Field(..., gt=0, description="Length of each slot (Y direction)")
    slot_depth_mm: float = Field(..., gt=0, description="Depth of each slot (Z direction)")
    slot_width_mm: float = Field(..., gt=0, description="Width of each slot")
    stock_thickness_mm: float = Field(..., gt=0, description="Thickness of nut blank")
    tool_diameter_mm: float = Field(..., gt=0, description="Cutting tool diameter")
    safe_z_mm: float = Field(default=5.0, gt=0, description="Safe Z height for rapids")


# -----------------------------------------------------------------------------
# Toolpath Move
# -----------------------------------------------------------------------------

class ToolpathMove(BaseModel):
    """A single toolpath move."""
    type: Literal["rapid", "plunge", "linear", "retract"]
    x: float
    y: float
    z: float


# -----------------------------------------------------------------------------
# Slot Toolpath
# -----------------------------------------------------------------------------

class SlotToolpath(BaseModel):
    """Toolpath for a single nut slot."""
    slot_index: int
    string_number: int
    x_mm: float
    slot_width_mm: float
    slot_depth_mm: float
    moves: List[ToolpathMove]


# -----------------------------------------------------------------------------
# Coordinate System Metadata
# -----------------------------------------------------------------------------

class CoordinateSystem(BaseModel):
    """Coordinate system definition."""
    origin: str = "local_nut_left_face"
    z_zero: str = "top_of_stock"
    x_axis: str = "string_to_string"
    y_axis: str = "slot_length"


# -----------------------------------------------------------------------------
# Tool Metadata
# -----------------------------------------------------------------------------

class ToolMetadata(BaseModel):
    """Tool information."""
    diameter_mm: float


# -----------------------------------------------------------------------------
# Statistics
# -----------------------------------------------------------------------------

class PreviewStatistics(BaseModel):
    """Preview statistics."""
    total_slots: int
    max_depth_mm: float
    estimated_time_s: Optional[float] = None


# -----------------------------------------------------------------------------
# Response Model
# -----------------------------------------------------------------------------

class NutSlotPreviewResponse(BaseModel):
    """Response for nut slot CAM preview."""
    operation: str = "nut_slot_preview"
    status: str = "experimental"
    gate: CamGate
    units: str = "mm"
    coordinate_system: CoordinateSystem
    machine_profile: str = "generic_cnc_mm_preview_only"
    tool: ToolMetadata
    toolpaths: List[SlotToolpath]
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    statistics: PreviewStatistics


# -----------------------------------------------------------------------------
# Gate Evaluation
# -----------------------------------------------------------------------------

@dataclass
class GateEvaluation:
    """Result of gate evaluation."""
    gate: CamGate = CamGate.GREEN
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)
        self.gate = CamGate.RED

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)
        if self.gate != CamGate.RED:
            self.gate = CamGate.YELLOW


def evaluate_gate(
    request: NutSlotPreviewRequest,
    string_positions: List[float],
) -> GateEvaluation:
    """
    Evaluate CAM safety gate for nut slot preview.

    RED conditions (block export):
      - slot_depth_mm >= stock_thickness_mm
      - slot_depth_mm > 0.80 * stock_thickness_mm
      - tool_diameter_mm > slot_width_mm
      - positions outside [0, nut_width_mm]
      - positions not strictly increasing
      - slot_length_mm <= 0 (already validated by Pydantic)
      - safe_z_mm <= 0 (already validated by Pydantic)

    YELLOW conditions (warnings):
      - slot_depth_mm > 0.60 * stock_thickness_mm but <= 0.80
      - tool_diameter_mm 90-100% of slot_width_mm
      - edge offsets under 2.0 mm
      - adjacent string spacing under 5.0 mm
      - stock_thickness_mm under 3.0 mm
      - slot_width_mm under 0.20 mm
      - slot_length_mm under 2.0 mm
    """
    eval_result = GateEvaluation()

    # --- RED checks ---

    # Depth vs stock thickness
    if request.slot_depth_mm >= request.stock_thickness_mm:
        eval_result.add_error(
            f"Slot depth ({request.slot_depth_mm}mm) >= stock thickness ({request.stock_thickness_mm}mm)"
        )
    elif request.slot_depth_mm > 0.80 * request.stock_thickness_mm:
        eval_result.add_error(
            f"Slot depth ({request.slot_depth_mm}mm) > 80% of stock thickness ({request.stock_thickness_mm}mm)"
        )

    # Tool vs slot width
    if request.tool_diameter_mm > request.slot_width_mm:
        eval_result.add_error(
            f"Tool diameter ({request.tool_diameter_mm}mm) > slot width ({request.slot_width_mm}mm)"
        )

    # Positions within nut width
    for i, pos in enumerate(string_positions):
        if pos < 0:
            eval_result.add_error(f"String {i+1} position ({pos}mm) is negative")
        elif pos > request.nut_width_mm:
            eval_result.add_error(
                f"String {i+1} position ({pos}mm) exceeds nut width ({request.nut_width_mm}mm)"
            )

    # Positions strictly increasing
    for i in range(1, len(string_positions)):
        if string_positions[i] <= string_positions[i - 1]:
            eval_result.add_error(
                f"String positions not strictly increasing: "
                f"position {i} ({string_positions[i-1]}mm) >= position {i+1} ({string_positions[i]}mm)"
            )

    # --- YELLOW checks (only if not already RED) ---

    # Depth warnings
    if request.slot_depth_mm > 0.60 * request.stock_thickness_mm:
        if request.slot_depth_mm <= 0.80 * request.stock_thickness_mm:
            eval_result.add_warning(
                f"Slot depth ({request.slot_depth_mm}mm) is 60-80% of stock thickness"
            )

    # Tool diameter close to slot width
    tool_ratio = request.tool_diameter_mm / request.slot_width_mm
    if 0.90 <= tool_ratio <= 1.0:
        eval_result.add_warning(
            f"Tool diameter is {tool_ratio*100:.0f}% of slot width (tight fit)"
        )

    # Edge offsets
    if request.edge_offset_bass_mm < 2.0:
        eval_result.add_warning(
            f"Bass edge offset ({request.edge_offset_bass_mm}mm) under 2.0mm"
        )
    if request.edge_offset_treble_mm < 2.0:
        eval_result.add_warning(
            f"Treble edge offset ({request.edge_offset_treble_mm}mm) under 2.0mm"
        )

    # Adjacent string spacing
    for i in range(1, len(string_positions)):
        spacing = string_positions[i] - string_positions[i - 1]
        if spacing < 5.0:
            eval_result.add_warning(
                f"String {i} to {i+1} spacing ({spacing:.2f}mm) under 5.0mm"
            )

    # Stock thickness warning
    if request.stock_thickness_mm < 3.0:
        eval_result.add_warning(
            f"Stock thickness ({request.stock_thickness_mm}mm) under 3.0mm"
        )

    # Slot width warning
    if request.slot_width_mm < 0.20:
        eval_result.add_warning(
            f"Slot width ({request.slot_width_mm}mm) under 0.20mm"
        )

    # Slot length warning
    if request.slot_length_mm < 2.0:
        eval_result.add_warning(
            f"Slot length ({request.slot_length_mm}mm) under 2.0mm"
        )

    return eval_result


# -----------------------------------------------------------------------------
# String Position Generator
# -----------------------------------------------------------------------------

def generate_string_positions(
    num_strings: int,
    nut_width_mm: float,
    edge_offset_treble_mm: float,
    edge_offset_bass_mm: float,
) -> List[float]:
    """
    Generate evenly spaced string positions.

    String 1 (high E) is at treble side (low X).
    String N (bass) is at bass side (high X).

    Returns X positions in mm from left face of nut.
    """
    if num_strings == 1:
        return [edge_offset_treble_mm]

    # Available width for string spacing
    available_width = nut_width_mm - edge_offset_treble_mm - edge_offset_bass_mm

    # Spacing between strings
    spacing = available_width / (num_strings - 1)

    # Generate positions from treble to bass
    positions = []
    for i in range(num_strings):
        pos = edge_offset_treble_mm + (i * spacing)
        positions.append(round(pos, 3))

    return positions


# -----------------------------------------------------------------------------
# Toolpath Generator
# -----------------------------------------------------------------------------

def generate_slot_toolpath(
    slot_index: int,
    string_number: int,
    x_position_mm: float,
    slot_depth_mm: float,
    slot_width_mm: float,
    slot_length_mm: float,
    safe_z_mm: float,
) -> SlotToolpath:
    """
    Generate toolpath for a single nut slot.

    Sequence:
      1. Rapid to slot start position at safe Z
      2. Plunge to cutting depth
      3. Linear move along slot length
      4. Retract to safe Z
    """
    moves = [
        ToolpathMove(type="rapid", x=round(x_position_mm, 3), y=0, z=round(safe_z_mm, 3)),
        ToolpathMove(type="plunge", x=round(x_position_mm, 3), y=0, z=round(-slot_depth_mm, 3)),
        ToolpathMove(type="linear", x=round(x_position_mm, 3), y=round(slot_length_mm, 3), z=round(-slot_depth_mm, 3)),
        ToolpathMove(type="retract", x=round(x_position_mm, 3), y=round(slot_length_mm, 3), z=round(safe_z_mm, 3)),
    ]

    return SlotToolpath(
        slot_index=slot_index,
        string_number=string_number,
        x_mm=round(x_position_mm, 3),
        slot_width_mm=slot_width_mm,
        slot_depth_mm=slot_depth_mm,
        moves=moves,
    )


# -----------------------------------------------------------------------------
# Main Preview Generator
# -----------------------------------------------------------------------------

def generate_nut_slot_preview(request: NutSlotPreviewRequest) -> NutSlotPreviewResponse:
    """
    Generate nut slot CAM preview with toolpath JSON.

    This is a software proof-of-concept only.
    No G-code output. No machine-specific postprocessing.
    """
    # Determine string positions
    if request.string_positions_x_mm is not None:
        string_positions = request.string_positions_x_mm
    else:
        string_positions = generate_string_positions(
            num_strings=request.num_strings,
            nut_width_mm=request.nut_width_mm,
            edge_offset_treble_mm=request.edge_offset_treble_mm,
            edge_offset_bass_mm=request.edge_offset_bass_mm,
        )

    # Evaluate gate
    gate_eval = evaluate_gate(request, string_positions)

    # Generate toolpaths (even if RED, for preview purposes)
    toolpaths = []
    for i, x_pos in enumerate(string_positions):
        toolpath = generate_slot_toolpath(
            slot_index=i,
            string_number=i + 1,
            x_position_mm=x_pos,
            slot_depth_mm=request.slot_depth_mm,
            slot_width_mm=request.slot_width_mm,
            slot_length_mm=request.slot_length_mm,
            safe_z_mm=request.safe_z_mm,
        )
        toolpaths.append(toolpath)

    # Build response
    return NutSlotPreviewResponse(
        gate=gate_eval.gate,
        coordinate_system=CoordinateSystem(),
        tool=ToolMetadata(diameter_mm=request.tool_diameter_mm),
        toolpaths=toolpaths,
        warnings=gate_eval.warnings,
        errors=gate_eval.errors,
        statistics=PreviewStatistics(
            total_slots=len(toolpaths),
            max_depth_mm=request.slot_depth_mm,
            estimated_time_s=None,
        ),
    )
