"""
G-code Parser and Simulator Module (Backward Compatibility)

This module re-exports from the split gcode/ package for backward compatibility.
New code should import directly from app.util.gcode instead.

Original module split into:
- gcode/types.py: Modal type alias
- gcode/lexer.py: parse_lines(), tokenization
- gcode/geometry.py: Arc calculations
- gcode/simulator.py: simulate(), simulate_segments()
- gcode/render.py: svg_from_points()
"""
from __future__ import annotations

# Re-export all public API for backward compatibility
from .gcode import (
    Modal,
    parse_lines,
    simulate,
    simulate_segments,
    svg_from_points,
)

__all__ = [
    "Modal",
    "parse_lines",
    "simulate",
    "simulate_segments",
    "svg_from_points",
]
