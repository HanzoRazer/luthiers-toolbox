"""
Neck Taper Suite: FastAPI Router

Wave 17 - Instrument Geometry Integration

Provides HTTP endpoints for:
- JSON outline generation
- DXF file download
- Integration with Art Studio / RMOS / CAM pipelines
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Response

from .taper_math import TaperInputs
from .neck_outline_generator import generate_neck_outline
from .dxf_exporter import build_r12_polyline_dxf

router = APIRouter(prefix="/instrument/neck_taper", tags=["Neck Taper"])


@router.post("/outline")
def get_neck_outline(
    scale_length: float,
    nut_width: float,
    end_fret: int,
    end_width: float,
    frets: List[int] = None
):
    """
    Generate tapered neck outline as JSON coordinates.
    
    Returns a list of (x, y) points forming a closed polyline.
    
    Args:
        scale_length: Scale length in mm or inches
        nut_width: Width at nut
        end_fret: Reference end fret (typically 12)
        end_width: Width at end fret
        frets: List of fret numbers to include (default 0-12)
        
    Returns:
        JSON with 'outline' key containing list of [x, y] points
        
    Example:
        POST /instrument/neck_taper/outline
        {
          "scale_length": 647.7,
          "nut_width": 42.0,
          "end_fret": 12,
          "end_width": 57.0
        }
    """
    if frets is None:
        frets = list(range(0, 13))
    inputs = TaperInputs(
        scale_length=scale_length,
        nut_width=nut_width,
        end_fret=end_fret,
        end_width=end_width,
    )

    outline = generate_neck_outline(inputs, frets)
    return {"outline": outline}


@router.post("/outline.dxf")
def get_neck_outline_dxf(
    scale_length: float,
    nut_width: float,
    end_fret: int,
    end_width: float,
    frets: List[int] = None,
    layer: str = "NECK_TAPER",
):
    """
    Generate tapered neck outline as DXF file download.
    
    Returns a minimal R12 DXF file containing a POLYLINE entity.
    
    Args:
        scale_length: Scale length in mm or inches
        nut_width: Width at nut
        end_fret: Reference end fret (typically 12)
        end_width: Width at end fret
        frets: List of fret numbers to include (default 0-12)
        layer: DXF layer name (default "NECK_TAPER")
        
    Returns:
        DXF file as downloadable response
        
    Example:
        POST /instrument/neck_taper/outline.dxf
        {
          "scale_length": 647.7,
          "nut_width": 42.0,
          "end_fret": 12,
          "end_width": 57.0
        }
        
    Clients can save the response as .dxf and open in CAD/CAM software.
    """
    if frets is None:
        frets = list(range(0, 13))
    inputs = TaperInputs(
        scale_length=scale_length,
        nut_width=nut_width,
        end_fret=end_fret,
        end_width=end_width,
    )
    outline = generate_neck_outline(inputs, frets)
    dxf_text = build_r12_polyline_dxf(outline, layer=layer, closed=True)

    return Response(
        content=dxf_text,
        media_type="application/dxf",
        headers={"Content-Disposition": "attachment; filename=neck_taper.dxf"},
    )
