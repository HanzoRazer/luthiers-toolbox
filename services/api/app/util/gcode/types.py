"""
G-code Module Types

Shared type definitions and data classes for G-code parsing, simulation, and analysis.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# Type aliases
Pt = Tuple[float, float]
Pt3D = Tuple[float, float, float]
Modal = Dict[str, Any]


@dataclass
class Move:
    """Represents a single G-code motion command."""
    n: int
    code: str  # G0/G1/G2/G3 etc.
    start: Pt3D
    end: Pt3D
    feed: Optional[float] = None
    rapid: bool = False
    arc: bool = False
    cw: bool = False
    plane: str = "G17"  # G17 XY, G18 XZ, G19 YZ
    tool: Optional[str] = None
    spindle: Optional[float] = None  # RPM
    raw: str = ""


@dataclass
class Summary:
    """Summary statistics for a G-code program."""
    units: str = "mm"
    absolute: bool = True
    plane: str = "G17"
    line_count: int = 0
    motion_count: int = 0
    rapid_count: int = 0
    feed_count: int = 0
    arc_count: int = 0
    length_total: float = 0.0
    length_rapid: float = 0.0
    length_feed: float = 0.0
    bbox_min: List[float] = field(default_factory=lambda: [float("inf")] * 3)
    bbox_max: List[float] = field(default_factory=lambda: [float("-inf")] * 3)
    feed_min: Optional[float] = None
    feed_max: Optional[float] = None
    rpm_min: Optional[float] = None
    rpm_max: Optional[float] = None
    tools: List[str] = field(default_factory=list)
    planes: List[str] = field(default_factory=lambda: ["G17"])
    notes: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    filename: str = ""
    file_size_bytes: int = 0
    estimated_time_minutes: Optional[float] = None


@dataclass
class MoveSegment:
    """A segment of a G-code move for animation playback."""
    type: str  # "rapid", "cut", "arc_cw", "arc_ccw"
    from_pos: List[float]
    to_pos: List[float]
    feed: float
    duration_ms: float
    line_number: int
    line_text: str
    tool_number: int = 1
    spindle_rpm: float = 0.0
    spindle_on: bool = False


def default_modal() -> Modal:
    """Create default modal state for G-code simulation."""
    return {
        "G": 0,
        "F": 500.0,  # Default feed rate
        "units": 1.0,  # mm (25.4 for inches)
        "plane": 17,  # XY plane
        # Tool state
        "T": 1,
        "pending_tool": 1,
        # Spindle state
        "S": 0.0,
        "spindle_on": False,
        "spindle_dir": "cw",
    }
