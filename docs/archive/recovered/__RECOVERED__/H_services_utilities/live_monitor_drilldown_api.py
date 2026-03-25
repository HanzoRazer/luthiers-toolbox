"""
RMOS N10.1: LiveMonitor Drill-Down API

Endpoint for fetching deep subjob and CAM event details for a job.
"""

from __future__ import annotations
from fastapi import APIRouter, HTTPException

from ..core.live_monitor_event_builder import SubjobEventBuilder
from app.api.deps.rmos_stores import get_joblog_store

router = APIRouter(prefix="/rmos/live-monitor", tags=["live-monitor"])


@router.get("/{job_id}/drilldown")
def get_drilldown(job_id: str):
    """
    Get drill-down subjob and CAM event details for a job.
    
    Returns:
        {
            "job_id": "J_001",
            "subjobs": [
                {
                    "subjob_type": "roughing",
                    "started_at": "2025-11-30T12:00:00",
                    "ended_at": "2025-11-30T12:05:00",
                    "cam_events": [
                        {
                            "timestamp": "2025-11-30T12:01:00",
                            "feedrate": 800,
                            "spindle_speed": 18000,
                            "doc": 0.3,
                            "feed_state": "decreasing",
                            "heuristic": "warning",
                            "message": null
                        }
                    ]
                }
            ]
        }
    
    Raises:
        404: Job not found
    """
    store = get_joblog_store()
    job = store.get(job_id)

    if not job:
        raise HTTPException(404, detail=f"Job '{job_id}' not found.")

    builder = SubjobEventBuilder()
    subjobs = builder.build_subjobs_from_metadata(job)

    return {
        "job_id": job_id,
        "subjobs": [sj.dict() for sj in subjobs]
    }
