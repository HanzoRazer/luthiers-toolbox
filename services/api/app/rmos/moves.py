"""
RMOS Canonical Move Structures

LANE: OPERATION (infrastructure)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md, ADR-003

This module defines the canonical GCodeMove structure used by all OPERATION lane
CAM endpoints. It provides:

1. **GCodeMove** - Canonical move dict structure (TypedDict)
2. **MoveType** - Enumeration of move types
3. **move_to_gcode()** - Convert single move to G-code string
4. **moves_to_gcode()** - Convert move list to G-code program

DESIGN PHILOSOPHY:
------------------
All CAM endpoints should generate List[GCodeMove] internally, then use a
post-processor to convert to dialect-specific G-code. This enables:

- Deterministic replay (moves are hashable/serializable)
- Multi-dialect support (GRBL, FANUC, LinuxCNC, etc.)
- Artifact persistence (moves stored as JSON)
- Testing (compare move lists, not G-code strings)

MOVE STRUCTURE:
---------------
```python
GCodeMove = {
    "type": MoveType,           # Required: "rapid", "linear", "cw_arc", "ccw_arc", "dwell"
    "x": Optional[float],       # X coordinate (mm)
    "y": Optional[float],       # Y coordinate (mm)
    "z": Optional[float],       # Z coordinate (mm)
    "i": Optional[float],       # Arc center I offset (I/J mode)
    "j": Optional[float],       # Arc center J offset (I/J mode)
    "r": Optional[float],       # Arc radius (R mode)
    "f": Optional[float],       # Feed rate (mm/min)
    "p": Optional[float],       # Dwell time (milliseconds)
    "comment": Optional[str],   # Inline comment
}
```

COMPATIBILITY:
--------------
This structure is backward-compatible with:
- SawToolpathMove (saw_lab/models.py)
- helical_core.py move dicts
- GRBL/FANUC post-processor input format
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from typing_extensions import TypedDict, NotRequired
from pydantic import BaseModel, Field


class MoveType(str, Enum):
    """Canonical move types for G-code generation."""
    RAPID = "rapid"         # G0 - Rapid positioning
    LINEAR = "linear"       # G1 - Linear interpolation
    CW_ARC = "cw_arc"       # G2 - Clockwise arc
    CCW_ARC = "ccw_arc"     # G3 - Counter-clockwise arc
    DWELL = "dwell"         # G4 - Dwell/pause


class GCodeMove(TypedDict, total=False):
    """
    Canonical G-code move structure.

    All fields are optional except 'type'. A minimal rapid move:
        {"type": "rapid", "x": 10.0, "y": 20.0}

    Arc moves require either I/J (center offset) or R (radius):
        {"type": "cw_arc", "x": 10, "y": 0, "i": 5, "j": 0, "f": 1000}
        {"type": "ccw_arc", "x": 10, "y": 0, "r": 5, "f": 1000}
    """
    type: str               # Required: MoveType value
    x: float                # X coordinate (mm)
    y: float                # Y coordinate (mm)
    z: float                # Z coordinate (mm)
    i: float                # Arc center I offset from current X
    j: float                # Arc center J offset from current Y
    r: float                # Arc radius (alternative to I/J)
    f: float                # Feed rate (mm/min)
    p: float                # Dwell time (milliseconds)
    comment: str            # Inline comment


class GCodeMoveModel(BaseModel):
    """
    Pydantic model for GCodeMove validation and serialization.

    Use this when you need:
    - Schema validation (API requests)
    - JSON serialization (artifact storage)
    - Type checking at runtime

    For internal toolpath generation, use the GCodeMove TypedDict directly.
    """
    type: MoveType = Field(..., description="Move type (rapid, linear, cw_arc, ccw_arc, dwell)")
    x: Optional[float] = Field(None, description="X coordinate (mm)")
    y: Optional[float] = Field(None, description="Y coordinate (mm)")
    z: Optional[float] = Field(None, description="Z coordinate (mm)")
    i: Optional[float] = Field(None, description="Arc center I offset (mm)")
    j: Optional[float] = Field(None, description="Arc center J offset (mm)")
    r: Optional[float] = Field(None, description="Arc radius (mm)")
    f: Optional[float] = Field(None, ge=0, description="Feed rate (mm/min)")
    p: Optional[float] = Field(None, ge=0, description="Dwell time (ms)")
    comment: Optional[str] = Field(None, description="Inline comment")

    def to_dict(self) -> GCodeMove:
        """Convert to GCodeMove TypedDict."""
        result: Dict[str, Any] = {"type": self.type.value}
        for field in ["x", "y", "z", "i", "j", "r", "f", "p", "comment"]:
            val = getattr(self, field)
            if val is not None:
                result[field] = val
        return result  # type: ignore


# G-code command mapping
GCODE_COMMANDS = {
    MoveType.RAPID: "G0",
    MoveType.LINEAR: "G1",
    MoveType.CW_ARC: "G2",
    MoveType.CCW_ARC: "G3",
    MoveType.DWELL: "G4",
}

# Reverse mapping for parsing
GCODE_TO_MOVETYPE = {
    "G0": MoveType.RAPID,
    "G00": MoveType.RAPID,
    "G1": MoveType.LINEAR,
    "G01": MoveType.LINEAR,
    "G2": MoveType.CW_ARC,
    "G02": MoveType.CW_ARC,
    "G3": MoveType.CCW_ARC,
    "G03": MoveType.CCW_ARC,
    "G4": MoveType.DWELL,
    "G04": MoveType.DWELL,
}


def _fmt(value: float, decimals: int = 3) -> str:
    """Format coordinate value, stripping trailing zeros."""
    formatted = f"{value:.{decimals}f}"
    return formatted.rstrip('0').rstrip('.') if '.' in formatted else formatted


def move_to_gcode(
    move: GCodeMove,
    *,
    use_r_mode: bool = False,
    dwell_in_seconds: bool = False,
) -> str:
    """
    Convert a single GCodeMove to G-code string.

    Args:
        move: GCodeMove dictionary
        use_r_mode: If True, prefer R word for arcs (Haas). If False, use I/J (GRBL).
        dwell_in_seconds: If True, G4 uses S (seconds). If False, G4 uses P (ms).

    Returns:
        G-code line (e.g., "G1 X10.0 Y20.0 F1000")

    Example:
        >>> move_to_gcode({"type": "linear", "x": 10, "y": 20, "f": 1000})
        'G1 X10 Y20 F1000'

        >>> move_to_gcode({"type": "cw_arc", "x": 10, "y": 0, "i": 5, "j": 0, "f": 800})
        'G2 X10 Y0 I5 J0 F800'
    """
    move_type_str = move.get("type", "linear")

    # Handle string or enum
    if isinstance(move_type_str, MoveType):
        move_type = move_type_str
    else:
        move_type = MoveType(move_type_str)

    parts = [GCODE_COMMANDS[move_type]]

    # Handle dwell specially
    if move_type == MoveType.DWELL:
        dwell_ms = move.get("p", 0)
        if dwell_in_seconds:
            parts.append(f"S{_fmt(dwell_ms / 1000.0)}")
        else:
            parts.append(f"P{int(dwell_ms)}")
        if move.get("comment"):
            parts.append(f"; {move['comment']}")
        return " ".join(parts)

    # Coordinates
    if "x" in move:
        parts.append(f"X{_fmt(move['x'])}")
    if "y" in move:
        parts.append(f"Y{_fmt(move['y'])}")
    if "z" in move:
        parts.append(f"Z{_fmt(move['z'])}")

    # Arc parameters
    if move_type in (MoveType.CW_ARC, MoveType.CCW_ARC):
        if use_r_mode and "r" in move:
            parts.append(f"R{_fmt(move['r'])}")
        else:
            if "i" in move:
                parts.append(f"I{_fmt(move['i'])}")
            if "j" in move:
                parts.append(f"J{_fmt(move['j'])}")

    # Feed rate (not for rapid moves)
    if move_type != MoveType.RAPID and "f" in move:
        parts.append(f"F{_fmt(move['f'])}")

    # Comment
    if move.get("comment"):
        parts.append(f"; {move['comment']}")

    return " ".join(parts)


def moves_to_gcode(
    moves: List[GCodeMove],
    *,
    use_r_mode: bool = False,
    dwell_in_seconds: bool = False,
    include_line_numbers: bool = False,
    line_number_start: int = 10,
    line_number_increment: int = 10,
) -> List[str]:
    """
    Convert a list of GCodeMoves to G-code lines.

    Args:
        moves: List of GCodeMove dictionaries
        use_r_mode: If True, prefer R word for arcs
        dwell_in_seconds: If True, G4 uses S (seconds)
        include_line_numbers: If True, prefix lines with N-codes (FANUC style)
        line_number_start: Starting N-code number
        line_number_increment: N-code increment per line

    Returns:
        List of G-code lines

    Example:
        >>> moves = [
        ...     {"type": "rapid", "z": 5},
        ...     {"type": "rapid", "x": 0, "y": 0},
        ...     {"type": "linear", "z": -5, "f": 200},
        ... ]
        >>> moves_to_gcode(moves)
        ['G0 Z5', 'G0 X0 Y0', 'G1 Z-5 F200']
    """
    lines = []
    line_num = line_number_start

    for move in moves:
        gcode = move_to_gcode(
            move,
            use_r_mode=use_r_mode,
            dwell_in_seconds=dwell_in_seconds,
        )

        if include_line_numbers:
            gcode = f"N{line_num} {gcode}"
            line_num += line_number_increment

        lines.append(gcode)

    return lines


def legacy_move_to_canonical(move: Dict[str, Any]) -> GCodeMove:
    """
    Convert legacy move dict (helical_core style) to canonical GCodeMove.

    Legacy format uses "code" field (G0, G1, G2, G3) instead of "type".

    Args:
        move: Legacy move dict with "code" field

    Returns:
        Canonical GCodeMove with "type" field

    Example:
        >>> legacy_move_to_canonical({"code": "G2", "x": 10, "y": 0, "i": 5, "j": 0})
        {"type": "cw_arc", "x": 10, "y": 0, "i": 5, "j": 0}
    """
    result: Dict[str, Any] = {}

    # Convert code to type
    code = move.get("code", "G1")
    if code in GCODE_TO_MOVETYPE:
        result["type"] = GCODE_TO_MOVETYPE[code].value
    else:
        # Fallback: if already has type, use it
        result["type"] = move.get("type", MoveType.LINEAR.value)

    # Copy coordinate fields
    for field in ["x", "y", "z", "i", "j", "r", "f", "p", "comment"]:
        if field in move:
            result[field] = move[field]

    return result  # type: ignore


def canonical_to_legacy_move(move: GCodeMove) -> Dict[str, Any]:
    """
    Convert canonical GCodeMove to legacy format (for backward compatibility).

    Args:
        move: Canonical GCodeMove with "type" field

    Returns:
        Legacy move dict with "code" field
    """
    result: Dict[str, Any] = {}

    # Convert type to code
    move_type_str = move.get("type", "linear")
    if isinstance(move_type_str, MoveType):
        move_type = move_type_str
    else:
        move_type = MoveType(move_type_str)

    result["code"] = GCODE_COMMANDS[move_type]

    # Copy coordinate fields
    for field in ["x", "y", "z", "i", "j", "r", "f", "p", "comment"]:
        if field in move:
            result[field] = move[field]

    return result


# Convenience constructors
def rapid(
    x: Optional[float] = None,
    y: Optional[float] = None,
    z: Optional[float] = None,
    comment: Optional[str] = None,
) -> GCodeMove:
    """Create a rapid move (G0)."""
    move: Dict[str, Any] = {"type": MoveType.RAPID.value}
    if x is not None:
        move["x"] = x
    if y is not None:
        move["y"] = y
    if z is not None:
        move["z"] = z
    if comment is not None:
        move["comment"] = comment
    return move  # type: ignore


def linear(
    x: Optional[float] = None,
    y: Optional[float] = None,
    z: Optional[float] = None,
    f: Optional[float] = None,
    comment: Optional[str] = None,
) -> GCodeMove:
    """Create a linear move (G1)."""
    move: Dict[str, Any] = {"type": MoveType.LINEAR.value}
    if x is not None:
        move["x"] = x
    if y is not None:
        move["y"] = y
    if z is not None:
        move["z"] = z
    if f is not None:
        move["f"] = f
    if comment is not None:
        move["comment"] = comment
    return move  # type: ignore


def cw_arc(
    x: float,
    y: float,
    i: Optional[float] = None,
    j: Optional[float] = None,
    r: Optional[float] = None,
    z: Optional[float] = None,
    f: Optional[float] = None,
    comment: Optional[str] = None,
) -> GCodeMove:
    """Create a clockwise arc (G2)."""
    move: Dict[str, Any] = {"type": MoveType.CW_ARC.value, "x": x, "y": y}
    if i is not None:
        move["i"] = i
    if j is not None:
        move["j"] = j
    if r is not None:
        move["r"] = r
    if z is not None:
        move["z"] = z
    if f is not None:
        move["f"] = f
    if comment is not None:
        move["comment"] = comment
    return move  # type: ignore


def ccw_arc(
    x: float,
    y: float,
    i: Optional[float] = None,
    j: Optional[float] = None,
    r: Optional[float] = None,
    z: Optional[float] = None,
    f: Optional[float] = None,
    comment: Optional[str] = None,
) -> GCodeMove:
    """Create a counter-clockwise arc (G3)."""
    move: Dict[str, Any] = {"type": MoveType.CCW_ARC.value, "x": x, "y": y}
    if i is not None:
        move["i"] = i
    if j is not None:
        move["j"] = j
    if r is not None:
        move["r"] = r
    if z is not None:
        move["z"] = z
    if f is not None:
        move["f"] = f
    if comment is not None:
        move["comment"] = comment
    return move  # type: ignore


def dwell(ms: float, comment: Optional[str] = None) -> GCodeMove:
    """Create a dwell command (G4)."""
    move: Dict[str, Any] = {"type": MoveType.DWELL.value, "p": ms}
    if comment is not None:
        move["comment"] = comment
    return move  # type: ignore
