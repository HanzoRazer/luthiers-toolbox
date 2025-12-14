# services/api/app/instrument_geometry/fan_fret_guard.py
"""
Fan-Fret Geometry Guard

Validates multiscale/fan-fret geometry for:
- Perpendicular fret angle deviation
- Fan direction (bass vs treble)
- String crossing detection
- Extreme fret angle warnings

Wave 7 Implementation (Fan-Fret Visual Debug Overlay)
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import math


class FanFretGuardResult(BaseModel):
    """Result from fan-fret geometry guard."""
    warnings: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    perpendicular_fret: int
    perpendicular_angle_deg: float
    max_fret_angle_deg: float
    fan_direction: str  # "normal", "reversed", "none"


def compute_fan_fret_geometry_guard(
    frets: List[Dict[str, Any]],
    bass_scale_mm: float,
    treble_scale_mm: float,
    perpendicular_fret: int,
    max_perp_deviation_deg: float = 0.5,
    max_fret_angle_deg: float = 12.0,
) -> FanFretGuardResult:
    """
    Run geometry guards on fan-fret layout.
    
    Args:
        frets: List of fret dicts with keys: fret_number, angle_rad, bass_x, treble_x
        bass_scale_mm: Scale length on bass side
        treble_scale_mm: Scale length on treble side
        perpendicular_fret: Which fret should be perpendicular (1-indexed)
        max_perp_deviation_deg: Max allowed perpendicular fret deviation
        max_fret_angle_deg: Warning threshold for extreme angles
    
    Returns:
        FanFretGuardResult with warnings and errors
    """
    warnings: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []
    
    # Default values
    perp_angle_deg = 0.0
    max_angle_deg = 0.0
    fan_direction = "none"
    
    # Determine fan direction
    scale_diff = bass_scale_mm - treble_scale_mm
    if abs(scale_diff) < 1.0:
        fan_direction = "none"  # Essentially straight frets
    elif scale_diff > 0:
        fan_direction = "normal"  # Bass longer than treble (standard)
    else:
        fan_direction = "reversed"  # Treble longer than bass (unusual)
        warnings.append({
            "code": "FANFRET_DIRECTION_INVERTED",
            "severity": "warning",
            "message": "Treble scale is longer than bass scale — reversed fan layout.",
            "bass_scale_mm": bass_scale_mm,
            "treble_scale_mm": treble_scale_mm,
        })
    
    if not frets:
        return FanFretGuardResult(
            warnings=warnings,
            errors=errors,
            perpendicular_fret=perpendicular_fret,
            perpendicular_angle_deg=0.0,
            max_fret_angle_deg=0.0,
            fan_direction=fan_direction,
        )
    
    # --- 1. Perpendicular fret angle check ---
    perp_idx = perpendicular_fret - 1  # Convert to 0-indexed
    if 0 <= perp_idx < len(frets):
        pfret = frets[perp_idx]
        angle_rad = abs(pfret.get("angle_rad", 0.0))
        perp_angle_deg = math.degrees(angle_rad)
        
        if perp_angle_deg > max_perp_deviation_deg:
            errors.append({
                "code": "FANFRET_PERP_DRIFT",
                "severity": "error",
                "message": f"Perpendicular fret {perpendicular_fret} deviates from 90° by {perp_angle_deg:.2f}°.",
                "fret": perpendicular_fret,
                "angle_deg": perp_angle_deg,
                "max_allowed_deg": max_perp_deviation_deg,
            })
    else:
        warnings.append({
            "code": "FANFRET_PERP_OUT_OF_RANGE",
            "severity": "warning",
            "message": f"Perpendicular fret {perpendicular_fret} is outside fret range (1-{len(frets)}).",
            "perpendicular_fret": perpendicular_fret,
            "fret_count": len(frets),
        })
    
    # --- 2. String crossing geometry check ---
    for f in frets:
        fret_num = f.get("fret_number", 0)
        bass_x = f.get("bass_x")
        treble_x = f.get("treble_x")
        
        if bass_x is not None and treble_x is not None:
            # In normal fan-fret, treble_x should be slightly ahead of bass_x
            # (or equal for perpendicular fret)
            if fan_direction == "normal" and treble_x < bass_x - 0.01:
                errors.append({
                    "code": "STRING_CROSSING",
                    "severity": "error",
                    "message": f"Fan-fret geometry causes string crossing at fret {fret_num}.",
                    "fret": fret_num,
                    "bass_x": bass_x,
                    "treble_x": treble_x,
                })
            elif fan_direction == "reversed" and bass_x < treble_x - 0.01:
                errors.append({
                    "code": "STRING_CROSSING",
                    "severity": "error",
                    "message": f"Fan-fret geometry causes string crossing at fret {fret_num}.",
                    "fret": fret_num,
                    "bass_x": bass_x,
                    "treble_x": treble_x,
                })
    
    # --- 3. Slot angle sanity check ---
    for f in frets:
        fret_num = f.get("fret_number", 0)
        angle_rad = abs(f.get("angle_rad", 0.0))
        angle_deg = math.degrees(angle_rad)
        
        # Track max angle
        if angle_deg > max_angle_deg:
            max_angle_deg = angle_deg
        
        # Warn on extreme angles
        if angle_deg > max_fret_angle_deg:
            warnings.append({
                "code": "EXTREME_FRET_ANGLE",
                "severity": "warning",
                "message": f"Fret {fret_num} has extreme angle ({angle_deg:.1f}°) — may cause tooling instability.",
                "fret": fret_num,
                "angle_deg": angle_deg,
                "threshold_deg": max_fret_angle_deg,
            })
    
    # --- 4. Scale length sanity check ---
    if bass_scale_mm < 400 or bass_scale_mm > 1000:
        warnings.append({
            "code": "UNUSUAL_SCALE_LENGTH",
            "severity": "warning",
            "message": f"Bass scale length ({bass_scale_mm}mm) is outside typical guitar range.",
            "bass_scale_mm": bass_scale_mm,
        })
    
    if treble_scale_mm < 400 or treble_scale_mm > 1000:
        warnings.append({
            "code": "UNUSUAL_SCALE_LENGTH",
            "severity": "warning",
            "message": f"Treble scale length ({treble_scale_mm}mm) is outside typical guitar range.",
            "treble_scale_mm": treble_scale_mm,
        })
    
    return FanFretGuardResult(
        warnings=warnings,
        errors=errors,
        perpendicular_fret=perpendicular_fret,
        perpendicular_angle_deg=perp_angle_deg,
        max_fret_angle_deg=max_angle_deg,
        fan_direction=fan_direction,
    )
