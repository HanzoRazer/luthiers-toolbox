# services/api/app/services/pipeline_ops_rosette.py

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from app.services.art_jobs_store import get_art_job


class RosetteCamOpInput(BaseModel):
    """Input payload for a RosetteCam pipeline op."""

    job_id: str = Field(..., description="Existing Rosette CAM job id")
    post_preset: Optional[str] = Field(
        default=None,
        description="Optional override for post preset (e.g. 'grbl_safe')",
    )


class RosetteCamOpResult(BaseModel):
    """Normalized RosetteCam pipeline result."""

    status: str = Field(..., description="Pipeline status (e.g. 'ok')")
    job_id: str
    lane: str
    kind: str
    preset: Optional[str] = None
    toolpath_stats: Dict[str, Any] = Field(default_factory=dict)
    gcode_stats: Dict[str, Any] = Field(default_factory=dict)
    meta: Dict[str, Any] = Field(default_factory=dict)


def _derive_lane(job_meta: Optional[Dict[str, Any]]) -> str:
    if isinstance(job_meta, dict):
        lane = job_meta.get("lane")
        if isinstance(lane, str) and lane:
            return lane
    return "rosette"


def _build_toolpath_stats(job) -> Dict[str, Any]:
    stats: Dict[str, Any] = {}
    if isinstance(job.meta, dict):
        meta_stats = job.meta.get("toolpath_stats")
        if isinstance(meta_stats, dict):
            stats.update(meta_stats)

    if job.rings is not None and "rings" not in stats:
        stats["rings"] = job.rings
    if job.z_passes is not None and "z_passes" not in stats:
        stats["z_passes"] = job.z_passes
    if job.length_mm is not None and "length" not in stats:
        stats["length"] = job.length_mm
        stats.setdefault("length_units", "mm")

    return stats


def _build_gcode_stats(job) -> Dict[str, Any]:
    stats: Dict[str, Any] = {}
    if isinstance(job.meta, dict):
        meta_stats = job.meta.get("gcode_stats")
        if isinstance(meta_stats, dict):
            stats.update(meta_stats)

    if job.gcode_lines is not None and "lines" not in stats:
        stats["lines"] = job.gcode_lines

    return stats


def run_rosette_cam_op(input: RosetteCamOpInput) -> RosetteCamOpResult:
    """Execute a RosetteCam op by hydrating an existing Rosette CAM job."""

    job = get_art_job(input.job_id)
    if job is None:
        raise ValueError(f"Rosette job '{input.job_id}' not found")

    lane = _derive_lane(job.meta)
    if lane != "rosette":
        raise ValueError(
            f"RosetteCam op expected lane 'rosette' but received '{lane}'"
        )

    kind = "RosetteCam"
    if isinstance(job.meta, dict):
        kind = job.meta.get("kind") or kind

    preset = input.post_preset or job.post_preset

    toolpath_stats = _build_toolpath_stats(job)
    gcode_stats = _build_gcode_stats(job)
    meta = job.meta if isinstance(job.meta, dict) else {}

    return RosetteCamOpResult(
        status="ok",
        job_id=job.id,
        lane=lane,
        kind=kind,
        preset=preset,
        toolpath_stats=toolpath_stats,
        gcode_stats=gcode_stats,
        meta=meta,
    )
