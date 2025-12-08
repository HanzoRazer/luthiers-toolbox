"""
Body Outlines: Basic body outline generation for instruments.

Wave 14 Module - Instrument Geometry Core

Provides placeholder body outline geometry for various instrument types.
Real implementations will load from DXF assets or generate parametrically.
"""

from __future__ import annotations

from typing import List, Tuple, Optional, Dict, Any

from ..models import InstrumentModelId


# Placeholder body outlines (simplified rectangles for now)
# Real implementations will load from DXF assets
_BODY_OUTLINES: Dict[str, List[Tuple[float, float]]] = {
    # Electric guitar bodies (approximate bounding boxes in mm)
    "stratocaster": [
        (0, 0), (330, 0), (330, 460), (0, 460)
    ],
    "telecaster": [
        (0, 0), (320, 0), (320, 430), (0, 430)
    ],
    "les_paul": [
        (0, 0), (330, 0), (330, 440), (0, 440)
    ],
    "sg": [
        (0, 0), (320, 0), (320, 400), (0, 400)
    ],
    "flying_v": [
        (0, 0), (400, 0), (400, 500), (0, 500)
    ],
    "explorer": [
        (0, 0), (420, 0), (420, 460), (0, 460)
    ],
    
    # Acoustic guitar bodies (approximate bounding boxes in mm)
    "dreadnought": [
        (0, 0), (400, 0), (400, 510), (0, 510)
    ],
    "om_000": [
        (0, 0), (380, 0), (380, 490), (0, 490)
    ],
    "j_45": [
        (0, 0), (410, 0), (410, 510), (0, 510)
    ],
    "jumbo_j200": [
        (0, 0), (430, 0), (430, 530), (0, 530)
    ],
    "classical": [
        (0, 0), (370, 0), (370, 480), (0, 480)
    ],
    
    # Bass body
    "jazz_bass": [
        (0, 0), (340, 0), (340, 480), (0, 480)
    ],
    
    # Small body
    "ukulele": [
        (0, 0), (200, 0), (200, 280), (0, 280)
    ],
}


def get_body_outline(
    model_id: InstrumentModelId,
    scale: float = 1.0,
) -> List[Tuple[float, float]]:
    """
    Get a body outline for the specified instrument model.
    
    Args:
        model_id: InstrumentModelId enum value
        scale: Optional scale factor (default 1.0)
        
    Returns:
        List of (x, y) points forming the body outline polygon.
        Points are in mm, counterclockwise from bottom-left.
        
    Note:
        Current implementation returns simplified bounding boxes.
        Future versions will load actual body curves from DXF assets.
    """
    # Get outline by model value (string)
    outline = _BODY_OUTLINES.get(model_id.value)
    
    if outline is None:
        # Return a generic guitar body shape
        outline = [(0, 0), (350, 0), (350, 470), (0, 470)]
    
    if scale != 1.0:
        outline = [(x * scale, y * scale) for x, y in outline]
    
    return outline


def get_body_dimensions(model_id: InstrumentModelId) -> Dict[str, float]:
    """
    Get the bounding box dimensions for a body outline.
    
    Args:
        model_id: InstrumentModelId enum value
        
    Returns:
        Dict with 'width' and 'length' in mm.
    """
    outline = get_body_outline(model_id)
    
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
    return list(_BODY_OUTLINES.keys())
