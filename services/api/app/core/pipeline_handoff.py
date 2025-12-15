from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, Optional, Tuple

from app.schemas.pipeline_handoff import PipelineHandoffRequest
from app.core.cam_profile_registry import summarize_profiles_for_family

EXPORT_DIR = os.path.join("exports", "rmos_handoff")


def _ensure_export_dir() -> None:
    os.makedirs(EXPORT_DIR, exist_ok=True)


def try_pipeline_service_handoff(payload: Dict[str, Any]) -> Optional[str]:
    """Attempt to hand off payload to the primary pipeline service."""
    try:
        from app.pipeline.service import PIPELINE_SERVICE  # type: ignore

        job = PIPELINE_SERVICE.create_job(payload)  # type: ignore[attr-defined]
        return getattr(job, "id", None)
    except Exception:
        return None


def local_queue_handoff(payload: Dict[str, Any]) -> Tuple[str, str]:
    """Persist payload to exports/rmos_handoff for later ingestion."""
    _ensure_export_dir()
    job_id = f"rmos_handoff_{int(time.time())}"
    path = os.path.join(EXPORT_DIR, f"{job_id}.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return job_id, path


def build_pipeline_payload(req: PipelineHandoffRequest) -> Dict[str, Any]:
    payload = {
        "job_type": "rmos_rosette_saw_batch",
        "lane": req.lane,
        "machine_profile": req.machine_profile,
        "priority": req.priority,
        "notes": req.notes,
        "pattern_id": req.pattern_id,
        "batch_op": req.batch_op,
        "manufacturing_plan": req.manufacturing_plan,
        "geometry_source": req.batch_op.get("geometry_source"),
        "tool_id": req.batch_op.get("tool_id"),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    
    # MM-2: Add CAM profile summary if strip family materials are present
    strip_family = req.batch_op.get("strip_family")
    if strip_family:
        try:
            cam_summary = summarize_profiles_for_family(strip_family)
            payload.setdefault("metadata", {})
            payload["metadata"]["cam_profile_summary"] = cam_summary
            payload["metadata"]["materials"] = strip_family.get("materials") or []
            
            # Lane hint injection based on CAM profiles
            lane_hint = cam_summary.get("dominant_lane_hint")
            if lane_hint and not req.lane:
                payload["metadata"]["suggested_lane"] = lane_hint
            
            # Flag fragile jobs (MM-4 will use this for risk modeling)
            worst_fragility = cam_summary.get("worst_fragility_score", 0.0)
            if worst_fragility >= 0.75:
                payload["metadata"]["fragile_job"] = True
                payload["metadata"]["fragility_reason"] = f"Worst material fragility: {worst_fragility:.2f}"
        except Exception:
            # Don't fail handoff if CAM summary fails
            pass
    
    return payload


def handoff_to_pipeline(req: PipelineHandoffRequest) -> Dict[str, Any]:
    payload = build_pipeline_payload(req)

    pipeline_job_id = try_pipeline_service_handoff(payload)
    if pipeline_job_id:
        return {
            "success": True,
            "handoff_mode": "pipeline_service",
            "job_id": pipeline_job_id,
            "message": "Handoff delivered to pipeline service.",
            "payload_path": None,
        }

    job_id, path = local_queue_handoff(payload)
    return {
        "success": True,
        "handoff_mode": "local_queue",
        "job_id": job_id,
        "message": "Pipeline service not detected; payload queued locally.",
        "payload_path": path,
    }
