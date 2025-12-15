"""
Body Outlines: Body outline generation for instruments.

Wave 14 Module - Instrument Geometry Core
Updated: Wave 1 Integration (December 2025) - Added 19 detailed body outlines from DXF

Provides body outline geometry for various instrument types.
Detailed outlines extracted from DXF files are in detailed_outlines.py.
"""

from __future__ import annotations

from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path

from ..models import InstrumentModelId

# Import detailed outlines extracted from DXF files
try:
    from .detailed_outlines import BODY_OUTLINES as _DETAILED_OUTLINES
except ImportError:
    _DETAILED_OUTLINES = {}

# Import J45 bulge data for arc-accurate toolpaths
try:
    from .j45_bulge import J45_BODY_OUTLINE, J45_BODY_OUTLINE_WITH_BULGE, J45_DIMENSIONS
except ImportError:
    J45_BODY_OUTLINE = None
    J45_BODY_OUTLINE_WITH_BULGE = None
    J45_DIMENSIONS = None


# Body outline metadata (dimensions extracted from DXF sources)
_BODY_METADATA: Dict[str, Dict[str, Any]] = {
    # Electric guitars
    "stratocaster": {"width_mm": 322.3, "height_mm": 458.8, "category": "electric", "dxf": "electric/Stratocaster_body.dxf"},
    "les_paul": {"width_mm": 383.5, "height_mm": 269.2, "category": "electric", "dxf": "electric/LesPaul_body.dxf"},
    "js1000": {"width_mm": 450.7, "height_mm": 314.6, "category": "electric", "dxf": "electric/JS1000_body.dxf"},
    "gibson_explorer": {"width_mm": 556.5, "height_mm": 434.7, "category": "electric", "dxf": "electric/gibson_explorer_body.dxf"},
    "flying_v": {"width_mm": 486.0, "height_mm": 607.0, "category": "electric", "dxf": "electric/flying_v_body.dxf"},
    "harmony_h44": {"width_mm": 390.0, "height_mm": 270.0, "category": "electric", "dxf": "electric/harmony_h44_body.dxf"},
    
    # Acoustic guitars
    "j45": {"width_mm": 398.5, "height_mm": 504.8, "category": "acoustic", "dxf": "acoustic/J45_body_outline.dxf"},
    "jumbo": {"width_mm": 474.2, "height_mm": 385.1, "category": "acoustic", "dxf": "acoustic/Jumbo_body.dxf"},
    "dreadnought": {"width_mm": 404.0, "height_mm": 510.2, "category": "acoustic", "dxf": "acoustic/dreadnought_body.dxf"},
    "classical": {"width_mm": 371.0, "height_mm": 490.0, "category": "acoustic", "dxf": "acoustic/classical_body.dxf"},
    "om_000": {"width_mm": 397.6, "height_mm": 499.6, "category": "acoustic", "dxf": "acoustic/om_000_body.dxf"},
    "gibson_l_00": {"width_mm": 376.3, "height_mm": 500.0, "category": "acoustic", "dxf": "acoustic/gibson_l_00_body.dxf"},
    
    # Other instruments
    "soprano_ukulele": {"width_mm": 176.9, "height_mm": 200.0, "category": "other", "dxf": "other/soprano_ukulele_body.dxf"},
    "concert_ukulele": {"width_mm": 203.1, "height_mm": 393.7, "category": "other", "dxf": "other/concert_ukulele_body.dxf"},
    "octave_mandolin": {"width_mm": 280.0, "height_mm": 350.0, "category": "other", "dxf": "other/octave_mandolin_body.dxf"},
}

# Fallback placeholder outlines (simple rectangles for models without detailed data)
_PLACEHOLDER_OUTLINES: Dict[str, List[Tuple[float, float]]] = {
    "telecaster": [(0, 0), (320, 0), (320, 430), (0, 430)],
    "sg": [(0, 0), (320, 0), (320, 400), (0, 400)],
    "jazz_bass": [(0, 0), (340, 0), (340, 480), (0, 480)],
}


def get_body_outline(
    model_id: InstrumentModelId,
    scale: float = 1.0,
    detailed: bool = True,
) -> List[Tuple[float, float]]:
    """
    Get a body outline for the specified instrument model.
    
    Args:
        model_id: InstrumentModelId enum value or string model ID
        scale: Optional scale factor (default 1.0)
        detailed: If True, return detailed DXF-extracted outlines when available
        
    Returns:
        List of (x, y) points forming the body outline polygon.
        Points are in mm, counterclockwise from start point.
        
    Note:
        Detailed outlines have hundreds of points extracted from DXF files.
        Set detailed=False to get simple bounding box for performance.
    """
    # Handle both enum and string
    key = model_id.value if hasattr(model_id, 'value') else str(model_id)
    
    # Normalize key (handle variations)
    key_normalized = key.lower().replace("-", "_").replace(" ", "_")
    
    # Try detailed outlines first
    if detailed and key_normalized in _DETAILED_OUTLINES:
        outline = _DETAILED_OUTLINES[key_normalized]
    elif detailed and key_normalized in ["j45", "j_45", "gibson_j45"] and J45_BODY_OUTLINE:
        outline = J45_BODY_OUTLINE
    elif key_normalized in _PLACEHOLDER_OUTLINES:
        outline = _PLACEHOLDER_OUTLINES[key_normalized]
    elif key_normalized in _BODY_METADATA:
        # Generate bounding box from metadata
        meta = _BODY_METADATA[key_normalized]
        w, h = meta["width_mm"], meta["height_mm"]
        outline = [(0, 0), (w, 0), (w, h), (0, h)]
    else:
        # Return a generic guitar body shape
        outline = [(0, 0), (350, 0), (350, 470), (0, 470)]
    
    if scale != 1.0:
        outline = [(x * scale, y * scale) for x, y in outline]
    
    return outline


def get_body_dimensions(model_id: InstrumentModelId) -> Dict[str, float]:
    """
    Get the bounding box dimensions for a body outline.
    
    Args:
        model_id: InstrumentModelId enum value or string
        
    Returns:
        Dict with 'width' and 'length' in mm.
    """
    key = model_id.value if hasattr(model_id, 'value') else str(model_id)
    key_normalized = key.lower().replace("-", "_").replace(" ", "_")
    
    # Use metadata if available
    if key_normalized in _BODY_METADATA:
        meta = _BODY_METADATA[key_normalized]
        return {"width": meta["width_mm"], "length": meta["height_mm"]}
    
    # Fall back to calculating from outline
    outline = get_body_outline(model_id, detailed=False)
    
    if not outline:
        return {"width": 0.0, "length": 0.0}
    
    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]
    
    return {
        "width": max(xs) - min(xs),
        "length": max(ys) - min(ys),
    }


def get_available_outlines() -> List[str]:
    """
    Get list of model IDs with available body outlines.
    
    Returns:
        List of model ID strings.
    """
    # Combine all sources
    all_keys = set(_BODY_METADATA.keys())
    all_keys.update(_DETAILED_OUTLINES.keys())
    all_keys.update(_PLACEHOLDER_OUTLINES.keys())
    return sorted(list(all_keys))


def get_body_metadata(model_id: str) -> Optional[Dict[str, Any]]:
    """
    Get metadata for a body outline including dimensions, category, and DXF path.
    
    Args:
        model_id: String model identifier
        
    Returns:
        Dict with width_mm, height_mm, category, dxf path, or None if not found.
    """
    key = model_id.lower().replace("-", "_").replace(" ", "_")
    return _BODY_METADATA.get(key)


def get_dxf_path(model_id: str) -> Optional[Path]:
    """
    Get the path to the DXF file for a body outline.
    
    Args:
        model_id: String model identifier
        
    Returns:
        Path object relative to body/dxf/, or None if no DXF available.
    """
    meta = get_body_metadata(model_id)
    if meta and "dxf" in meta:
        # Return path relative to this file's directory
        return Path(__file__).parent / "dxf" / meta["dxf"]
    return None


def list_bodies_by_category(category: str) -> List[str]:
    """
    List all body outlines in a category.
    
    Args:
        category: One of 'electric', 'acoustic', 'other'
        
    Returns:
        List of model IDs in that category.
    """
    return [k for k, v in _BODY_METADATA.items() if v.get("category") == category]
