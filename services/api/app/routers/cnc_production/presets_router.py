"""CNC Production preset CRUD endpoints (B20)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...services.preset_store import load_all_presets, save_all_presets

router = APIRouter(prefix="/cnc/presets", tags=["cnc-production", "presets"])


class PresetIn(BaseModel):
    name: str
    description: str = ""
    lane: str = "adaptive"
    machine_id: Optional[str] = None
    post_id: Optional[str] = None
    material: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    params: Dict[str, Any] = Field(default_factory=dict)
    stats: Dict[str, Any] = Field(default_factory=dict)
    job_source_id: Optional[str] = None
    baseline_id: Optional[str] = None


@router.get("")
def list_presets() -> List[Dict[str, Any]]:
    return load_all_presets()


@router.get("/{preset_id}")
def get_preset(preset_id: str) -> Dict[str, Any]:
    presets = load_all_presets()
    for preset in presets:
        if str(preset.get("id")) == str(preset_id):
            return preset
    raise HTTPException(status_code=404, detail="Preset not found")


@router.post("")
def create_preset(payload: PresetIn) -> Dict[str, Any]:
    presets = load_all_presets()
    record = payload.model_dump()
    now = datetime.now(timezone.utc).isoformat()
    record.setdefault("id", str(uuid4()))
    record.setdefault("created_at", now)
    record["updated_at"] = now
    presets.append(record)
    save_all_presets(presets)
    return record


@router.patch("/{preset_id}")
def update_preset(preset_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    presets = load_all_presets()
    for idx, preset in enumerate(presets):
        if str(preset.get("id")) == str(preset_id):
            merged = {**preset, **payload}
            merged["updated_at"] = datetime.now(timezone.utc).isoformat()
            presets[idx] = merged
            save_all_presets(presets)
            return merged
    raise HTTPException(status_code=404, detail="Preset not found")


@router.delete("/{preset_id}")
def delete_preset(preset_id: str) -> Dict[str, Any]:
    presets = load_all_presets()
    kept = [p for p in presets if str(p.get("id")) != str(preset_id)]
    if len(kept) == len(presets):
        raise HTTPException(status_code=404, detail="Preset not found")
    save_all_presets(kept)
    return {"ok": True, "deleted": preset_id}
