# server/app/api/routes/manufacturing.py
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.schemas.rosette_pattern import RosettePatternInDB
from app.schemas.manufacturing_plan import ManufacturingPlan
from app.core.rosette_planner import generate_manufacturing_plan
from app.api.routes.rosette_patterns import ROSETTE_PATTERNS_DB

from app.schemas.job_log import RosettePlanJobLog
from app.api.routes.joblog import JOBLOG_DB

router = APIRouter(prefix="/rosette", tags=["rosette-manufacturing"])


class ManufacturingPlanRequest(BaseModel):
    pattern_id: str
    guitars: int = 1
    tile_length_mm: float = 8.0
    scrap_factor: float = 0.12
    record_joblog: bool = True


@router.post("/manufacturing-plan", response_model=ManufacturingPlan)
def manufacturing_plan(req: ManufacturingPlanRequest) -> ManufacturingPlan:
    """
    Compute a multi-strip-family manufacturing plan for a rosette pattern.

    Optionally (default) writes a RosettePlanJobLog entry into JOBLOG_DB.
    """
    pat: RosettePatternInDB | None = ROSETTE_PATTERNS_DB.get(req.pattern_id)
    if not pat:
        raise HTTPException(status_code=404, detail="Pattern not found")

    plan = generate_manufacturing_plan(
        pattern=pat,
        guitars=req.guitars,
        tile_length_mm=req.tile_length_mm,
        scrap_factor=req.scrap_factor,
    )

    if req.record_joblog:
        # Aggregate total tiles across all strip families
        total_tiles = sum(sp.total_tiles_needed for sp in plan.strip_plans)

        job_id = (
            f"rosette_plan_{pat.id}_"
            f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        )

        joblog_entry = RosettePlanJobLog(
            id=job_id,
            job_type="rosette_plan",
            pipeline_id=None,
            node_id=None,
            plan_pattern_id=pat.id,
            plan_guitars=req.guitars,
            plan_total_tiles=total_tiles,
            summary_risk_grade="GREEN",  # planner is logical only; treat as safe
            extra={
                "plan_type": "rosette_multifamily",
                "tile_length_mm": req.tile_length_mm,
                "scrap_factor": req.scrap_factor,
                "strip_plans": [sp.dict() for sp in plan.strip_plans],
            },
        )

        JOBLOG_DB[job_id] = joblog_entry

    return plan
