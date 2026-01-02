"""
OM Instrument Router (Non-CAM)
==============================

Instrument specifications, geometry, and templates for OM acoustic guitars.
CAM operations moved to /api/cam/guitar/om/*

Endpoints:
  GET /spec - OM specifications
  GET /geometry - Body geometry and dimensions
  GET /templates - Available design templates
  GET /info - Model overview

Wave 15: Option C API Restructuring
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["OM", "Instruments"])


class OMSpec(BaseModel):
    """OM acoustic guitar specifications"""
    model: str = "om"
    display_name: str = "OM/000 Acoustic"
    category: str = "acoustic_guitar"
    scale_length_mm: float = 645.16  # 25.4"
    scale_length_inches: float = 25.4
    nut_width_mm: float = 44.45  # 1.75"
    fret_count: int = 20
    string_count: int = 6
    body_style: str = "orchestra_model"
    bracing: str = "X-bracing"
    features: List[str] = [
        "Orchestra Model body shape",
        "Balanced tone across frequencies",
        "14-fret neck joint",
        "Ideal for fingerstyle",
        "X-braced top",
    ]


class OMGeometry(BaseModel):
    """OM body geometry"""
    body_length_mm: float = 495.3  # 19.5"
    upper_bout_mm: float = 282.6  # 11.125"
    lower_bout_mm: float = 384.2  # 15.125"
    waist_mm: float = 241.3  # 9.5"
    body_depth_upper_mm: float = 101.6  # 4"
    body_depth_lower_mm: float = 111.1  # 4.375"
    soundhole_diameter_mm: float = 101.6  # 4"
    fingerboard_width_nut_mm: float = 44.45
    fingerboard_width_12th_mm: float = 55.56


class OMTemplate(BaseModel):
    """Template file reference"""
    name: str
    type: str  # 'body', 'mold', 'graduation', 'bracing'
    format: str  # 'dxf', 'svg', 'pdf'
    description: Optional[str] = None


@router.get("/spec")
def get_om_spec() -> OMSpec:
    """
    Get OM guitar specifications.
    
    Returns standard dimensions and features for OM acoustic guitars.
    """
    return OMSpec()


@router.get("/geometry")
def get_om_geometry() -> OMGeometry:
    """
    Get OM body geometry.
    
    Returns dimensional data for body design.
    """
    return OMGeometry()


@router.get("/templates")
def list_om_templates() -> Dict[str, Any]:
    """
    List available OM design templates.
    
    Returns references to DXF/SVG templates for:
    - Body outline
    - Internal mold
    - Graduation maps
    - Bracing patterns
    """
    return {
        "ok": True,
        "model": "om",
        "templates": [
            OMTemplate(
                name="OM Body Outline",
                type="body",
                format="dxf",
                description="Standard OM body outline"
            ).model_dump(),
            OMTemplate(
                name="OM Internal Mold",
                type="mold",
                format="dxf",
                description="CNC mold for body assembly"
            ).model_dump(),
            OMTemplate(
                name="Top Graduation Map",
                type="graduation",
                format="svg",
                description="Thickness graduation map (Sitka spruce)"
            ).model_dump(),
            OMTemplate(
                name="X-Bracing Pattern",
                type="bracing",
                format="dxf",
                description="Standard X-bracing layout"
            ).model_dump(),
        ],
        "note": "For CAM operations, see /api/cam/guitar/om/*"
    }


@router.get("/info")
def get_om_info() -> Dict[str, Any]:
    """
    Get OM model overview.
    
    Returns summary info for UI display.
    """
    return {
        "ok": True,
        "model_id": "om",
        "display_name": "OM/000 Acoustic",
        "category": "acoustic_guitar",
        "description": (
            "Orchestra Model / 000 body acoustic guitar. "
            "A versatile steel-string design with balanced tone, "
            "ideal for fingerstyle and recording."
        ),
        "year_introduced": 1929,
        "manufacturer": "Martin",
        "related_endpoints": {
            "spec": "/api/instruments/guitar/om/spec",
            "geometry": "/api/instruments/guitar/om/geometry",
            "templates": "/api/instruments/guitar/om/templates",
            "cam": "/api/cam/guitar/om/health"
        }
    }
