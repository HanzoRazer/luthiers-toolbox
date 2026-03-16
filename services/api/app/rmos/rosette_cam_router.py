"""
Rosette CAM Router

Rosette CNC/CAM endpoints delegating to real cam.rosette engines.
Extracted from stub_routes.py during decomposition.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Query
from dataclasses import asdict
from shapely.errors import GEOSException

from ..cam.rosette.models import RosetteRingConfig, SegmentationResult, SliceBatch
from ..cam.rosette.tile_segmentation import (
    compute_tile_segmentation,
    generate_slices_for_ring,
    build_preview_snapshot,
)
from ..cam.rosette.rosette_cnc_wiring import build_ring_cnc_export
from ..cam.rosette.cnc import (
    MaterialType,
    JigAlignment,
    MachineEnvelope,
    MachineProfile,
    GCodePostConfig,
    generate_gcode_from_toolpaths,
)
from ..services.art_jobs_store import get_art_job, _load_jobs


router = APIRouter(tags=["rmos", "rosette", "cam"])


def _parse_ring_config(data: Dict[str, Any]) -> RosetteRingConfig:
    """Parse ring config from request payload."""
    return RosetteRingConfig(
        ring_id=data.get("ring_id", 0),
        radius_mm=float(data.get("radius_mm", 50.0)),
        width_mm=float(data.get("width_mm", 5.0)),
        tile_length_mm=float(data.get("tile_length_mm", 10.0)),
        kerf_mm=float(data.get("kerf_mm", 0.3)),
        herringbone_angle_deg=float(data.get("herringbone_angle_deg", 0.0)),
        twist_angle_deg=float(data.get("twist_angle_deg", 0.0)),
    )


@router.post("/rosette/segment-ring")
def generate_segment_ring(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generate rosette segment ring geometry."""
    if payload is None:
        payload = {}

    try:
        ring = _parse_ring_config(payload.get("ring", payload))
        tile_count_override = payload.get("tile_count")

        result = compute_tile_segmentation(ring, tile_count_override)

        return {
            "ok": True,
            "segmentation_id": result.segmentation_id,
            "ring_id": result.ring_id,
            "tile_count": result.tile_count,
            "tile_length_mm": result.tile_length_mm,
            "segments": [asdict(t) for t in result.tiles],
        }
    except (ValueError, TypeError, KeyError, AttributeError, ZeroDivisionError, GEOSException) as e:
        return {"ok": False, "error": str(e), "segments": []}


@router.post("/rosette/generate-slices")
def generate_slices(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generate rosette slices for manufacturing."""
    if payload is None:
        payload = {}

    try:
        ring = _parse_ring_config(payload.get("ring", payload))
        tile_count_override = payload.get("tile_count")

        segmentation = compute_tile_segmentation(ring, tile_count_override)
        batch = generate_slices_for_ring(ring, segmentation)

        return {
            "ok": True,
            "batch_id": batch.batch_id,
            "ring_id": batch.ring_id,
            "slices": [asdict(s) for s in batch.slices],
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "slices": []}


@router.post("/rosette/preview")
def preview_rosette(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generate rosette preview data."""
    if payload is None:
        payload = {}

    try:
        pattern_id = payload.get("pattern_id")
        rings_data = payload.get("rings", [])

        if not rings_data and any(k in payload for k in ["ring_id", "radius_mm"]):
            rings_data = [payload]

        rings = [_parse_ring_config(r) for r in rings_data]

        segmentations = {}
        slice_batches = {}

        for ring in rings:
            seg = compute_tile_segmentation(ring)
            segmentations[ring.ring_id] = seg

            batch = generate_slices_for_ring(ring, seg)
            slice_batches[ring.ring_id] = batch

        snapshot = build_preview_snapshot(pattern_id, rings, segmentations, slice_batches)

        return {
            "ok": True,
            "pattern_id": snapshot.pattern_id,
            "preview": snapshot.payload,
            "rings": [asdict(r) for r in snapshot.rings],
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "preview": None}


@router.post("/rosette/export-cnc")
def export_rosette_cnc(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Export rosette to CNC-ready G-code format."""
    if payload is None:
        payload = {}

    try:
        import uuid
        from datetime import datetime

        ring = _parse_ring_config(payload.get("ring", payload))
        tile_count_override = payload.get("tile_count")

        segmentation = compute_tile_segmentation(ring, tile_count_override)
        slice_batch = generate_slices_for_ring(ring, segmentation)

        material_str = payload.get("material", "hardwood").lower()
        material_map = {
            "hardwood": MaterialType.HARDWOOD,
            "softwood": MaterialType.SOFTWOOD,
            "composite": MaterialType.COMPOSITE,
        }
        material = material_map.get(material_str, MaterialType.HARDWOOD)

        jig_alignment = JigAlignment(
            origin_x_mm=float(payload.get("origin_x_mm", 0.0)),
            origin_y_mm=float(payload.get("origin_y_mm", 0.0)),
            rotation_deg=float(payload.get("rotation_deg", 0.0)),
        )

        envelope = MachineEnvelope(
            x_min_mm=-200.0,
            x_max_mm=200.0,
            y_min_mm=-200.0,
            y_max_mm=200.0,
            z_min_mm=-50.0,
            z_max_mm=50.0,
        )

        export_bundle, simulation = build_ring_cnc_export(
            ring=ring,
            slice_batch=slice_batch,
            material=material,
            jig_alignment=jig_alignment,
            envelope=envelope,
        )

        profile_str = payload.get("machine_profile", "grbl").lower()
        profile_map = {
            "grbl": MachineProfile.GRBL,
            "fanuc": MachineProfile.FANUC,
        }
        profile = profile_map.get(profile_str, MachineProfile.GRBL)

        post_config = GCodePostConfig(
            profile=profile,
            safe_z_mm=float(payload.get("safe_z_mm", 5.0)),
            spindle_rpm=int(payload.get("spindle_rpm", 12000)),
            tool_id=int(payload.get("tool_id", 1)),
        )
        gcode = generate_gcode_from_toolpaths(export_bundle.toolpaths, post_config)

        job_id = f"JOB-ROSETTE-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"

        return {
            "ok": True,
            "gcode": gcode,
            "job_id": job_id,
            "ring_id": ring.ring_id,
            "segment_count": len(export_bundle.toolpaths.segments),
            "estimated_runtime_sec": simulation.estimated_runtime_sec,
            "safety": {
                "decision": export_bundle.safety_decision.decision,
                "risk_level": export_bundle.safety_decision.risk_level,
                "requires_override": export_bundle.safety_decision.requires_override,
                "reasons": export_bundle.safety_decision.reasons,
            },
            "metadata": export_bundle.metadata,
        }
    except (ValueError, TypeError, KeyError, AttributeError, ZeroDivisionError, GEOSException) as e:
        return {
            "ok": False,
            "gcode": None,
            "job_id": None,
            "error": str(e),
        }


@router.get("/rosette/cnc-history")
def get_cnc_history(
    limit: int = Query(default=50, ge=1, le=200),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
) -> Dict[str, Any]:
    """Get CNC job history for rosettes."""
    all_jobs = _load_jobs()

    if job_type:
        filtered = [j for j in all_jobs if j.get("job_type") == job_type]
    else:
        filtered = [j for j in all_jobs if j.get("job_type", "").startswith("rosette")]

    filtered.sort(key=lambda x: x.get("created_at", 0), reverse=True)
    jobs = filtered[:limit]

    for job in jobs:
        if "created_at" in job and isinstance(job["created_at"], (int, float)):
            job["created_at"] = datetime.fromtimestamp(job["created_at"]).isoformat() + "Z"

    return {
        "jobs": jobs,
        "total": len(filtered),
    }


@router.get("/rosette/cnc-job/{job_id}")
def get_cnc_job(job_id: str) -> Dict[str, Any]:
    """Get CNC job details."""
    from fastapi import HTTPException

    job = get_art_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    created_at = job.created_at
    if isinstance(created_at, (int, float)):
        created_at = datetime.fromtimestamp(created_at).isoformat() + "Z"

    return {
        "job_id": job.id,
        "job_type": job.job_type,
        "created_at": created_at,
        "post_preset": job.post_preset,
        "rings": job.rings,
        "z_passes": job.z_passes,
        "length_mm": job.length_mm,
        "gcode_lines": job.gcode_lines,
        "meta": job.meta,
        "status": "complete",
    }
