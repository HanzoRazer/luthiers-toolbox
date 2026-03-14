"""Settings Router — CAM settings import/export endpoints.

Provides:
- GET /settings/summary - Get counts of machines, posts, presets
- GET /settings/export - Export full CAM configuration
- POST /settings/import - Import full CAM configuration
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from ....services.pipeline_preset_store import PipelinePresetStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings")


# =============================================================================
# SCHEMA MODELS
# =============================================================================


class MachineLimits(BaseModel):
    min_x: Optional[float] = None
    max_x: Optional[float] = None
    min_y: Optional[float] = None
    max_y: Optional[float] = None
    min_z: Optional[float] = None
    max_z: Optional[float] = None


class MachineCamDefaults(BaseModel):
    tool_d: Optional[float] = None
    stepover: Optional[float] = None
    stepdown: Optional[float] = None
    feed_xy: Optional[float] = None
    safe_z: Optional[float] = None
    z_rough: Optional[float] = None


class MachineIn(BaseModel):
    id: str
    name: str
    controller: Optional[str] = None
    description: Optional[str] = None
    units: Optional[str] = Field(default="mm", pattern="^(mm|inch|in)$")
    limits: Optional[MachineLimits] = None
    feed_xy: Optional[float] = None
    rapid: Optional[float] = None
    accel: Optional[float] = None
    camDefaults: Optional[MachineCamDefaults] = None


class LineNumberCfg(BaseModel):
    enabled: Optional[bool] = None
    start: Optional[int] = None
    step: Optional[int] = None
    prefix: Optional[str] = None


class PostOptions(BaseModel):
    use_percent: Optional[bool] = None
    use_o_word: Optional[bool] = None
    supports_arcs: Optional[bool] = None


class PostIn(BaseModel):
    id: str
    name: str
    dialect: Optional[str] = None
    description: Optional[str] = None
    line_numbers: Optional[LineNumberCfg] = None
    options: Optional[PostOptions] = None
    header_template: Optional[str] = None
    footer_template: Optional[str] = None
    canned_cycles: Optional[dict] = None


class PresetIn(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    spec: dict


class CamBackupIn(BaseModel):
    version: Optional[str] = None
    machines: List[MachineIn] = Field(default_factory=list)
    posts: List[PostIn] = Field(default_factory=list)
    pipeline_presets: List[PresetIn] = Field(default_factory=list)


# =============================================================================
# ROUTES
# =============================================================================


@router.get("/summary")
def get_settings_summary() -> Dict[str, Any]:
    """Return counts of machines, posts, and pipeline presets."""
    machines_count = 0
    posts_count = 0
    pipeline_presets_count = 0

    try:
        from ....services.machine_store import MachineStore
        ms = MachineStore()
        machines_count = len(ms.list_all())
    except (ImportError, OSError):
        pass

    try:
        from ....services.post_store import PostStore
        ps = PostStore()
        posts_count = len(ps.list_all())
    except (ImportError, OSError):
        pass

    try:
        pps = PipelinePresetStore()
        pipeline_presets_count = len(pps.list())
    except (ImportError, OSError, AttributeError):
        pass

    return {
        "machines_count": machines_count,
        "posts_count": posts_count,
        "pipeline_presets_count": pipeline_presets_count,
    }


@router.get("/export")
async def cam_settings_export() -> Dict[str, Any]:
    """Export full CAM configuration for backup/sharing."""
    machines: List[Dict[str, Any]] = []
    posts: List[Dict[str, Any]] = []
    presets: List[Dict[str, Any]] = []

    try:
        from ....services.machine_store import MachineStore
        m_store = MachineStore()
        machines = list(m_store.list_all() or [])
    except (ImportError, OSError):
        machines = []

    try:
        from ....services.post_store import PostStore
        p_store = PostStore()
        posts = list(p_store.list_all() or [])
    except (ImportError, OSError):
        posts = []

    try:
        pps = PipelinePresetStore()
        presets = list(pps.list() or [])
    except (ImportError, OSError, AttributeError):
        presets = []

    return {
        "version": "A_N",
        "machines": machines,
        "posts": posts,
        "pipeline_presets": presets,
    }


@router.post("/import")
async def cam_settings_import(
    payload: CamBackupIn, overwrite: bool = Query(False)
) -> Dict[str, Any]:
    """Import full CAM configuration (backup restore)."""
    report: Dict[str, Any] = {
        "imported": {"machines": 0, "posts": 0, "pipeline_presets": 0},
        "skipped": {"machines": 0, "posts": 0, "pipeline_presets": 0},
        "errors": [],
    }

    def add_error(kind: str, item_id: str, exc: Exception) -> None:
        report["errors"].append({"kind": kind, "id": item_id, "error": str(exc)})

    try:
        from ....services.machine_store import MachineStore
        mstore = MachineStore()
        existing_ids = {m.get("id") for m in (mstore.list_all() or [])}
        for m in payload.machines:
            try:
                if (m.id in existing_ids) and not overwrite:
                    report["skipped"]["machines"] += 1
                    continue
                mstore.upsert(m.model_dump(exclude_none=True))
                report["imported"]["machines"] += 1
            except (ValueError, TypeError, KeyError, OSError) as exc:
                logger.warning("Machine import failed for '%s': %s", m.id, exc)
                add_error("machine", m.id, exc)
    except (ImportError, OSError) as exc:
        add_error("machine_store", "_", exc)

    try:
        from ....services.post_store import PostStore
        pstore = PostStore()
        existing_ids = {p.get("id") for p in (pstore.list_all() or [])}
        for p in payload.posts:
            try:
                if (p.id in existing_ids) and not overwrite:
                    report["skipped"]["posts"] += 1
                    continue
                pstore.upsert(p.model_dump(exclude_none=True))
                report["imported"]["posts"] += 1
            except (ValueError, TypeError, KeyError, OSError) as exc:
                logger.warning("Post import failed for '%s': %s", p.id, exc)
                add_error("post", p.id, exc)
    except (ImportError, OSError) as exc:
        add_error("post_store", "_", exc)

    try:
        pps = PipelinePresetStore()
        existing = {pr.get("id") for pr in (pps.list() or [])}
        for pr in payload.pipeline_presets:
            try:
                pid = pr.id or pps.new_id(pr.name)
                if (pid in existing) and not overwrite:
                    report["skipped"]["pipeline_presets"] += 1
                    continue
                pps.upsert({**pr.model_dump(exclude_none=True), "id": pid})
                report["imported"]["pipeline_presets"] += 1
            except (ValueError, TypeError, KeyError, OSError) as exc:
                logger.warning("Pipeline preset import failed for '%s': %s", pr.id or pr.name, exc)
                add_error("pipeline_preset", pr.id or pr.name, exc)
    except (ImportError, OSError) as exc:
        add_error("preset_store", "_", exc)

    return report


__all__ = [
    "router",
    "MachineLimits",
    "MachineCamDefaults",
    "MachineIn",
    "LineNumberCfg",
    "PostOptions",
    "PostIn",
    "PresetIn",
    "CamBackupIn",
]
