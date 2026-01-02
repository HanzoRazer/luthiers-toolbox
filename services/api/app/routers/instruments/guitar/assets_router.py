"""
Instrument Assets Router
========================

E2E asset path for models with actual files.
Serves DXF, SVG, and other design assets.

Models with assets (ASSETS_ONLY status):
  - flying_v
  - jumbo_j200
  - gibson_l_00
  - ukulele

Endpoints:
  GET /{model_id}/assets - List available assets
  GET /{model_id}/assets/{asset_name} - Download specific asset
  GET /{model_id}/preview - Get SVG preview if available

Wave 20: Option C API Restructuring
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

router = APIRouter(tags=["Instruments", "Assets"])

# Paths
BASE_PATH = Path(__file__).parent.parent.parent.parent
REGISTRY_PATH = BASE_PATH / "instrument_geometry" / "instrument_model_registry.json"
GEOMETRY_PATH = BASE_PATH / "instrument_geometry"


def _load_registry() -> Dict[str, Any]:
    """Load instrument model registry."""
    if not REGISTRY_PATH.exists():
        return {"models": {}}
    with open(REGISTRY_PATH) as f:
        return json.load(f)


def _get_model(model_id: str) -> Optional[Dict[str, Any]]:
    """Get model from registry with flexible ID matching."""
    registry = _load_registry()
    models = registry.get("models", {})
    
    for check_id in [model_id, model_id.replace("-", "_"), model_id.replace("_", "-")]:
        if check_id in models:
            return models[check_id]
    return None


def _get_asset_path(model_id: str, asset_name: str) -> Optional[Path]:
    """Resolve asset file path."""
    # Common asset locations
    search_paths = [
        GEOMETRY_PATH / model_id / asset_name,
        GEOMETRY_PATH / model_id.replace("_", "-") / asset_name,
        GEOMETRY_PATH / "dxf" / f"{model_id}_{asset_name}",
        GEOMETRY_PATH / "dxf" / f"{model_id}.dxf",
        BASE_PATH / "data" / "instruments" / model_id / asset_name,
        BASE_PATH / "data" / "dxf" / f"{model_id}.dxf",
    ]
    
    for path in search_paths:
        if path.exists():
            return path
    
    return None


def _discover_assets(model_id: str) -> List[Dict[str, Any]]:
    """Discover all assets for a model on disk."""
    assets = []
    
    # Check multiple possible locations
    search_dirs = [
        GEOMETRY_PATH / model_id,
        GEOMETRY_PATH / model_id.replace("_", "-"),
        GEOMETRY_PATH / "dxf",
        BASE_PATH / "data" / "instruments" / model_id,
        BASE_PATH / "data" / "dxf",
    ]
    
    extensions = {".dxf", ".svg", ".json", ".nc", ".gcode"}
    seen_files = set()
    
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
            
        for file in search_dir.iterdir():
            if file.suffix.lower() in extensions:
                # Check if file name matches model
                if model_id in file.stem or model_id.replace("_", "-") in file.stem or model_id.replace("-", "_") in file.stem:
                    if file.name not in seen_files:
                        seen_files.add(file.name)
                        assets.append({
                            "name": file.name,
                            "type": file.suffix[1:].upper(),
                            "path": str(file.relative_to(BASE_PATH)),
                            "size_bytes": file.stat().st_size
                        })
    
    return assets


# =============================================================================
# MODELS
# =============================================================================

class AssetInfo(BaseModel):
    """Single asset metadata"""
    name: str
    type: str
    path: str
    size_bytes: int
    download_url: str


class AssetList(BaseModel):
    """Asset listing response"""
    model_id: str
    has_assets: bool
    total_assets: int
    assets: List[AssetInfo]
    preview_available: bool


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/{model_id}/assets")
def list_model_assets(model_id: str) -> AssetList:
    """
    List all available assets for a model.
    
    Discovers DXF, SVG, NC files on disk.
    """
    model = _get_model(model_id)
    if not model:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_id}' not found in registry"
        )
    
    # Check registry assets first, then discover on disk
    registry_assets = model.get("assets", [])
    discovered = _discover_assets(model_id)
    
    # Merge: registry info + discovered files
    assets = []
    for asset in discovered:
        assets.append(AssetInfo(
            name=asset["name"],
            type=asset["type"],
            path=asset["path"],
            size_bytes=asset["size_bytes"],
            download_url=f"/api/instruments/guitar/{model_id}/assets/{asset['name']}"
        ))
    
    # Check for preview
    has_preview = any(a.type == "SVG" for a in assets)
    
    return AssetList(
        model_id=model_id,
        has_assets=len(assets) > 0,
        total_assets=len(assets),
        assets=assets,
        preview_available=has_preview
    )


@router.get("/{model_id}/assets/{asset_name}")
def download_asset(model_id: str, asset_name: str):
    """
    Download a specific asset file.
    
    Returns the raw file (DXF, SVG, etc).
    """
    model = _get_model(model_id)
    if not model:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_id}' not found in registry"
        )
    
    file_path = _get_asset_path(model_id, asset_name)
    if not file_path:
        raise HTTPException(
            status_code=404,
            detail=f"Asset '{asset_name}' not found for model '{model_id}'"
        )
    
    # Determine media type
    media_types = {
        ".dxf": "application/dxf",
        ".svg": "image/svg+xml",
        ".json": "application/json",
        ".nc": "text/plain",
        ".gcode": "text/plain",
    }
    media_type = media_types.get(file_path.suffix.lower(), "application/octet-stream")
    
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=asset_name
    )


@router.get("/{model_id}/preview")
def get_model_preview(model_id: str):
    """
    Get SVG preview if available.
    
    Returns inline SVG for UI display.
    """
    model = _get_model(model_id)
    if not model:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_id}' not found in registry"
        )
    
    # Find SVG file
    assets = _discover_assets(model_id)
    svg_assets = [a for a in assets if a["type"] == "SVG"]
    
    if not svg_assets:
        raise HTTPException(
            status_code=404,
            detail=f"No SVG preview available for model '{model_id}'"
        )
    
    svg_path = BASE_PATH / svg_assets[0]["path"]
    if not svg_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"SVG file not found on disk for model '{model_id}'"
        )
    
    svg_content = svg_path.read_text()
    
    return Response(
        content=svg_content,
        media_type="image/svg+xml"
    )


@router.get("/with-assets")
def list_models_with_assets() -> Dict[str, Any]:
    """
    List all models that have actual asset files.
    
    Useful for UI to know which models support CAM export.
    """
    registry = _load_registry()
    models = registry.get("models", {})
    
    models_with_assets = []
    
    for model_id, model in models.items():
        assets = _discover_assets(model_id)
        if assets:
            models_with_assets.append({
                "model_id": model_id,
                "display_name": model.get("display_name", model_id),
                "status": model.get("status", "STUB"),
                "asset_count": len(assets),
                "asset_types": list(set(a["type"] for a in assets))
            })
    
    return {
        "ok": True,
        "total_with_assets": len(models_with_assets),
        "models": models_with_assets
    }
