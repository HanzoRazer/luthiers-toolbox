"""
Luthier's Tool Box - CNC Guitar Lutherie CAD/CAM Toolbox
Pipeline Preset Router - Single-preset import/export endpoints

Repository: HanzoRazer/luthiers-toolbox
Updated: November 2025
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..services.pipeline_preset_store import PipelinePresetStore

router = APIRouter(prefix="/cam/pipeline/presets", tags=["cam", "pipeline", "presets"])
_store = PipelinePresetStore()


class PresetUpsertIn(BaseModel):
    id: Optional[str] = Field(
        None, description="If omitted, a new id will be generated from name."
    )
    name: str
    description: Optional[str] = None
    spec: Dict[str, Any]


@router.get("/{preset_id}/export")
async def export_preset(preset_id: str) -> Dict[str, Any]:
    """
    Export a single preset by ID.

    Args:
        preset_id: The ID of the preset to export

    Returns:
        The preset object with id, name, description, and spec
    """
    preset = _store.get(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found")
    return preset


@router.post("/import")
async def import_preset(
    body: PresetUpsertIn, overwrite: bool = Query(False)
) -> Dict[str, Any]:
    """
    Import a single preset.

    Args:
        body: The preset data (id optional, will be generated if missing)
        overwrite: If True, replace existing preset with same id

    Returns:
        {"status": "imported"|"skipped", "id": "...", "reason": "..."}
    """
    pid = body.id or _store.new_id(body.name)
    existing = _store.get(pid)

    if existing and not overwrite:
        return {
            "status": "skipped",
            "id": pid,
            "reason": "exists (use overwrite=true to replace)",
        }

    data = {"id": pid, **body.model_dump(exclude={"id"}, exclude_none=True)}
    _store.upsert(data)

    return {"status": "imported", "id": pid}
