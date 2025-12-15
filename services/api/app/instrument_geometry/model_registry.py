"""
Instrument Geometry: Model Registry

Wave 14 Module - Instrument Geometry Core

JSON-backed registry for instrument model metadata with caching.
Loads model specifications from instrument_model_registry.json.

Usage:
    from instrument_geometry.model_registry import get_model_info, list_models
    
    info = get_model_info(InstrumentModelId.STRAT)
    print(info["display_name"])  # "Fender Stratocaster"
    
    models = list_models(status=InstrumentModelStatus.PRODUCTION)
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Any

from .models import InstrumentModelId, InstrumentModelStatus, InstrumentCategory, ScaleLengthSpec


# Path to JSON registry (same directory as this file)
_REGISTRY_PATH = Path(__file__).parent / "instrument_model_registry.json"

# Cached registry data
_registry_cache: Optional[Dict[str, Any]] = None


def _load_registry() -> Dict[str, Any]:
    """
    Load the registry JSON file.
    
    Returns:
        Dict containing the full registry data.
        
    Raises:
        FileNotFoundError: If registry JSON doesn't exist.
        json.JSONDecodeError: If JSON is malformed.
    """
    global _registry_cache
    
    if _registry_cache is not None:
        return _registry_cache
    
    if not _REGISTRY_PATH.exists():
        # Return empty registry if file doesn't exist yet
        _registry_cache = {"models": {}, "version": "1.0.0"}
        return _registry_cache
    
    with open(_REGISTRY_PATH, "r", encoding="utf-8") as f:
        _registry_cache = json.load(f)
    
    return _registry_cache


def clear_cache() -> None:
    """Clear the registry cache (useful for testing)."""
    global _registry_cache
    _registry_cache = None
    get_model_info.cache_clear()


@lru_cache(maxsize=32)
def get_model_info(model_id: InstrumentModelId) -> Dict[str, Any]:
    """
    Get metadata for a specific model.
    
    Args:
        model_id: InstrumentModelId enum value
        
    Returns:
        Dict with model metadata including:
        - display_name: Human-readable name
        - status: InstrumentModelStatus value
        - category: InstrumentCategory value
        - scale_length_mm: Default scale length
        - fret_count: Default fret count
        - string_count: Number of strings
        - description: Brief description
        - assets: List of available asset paths
        
    Raises:
        KeyError: If model_id not found in registry
    """
    registry = _load_registry()
    models = registry.get("models", {})
    
    model_key = model_id.value
    if model_key not in models:
        # Return stub info for unregistered models
        return {
            "id": model_id.value,
            "display_name": model_id.name.replace("_", " ").title(),
            "status": InstrumentModelStatus.STUB.value,
            "category": "unknown",
            "scale_length_mm": 648.0,
            "fret_count": 22,
            "string_count": 6,
            "description": f"Stub entry for {model_id.name}",
            "assets": [],
        }
    
    return models[model_key]


def get_model_status(model_id: InstrumentModelId) -> InstrumentModelStatus:
    """
    Get the implementation status for a model.
    
    Args:
        model_id: InstrumentModelId enum value
        
    Returns:
        InstrumentModelStatus enum value
    """
    info = get_model_info(model_id)
    status_str = info.get("status", "STUB")
    return InstrumentModelStatus(status_str)


def list_models(
    status: Optional[InstrumentModelStatus] = None,
    category: Optional[InstrumentCategory] = None,
) -> List[InstrumentModelId]:
    """
    List models, optionally filtered by status or category.
    
    Args:
        status: Filter by implementation status
        category: Filter by instrument category
        
    Returns:
        List of InstrumentModelId values matching filters
    """
    result = []
    
    for model_id in InstrumentModelId:
        info = get_model_info(model_id)
        
        # Filter by status
        if status is not None:
            model_status = info.get("status", "STUB")
            if model_status != status.value:
                continue
        
        # Filter by category
        if category is not None:
            model_category = info.get("category", "unknown")
            if model_category != category.value:
                continue
        
        result.append(model_id)
    
    return result


def list_production_models() -> List[InstrumentModelId]:
    """
    List all production-ready models.
    
    Returns:
        List of InstrumentModelId values with PRODUCTION status
    """
    return list_models(status=InstrumentModelStatus.PRODUCTION)


def list_stub_models() -> List[InstrumentModelId]:
    """
    List all stub models that need implementation.
    
    Returns:
        List of InstrumentModelId values with STUB status
    """
    return list_models(status=InstrumentModelStatus.STUB)


def get_registry_version() -> str:
    """
    Get the registry version string.
    
    Returns:
        Version string (e.g., "1.0.0")
    """
    registry = _load_registry()
    return registry.get("version", "0.0.0")


def get_all_models_summary() -> Dict[str, Any]:
    """
    Get a summary of all models in the registry.
    
    Returns:
        Dict with:
        - total: Total model count
        - by_status: Count per status
        - by_category: Count per category
        - models: List of model summaries
    """
    by_status: Dict[str, int] = {}
    by_category: Dict[str, int] = {}
    model_summaries = []
    
    for model_id in InstrumentModelId:
        info = get_model_info(model_id)
        status = info.get("status", "STUB")
        category = info.get("category", "unknown")
        
        by_status[status] = by_status.get(status, 0) + 1
        by_category[category] = by_category.get(category, 0) + 1
        
        model_summaries.append({
            "id": model_id.value,
            "display_name": info.get("display_name", model_id.name),
            "status": status,
            "category": category,
        })
    
    return {
        "total": len(InstrumentModelId),
        "by_status": by_status,
        "by_category": by_category,
        "models": model_summaries,
    }


# =============================================================================
# Wave 16: get_default_scale() - Real Tier 1 Scale Lengths
# =============================================================================

def get_default_scale(model_id: InstrumentModelId) -> ScaleLengthSpec:
    """
    Return a nominal scale length for a given model.

    Wave 16:
    - Stratocaster, Telecaster, Jazz Bass → 648.0 mm (25.5")
    - Les Paul family → 628.65 mm (24.75")
    - Steel-string acoustics (Dreadnought, OM, J-45, L-00, J-200) → 645.0 mm (25.4")
    - Classical → 650.0 mm
    - Ukulele (soprano-ish) → 349.0 mm
    - PRS → 635.0 mm (25")
    - Archtop → 648.0 mm (25.5") baseline
    """

    # Fender-style family
    if model_id in (
        InstrumentModelId.STRAT,
        InstrumentModelId.TELE,
        InstrumentModelId.JAZZ_BASS,
    ):
        return ScaleLengthSpec(
            model_id=model_id,
            scale_length_mm=648.0,  # 25.5"
            num_frets=21,
            description="Fender-style scale length (Tier 1 real geometry for Strat)",
        )

    # Gibson-style electrics
    if model_id in (
        InstrumentModelId.LES_PAUL,
        InstrumentModelId.SG,
        InstrumentModelId.FLYING_V,
        InstrumentModelId.ES_335,
        InstrumentModelId.EXPLORER,
        InstrumentModelId.FIREBIRD,
        InstrumentModelId.MODERNE,
    ):
        return ScaleLengthSpec(
            model_id=model_id,
            scale_length_mm=628.65,  # 24.75"
            num_frets=22,
            description="Gibson-style 24.75\" scale length",
        )

    # Steel-string acoustics
    if model_id in (
        InstrumentModelId.DREADNOUGHT,
        InstrumentModelId.OM_000,
        InstrumentModelId.J_45,
        InstrumentModelId.JUMBO_J200,
        InstrumentModelId.GIBSON_L_00,
    ):
        return ScaleLengthSpec(
            model_id=model_id,
            scale_length_mm=645.0,  # 25.4"
            num_frets=20,
            description="Steel-string acoustic scale length (Martin-style 25.4\")",
        )

    # Classical / nylon
    if model_id == InstrumentModelId.CLASSICAL:
        return ScaleLengthSpec(
            model_id=model_id,
            scale_length_mm=650.0,
            num_frets=19,
            description="Classical guitar scale length",
        )

    # Ukulele (soprano baseline)
    if model_id == InstrumentModelId.UKULELE:
        return ScaleLengthSpec(
            model_id=model_id,
            scale_length_mm=349.0,  # ~13.75"
            num_frets=15,
            description="Ukulele (soprano) scale length placeholder",
        )

    # PRS
    if model_id == InstrumentModelId.PRS:
        return ScaleLengthSpec(
            model_id=model_id,
            scale_length_mm=635.0,  # 25"
            num_frets=22,
            description="PRS-style 25\" scale length",
        )

    # Archtop default
    if model_id == InstrumentModelId.ARCHTOP:
        return ScaleLengthSpec(
            model_id=model_id,
            scale_length_mm=648.0,
            num_frets=20,
            description="Archtop scale length baseline",
        )

    # Fallback generic
    return ScaleLengthSpec(
        model_id=model_id,
        scale_length_mm=648.0,
        num_frets=21,
        description="Generic fallback scale length (Wave 16)",
    )
