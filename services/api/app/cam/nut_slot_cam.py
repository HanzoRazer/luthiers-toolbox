"""
Nut Slot CAM Preview Generator

CAM Dev Order 1: Toolpath JSON preview for nut slot cutting.
CAM Dev Order 2B: Safety hardening with structured issues.
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

from app.core.safety import safety_critical


# -----------------------------------------------------------------------------
# Gate Enum
# -----------------------------------------------------------------------------

class CamGate(str, Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


# -----------------------------------------------------------------------------
# Structured Issue Model (Dev Order 2B)
# -----------------------------------------------------------------------------

class CamIssue(BaseModel):
    """Structured CAM safety issue."""
    code: str
    severity: Literal["yellow", "red"]
    message: str
    field: Optional[str] = None


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
    min_adjacent_spacing_mm: Optional[float] = None
    max_adjacent_spacing_mm: Optional[float] = None
    cutting_move_count: int = 0
    rapid_move_count: int = 0
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
    issues: List[CamIssue] = Field(default_factory=list)
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
    issues: List[CamIssue] = field(default_factory=list)

    def add_error(self, code: str, msg: str, field_name: Optional[str] = None) -> None:
        """Add RED error with structured issue."""
        self.errors.append(msg)
        self.issues.append(CamIssue(code=code, severity="red", message=msg, field=field_name))
        self.gate = CamGate.RED

    def add_warning(self, code: str, msg: str, field_name: Optional[str] = None) -> None:
        """Add YELLOW warning with structured issue."""
        self.warnings.append(msg)
        self.issues.append(CamIssue(code=code, severity="yellow", message=msg, field=field_name))
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
      - edge offsets consume entire nut width
      - explicit position count != num_strings
      - adjacent spacing < 3.0 mm

    YELLOW conditions (warnings):
      - slot_depth_mm > 0.60 * stock_thickness_mm but <= 0.80
      - tool_diameter_mm 90-100% of slot_width_mm
      - edge offsets under 2.0 mm
      - adjacent string spacing 3.0-5.0 mm
      - stock_thickness_mm under 3.0 mm
      - slot_width_mm under 0.20 mm
      - slot_length_mm under 2.0 mm
      - safe_z_mm under 2.0 mm
    """
    eval_result = GateEvaluation()

    # --- RED checks ---

    # Depth vs stock thickness
    if request.slot_depth_mm >= request.stock_thickness_mm:
        eval_result.add_error(
            "SLOT_DEPTH_EXCEEDS_STOCK",
            f"Slot depth ({request.slot_depth_mm}mm) >= stock thickness ({request.stock_thickness_mm}mm)",
            "slot_depth_mm",
        )
    elif request.slot_depth_mm > 0.80 * request.stock_thickness_mm:
        eval_result.add_error(
            "SLOT_DEPTH_EXCEEDS_SAFE_RATIO",
            f"Slot depth ({request.slot_depth_mm}mm) > 80% of stock thickness ({request.stock_thickness_mm}mm)",
            "slot_depth_mm",
        )

    # Tool vs slot width
    if request.tool_diameter_mm > request.slot_width_mm:
        eval_result.add_error(
            "TOOL_DIAMETER_EXCEEDS_SLOT_WIDTH",
            f"Tool diameter ({request.tool_diameter_mm}mm) > slot width ({request.slot_width_mm}mm)",
            "tool_diameter_mm",
        )

    # Negative edge offsets
    if request.edge_offset_bass_mm < 0:
        eval_result.add_error(
            "NEGATIVE_EDGE_OFFSET",
            f"Bass edge offset ({request.edge_offset_bass_mm}mm) is negative",
            "edge_offset_bass_mm",
        )
    if request.edge_offset_treble_mm < 0:
        eval_result.add_error(
            "NEGATIVE_EDGE_OFFSET",
            f"Treble edge offset ({request.edge_offset_treble_mm}mm) is negative",
            "edge_offset_treble_mm",
        )

    # Edge offsets consume entire nut width
    total_edge_offset = request.edge_offset_bass_mm + request.edge_offset_treble_mm
    if total_edge_offset >= request.nut_width_mm:
        eval_result.add_error(
            "EDGE_OFFSETS_CONSUME_NUT_WIDTH",
            f"Edge offsets ({total_edge_offset}mm) >= nut width ({request.nut_width_mm}mm)",
            "edge_offset_bass_mm",
        )

    # Explicit position count mismatch
    if request.string_positions_x_mm is not None:
        if len(request.string_positions_x_mm) != request.num_strings:
            eval_result.add_error(
                "POSITION_COUNT_MISMATCH",
                f"Explicit position count ({len(request.string_positions_x_mm)}) != num_strings ({request.num_strings})",
                "string_positions_x_mm",
            )

    # Positions within nut width
    for i, pos in enumerate(string_positions):
        if pos < 0:
            eval_result.add_error(
                "STRING_POSITION_OUT_OF_BOUNDS",
                f"String {i+1} position ({pos}mm) is negative",
                "string_positions_x_mm",
            )
        elif pos > request.nut_width_mm:
            eval_result.add_error(
                "STRING_POSITION_OUT_OF_BOUNDS",
                f"String {i+1} position ({pos}mm) exceeds nut width ({request.nut_width_mm}mm)",
                "string_positions_x_mm",
            )

    # Positions strictly increasing
    for i in range(1, len(string_positions)):
        if string_positions[i] <= string_positions[i - 1]:
            eval_result.add_error(
                "POSITIONS_NOT_INCREASING",
                f"String positions not strictly increasing: "
                f"position {i} ({string_positions[i-1]}mm) >= position {i+1} ({string_positions[i]}mm)",
                "string_positions_x_mm",
            )

    # Adjacent spacing - calculate once, use for both RED and YELLOW
    spacings = []
    for i in range(1, len(string_positions)):
        spacing = string_positions[i] - string_positions[i - 1]
        spacings.append(spacing)
        if spacing <= 0:
            eval_result.add_error(
                "ADJACENT_SPACING_INVALID",
                f"String {i} to {i+1} spacing ({spacing:.2f}mm) <= 0",
                "string_positions_x_mm",
            )
        elif spacing < 3.0:
            eval_result.add_error(
                "ADJACENT_STRING_SPACING_CRITICAL",
                f"String {i} to {i+1} spacing ({spacing:.2f}mm) < 3.0mm (collision risk)",
                "string_positions_x_mm",
            )

    # --- YELLOW checks ---

    # Depth warnings (only if not already RED)
    depth_ratio = request.slot_depth_mm / request.stock_thickness_mm
    if 0.60 < depth_ratio <= 0.80:
        eval_result.add_warning(
            "SLOT_DEPTH_HIGH",
            f"Slot depth ({request.slot_depth_mm}mm) is 60-80% of stock thickness",
            "slot_depth_mm",
        )

    # Tool diameter close to slot width
    if request.slot_width_mm > 0:
        tool_ratio = request.tool_diameter_mm / request.slot_width_mm
        if 0.90 <= tool_ratio <= 1.0:
            eval_result.add_warning(
                "TOOL_SLOT_TIGHT_FIT",
                f"Tool diameter is {tool_ratio*100:.0f}% of slot width (tight fit)",
                "tool_diameter_mm",
            )

    # Edge offsets under 2mm
    if 0 <= request.edge_offset_bass_mm < 2.0:
        eval_result.add_warning(
            "EDGE_OFFSET_LOW",
            f"Bass edge offset ({request.edge_offset_bass_mm}mm) under 2.0mm",
            "edge_offset_bass_mm",
        )
    if 0 <= request.edge_offset_treble_mm < 2.0:
        eval_result.add_warning(
            "EDGE_OFFSET_LOW",
            f"Treble edge offset ({request.edge_offset_treble_mm}mm) under 2.0mm",
            "edge_offset_treble_mm",
        )

    # Adjacent string spacing 3.0-5.0mm (warning, not error)
    for i, spacing in enumerate(spacings):
        if 3.0 <= spacing < 5.0:
            eval_result.add_warning(
                "ADJACENT_STRING_SPACING_TIGHT",
                f"String {i+1} to {i+2} spacing ({spacing:.2f}mm) under 5.0mm",
                "string_positions_x_mm",
            )

    # Stock thickness warning
    if request.stock_thickness_mm < 3.0:
        eval_result.add_warning(
            "STOCK_THIN",
            f"Stock thickness ({request.stock_thickness_mm}mm) under 3.0mm",
            "stock_thickness_mm",
        )

    # Slot width warning
    if request.slot_width_mm < 0.20:
        eval_result.add_warning(
            "SLOT_WIDTH_NARROW",
            f"Slot width ({request.slot_width_mm}mm) under 0.20mm",
            "slot_width_mm",
        )

    # Slot length warning
    if request.slot_length_mm < 2.0:
        eval_result.add_warning(
            "SLOT_LENGTH_SHORT",
            f"Slot length ({request.slot_length_mm}mm) under 2.0mm",
            "slot_length_mm",
        )

    # Safe Z warning
    if request.safe_z_mm < 2.0:
        eval_result.add_warning(
            "SAFE_Z_LOW",
            f"Safe Z ({request.safe_z_mm}mm) under 2.0mm; verify clearance manually",
            "safe_z_mm",
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
# Preview Integrity Checker (Dev Order 2B)
# -----------------------------------------------------------------------------

@safety_critical
def validate_toolpath_integrity(
    toolpaths: List[SlotToolpath],
    request: NutSlotPreviewRequest,
    eval_result: GateEvaluation,
) -> None:
    """
    Validate generated toolpaths for internal consistency.

    Checks:
      - Every move has x, y, z
      - Move sequence is valid (rapid, plunge, linear, retract)
      - Slot count equals num_strings
      - String numbers are 1-based and sequential
      - Slot indices are 0-based and sequential
      - All X values within nut width
      - All Y values within [0, slot_length_mm]
      - Cutting Z values within bounds
      - Retract/rapid Z equals safe_z_mm

    If any check fails, adds RED error.
    """
    # Slot count check
    if len(toolpaths) != request.num_strings:
        eval_result.add_error(
            "INTEGRITY_SLOT_COUNT_MISMATCH",
            f"Toolpath slot count ({len(toolpaths)}) != num_strings ({request.num_strings})",
        )

    valid_sequence = ["rapid", "plunge", "linear", "retract"]

    for tp in toolpaths:
        # Check slot_index is 0-based and sequential
        expected_index = tp.string_number - 1
        if tp.slot_index != expected_index:
            eval_result.add_error(
                "INTEGRITY_SLOT_INDEX_INVALID",
                f"Slot {tp.slot_index} has string_number {tp.string_number} (expected slot_index={expected_index})",
            )

        # Check string_number is 1-based
        if tp.string_number < 1 or tp.string_number > request.num_strings:
            eval_result.add_error(
                "INTEGRITY_STRING_NUMBER_INVALID",
                f"String number {tp.string_number} out of range [1, {request.num_strings}]",
            )

        # Check move sequence
        if len(tp.moves) != 4:
            eval_result.add_error(
                "INTEGRITY_MOVE_COUNT_INVALID",
                f"Slot {tp.slot_index} has {len(tp.moves)} moves (expected 4)",
            )
        else:
            for i, move in enumerate(tp.moves):
                if move.type != valid_sequence[i]:
                    eval_result.add_error(
                        "INTEGRITY_MOVE_SEQUENCE_INVALID",
                        f"Slot {tp.slot_index} move {i} is '{move.type}' (expected '{valid_sequence[i]}')",
                    )

        # Check all moves have valid coordinates
        for i, move in enumerate(tp.moves):
            # X within nut width
            if move.x < 0 or move.x > request.nut_width_mm:
                eval_result.add_error(
                    "INTEGRITY_X_OUT_OF_BOUNDS",
                    f"Slot {tp.slot_index} move {i}: X={move.x}mm outside [0, {request.nut_width_mm}]",
                )

            # Y within slot length
            if move.y < 0 or move.y > request.slot_length_mm:
                eval_result.add_error(
                    "INTEGRITY_Y_OUT_OF_BOUNDS",
                    f"Slot {tp.slot_index} move {i}: Y={move.y}mm outside [0, {request.slot_length_mm}]",
                )

            # Z bounds check
            if move.type in ("plunge", "linear"):
                # Cutting moves must be at or above stock bottom
                min_z = -request.stock_thickness_mm
                if move.z < min_z:
                    eval_result.add_error(
                        "INTEGRITY_Z_BELOW_STOCK",
                        f"Slot {tp.slot_index} move {i}: Z={move.z}mm below stock bottom ({min_z}mm)",
                    )
                if move.z > 0:
                    eval_result.add_error(
                        "INTEGRITY_CUTTING_Z_POSITIVE",
                        f"Slot {tp.slot_index} move {i}: cutting Z={move.z}mm is positive (should be <= 0)",
                    )
            elif move.type in ("rapid", "retract"):
                # Rapid/retract should be at safe Z
                if abs(move.z - request.safe_z_mm) > 0.001:
                    eval_result.add_error(
                        "INTEGRITY_SAFE_Z_MISMATCH",
                        f"Slot {tp.slot_index} move {i}: Z={move.z}mm != safe_z ({request.safe_z_mm}mm)",
                    )


# -----------------------------------------------------------------------------
# Statistics Calculator (Dev Order 2B)
# -----------------------------------------------------------------------------

def calculate_statistics(
    toolpaths: List[SlotToolpath],
    string_positions: List[float],
    request: NutSlotPreviewRequest,
) -> PreviewStatistics:
    """Calculate preview statistics including spacing and move counts."""
    # Count move types
    cutting_moves = 0
    rapid_moves = 0
    for tp in toolpaths:
        for move in tp.moves:
            if move.type in ("plunge", "linear"):
                cutting_moves += 1
            elif move.type in ("rapid", "retract"):
                rapid_moves += 1

    # Calculate adjacent spacings
    min_spacing = None
    max_spacing = None
    if len(string_positions) > 1:
        spacings = [
            string_positions[i] - string_positions[i - 1]
            for i in range(1, len(string_positions))
        ]
        min_spacing = round(min(spacings), 3)
        max_spacing = round(max(spacings), 3)

    return PreviewStatistics(
        total_slots=len(toolpaths),
        max_depth_mm=request.slot_depth_mm,
        min_adjacent_spacing_mm=min_spacing,
        max_adjacent_spacing_mm=max_spacing,
        cutting_move_count=cutting_moves,
        rapid_move_count=rapid_moves,
        estimated_time_s=None,
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
        string_positions = list(request.string_positions_x_mm)
    else:
        string_positions = generate_string_positions(
            num_strings=request.num_strings,
            nut_width_mm=request.nut_width_mm,
            edge_offset_treble_mm=request.edge_offset_treble_mm,
            edge_offset_bass_mm=request.edge_offset_bass_mm,
        )

    # Evaluate gate (input validation)
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

    # Validate toolpath integrity (Dev Order 2B)
    validate_toolpath_integrity(toolpaths, request, gate_eval)

    # Calculate statistics (Dev Order 2B)
    statistics = calculate_statistics(toolpaths, string_positions, request)

    # Build response
    return NutSlotPreviewResponse(
        gate=gate_eval.gate,
        coordinate_system=CoordinateSystem(),
        tool=ToolMetadata(diameter_mm=request.tool_diameter_mm),
        toolpaths=toolpaths,
        warnings=gate_eval.warnings,
        errors=gate_eval.errors,
        issues=gate_eval.issues,
        statistics=statistics,
    )
