"""
RMOS Live Monitor Router

Live monitor drilldown endpoints wired to runs_v2 store.
Extracted from stub_routes.py during decomposition.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter

from .runs_v2.store_api import get_run as get_run_artifact


router = APIRouter(tags=["rmos", "live-monitor"])


def _synthesize_subjobs_from_run(run: Any) -> List[Dict[str, Any]]:
    """
    Synthesize subjob phases from run artifact data.

    Creates subjobs based on the operation mode and parameters.
    Generates CAM events from planned parameters (feedrate, spindle, DOC).
    """
    subjobs = []
    created_at = run.created_at_utc if hasattr(run, 'created_at_utc') else datetime.now(timezone.utc)
    if isinstance(created_at, str):
        try:
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        except ValueError:
            created_at = datetime.now(timezone.utc)

    req = run.request_summary if hasattr(run, 'request_summary') else {}
    feed_xy = float(req.get('feed_xy', req.get('feed', req.get('feedrate', 1000))))
    spindle = float(req.get('spindle_rpm', req.get('rpm', req.get('spindle', 18000))))
    doc = float(req.get('stepdown', req.get('depth_of_cut', req.get('doc', 3.0))))
    tool_d = float(req.get('tool_d', req.get('tool_diameter', 6.0)))

    decision = run.decision if hasattr(run, 'decision') else {}
    risk_level = decision.risk_level if hasattr(decision, 'risk_level') else decision.get('risk_level', 'GREEN')

    heuristic_map = {'GREEN': 'info', 'YELLOW': 'warning', 'RED': 'danger'}
    base_heuristic = heuristic_map.get(str(risk_level).upper(), 'info')

    mode = run.mode if hasattr(run, 'mode') else 'router'
    if mode in ('saw', 'saw_lab'):
        phases = [('infeed', 0.1), ('roughing', 0.6), ('outfeed', 0.1)]
    else:
        phases = [('roughing', 0.5), ('profiling', 0.3), ('finishing', 0.2)]

    elapsed = timedelta(seconds=0)
    for phase_type, time_fraction in phases:
        phase_duration = timedelta(seconds=30 * time_fraction)
        start_time = created_at + elapsed
        end_time = start_time + phase_duration

        cam_events = []
        event_count = 3 if phase_type in ('infeed', 'outfeed') else 5
        for i in range(event_count):
            event_time = start_time + (phase_duration * i / event_count)

            if phase_type == 'roughing':
                event_feed = feed_xy * 0.8
                event_doc = doc
            elif phase_type == 'finishing':
                event_feed = feed_xy * 0.6
                event_doc = doc * 0.3
            else:
                event_feed = feed_xy
                event_doc = doc * 0.5

            if i == 0:
                feed_state = 'increasing'
            elif i == event_count - 1:
                feed_state = 'decreasing'
            else:
                feed_state = 'stable'

            cam_events.append({
                'timestamp': event_time.isoformat(),
                'feedrate': round(event_feed, 1),
                'spindle_speed': round(spindle, 0),
                'doc': round(event_doc, 2),
                'feed_state': feed_state,
                'heuristic': base_heuristic,
            })

        subjobs.append({
            'subjob_type': phase_type,
            'started_at': start_time.isoformat(),
            'ended_at': end_time.isoformat(),
            'cam_events': cam_events,
        })

        elapsed += phase_duration

    return subjobs


@router.get("/live-monitor/{job_id}/drilldown")
def get_live_monitor_drilldown(job_id: str) -> Dict[str, Any]:
    """
    Get live monitor drilldown data for a job.

    Synthesizes subjob phases and CAM events from stored run artifact data.
    """
    run = get_run_artifact(job_id)

    if not run:
        return {
            "job_id": job_id,
            "subjobs": [],
            "status": "not_found",
            "message": f"No run found for job_id: {job_id}",
        }

    subjobs = _synthesize_subjobs_from_run(run)
    status = run.status.value if hasattr(run.status, 'value') else str(run.status)

    return {
        "job_id": job_id,
        "subjobs": subjobs,
        "status": status.lower(),
        "message": None,
    }
