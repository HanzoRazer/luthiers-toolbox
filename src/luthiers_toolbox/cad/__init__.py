"""
CAD Module - Parametric design tools for guitar components.

This module provides classes and functions for creating parametric designs of
guitar bodies, necks, fretboards, and other components. Designs can be exported
to DXF and other formats for manufacturing.
"""

from .body import GuitarBody
from .neck import GuitarNeck
from .fretboard import Fretboard
from .geometry import Point, Line, Arc, Circle

__all__ = ["GuitarBody", "GuitarNeck", "Fretboard", "Point", "Line", "Arc", "Circle"]
