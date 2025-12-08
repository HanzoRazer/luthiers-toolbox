"""
Bridge Compensation: Compute intonation compensation for strings.

Wave 14 Module - Instrument Geometry Core

Provides helpers for computing saddle compensation based on:
- String gauge and type (wound/plain)
- Scale length
- Action height
- Playing style preferences
"""

from __future__ import annotations

from typing import Dict, List, Optional
from dataclasses import dataclass

from ..neck.neck_profiles import InstrumentSpec, BridgeSpec
from .geometry import (
    compute_compensation_estimate,
    compute_saddle_positions_mm,
    STANDARD_6_STRING_COMPENSATION,
    STANDARD_4_STRING_BASS_COMPENSATION,
)


@dataclass
class CompensatedBridge:
    """
    Result of bridge compensation calculation.
    
    Attributes:
        scale_length_mm: Nominal scale length
        saddle_positions_mm: Dict of string_id -> actual saddle position
        total_compensation_range_mm: Max - min compensation across strings
    """
    scale_length_mm: float
    saddle_positions_mm: Dict[str, float]
    total_compensation_range_mm: float


def compute_compensated_bridge(
    spec: InstrumentSpec,
    string_gauges_mm: Optional[Dict[str, float]] = None,
    wound_strings: Optional[List[str]] = None,
    action_mm: float = 2.0,
) -> CompensatedBridge:
    """
    Compute fully compensated saddle positions for all strings.
    
    Args:
        spec: InstrumentSpec with scale_length_mm and string_count
        string_gauges_mm: Optional dict of string_id -> gauge in mm.
            If not provided, uses standard compensation values.
        wound_strings: List of string IDs that are wound (e.g., ["E6", "A5", "D4"])
        action_mm: String height at 12th fret (affects compensation)
        
    Returns:
        CompensatedBridge with saddle positions
        
    Example:
        >>> spec = InstrumentSpec("electric", 648.0, 22, 6)
        >>> result = compute_compensated_bridge(spec)
        >>> result.saddle_positions_mm["E6"]
        650.5
    """
    # Use standard compensation if no gauges provided
    if string_gauges_mm is None:
        if spec.string_count == 4:
            compensations = STANDARD_4_STRING_BASS_COMPENSATION.copy()
        else:
            compensations = STANDARD_6_STRING_COMPENSATION.copy()
    else:
        # Calculate compensation from gauges
        wound_set = set(wound_strings or [])
        compensations = {}
        for string_id, gauge in string_gauges_mm.items():
            is_wound = string_id in wound_set
            comp = compute_compensation_estimate(gauge, is_wound, action_mm)
            compensations[string_id] = comp
    
    # Compute actual saddle positions
    saddle_positions = compute_saddle_positions_mm(spec.scale_length_mm, compensations)
    
    # Calculate total range
    if saddle_positions:
        positions = list(saddle_positions.values())
        comp_range = max(positions) - min(positions)
    else:
        comp_range = 0.0
    
    return CompensatedBridge(
        scale_length_mm=spec.scale_length_mm,
        saddle_positions_mm=saddle_positions,
        total_compensation_range_mm=comp_range,
    )


def get_standard_compensations(string_count: int = 6) -> Dict[str, float]:
    """
    Get standard intonation compensation values.
    
    Args:
        string_count: 4 for bass, 6 for guitar (default)
        
    Returns:
        Dict of string_id -> compensation in mm
    """
    if string_count == 4:
        return STANDARD_4_STRING_BASS_COMPENSATION.copy()
    return STANDARD_6_STRING_COMPENSATION.copy()


def compute_compensation_for_gauge(
    gauge_mm: float,
    is_wound: bool = False,
    action_mm: float = 2.0,
) -> float:
    """
    Compute compensation for a single string.
    
    Convenience wrapper around geometry.compute_compensation_estimate.
    
    Args:
        gauge_mm: String diameter in mm
        is_wound: Whether the string is wound
        action_mm: String height at 12th fret
        
    Returns:
        Estimated compensation in mm
    """
    return compute_compensation_estimate(gauge_mm, is_wound, action_mm)
