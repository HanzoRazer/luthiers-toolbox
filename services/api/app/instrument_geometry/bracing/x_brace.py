"""
X-Bracing Patterns: Generate X-brace patterns for acoustic guitars.

Wave 14 Module - Instrument Geometry Core

Provides X-bracing pattern generation for:
- Dreadnought
- Jumbo (J-200)
- OM/000
- Other steel-string acoustics
"""

from __future__ import annotations

from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class BracePattern:
    """
    Represents a bracing pattern as a list of brace segments.
    
    Attributes:
        name: Pattern name (e.g., "standard_x", "scalloped_x")
        braces: List of brace definitions, each with endpoints and profile
        soundhole_diameter_mm: Soundhole diameter this pattern is designed for
    """
    name: str
    braces: List[Dict[str, Any]]
    soundhole_diameter_mm: float = 100.0


def get_x_brace_pattern(
    body_width_mm: float = 400.0,
    body_length_mm: float = 510.0,
    soundhole_center_y_mm: float = 200.0,
    bridge_y_mm: float = 350.0,
    scalloped: bool = False,
) -> BracePattern:
    """
    Generate a standard X-bracing pattern.
    
    X-bracing is the most common pattern for steel-string acoustic guitars.
    The two main braces cross below the soundhole, forming an X.
    
    Args:
        body_width_mm: Body width at widest point
        body_length_mm: Total body length
        soundhole_center_y_mm: Y position of soundhole center from top
        bridge_y_mm: Y position of bridge from top
        scalloped: Whether to scallop the braces (reduces mass, opens tone)
        
    Returns:
        BracePattern with X-brace configuration
        
    Note:
        This is a simplified pattern. Production patterns require
        precise measurements from specific body templates.
    """
    half_width = body_width_mm / 2.0
    
    # X-brace crossing point (typically below soundhole, above bridge)
    x_cross_y = soundhole_center_y_mm + 60.0  # ~60mm below soundhole center
    x_cross_x = half_width  # Centered
    
    # X-brace endpoints spread toward edges
    x_spread = half_width * 0.7
    
    braces = [
        # Main X-brace - left arm
        {
            "name": "x_brace_left",
            "start": (x_cross_x - x_spread, soundhole_center_y_mm - 30),
            "end": (x_cross_x + x_spread, bridge_y_mm + 60),
            "width_mm": 12.0,
            "height_mm": 15.0,
            "scalloped": scalloped,
        },
        # Main X-brace - right arm
        {
            "name": "x_brace_right",
            "start": (x_cross_x + x_spread, soundhole_center_y_mm - 30),
            "end": (x_cross_x - x_spread, bridge_y_mm + 60),
            "width_mm": 12.0,
            "height_mm": 15.0,
            "scalloped": scalloped,
        },
        # Upper transverse brace (above soundhole)
        {
            "name": "upper_transverse",
            "start": (half_width * 0.2, soundhole_center_y_mm - 80),
            "end": (half_width * 1.8, soundhole_center_y_mm - 80),
            "width_mm": 10.0,
            "height_mm": 12.0,
            "scalloped": False,
        },
        # Lower face braces (tone bars)
        {
            "name": "tone_bar_bass",
            "start": (half_width * 0.3, bridge_y_mm + 20),
            "end": (half_width * 0.15, body_length_mm * 0.9),
            "width_mm": 8.0,
            "height_mm": 10.0,
            "scalloped": scalloped,
        },
        {
            "name": "tone_bar_treble",
            "start": (half_width * 1.7, bridge_y_mm + 20),
            "end": (half_width * 1.85, body_length_mm * 0.9),
            "width_mm": 8.0,
            "height_mm": 10.0,
            "scalloped": scalloped,
        },
    ]
    
    return BracePattern(
        name="scalloped_x" if scalloped else "standard_x",
        braces=braces,
        soundhole_diameter_mm=100.0,
    )


def get_dreadnought_bracing() -> BracePattern:
    """
    Get standard dreadnought X-bracing pattern.
    
    Returns:
        BracePattern configured for dreadnought body.
    """
    return get_x_brace_pattern(
        body_width_mm=400.0,
        body_length_mm=510.0,
        soundhole_center_y_mm=200.0,
        bridge_y_mm=350.0,
        scalloped=True,  # Modern dreadnoughts typically scalloped
    )


def get_jumbo_bracing() -> BracePattern:
    """
    Get X-bracing pattern for jumbo (J-200 style) body.
    
    Returns:
        BracePattern configured for jumbo body.
    """
    return get_x_brace_pattern(
        body_width_mm=430.0,
        body_length_mm=530.0,
        soundhole_center_y_mm=210.0,
        bridge_y_mm=370.0,
        scalloped=True,
    )
