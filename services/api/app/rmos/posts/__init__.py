"""
CNC Post-Processors Package

This package contains post-processor modules for various CNC controllers.
Each module provides a `render()` function that converts toolpaths to G-code.

Available post-processors:
- fanuc: FANUC-style industrial CNC (O-numbers, N-codes, parentheses comments)
- grbl: GRBL hobby CNC controller (no line numbers, semicolon comments)
"""
from .fanuc import render as render_fanuc
from .grbl import render as render_grbl

__all__ = [
    "render_fanuc",
    "render_grbl",
]
