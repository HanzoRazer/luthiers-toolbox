"""CAM Run Logs API - Write and query execution telemetry."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..telemetry.cam_logs import fetch_caps_by_machine, insert_run, insert_segments

router = APIRouter(tags=["cam-logs"])


class RunIn(BaseModel):
    """Metadata for a single CAM run (plan or execution)."""

    job_name: Optional[str] = None
    machine_id: str
    material_id: str
    tool_d: float
    stepover: float  # 0..1
    stepdown: float
    post_id: Optional[str] = None
    feed_xy: Optional[float] = None
    rpm: Optional[int] = None
    est_time_s: Optional[float] = None  # Predicted time (jerk-aware)
    act_time_s: Optional[float] = None  # Actual time if known
    notes: Optional[str] = None


class SegmentIn(BaseModel):
    """Per-segment telemetry (G-code line details)."""

    idx: int
    code: str  # G0, G1, G2, G3
    x: Optional[float] = None
    y: Optional[float] = None
    len_mm: Optional[float] = None
    limit: Optional[str] = None  # feed_cap|accel|jerk|none
    slowdown: Optional[float] = None  # meta.slowdown (engagement penalty)
    trochoid: Optional[bool] = None  # Trochoidal arc flag
    radius_mm: Optional[float] = None  # Arc radius for G2/G3
    feed_f: Optional[float] = None  # Stamped feed on line


class RunWithSegmentsIn(BaseModel):
    """Complete run log (run metadata + all segments)."""

    run: RunIn
    segments: List[SegmentIn]


@router.post("/write")
def write_log(body: RunWithSegmentsIn) -> Dict[str, Any]:
    """
    Log a CAM run with per-segment details.

    Returns run_id for reference in subsequent queries or training.
    """
    rid = insert_run(body.run.model_dump())
    insert_segments(rid, [s.model_dump() for s in body.segments])
    return {"status": "ok", "run_id": rid}


@router.get("/caps/{machine_id}")
def caps(machine_id: str) -> Dict[str, Any]:
    """
    Get bottleneck distribution (feed_cap/accel/jerk/none counts) for a machine.

    Useful for profiling: if 80% of moves are feed-capped, increasing feed won't help.
    """
    rows = fetch_caps_by_machine(machine_id)
    return {r["limit"]: r["c"] for r in rows}
