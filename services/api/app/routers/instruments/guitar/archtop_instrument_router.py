"""
Archtop Instrument Router (Non-CAM)
===================================

Instrument specifications, geometry, and templates for archtop guitars.
CAM operations moved to /api/cam/guitar/archtop/*

Endpoints:
  GET /spec - Archtop specifications
  GET /geometry - Body geometry and dimensions
  GET /templates - Available design templates
  GET /info - Model overview

Wave 15: Option C API Restructuring
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["Archtop", "Instruments"])


class ArchtopSpec(BaseModel):
    """Archtop guitar specifications"""
    model: str = "archtop"
    display_name: str = "Jazz Archtop"
    category: str = "archtop"
    scale_length_mm: float = 635.0
    scale_length_inches: float = 25.0
    fret_count: int = 20
    string_count: int = 6
    body_style: str = "carved_top"
    typical_top_arch_mm: float = 18.0
    typical_back_arch_mm: float = 15.0
    typical_body_depth_mm: float = 76.0  # 3"
    features: List[str] = [
        "Carved spruce top",
        "Carved maple back", 
        "Floating bridge",
        "Neck angle compensation",
        "F-holes",
    ]


class ArchtopGeometry(BaseModel):
    """Archtop body geometry"""
    body_length_mm: float = 508.0  # 20"
    upper_bout_mm: float = 279.4  # 11"
    lower_bout_mm: float = 406.4  # 16" 
    waist_mm: float = 241.3  # 9.5"
    top_arch_height_mm: float = 18.0
    back_arch_height_mm: float = 15.0
    rim_depth_mm: float = 76.0
    neck_angle_deg: float = 3.0
    fingerboard_extension_mm: float = 70.0


class ArchtopTemplate(BaseModel):
    """Template file reference"""
    name: str
    type: str  # 'body', 'graduation', 'f_hole', 'binding'
    format: str  # 'dxf', 'svg', 'pdf'
    description: Optional[str] = None


@router.get("/spec")
def get_archtop_spec() -> ArchtopSpec:
    """
    Get archtop guitar specifications.
    
    Returns standard dimensions and features for archtop guitars.
    """
    return ArchtopSpec()


@router.get("/geometry")
def get_archtop_geometry() -> ArchtopGeometry:
    """
    Get archtop body geometry.
    
    Returns dimensional data for body design.
    """
    return ArchtopGeometry()


@router.get("/templates")
def list_archtop_templates() -> Dict[str, Any]:
    """
    List available archtop design templates.
    
    Returns references to DXF/SVG templates for:
    - Body outline
    - Graduation maps
    - F-hole patterns
    - Binding routes
    """
    return {
        "ok": True,
        "model": "archtop",
        "templates": [
            ArchtopTemplate(
                name="Archtop Body Outline",
                type="body",
                format="dxf",
                description="Standard 16\" lower bout archtop body"
            ).model_dump(),
            ArchtopTemplate(
                name="Top Graduation Map",
                type="graduation",
                format="svg",
                description="Thickness graduation map for carved top"
            ).model_dump(),
            ArchtopTemplate(
                name="F-Hole Pattern",
                type="f_hole",
                format="dxf",
                description="Standard f-hole cutout pattern"
            ).model_dump(),
        ],
        "note": "For CAM operations, see /api/cam/guitar/archtop/*"
    }


@router.get("/info")
def get_archtop_info() -> Dict[str, Any]:
    """
    Get archtop model overview.
    
    Returns summary info for UI display.
    """
    return {
        "ok": True,
        "model_id": "archtop",
        "display_name": "Jazz Archtop",
        "category": "archtop",
        "description": (
            "Carved-top jazz guitar with floating bridge. "
            "Features include arched top and back, f-holes, "
            "and neck angle compensation for optimal playability."
        ),
        "year_introduced": 1922,
        "manufacturer": "Various",
        "related_endpoints": {
            "spec": "/api/instruments/guitar/archtop/spec",
            "geometry": "/api/instruments/guitar/archtop/geometry",
            "templates": "/api/instruments/guitar/archtop/templates",
            "cam": "/api/cam/guitar/archtop/health"
        }
    }
