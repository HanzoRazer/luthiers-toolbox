"""
Stratocaster Instrument Router (Non-CAM)
========================================

Instrument specifications, geometry, and templates for Stratocaster guitars.
CAM operations moved to /api/cam/guitar/stratocaster/*

Endpoints:
  GET /spec - Stratocaster specifications
  GET /geometry - Body geometry and dimensions
  GET /templates - Available design templates
  GET /info - Model overview

Wave 15: Option C API Restructuring
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["Stratocaster", "Instruments"])


class StratocasterSpec(BaseModel):
    """Stratocaster guitar specifications"""
    model: str = "stratocaster"
    display_name: str = "Fender Stratocaster"
    category: str = "electric_guitar"
    scale_length_mm: float = 648.0  # 25.5"
    scale_length_inches: float = 25.5
    nut_width_mm: float = 42.86  # 1.6875"
    fret_count: int = 22
    string_count: int = 6
    body_style: str = "double_cutaway"
    body_wood: str = "alder"  # or ash
    neck_joint: str = "bolt_on"
    features: List[str] = [
        "Double-cutaway body",
        "Contoured body for comfort",
        "Three single-coil pickups",
        "5-way pickup selector",
        "Synchronized tremolo bridge",
        "Bolt-on maple neck",
    ]


class StratocasterGeometry(BaseModel):
    """Stratocaster body geometry"""
    body_length_mm: float = 406.4  # 16"
    body_width_mm: float = 317.5  # 12.5"
    body_thickness_mm: float = 44.45  # 1.75"
    neck_pocket_length_mm: float = 76.2
    neck_pocket_width_mm: float = 56.0
    tremolo_route_length_mm: float = 89.0
    tremolo_route_width_mm: float = 57.0
    control_cavity_length_mm: float = 127.0
    control_cavity_width_mm: float = 63.5
    pickup_route_count: int = 3


class StratocasterTemplate(BaseModel):
    """Template file reference"""
    name: str
    type: str  # 'body', 'neck', 'pickguard', 'hardware'
    format: str  # 'dxf', 'svg', 'pdf'
    description: Optional[str] = None


@router.get("/spec")
def get_stratocaster_spec() -> StratocasterSpec:
    """
    Get Stratocaster specifications.
    
    Returns standard dimensions and features for Stratocaster guitars.
    """
    return StratocasterSpec()


@router.get("/geometry")
def get_stratocaster_geometry() -> StratocasterGeometry:
    """
    Get Stratocaster body geometry.
    
    Returns dimensional data for body design and routing.
    """
    return StratocasterGeometry()


@router.get("/templates")
def list_stratocaster_templates() -> Dict[str, Any]:
    """
    List available Stratocaster design templates.
    
    Returns references to DXF/SVG templates for:
    - Body outline
    - Neck profile
    - Pickguard
    - Hardware routes
    """
    return {
        "ok": True,
        "model": "stratocaster",
        "templates": [
            StratocasterTemplate(
                name="Stratocaster Body Top",
                type="body",
                format="dxf",
                description="Body top view with pickup routes"
            ).model_dump(),
            StratocasterTemplate(
                name="Stratocaster Body Bottom",
                type="body",
                format="dxf",
                description="Body bottom with tremolo and control routes"
            ).model_dump(),
            StratocasterTemplate(
                name="Stratocaster Neck",
                type="neck",
                format="dxf",
                description="22-fret maple neck profile"
            ).model_dump(),
            StratocasterTemplate(
                name="Stratocaster Pickguard",
                type="pickguard",
                format="dxf",
                description="11-hole SSS pickguard"
            ).model_dump(),
        ],
        "note": "For CAM operations, see /api/cam/guitar/stratocaster/*"
    }


@router.get("/info")
def get_stratocaster_info() -> Dict[str, Any]:
    """
    Get Stratocaster model overview.
    
    Returns summary info for UI display.
    """
    return {
        "ok": True,
        "model_id": "stratocaster",
        "display_name": "Fender Stratocaster",
        "category": "electric_guitar",
        "description": (
            "Classic Fender double-cutaway electric guitar. "
            "Features contoured body, 25.5\" scale length, "
            "and synchronized tremolo system."
        ),
        "year_introduced": 1954,
        "manufacturer": "Fender",
        "related_endpoints": {
            "spec": "/api/instruments/guitar/stratocaster/spec",
            "geometry": "/api/instruments/guitar/stratocaster/geometry",
            "templates": "/api/instruments/guitar/stratocaster/templates",
            "cam": "/api/cam/guitar/stratocaster/health"
        }
    }
