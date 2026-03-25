# services/api/app/rmos/api_ai_snapshots.py
"""
Generator Snapshot API - Inspect generator behavior for tuning and debugging.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from .api_contracts import RmosContext
from .models import SearchBudgetSpec
from .generator_snapshot import snapshot_generator_behavior, GeneratorSampleStats
from .constraint_profiles import RosetteGeneratorConstraints

router = APIRouter(
    prefix="/rmos/ai/snapshots",
    tags=["rmos-ai-snapshots"],
)


class RosetteGeneratorConstraintsModel(BaseModel):
    """Pydantic model for RosetteGeneratorConstraints."""
    min_rings: int
    max_rings: int
    min_ring_width_mm: float
    max_ring_width_mm: float
    min_total_width_mm: float
    max_total_width_mm: float
    allow_mosaic: bool
    allow_segmented: bool
    palette_key: str
    bias_simple: bool

    @classmethod
    def from_dataclass(cls, c: RosetteGeneratorConstraints) -> "RosetteGeneratorConstraintsModel":
        return cls(
            min_rings=c.min_rings,
            max_rings=c.max_rings,
            min_ring_width_mm=c.min_ring_width_mm,
            max_ring_width_mm=c.max_ring_width_mm,
            min_total_width_mm=c.min_total_width_mm,
            max_total_width_mm=c.max_total_width_mm,
            allow_mosaic=c.allow_mosaic,
            allow_segmented=c.allow_segmented,
            palette_key=c.palette_key,
            bias_simple=c.bias_simple,
        )


class GeneratorSnapshotResponse(BaseModel):
    """API response model for generator behavior snapshot."""

    tool_id: Optional[str]
    material_id: Optional[str]
    machine_id: Optional[str]

    n_samples: int

    profile: RosetteGeneratorConstraintsModel

    ring_count_min: int
    ring_count_max: int
    ring_count_avg: float

    total_width_min_mm: float
    total_width_max_mm: float
    total_width_avg_mm: float


@router.get(
    "",
    response_model=GeneratorSnapshotResponse,
    summary="Sample generator behavior for a given context.",
)
def get_generator_snapshot(
    tool_id: str | None = Query(default=None),
    material_id: str | None = Query(default=None),
    machine_id: str | None = Query(default=None),
    n_samples: int = Query(
        default=50,
        ge=5,
        le=500,
        description="Number of samples to generate for the snapshot.",
    ),
    max_attempts: int = Query(
        default=50,
        ge=1,
        le=200,
        description="SearchBudgetSpec.max_attempts used for RNG seeding / policy.",
    ),
    time_limit_seconds: float = Query(
        default=5.0,
        ge=0.1,
        le=60.0,
        description="SearchBudgetSpec.time_limit_seconds.",
    ),
    deterministic: bool = Query(
        default=True,
        description="Whether to use deterministic RNG per attempt.",
    ),
) -> GeneratorSnapshotResponse:
    """
    Build a temporary RmosContext + SearchBudgetSpec and run a generator snapshot
    without going through the full feasibility loop.
    """
    ctx = RmosContext(
        tool_id=tool_id,
        material_id=material_id,
        machine_profile_id=machine_id,
    )

    budget = SearchBudgetSpec(
        max_attempts=max_attempts,
        time_limit_seconds=time_limit_seconds,
        min_feasibility_score=0.0,
        stop_on_first_green=False,
        deterministic=deterministic,
    )

    stats: GeneratorSampleStats = snapshot_generator_behavior(
        ctx=ctx,
        budget=budget,
        n_samples=n_samples,
    )

    return GeneratorSnapshotResponse(
        tool_id=stats.tool_id,
        material_id=stats.material_id,
        machine_id=stats.machine_id,
        n_samples=stats.n_samples,
        profile=RosetteGeneratorConstraintsModel.from_dataclass(stats.profile),
        ring_count_min=stats.ring_count_min,
        ring_count_max=stats.ring_count_max,
        ring_count_avg=stats.ring_count_avg,
        total_width_min_mm=stats.total_width_min_mm,
        total_width_max_mm=stats.total_width_max_mm,
        total_width_avg_mm=stats.total_width_avg_mm,
    )
