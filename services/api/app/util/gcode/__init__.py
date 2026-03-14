"""
G-code Module

Comprehensive G-code parsing, simulation, and analysis toolkit.

Sub-modules
-----------
- types: Data classes (Move, Summary, Modal)
- lexer: Tokenization and comment stripping
- geometry: Arc calculations and interpolation
- simulator: State machine simulation
- reader: File parsing and validation
- render: SVG visualization
- report: Human-readable reports and CSV/JSON export
- cli: Command-line interface

Quick Start
-----------
>>> from app.util.gcode import simulate, svg_from_points
>>> result = simulate("G0 X10 Y10\\nG1 X20 F600")
>>> svg = svg_from_points(result['points_xy'])

>>> from app.util.gcode import parse_gcode, print_report
>>> summary, moves = parse_gcode("program.nc", validate=True)
>>> print_report(summary, moves)
"""
from __future__ import annotations

# Core types
from .types import (
    Modal,
    Move,
    MoveSegment,
    Pt,
    Pt3D,
    Summary,
    default_modal,
)

# Lexer
from .lexer import (
    parse_lines,
    parse_words,
    strip_comments,
)

# Geometry
from .geometry import (
    arc_center_from_ijk,
    arc_center_from_r,
    arc_len,
    dist2d,
    dist3d,
    interpolate_arc_points,
)

# Simulator
from .simulator import (
    simulate,
    simulate_segments,
)

# Reader
from .reader import (
    parse_gcode,
    validate_gcode,
)

# Render
from .render import (
    svg_from_points,
    svg_from_segments,
)

# Report
from .report import (
    fmt_num,
    print_report,
    summary_to_dict,
    write_csv,
    write_json,
)

__all__ = [
    # Types
    "Pt",
    "Pt3D",
    "Modal",
    "Move",
    "MoveSegment",
    "Summary",
    "default_modal",
    # Lexer
    "parse_lines",
    "parse_words",
    "strip_comments",
    # Geometry
    "dist2d",
    "dist3d",
    "arc_center_from_ijk",
    "arc_center_from_r",
    "arc_len",
    "interpolate_arc_points",
    # Simulator
    "simulate",
    "simulate_segments",
    # Reader
    "parse_gcode",
    "validate_gcode",
    # Render
    "svg_from_points",
    "svg_from_segments",
    # Report
    "fmt_num",
    "print_report",
    "write_csv",
    "write_json",
    "summary_to_dict",
]
