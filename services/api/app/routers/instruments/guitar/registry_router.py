"""
Dynamic Instrument Registry Router
==================================

Serves /spec, /geometry, /info for ALL models in instrument_model_registry.json.
Single router handles all 19+ instruments dynamically.

Endpoints:
  GET /{model_id}/spec - Model specifications from registry
  GET /{model_id}/geometry - Body geometry (computed)
  GET /{model_id}/info - Model overview
  GET / - List all available models

Wave 20: Option C API Restructuring
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["Instruments", "Registry"])

# Load registry at module load
REGISTRY_PATH = Path(__file__).parent.parent.parent.parent / "instrument_geometry" / "instrument_model_registry.json"

def _load_registry() -> Dict[str, Any]:
    """Load instrument model registry."""
    if not REGISTRY_PATH.exists():
        return {"models": {}}
    with open(REGISTRY_PATH) as f:
        return json.load(f)


def _get_model(model_id: str) -> Dict[str, Any]:
    """Get a specific model from registry, including variants."""
    registry = _load_registry()
    models = registry.get("models", {})
    
    # Normalize ID
    check_ids = [model_id, model_id.replace("-", "_"), model_id.replace("_", "-")]
    
    for check_id in check_ids:
        # Try exact match first
        if check_id in models:
            return models[check_id]
        
        # Search in variants of each model
        for parent_id, parent in models.items():
            variants = parent.get("variants", {})
            if check_id in variants:
                # Merge parent defaults with variant
                variant = variants[check_id].copy()
                # Inherit from parent if not specified
                for key in ["category", "scale_length_mm", "fret_count", "string_count"]:
                    if key not in variant:
                        variant[key] = parent.get(key)
                variant["parent_model"] = parent_id
                return variant
    
    return None


def _get_all_models_flat() -> Dict[str, Any]:
    """Get all models including variants as flat dict."""
    registry = _load_registry()
    models = registry.get("models", {})
    flat = {}
    
    for model_id, model in models.items():
        flat[model_id] = model
        # Add variants
        for variant_id, variant in model.get("variants", {}).items():
            merged = variant.copy()
            for key in ["category", "scale_length_mm", "fret_count", "string_count"]:
                if key not in merged:
                    merged[key] = model.get(key)
            merged["parent_model"] = model_id
            flat[variant_id] = merged
    
    return flat


# =============================================================================
# MODELS
# =============================================================================

class InstrumentSpec(BaseModel):
    """Instrument specifications from registry"""
    model_id: str
    display_name: str
    category: str
    status: str
    scale_length_mm: float
    scale_length_inches: float
    fret_count: int
    string_count: int
    manufacturer: str
    year_introduced: int
    description: str
    features: List[str]


class InstrumentGeometry(BaseModel):
    """Computed geometry based on category"""
    model_id: str
    category: str
    scale_length_mm: float
    # Estimated body dimensions based on category
    body_length_mm: float
    body_width_mm: float
    body_depth_mm: Optional[float] = None
    neck_pocket_length_mm: Optional[float] = None
    notes: str


class InstrumentInfo(BaseModel):
    """Model overview for UI"""
    model_id: str
    display_name: str
    category: str
    status: str
    description: str
    manufacturer: str
    year_introduced: int
    has_assets: bool
    asset_count: int
    endpoints: Dict[str, str]


class ModelListItem(BaseModel):
    """Summary item for model list"""
    model_id: str
    display_name: str
    category: str
    status: str


# =============================================================================
# CATEGORY-BASED GEOMETRY ESTIMATES
# =============================================================================

GEOMETRY_BY_CATEGORY = {
    "electric_guitar": {
        "body_length_mm": 406.4,  # ~16"
        "body_width_mm": 330.0,   # ~13"
        "body_depth_mm": 44.45,   # ~1.75"
        "neck_pocket_length_mm": 76.2,
        "notes": "Solid body electric - dimensions vary by model"
    },
    "acoustic_guitar": {
        "body_length_mm": 508.0,  # ~20"
        "body_width_mm": 400.0,   # ~15.75" lower bout
        "body_depth_mm": 110.0,   # ~4.3"
        "neck_pocket_length_mm": None,
        "notes": "Acoustic body - actual dimensions depend on body style (dreadnought, OM, jumbo)"
    },
    "archtop": {
        "body_length_mm": 508.0,
        "body_width_mm": 406.4,   # 16" lower bout typical
        "body_depth_mm": 76.0,    # ~3"
        "neck_pocket_length_mm": None,
        "notes": "Carved archtop - floating bridge, f-holes"
    },
    "bass": {
        "body_length_mm": 457.0,  # ~18"
        "body_width_mm": 356.0,   # ~14"
        "body_depth_mm": 44.45,
        "neck_pocket_length_mm": 89.0,
        "notes": "Bass guitar body - longer scale requires adjusted body proportions"
    },
    "ukulele": {
        "body_length_mm": 228.6,  # ~9" soprano
        "body_width_mm": 165.0,   # ~6.5"
        "body_depth_mm": 63.5,    # ~2.5"
        "neck_pocket_length_mm": None,
        "notes": "Soprano ukulele - concert/tenor sizes larger"
    }
}


def _compute_geometry(model: Dict[str, Any]) -> Dict[str, Any]:
    """Compute geometry estimates based on category."""
    category = model.get("category", "electric_guitar")
    base = GEOMETRY_BY_CATEGORY.get(category, GEOMETRY_BY_CATEGORY["electric_guitar"])
    
    return {
        "model_id": model["id"],
        "category": category,
        "scale_length_mm": model.get("scale_length_mm", 648.0),
        **base
    }


def _get_features(model: Dict[str, Any]) -> List[str]:
    """Generate features list from model data."""
    features = []
    category = model.get("category", "")
    
    if category == "electric_guitar":
        features.extend([
            f"{model.get('fret_count', 22)}-fret neck",
            f"{model.get('string_count', 6)} strings",
            f"{model.get('scale_length_mm', 648.0)}mm scale ({round(model.get('scale_length_mm', 648.0) / 25.4, 2)}\")",
        ])
    elif category == "acoustic_guitar":
        features.extend([
            f"{model.get('fret_count', 20)}-fret neck",
            "Steel string acoustic",
            f"{model.get('scale_length_mm', 645.0)}mm scale",
        ])
    elif category == "archtop":
        features.extend([
            "Carved top and back",
            "Floating bridge",
            "F-holes",
        ])
    elif category == "bass":
        features.extend([
            f"{model.get('string_count', 4)}-string bass",
            f"34\" scale ({model.get('scale_length_mm', 863.6)}mm)",
        ])
    elif category == "ukulele":
        features.extend([
            f"{model.get('string_count', 4)} strings",
            "Nylon strings",
            "Soprano size",
        ])
    
    return features


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/")
def list_all_models() -> Dict[str, Any]:
    """
    List all available instrument models including variants.
    
    Returns hierarchical view with parent models and their variants.
    """
    registry = _load_registry()
    models = registry.get("models", {})
    
    items = []
    categories = {}
    hierarchy = {}
    
    for model_id, model in models.items():
        category = model.get("category", "unknown")
        variants = model.get("variants", {})
        
        items.append(ModelListItem(
            model_id=model_id,
            display_name=model.get("display_name", model_id),
            category=category,
            status=model.get("status", "STUB")
        ))
        
        if category not in categories:
            categories[category] = []
        categories[category].append(model_id)
        
        # Build hierarchy
        hierarchy[model_id] = {
            "display_name": model.get("display_name", model_id),
            "variants": []
        }
        
        # Add variants
        for variant_id, variant in variants.items():
            items.append(ModelListItem(
                model_id=variant_id,
                display_name=variant.get("display_name", variant_id),
                category=category,
                status=variant.get("status", "STUB")
            ))
            categories[category].append(variant_id)
            hierarchy[model_id]["variants"].append({
                "id": variant_id,
                "display_name": variant.get("display_name", variant_id),
                "status": variant.get("status", "STUB")
            })
    
    return {
        "ok": True,
        "total_models": len(items),
        "models": [m.model_dump() for m in items],
        "by_category": categories,
        "hierarchy": hierarchy,
        "registry_version": registry.get("version", "unknown")
    }


@router.get("/{model_id}/spec")
def get_model_spec(model_id: str) -> InstrumentSpec:
    """
    Get instrument specifications for a model.
    
    Returns scale length, fret count, string count, and metadata.
    """
    model = _get_model(model_id)
    if not model:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_id}' not found in registry"
        )
    
    return InstrumentSpec(
        model_id=model["id"],
        display_name=model.get("display_name", model["id"]),
        category=model.get("category", "unknown"),
        status=model.get("status", "STUB"),
        scale_length_mm=model.get("scale_length_mm", 648.0),
        scale_length_inches=round(model.get("scale_length_mm", 648.0) / 25.4, 2),
        fret_count=model.get("fret_count", 22),
        string_count=model.get("string_count", 6),
        manufacturer=model.get("manufacturer", "Unknown"),
        year_introduced=model.get("year_introduced", 0),
        description=model.get("description", ""),
        features=_get_features(model)
    )


@router.get("/{model_id}/geometry")
def get_model_geometry(model_id: str) -> InstrumentGeometry:
    """
    Get body geometry estimates for a model.
    
    Returns estimated body dimensions based on instrument category.
    """
    model = _get_model(model_id)
    if not model:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_id}' not found in registry"
        )
    
    geom = _compute_geometry(model)
    return InstrumentGeometry(**geom)


@router.get("/{model_id}/info")
def get_model_info(model_id: str) -> InstrumentInfo:
    """
    Get model overview for UI display.
    
    Returns summary info including asset availability.
    """
    model = _get_model(model_id)
    if not model:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_id}' not found in registry"
        )
    
    assets = model.get("assets", [])
    has_assets = len(assets) > 0
    
    return InstrumentInfo(
        model_id=model["id"],
        display_name=model.get("display_name", model["id"]),
        category=model.get("category", "unknown"),
        status=model.get("status", "STUB"),
        description=model.get("description", ""),
        manufacturer=model.get("manufacturer", "Unknown"),
        year_introduced=model.get("year_introduced", 0),
        has_assets=has_assets,
        asset_count=len(assets),
        endpoints={
            "spec": f"/api/instruments/guitar/{model_id}/spec",
            "geometry": f"/api/instruments/guitar/{model_id}/geometry",
            "assets": f"/api/instruments/guitar/{model_id}/assets" if has_assets else None,
            "cam": f"/api/cam/guitar/{model_id}/health"
        }
    )
