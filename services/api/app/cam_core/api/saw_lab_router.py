"""Saw Lab placeholder endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException

from ..saw_lab.models import SawLabRun

router = APIRouter(prefix="/saw-lab", tags=["cam-core", "saw-lab"])


@router.get("/runs/{run_id}")
def get_run(run_id: str) -> SawLabRun:
    raise HTTPException(status_code=404, detail="Saw Lab run not found")


@router.post("/runs")
def create_run(body: Dict[str, Any]) -> SawLabRun:
    return SawLabRun(id="placeholder", created_at=datetime.utcnow())
