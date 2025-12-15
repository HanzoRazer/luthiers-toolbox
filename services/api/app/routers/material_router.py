"""
Material database router for M.3 Energy & Heat Model.

Provides CRUD operations for material definitions including:
- Specific cutting energy (sce_j_per_mm3)
- Heat partition ratios (chip/tool/work)
"""

import json
import os
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/material", tags=["material"])

_ASSET = os.path.join(os.path.dirname(__file__), "..", "assets", "material_db.json")


def _load() -> List[Dict[str, Any]]:
    """Load material database from JSON file."""
    with open(_ASSET, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(materials: List[Dict[str, Any]]) -> None:
    """Save material database to JSON file."""
    with open(_ASSET, "w", encoding="utf-8") as f:
        json.dump(materials, f, indent=2)


@router.get("/list")
def list_materials() -> List[Dict[str, Any]]:
    """
    Get all materials in the database.
    
    Returns:
        List of material definitions with id, title, sce_j_per_mm3, heat_partition
    """
    return _load()


@router.get("/get/{mid}")
def get_material(mid: str) -> Dict[str, Any]:
    """
    Get a specific material by ID.
    
    Args:
        mid: Material ID (e.g., "maple_hard", "al_6061")
    
    Returns:
        Material definition dict
    
    Raises:
        HTTPException: 404 if material not found
    """
    for m in _load():
        if m["id"] == mid:
            return m
    raise HTTPException(404, f"Material '{mid}' not found")


@router.post("/upsert")
def upsert_material(m: dict) -> Dict[str, Any]:
    """
    Create or update a material definition.
    
    Args:
        m: Material dict with keys: id, title, sce_j_per_mm3, heat_partition
    
    Returns:
        {"status": "created"|"updated", "id": material_id}
    """
    if "id" not in m:
        raise HTTPException(400, "Material must have 'id' field")
    
    materials = _load()
    for i, mat in enumerate(materials):
        if mat["id"] == m["id"]:
            materials[i] = m
            _save(materials)
            return {"status": "updated", "id": m["id"]}
    
    materials.append(m)
    _save(materials)
    return {"status": "created", "id": m["id"]}
