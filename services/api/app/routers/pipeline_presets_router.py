# services/api/app/routers/pipeline_presets_router.py
"""
Pipeline presets router - named machine/post/units recipes.

Stores lightweight presets (not full op graphs) in JSON file.
Front-end constructs pipeline from preset settings.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import List, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/cam/pipeline", tags=["cam", "pipeline", "presets"])

PRESETS_PATH = Path(__file__).resolve().parent.parent / "data" / "pipeline_presets.json"
PRESETS_PATH.parent.mkdir(parents=True, exist_ok=True)


class PipelinePreset(BaseModel):
    """Named recipe for machine/post/units configuration."""
    id: str
    name: str
    description: Optional[str] = None
    units: Literal["mm", "inch"] = "mm"
    machine_id: Optional[str] = Field(
        None, description="Machine profile ID associated with this recipe."
    )
    post_id: Optional[str] = Field(
        None, description="Post preset ID associated with this recipe."
    )


class PipelinePresetCreate(BaseModel):
    """Create request for new preset."""
    name: str
    description: Optional[str] = None
    units: Literal["mm", "inch"] = "mm"
    machine_id: Optional[str] = None
    post_id: Optional[str] = None


def _load_presets() -> List[PipelinePreset]:
    """Load presets from JSON file."""
    if not PRESETS_PATH.exists():
        return []
    try:
        raw = json.loads(PRESETS_PATH.read_text(encoding="utf-8") or "[]")
        return [PipelinePreset(**item) for item in raw]
    except Exception:
        # Corrupt or invalid file; treat as empty
        return []


def _save_presets(presets: List[PipelinePreset]) -> None:
    """Save presets to JSON file."""
    data = [p.model_dump() for p in presets]
    PRESETS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


@router.get("/presets", response_model=List[PipelinePreset])
def list_presets() -> List[PipelinePreset]:
    """List all saved pipeline presets."""
    return _load_presets()


@router.post("/presets", response_model=PipelinePreset, status_code=201)
def create_preset(body: PipelinePresetCreate) -> PipelinePreset:
    """Create new pipeline preset."""
    presets = _load_presets()

    # Basic uniqueness by name (case-insensitive)
    for p in presets:
        if p.name.strip().lower() == body.name.strip().lower():
            raise HTTPException(
                status_code=400,
                detail=f"A preset named '{body.name}' already exists.",
            )

    new = PipelinePreset(
        id=str(uuid.uuid4()),
        name=body.name.strip(),
        description=body.description,
        units=body.units,
        machine_id=body.machine_id,
        post_id=body.post_id,
    )
    presets.append(new)
    _save_presets(presets)
    return new


@router.get("/presets/{preset_id}", response_model=PipelinePreset)
def get_preset(preset_id: str) -> PipelinePreset:
    """Get specific preset by ID."""
    presets = _load_presets()
    for p in presets:
        if p.id == preset_id:
            return p
    raise HTTPException(status_code=404, detail="Preset not found")


@router.delete("/presets/{preset_id}", status_code=204)
def delete_preset(preset_id: str) -> None:
    """Delete preset by ID."""
    presets = _load_presets()
    new_presets = [p for p in presets if p.id != preset_id]
    if len(new_presets) == len(presets):
        raise HTTPException(status_code=404, detail="Preset not found")
    _save_presets(new_presets)
