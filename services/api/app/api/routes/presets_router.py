# services/api/app/api/routes/presets_router.py
# Bundle B41 - UnifiedPresets Backend Skeleton
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ...util.presets_store import (
    PresetFilter,
    delete_preset,
    get_preset,
    insert_preset,
    list_presets,
    update_preset,
)

router = APIRouter(prefix="/api/presets", tags=["presets"])


PresetKind = Literal["cam", "export", "neck", "combo"]


class ExportIncludeFlags(BaseModel):
    include_baseline: bool = True
    include_candidate: bool = True
    include_diff_only: bool = False


class CamParams(BaseModel):
    stepover: float = Field(..., description="Fraction of tool diameter, e.g., 0.45")
    stepdown: float = Field(..., description="Stepdown per pass, in units")
    strategy: str = Field(..., description="Adaptive strategy name, e.g., Spiral/Lanes")
    margin: float = Field(..., description="Stock margin, in units")
    feed_xy: float = Field(..., description="Horizontal feed rate")
    safe_z: float = Field(..., description="Safe retract Z")
    z_rough: float = Field(..., description="Roughing Z level")


class ExportParams(BaseModel):
    default_format: str = Field(..., description="Default export format, e.g. 'gcode' or 'svg'")
    include_flags: ExportIncludeFlags = Field(default_factory=ExportIncludeFlags)
    filename_template: str = Field(
        "{preset}__{date}",
        description="Template with tokens like {preset}, {machine}, {neck_profile}, etc.",
    )
    default_directory: Optional[str] = Field(
        None,
        description="Optional default directory hint; purely advisory for now.",
    )


class NeckSectionDefault(BaseModel):
    name: str
    width_mm: float
    thickness_mm: float


class NeckParams(BaseModel):
    profile_id: str
    profile_name: str
    scale_length_mm: float
    section_defaults: List[NeckSectionDefault] = Field(default_factory=list)


class UnifiedPresetBase(BaseModel):
    kind: PresetKind
    name: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_by: Optional[str] = None
    job_source_id: Optional[str] = Field(
        None,
        description="Source job/run id if cloned from JobInt.",
    )
    source: Optional[str] = Field(
        None,
        description="Provenance hint: manual | clone | import | ...",
    )

    machine_id: Optional[str] = None
    post_id: Optional[str] = None
    units: Optional[Literal["mm", "inch"]] = None

    cam_params: Optional[CamParams] = None
    export_params: Optional[ExportParams] = None
    neck_params: Optional[NeckParams] = None


class PresetCreate(UnifiedPresetBase):
    """
    Request body for creating a preset. id/created_at are server-generated.
    """
    pass


class PresetUpdate(BaseModel):
    """
    Shallow PATCH of an existing preset. Any provided fields will overwrite
    the current value; missing fields are left as-is.
    """
    kind: Optional[PresetKind] = None
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    created_by: Optional[str] = None
    job_source_id: Optional[str] = None
    source: Optional[str] = None

    machine_id: Optional[str] = None
    post_id: Optional[str] = None
    units: Optional[Literal["mm", "inch"]] = None

    cam_params: Optional[CamParams] = None
    export_params: Optional[ExportParams] = None
    neck_params: Optional[NeckParams] = None


class UnifiedPreset(UnifiedPresetBase):
    id: str
    created_at: str


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@router.get("/", response_model=List[UnifiedPreset])
def list_presets_endpoint(
    kind: Optional[PresetKind] = Query(
        None,
        description="Optional kind filter: cam | export | neck | combo",
    ),
    tag: Optional[str] = Query(
        None,
        description="Optional tag filter; matches presets containing this tag.",
    ),
) -> List[UnifiedPreset]:
    """
    List all presets, optionally filtered by kind and/or tag.
    """
    raw = list_presets(PresetFilter(kind=kind, tag=tag))
    return [UnifiedPreset(**p) for p in raw]


@router.get("/{preset_id}", response_model=UnifiedPreset)
def get_preset_endpoint(preset_id: str) -> UnifiedPreset:
    """
    Retrieve a single preset by id.
    """
    p = get_preset(preset_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Preset not found")
    return UnifiedPreset(**p)


@router.post("/", response_model=UnifiedPreset, status_code=201)
def create_preset_endpoint(body: PresetCreate) -> UnifiedPreset:
    """
    Create a new preset. The backend generates id and created_at.
    """
    data: Dict[str, Any] = body.dict()
    data["created_at"] = _now_iso()
    inserted = insert_preset(data)
    return UnifiedPreset(**inserted)


@router.patch("/{preset_id}", response_model=UnifiedPreset)
def update_preset_endpoint(preset_id: str, body: PresetUpdate) -> UnifiedPreset:
    """
    Shallow update of an existing preset.
    """
    patch = body.dict(exclude_unset=True)
    if not patch:
        p = get_preset(preset_id)
        if p is None:
            raise HTTPException(status_code=404, detail="Preset not found")
        return UnifiedPreset(**p)

    updated = update_preset(preset_id, patch)
    if updated is None:
        raise HTTPException(status_code=404, detail="Preset not found")

    return UnifiedPreset(**updated)


@router.delete("/{preset_id}", status_code=204)
def delete_preset_endpoint(preset_id: str) -> None:
    """
    Delete a preset by id.
    """
    ok = delete_preset(preset_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Preset not found")
    # 204: no body
