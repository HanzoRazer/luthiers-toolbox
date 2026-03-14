"""Tool & Material Library Router.

Provides:
- GET /library/tools - List all tools
- GET /library/tools/{tool_id} - Get tool by ID
- GET /library/materials - List all materials
- GET /library/materials/{material_id} - Get material by ID
- GET /library/validate - Validate library

LANE: UTILITY (tool/material configuration)
"""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter

from app.data.tool_library import (
    load_tool_library,
    get_tool_profile,
    get_material_profile,
)
from app.data.validate_tool_library import validate_library

router = APIRouter(tags=["Tool Library", "Tooling"])


# =============================================================================
# TOOL ENDPOINTS
# =============================================================================

@router.get("/library/tools", summary="List all tools from JSON library")
def list_library_tools() -> List[Dict[str, Any]]:
    """
    List all tools from the JSON tool library.

    Returns lightweight summary for each tool (id, name, type, diameter, flutes).
    Use GET /tooling/library/tools/{tool_id} for full details.
    """
    lib = load_tool_library()
    results = []

    for tool_id in lib.list_tool_ids():
        tool = lib.get_tool(tool_id)
        if tool:
            results.append({
                "tool_id": tool.tool_id,
                "name": tool.name,
                "type": tool.tool_type,
                "diameter_mm": tool.diameter_mm,
                "flutes": tool.flutes,
            })

    return results


@router.get("/library/tools/{tool_id}", summary="Get tool by ID from JSON library")
def get_library_tool(tool_id: str) -> Dict[str, Any]:
    """
    Get detailed information for a specific tool from the JSON library.

    Returns error field if tool not found.
    """
    tool = get_tool_profile(tool_id)

    if tool is None:
        return {
            "tool_id": tool_id,
            "error": f"Tool not found: {tool_id}"
        }

    return {
        "tool_id": tool.tool_id,
        "name": tool.name,
        "type": tool.tool_type,
        "diameter_mm": tool.diameter_mm,
        "flutes": tool.flutes,
        "chipload_mm": {
            "min": tool.chipload_min_mm,
            "max": tool.chipload_max_mm,
        },
    }


# =============================================================================
# MATERIAL ENDPOINTS
# =============================================================================

@router.get("/library/materials", summary="List all materials from JSON library")
def list_library_materials() -> List[Dict[str, Any]]:
    """
    List all materials from the JSON library.

    Returns lightweight summary for each material.
    """
    lib = load_tool_library()
    results = []

    for mat_id in lib.list_material_ids():
        mat = lib.get_material(mat_id)
        if mat:
            results.append({
                "material_id": mat.material_id,
                "name": mat.name,
                "heat_sensitivity": mat.heat_sensitivity,
                "hardness": mat.hardness,
            })

    return results


@router.get("/library/materials/{material_id}", summary="Get material by ID from JSON library")
def get_library_material(material_id: str) -> Dict[str, Any]:
    """
    Get detailed information for a specific material from the JSON library.

    Returns error field if material not found.
    """
    mat = get_material_profile(material_id)

    if mat is None:
        return {
            "material_id": material_id,
            "error": f"Material not found: {material_id}"
        }

    return {
        "material_id": mat.material_id,
        "name": mat.name,
        "heat_sensitivity": mat.heat_sensitivity,
        "hardness": mat.hardness,
        "density_kg_m3": mat.density_kg_m3,
    }


# =============================================================================
# VALIDATION ENDPOINT
# =============================================================================

@router.get("/library/validate", summary="Validate tool library")
def validate_library_endpoint() -> Dict[str, Any]:
    """
    Validate the JSON tool and material library.

    Runs validation rules on all tools and materials.
    """
    lib = load_tool_library()
    errors = validate_library(lib)

    tool_count = len(lib.list_tool_ids())
    material_count = len(lib.list_material_ids())

    return {
        "valid": len(errors) == 0,
        "tool_count": tool_count,
        "material_count": material_count,
        "errors": errors,
    }


__all__ = ["router"]
