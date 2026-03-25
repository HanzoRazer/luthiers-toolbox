"""
RMOS Presets API Routes

Provides endpoints for listing and managing material/tool presets.
"""
from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from .presets import (
    MaterialPreset,
    ToolPreset,
    PresetCollection,
    get_preset_registry,
)


router = APIRouter(
    prefix="/api/rmos/presets",
    tags=["rmos_presets"],
)


# ---------------------------------------------------------------------------
# Material Presets
# ---------------------------------------------------------------------------

@router.get("/materials", response_model=List[MaterialPreset])
async def list_material_presets() -> List[MaterialPreset]:
    """List all available material presets."""
    registry = get_preset_registry()
    return registry.list_materials()


@router.get("/materials/{preset_id}", response_model=MaterialPreset)
async def get_material_preset(preset_id: str) -> MaterialPreset:
    """Get a specific material preset by ID."""
    registry = get_preset_registry()
    preset = registry.get_material(preset_id)
    if preset is None:
        raise HTTPException(status_code=404, detail=f"Material preset '{preset_id}' not found")
    return preset


@router.post("/materials", response_model=MaterialPreset, status_code=201)
async def create_material_preset(preset: MaterialPreset) -> MaterialPreset:
    """Create or update a material preset."""
    registry = get_preset_registry()
    registry.add_material(preset)
    return preset


@router.delete("/materials/{preset_id}")
async def delete_material_preset(preset_id: str) -> dict:
    """Delete a material preset."""
    registry = get_preset_registry()
    if not registry.remove_material(preset_id):
        raise HTTPException(status_code=404, detail=f"Material preset '{preset_id}' not found")
    return {"ok": True, "deleted": preset_id}


# ---------------------------------------------------------------------------
# Tool Presets
# ---------------------------------------------------------------------------

@router.get("/tools", response_model=List[ToolPreset])
async def list_tool_presets(
    tool_type: Optional[str] = Query(None, description="Filter by tool type (endmill, saw, etc.)"),
) -> List[ToolPreset]:
    """List all available tool presets, optionally filtered by type."""
    registry = get_preset_registry()
    tools = registry.list_tools()
    
    if tool_type:
        tools = [t for t in tools if t.tool_type == tool_type]
    
    return tools


@router.get("/tools/{preset_id}", response_model=ToolPreset)
async def get_tool_preset(preset_id: str) -> ToolPreset:
    """Get a specific tool preset by ID."""
    registry = get_preset_registry()
    preset = registry.get_tool(preset_id)
    if preset is None:
        raise HTTPException(status_code=404, detail=f"Tool preset '{preset_id}' not found")
    return preset


@router.post("/tools", response_model=ToolPreset, status_code=201)
async def create_tool_preset(preset: ToolPreset) -> ToolPreset:
    """Create or update a tool preset."""
    registry = get_preset_registry()
    registry.add_tool(preset)
    return preset


@router.delete("/tools/{preset_id}")
async def delete_tool_preset(preset_id: str) -> dict:
    """Delete a tool preset."""
    registry = get_preset_registry()
    if not registry.remove_tool(preset_id):
        raise HTTPException(status_code=404, detail=f"Tool preset '{preset_id}' not found")
    return {"ok": True, "deleted": preset_id}


# ---------------------------------------------------------------------------
# Collection Endpoint
# ---------------------------------------------------------------------------

@router.get("/all", response_model=PresetCollection)
async def get_all_presets() -> PresetCollection:
    """Get all material and tool presets as a collection."""
    registry = get_preset_registry()
    return registry.get_collection()
