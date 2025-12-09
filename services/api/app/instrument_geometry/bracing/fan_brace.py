"""
Fan Bracing Patterns: Generate fan-brace patterns for classical guitars.

Wave 14 Module - Instrument Geometry Core

Provides fan bracing pattern generation for:
- Classical guitars
- Flamenco guitars
- Romantic period guitars
"""

from __future__ import annotations

from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
import math


@dataclass
class FanBracePattern:
    """
    Represents a fan bracing pattern.
    
    Attributes:
        name: Pattern name (e.g., "torres_7", "traditional_5")
        braces: List of brace definitions radiating from apex
        apex_position: (x, y) position where braces originate
        soundhole_diameter_mm: Soundhole diameter
    """
    name: str
    braces: List[Dict[str, Any]]
    apex_position: Tuple[float, float]
    soundhole_diameter_mm: float = 85.0


def get_fan_brace_pattern(
    body_width_mm: float = 370.0,
    body_length_mm: float = 480.0,
    soundhole_center_y_mm: float = 190.0,
    bridge_y_mm: float = 340.0,
    num_braces: int = 7,
    symmetric: bool = True,
) -> FanBracePattern:
    """
    Generate a fan bracing pattern for classical/flamenco guitars.
    
    Fan bracing radiates outward from a point below the soundhole,
    spreading toward the lower bout. This pattern was perfected
    by Antonio de Torres in the 19th century.
    
    Args:
        body_width_mm: Body width at widest point
        body_length_mm: Total body length  
        soundhole_center_y_mm: Y position of soundhole center from top
        bridge_y_mm: Y position of bridge from top
        num_braces: Number of fan braces (typically 5 or 7)
        symmetric: Whether pattern is symmetric about centerline
        
    Returns:
        FanBracePattern with fan brace configuration
        
    Note:
        Traditional Torres pattern uses 7 braces. Modern variations
        may use 5, 7, or 9 braces with asymmetric arrangements.
    """
    half_width = body_width_mm / 2.0
    
    # Fan apex (where braces originate) - typically below soundhole
    apex_y = soundhole_center_y_mm + 50.0
    apex_x = half_width  # Centered
    
    # Fan spread at lower bout
    fan_spread_angle = 50.0  # degrees total spread
    fan_length = body_length_mm - apex_y - 20.0  # Leave margin at bottom
    
    braces = []
    
    if symmetric:
        # Symmetric fan - braces spread evenly from center
        half_braces = num_braces // 2
        center_brace = num_braces % 2 == 1
        
        if center_brace:
            # Center brace straight down
            braces.append({
                "name": "fan_center",
                "start": (apex_x, apex_y),
                "end": (apex_x, apex_y + fan_length),
                "width_mm": 5.0,
                "height_mm": 8.0,
                "index": 0,
            })
        
        # Side braces
        for i in range(half_braces):
            angle_offset = (i + 1) * (fan_spread_angle / 2.0 / (half_braces + 0.5))
            angle_rad = math.radians(angle_offset)
            
            # Calculate end points
            dx = fan_length * math.sin(angle_rad)
            dy = fan_length * math.cos(angle_rad)
            
            # Bass side (left)
            braces.append({
                "name": f"fan_bass_{i+1}",
                "start": (apex_x, apex_y),
                "end": (apex_x - dx, apex_y + dy),
                "width_mm": 5.0,
                "height_mm": 8.0,
                "index": -(i + 1),
            })
            
            # Treble side (right)
            braces.append({
                "name": f"fan_treble_{i+1}",
                "start": (apex_x, apex_y),
                "end": (apex_x + dx, apex_y + dy),
                "width_mm": 5.0,
                "height_mm": 8.0,
                "index": i + 1,
            })
    
    else:
        # Asymmetric fan - custom angles for each brace
        # This is a placeholder - real asymmetric patterns are instrument-specific
        pass
    
    # Add harmonic bars (cross braces above soundhole)
    braces.extend([
        {
            "name": "upper_harmonic",
            "start": (half_width * 0.25, soundhole_center_y_mm - 60),
            "end": (half_width * 1.75, soundhole_center_y_mm - 60),
            "width_mm": 8.0,
            "height_mm": 10.0,
            "index": None,
        },
        {
            "name": "lower_harmonic",
            "start": (half_width * 0.3, apex_y - 10),
            "end": (half_width * 1.7, apex_y - 10),
            "width_mm": 6.0,
            "height_mm": 8.0,
            "index": None,
        },
    ])
    
    return FanBracePattern(
        name=f"fan_{num_braces}{'_sym' if symmetric else '_asym'}",
        braces=braces,
        apex_position=(apex_x, apex_y),
        soundhole_diameter_mm=85.0,
    )


def get_torres_bracing() -> FanBracePattern:
    """
    Get traditional Torres 7-fan bracing pattern.
    
    Antonio de Torres established this pattern in the 1850s.
    It remains the foundation for classical guitar construction.
    
    Returns:
        FanBracePattern with Torres-style 7-fan configuration.
    """
    return get_fan_brace_pattern(
        body_width_mm=370.0,
        body_length_mm=480.0,
        soundhole_center_y_mm=190.0,
        bridge_y_mm=340.0,
        num_braces=7,
        symmetric=True,
    )


def get_flamenco_bracing() -> FanBracePattern:
    """
    Get flamenco guitar bracing pattern.
    
    Flamenco guitars typically use lighter bracing than classical
    for more percussive response and brighter tone.
    
    Returns:
        FanBracePattern configured for flamenco guitar.
    """
    pattern = get_fan_brace_pattern(
        body_width_mm=365.0,  # Slightly narrower body
        body_length_mm=470.0,
        soundhole_center_y_mm=185.0,
        bridge_y_mm=335.0,
        num_braces=5,  # Often fewer braces
        symmetric=True,
    )
    
    # Reduce brace dimensions for lighter build
    for brace in pattern.braces:
        if "fan" in brace["name"]:
            brace["width_mm"] = 4.5
            brace["height_mm"] = 7.0
    
    pattern.name = "flamenco_5"
    return pattern
