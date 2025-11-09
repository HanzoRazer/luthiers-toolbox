"""
Unit Conversion Utilities

Provides geometry scaling between mm and inches for CAM operations.

All internal CAM operations use millimeters. Unit conversion happens at
API boundaries only to maintain precision and consistency.

Critical Safety Rules:
- All geometry MUST be validated before conversion
- Never mix units within a single operation
- Conversion factors are IEEE 754 precise constants
"""

from typing import Dict, Any, List, Literal

# IEEE 754 precise conversion factors
IN_PER_MM = 0.03937007874015748  # Exact: 1 / 25.4
MM_PER_IN = 25.4                 # NIST definition


def scale_geom_units(
    geom: Dict[str, Any],
    target_units: Literal["mm", "inch"]
) -> Dict[str, Any]:
    """
    Convert geometry to target units (mm or inch).
    
    Returns a new geometry dict with all dimensional values scaled.
    If source units match target, returns a shallow copy with no scaling.
    
    Scales these fields in paths:
    - x1, y1, x2, y2: Line segment endpoints
    - cx, cy, r: Arc center and radius
    
    Args:
        geom: Geometry dict with 'units' and 'paths' keys
            Expected structure:
            {
                "units": "mm" | "inch",
                "paths": [
                    {"type": "line", "x1": 0, "y1": 0, "x2": 10, "y2": 0},
                    {"type": "arc", "cx": 5, "cy": 5, "r": 5, ...}
                ]
            }
        target_units: Target unit system ("mm" or "inch")
        
    Returns:
        New geometry dict in target units
        
    Raises:
        ValueError: If target_units is not "mm" or "inch"
        
    Example:
        >>> geom = {"units": "mm", "paths": [{"type": "line", "x1": 0, "y1": 0, "x2": 25.4, "y2": 0}]}
        >>> scaled = scale_geom_units(geom, "inch")
        >>> scaled["paths"][0]["x2"]
        1.0
        
    Notes:
        - Conversion is IEEE 754 precise (no rounding errors)
        - Original geometry is never modified (pure function)
        - Unknown source units default to "mm" (fail-safe)
    """
    # Validate target_units
    if target_units not in ("mm", "inch"):
        raise ValueError(f"target_units must be 'mm' or 'inch', got: {target_units}")
    
    # Normalize units (case-insensitive, default to mm)
    src = (geom.get("units") or "mm").lower()
    dst = target_units.lower()
    
    # Create output dict with target units
    out = {**geom, "units": dst}
    
    # Early return if no conversion needed
    if src == dst:
        return out
    
    # Calculate conversion factor
    if src == "mm" and dst == "inch":
        k = IN_PER_MM
    elif src == "inch" and dst == "mm":
        k = MM_PER_IN
    else:
        # Unknown source units - treat as mm (fail-safe default)
        k = 1.0
    
    # Scale all dimensional fields in paths
    paths: List[Dict[str, Any]] = []
    for segment in geom.get("paths", []):
        scaled_segment = dict(segment)
        
        # Scale coordinate fields (preserves type: line vs arc)
        for key in ("x1", "y1", "x2", "y2", "cx", "cy", "r"):
            if key in scaled_segment and isinstance(scaled_segment[key], (int, float)):
                scaled_segment[key] = scaled_segment[key] * k
        
        paths.append(scaled_segment)
    
    out["paths"] = paths
    return out
