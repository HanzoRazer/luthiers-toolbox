"""
Dynamic CAM Registry Router
============================

Serves CAM stubs for ALL models in instrument_model_registry.json.
Single router handles all 19+ instruments dynamically.

Endpoints:
  GET /{model_id}/health - CAM health check
  GET /{model_id}/capabilities - What CAM operations are available
  GET /{model_id}/templates - Available CAM templates
  POST /{model_id}/contours/body - Generate body contour (if supported)
  POST /{model_id}/toolpaths/pocket - Generate pocket toolpath (stub)

Wave 20: Option C API Restructuring
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["CAM", "Registry"])

# Load registry
REGISTRY_PATH = Path(__file__).parent.parent.parent.parent / "instrument_geometry" / "instrument_model_registry.json"


def _load_registry() -> Dict[str, Any]:
    """Load instrument model registry."""
    if not REGISTRY_PATH.exists():
        return {"models": {}}
    with open(REGISTRY_PATH) as f:
        return json.load(f)


def _get_model(model_id: str) -> Optional[Dict[str, Any]]:
    """Get model from registry."""
    registry = _load_registry()
    models = registry.get("models", {})
    
    for check_id in [model_id, model_id.replace("-", "_"), model_id.replace("_", "-")]:
        if check_id in models:
            return models[check_id]
    return None


# =============================================================================
# MODELS
# =============================================================================

class CamHealth(BaseModel):
    """CAM subsystem health for a model"""
    model_id: str
    status: str  # "active", "stub", "no_assets"
    cam_ready: bool
    message: str


class CamCapabilities(BaseModel):
    """What CAM operations are available for a model"""
    model_id: str
    has_assets: bool
    capabilities: List[str]
    supported_operations: Dict[str, bool]
    recommended_posts: List[str]


class CamTemplate(BaseModel):
    """CAM template definition"""
    template_id: str
    name: str
    description: str
    operations: List[str]
    defaults: Dict[str, Any]


class ContourRequest(BaseModel):
    """Request for contour generation"""
    layer: str = "body_outline"
    offset_mm: float = 0.0
    simplify: bool = False


class ContourResponse(BaseModel):
    """Contour generation response"""
    model_id: str
    layer: str
    status: str
    message: str
    geometry: Optional[Dict[str, Any]] = None


class ToolpathRequest(BaseModel):
    """Toolpath generation request"""
    operation: str = "pocket"
    tool_diameter_mm: float = 6.35
    stepover_percent: float = 40.0
    depth_mm: float = 3.0


class ToolpathResponse(BaseModel):
    """Toolpath generation response"""
    model_id: str
    operation: str
    status: str
    message: str
    estimated_time_min: Optional[float] = None


# =============================================================================
# CAM CAPABILITIES BY STATUS
# =============================================================================

def _get_capabilities(model: Dict[str, Any]) -> Dict[str, Any]:
    """Determine CAM capabilities based on model status."""
    status = model.get("status", "STUB")
    assets = model.get("assets", [])
    
    if status == "COMPLETE":
        return {
            "has_assets": True,
            "capabilities": [
                "body_contour",
                "neck_pocket",
                "pickup_cavities",
                "control_cavity",
                "fret_slots",
                "toolpath_generation",
                "gcode_export",
                "dxf_export",
                "svg_export"
            ],
            "supported_operations": {
                "contour": True,
                "pocket": True,
                "drill": True,
                "profile": True,
                "engrave": False
            },
            "recommended_posts": ["grbl", "linuxcnc", "masso", "buildbotics"]
        }
    elif status == "ASSETS_ONLY":
        return {
            "has_assets": True,
            "capabilities": [
                "body_contour",
                "dxf_export",
                "svg_export",
                "basic_toolpath"
            ],
            "supported_operations": {
                "contour": True,
                "pocket": False,
                "drill": False,
                "profile": True,
                "engrave": False
            },
            "recommended_posts": ["grbl", "linuxcnc"]
        }
    else:  # STUB
        return {
            "has_assets": False,
            "capabilities": [
                "placeholder_geometry",
                "estimated_dimensions"
            ],
            "supported_operations": {
                "contour": False,
                "pocket": False,
                "drill": False,
                "profile": False,
                "engrave": False
            },
            "recommended_posts": []
        }


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/")
def list_all_cam_models() -> Dict[str, Any]:
    """
    List all models with their CAM status.
    """
    registry = _load_registry()
    models = registry.get("models", {})
    
    items = []
    for model_id, model in models.items():
        caps = _get_capabilities(model)
        items.append({
            "model_id": model_id,
            "display_name": model.get("display_name", model_id),
            "cam_ready": caps["has_assets"],
            "status": model.get("status", "STUB"),
            "capability_count": len(caps["capabilities"])
        })
    
    cam_ready = [i for i in items if i["cam_ready"]]
    
    return {
        "ok": True,
        "total_models": len(items),
        "cam_ready_count": len(cam_ready),
        "models": items
    }


@router.get("/{model_id}/health")
def cam_health(model_id: str) -> CamHealth:
    """
    CAM subsystem health check for a model.
    """
    model = _get_model(model_id)
    if not model:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_id}' not found in registry"
        )
    
    status = model.get("status", "STUB")
    has_assets = len(model.get("assets", [])) > 0 or status == "ASSETS_ONLY"
    
    if status == "COMPLETE":
        return CamHealth(
            model_id=model_id,
            status="active",
            cam_ready=True,
            message=f"Full CAM support available for {model.get('display_name', model_id)}"
        )
    elif has_assets or status == "ASSETS_ONLY":
        return CamHealth(
            model_id=model_id,
            status="partial",
            cam_ready=True,
            message=f"Basic CAM operations available - asset files present"
        )
    else:
        return CamHealth(
            model_id=model_id,
            status="stub",
            cam_ready=False,
            message=f"CAM stub only - no geometry assets for {model.get('display_name', model_id)}"
        )


@router.get("/{model_id}/capabilities")
def get_cam_capabilities(model_id: str) -> CamCapabilities:
    """
    Get available CAM operations for a model.
    """
    model = _get_model(model_id)
    if not model:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_id}' not found in registry"
        )
    
    caps = _get_capabilities(model)
    
    return CamCapabilities(
        model_id=model_id,
        **caps
    )


@router.get("/{model_id}/templates")
def get_cam_templates(model_id: str) -> Dict[str, Any]:
    """
    Get available CAM templates for a model.
    """
    model = _get_model(model_id)
    if not model:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_id}' not found in registry"
        )
    
    # Standard templates available for all models
    templates = [
        CamTemplate(
            template_id="outline_cut",
            name="Body Outline Cut",
            description="Profile cut around body perimeter",
            operations=["contour", "profile"],
            defaults={
                "tool_diameter_mm": 6.35,
                "depth_mm": 44.45,
                "tabs": True,
                "tab_width_mm": 12.0
            }
        ),
        CamTemplate(
            template_id="neck_pocket",
            name="Neck Pocket",
            description="Pocket operation for neck joint",
            operations=["pocket"],
            defaults={
                "tool_diameter_mm": 6.35,
                "depth_mm": 19.05,
                "stepover_percent": 40.0
            }
        ),
        CamTemplate(
            template_id="pickup_route",
            name="Pickup Routing",
            description="Humbucker or single-coil cavity",
            operations=["pocket"],
            defaults={
                "tool_diameter_mm": 3.175,
                "depth_mm": 19.05,
                "stepover_percent": 40.0
            }
        )
    ]
    
    caps = _get_capabilities(model)
    
    return {
        "model_id": model_id,
        "templates": [t.model_dump() for t in templates],
        "templates_enabled": caps["has_assets"],
        "note": "Templates require asset files for actual toolpath generation" if not caps["has_assets"] else None
    }


@router.post("/{model_id}/contours/body")
def generate_body_contour(model_id: str, request: ContourRequest) -> ContourResponse:
    """
    Generate body contour (stub for models without assets).
    """
    model = _get_model(model_id)
    if not model:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_id}' not found in registry"
        )
    
    caps = _get_capabilities(model)
    
    if not caps["supported_operations"].get("contour"):
        return ContourResponse(
            model_id=model_id,
            layer=request.layer,
            status="unavailable",
            message=f"Contour generation not available for {model_id} - no geometry assets"
        )
    
    # Placeholder response - actual implementation would read DXF/geometry
    return ContourResponse(
        model_id=model_id,
        layer=request.layer,
        status="stub",
        message=f"Contour generation available but requires full CAM module integration",
        geometry={
            "type": "placeholder",
            "note": "Connect to /api/geometry/export_bundle for actual DXF export"
        }
    )


@router.post("/{model_id}/toolpaths/pocket")
def generate_pocket_toolpath(model_id: str, request: ToolpathRequest) -> ToolpathResponse:
    """
    Generate pocket toolpath (stub).
    """
    model = _get_model(model_id)
    if not model:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_id}' not found in registry"
        )
    
    caps = _get_capabilities(model)
    
    if not caps["supported_operations"].get("pocket"):
        return ToolpathResponse(
            model_id=model_id,
            operation=request.operation,
            status="unavailable",
            message=f"Pocket toolpath not available for {model_id} - requires COMPLETE status"
        )
    
    # Placeholder
    return ToolpathResponse(
        model_id=model_id,
        operation=request.operation,
        status="stub",
        message="Pocket toolpath generation requires full CAM module integration",
        estimated_time_min=None
    )
