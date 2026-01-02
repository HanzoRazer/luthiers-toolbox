"""
Smart Guitar CAM Router
=======================

CAM operations for Smart Guitar: toolpath generation for IoT components.
Instrument specs moved to /api/instruments/guitar/smart/*
Temperament data moved to /api/music/temperament/*

Endpoints:
  GET /health - CAM subsystem health
  GET /toolpaths - Available toolpath generators
  POST /preview - Generate toolpath preview

Wave 15: Option C API Restructuring
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["Smart Guitar", "CAM"])


# =============================================================================
# MODELS
# =============================================================================

class SmartGuitarToolpath(BaseModel):
    """Toolpath definition"""
    name: str
    type: str  # 'pocket', 'drill', 'contour'
    description: str
    component: str  # 'electronics_cavity', 'battery', 'led_channel'


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/health")
def smart_guitar_cam_health() -> Dict[str, Any]:
    """
    Get Smart Guitar CAM subsystem health status.
    """
    return {
        "ok": True,
        "subsystem": "smart_guitar_cam",
        "model_id": "smart",
        "capabilities": [
            "toolpaths",
            "preview",
            "electronics_routing"
        ],
        "status": "Development - toolpath generation in progress",
        "instrument_spec": "/api/instruments/guitar/smart/spec",
        "temperament_api": "/api/music/temperament/health"
    }


@router.get("/toolpaths")
def list_smart_guitar_toolpaths() -> Dict[str, Any]:
    """
    List available toolpath generators for Smart Guitar components.
    
    Returns toolpath definitions for IoT electronics installation.
    """
    toolpaths = [
        SmartGuitarToolpath(
            name="Electronics Cavity",
            type="pocket",
            description="Pocket for Raspberry Pi 5 and electronics board",
            component="electronics_cavity"
        ),
        SmartGuitarToolpath(
            name="Battery Pocket",
            type="pocket",
            description="Li-ion battery compartment",
            component="battery"
        ),
        SmartGuitarToolpath(
            name="LED Channel",
            type="contour",
            description="Channel for LED strip along fretboard edge",
            component="led_channel"
        ),
        SmartGuitarToolpath(
            name="USB-C Port Hole",
            type="drill",
            description="Mounting hole for USB-C charging port",
            component="usb_port"
        ),
        SmartGuitarToolpath(
            name="Antenna Recess",
            type="pocket",
            description="Shallow recess for Bluetooth/WiFi antenna",
            component="antenna"
        ),
    ]
    
    return {
        "ok": True,
        "model": "smart",
        "toolpaths": [t.model_dump() for t in toolpaths],
        "count": len(toolpaths),
        "note": "Toolpath generation requires specific body dimensions - see /spec endpoint"
    }


@router.post("/preview")
def generate_toolpath_preview(
    component: str = "electronics_cavity",
    body_thickness_mm: float = 44.45,
    depth_mm: float = 25.0
) -> Dict[str, Any]:
    """
    Generate a toolpath preview for a Smart Guitar component.
    
    Args:
        component: Component name from /toolpaths
        body_thickness_mm: Body thickness (default 1.75")
        depth_mm: Pocket depth
    """
    # Component dimensions (simplified)
    components = {
        "electronics_cavity": {
            "length_mm": 100.0,
            "width_mm": 70.0,
            "corner_radius_mm": 5.0,
            "max_depth_mm": body_thickness_mm - 6.0  # Leave 6mm floor
        },
        "battery": {
            "length_mm": 70.0,
            "width_mm": 40.0,
            "corner_radius_mm": 3.0,
            "max_depth_mm": 20.0
        },
        "led_channel": {
            "width_mm": 8.0,
            "depth_mm": 3.0,
            "length_mm": 400.0  # Full fretboard length
        },
        "usb_port": {
            "diameter_mm": 12.0,
            "depth_mm": body_thickness_mm
        },
        "antenna": {
            "length_mm": 50.0,
            "width_mm": 30.0,
            "depth_mm": 2.0
        }
    }
    
    if component not in components:
        return {
            "ok": False,
            "error": f"Unknown component: {component}",
            "available": list(components.keys())
        }
    
    comp_data = components[component]
    
    return {
        "ok": True,
        "component": component,
        "dimensions": comp_data,
        "requested_depth_mm": depth_mm,
        "toolpath_params": {
            "step_over": 0.4,  # 40% step over
            "step_down": 3.0,  # 3mm per pass
            "feed_rate": 1500,  # mm/min
            "plunge_rate": 500,
            "tool_diameter_mm": 6.35  # 1/4" endmill
        },
        "estimated_time_minutes": round((comp_data.get("length_mm", 50) * comp_data.get("width_mm", 50) * depth_mm) / 50000, 1),
        "note": "Preview only - full G-code generation requires /generate endpoint (not yet implemented)"
    }
