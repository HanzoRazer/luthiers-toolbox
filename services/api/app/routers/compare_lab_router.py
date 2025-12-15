"""Compare Lab router for B22."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..models.compare_baseline import (
    Baseline,
    BaselineGeometry,
    BaselineToolpath,
)
from ..models.compare_diff import DiffResult
from ..services import compare_baseline_store
from ..services.geometry_diff import diff_geometry_segments


class BaselineCreate(BaseModel):
    name: str
    type: str = "geometry"
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    preset_id: str | None = None
    preset_name: str | None = None
    machine_id: str | None = None
    post_id: str | None = None
    geometry: BaselineGeometry | None = None
    toolpath: BaselineToolpath | None = None


class DiffPayload(BaseModel):
    baseline_id: str
    current_geometry: BaselineGeometry


class ExportPayload(DiffPayload):
    format: str = "json"

router = APIRouter(prefix="/api/compare/lab", tags=["Compare Lab"])


@router.get("/baselines", response_model=list[Baseline])
def list_compare_baselines() -> list[Baseline]:
    return compare_baseline_store.list_baselines()


@router.post("/baselines", response_model=Baseline)
def save_compare_baseline(baseline: BaselineCreate) -> Baseline:
    if not baseline.geometry:
        raise HTTPException(status_code=400, detail="Geometry payload required")
    return compare_baseline_store.save_baseline(baseline.model_dump())


@router.delete("/baselines/{baseline_id}")
def delete_compare_baseline(baseline_id: str) -> dict:
    deleted = compare_baseline_store.delete_baseline(baseline_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Baseline not found")
    return {"success": True}


def _compute_diff(payload: DiffPayload) -> DiffResult:
    baseline = compare_baseline_store.load_baseline(payload.baseline_id)
    if not baseline or not baseline.geometry:
        raise HTTPException(status_code=404, detail="Baseline not found")

    baseline_geom = baseline.geometry.model_dump()

    current_geometry = payload.current_geometry.model_dump()

    if current_geometry.get("units") and current_geometry.get("units") != baseline_geom.get("units"):
        raise HTTPException(status_code=400, detail="Mixed units not yet supported")

    return diff_geometry_segments(
        baseline_geom,
        current_geometry,
        baseline.id,
        baseline.name,
    )


@router.post("/diff", response_model=DiffResult)
def diff_baseline_geometry(payload: DiffPayload) -> DiffResult:
    return _compute_diff(payload)


@router.post("/export")
def export_compare_overlay(payload: ExportPayload) -> dict:
    diff = _compute_diff(payload)
    if payload.format == "json":
        return diff.model_dump()
    raise HTTPException(status_code=400, detail="Unsupported export format")
