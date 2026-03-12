"""
Rosette Manufacturing Routes — Phase 2 Consolidation

Wires the orphaned rosette_planner (manufacturing plan generator) and
TraditionalBuilder (craftsman project sheets) to the Art Studio API.

Endpoints:
    POST /api/art/rosette/manufacturing-plan   — Generate multi-family manufacturing plan
    GET  /api/art/rosette/traditional/masters   — List patterns grouped by master luthier
    GET  /api/art/rosette/traditional/patterns/{pattern_id} — Get pattern info
    POST /api/art/rosette/traditional/project   — Generate full traditional rosette project
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...schemas.rosette_pattern import RosettePatternInDB, RosetteRingBand
from ...schemas.manufacturing_plan import ManufacturingPlan
from ...core.rosette_planner import generate_manufacturing_plan

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/art/rosette",
    tags=["Art Studio", "Rosette Manufacturing"],
)


# ── Manufacturing Plan ──────────────────────────────────────────────────────

class ManufacturingPlanRequest(BaseModel):
    """Request body for manufacturing plan generation."""

    pattern: RosettePatternInDB = Field(
        ..., description="Full rosette pattern definition with ring bands"
    )
    guitars: int = Field(default=1, ge=1, le=500, description="Number of guitars to plan for")
    tile_length_mm: float = Field(default=8.0, ge=1.0, le=50.0, description="Default tile length (mm)")
    scrap_factor: float = Field(
        default=0.12, ge=0.0, le=1.0,
        description="Extra tiles fraction (0.12 = 12%% scrap allowance)"
    )


@router.post("/manufacturing-plan", response_model=ManufacturingPlan)
def create_manufacturing_plan(req: ManufacturingPlanRequest) -> ManufacturingPlan:
    """
    Generate a multi-family manufacturing plan for a rosette pattern.

    Computes tile counts, strip lengths, and stick requirements grouped
    by strip family, with scrap allowances. Returns everything a shop
    needs to prepare materials for a batch of guitars.
    """
    try:
        plan = generate_manufacturing_plan(
            pattern=req.pattern,
            guitars=req.guitars,
            tile_length_mm=req.tile_length_mm,
            scrap_factor=req.scrap_factor,
        )
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return plan


# ── Traditional Builder ─────────────────────────────────────────────────────

BUILDER_AVAILABLE = False
try:
    from ...cam.rosette.traditional_builder import TraditionalBuilder
    BUILDER_AVAILABLE = True
except ImportError as exc:
    logger.warning("TraditionalBuilder unavailable: %s", exc)


def _get_builder() -> TraditionalBuilder:
    if not BUILDER_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Traditional builder module is not available",
        )
    return TraditionalBuilder()


class PatternInfoResponse(BaseModel):
    id: str
    name: str
    rows: int
    columns: int
    materials: List[str]
    strip_width_mm: float
    strip_thickness_mm: float
    chip_length_mm: float
    notes: Optional[str] = None


class CutListItem(BaseModel):
    species: str
    num_strips: int
    strip_width_mm: float
    strip_length_mm: float
    strip_thickness_mm: float


class StickItem(BaseModel):
    stick_number: int
    strips: List[List]  # [[species, count], ...]
    total_strips: int


class AssemblyInfo(BaseModel):
    sequence: List[int]
    description: str
    pattern_width_chips: int


class TraditionalProjectResponse(BaseModel):
    name: str
    master_attribution: Optional[str] = None
    description: str
    cut_list: List[CutListItem]
    stick_definitions: List[StickItem]
    assembly_sequence: AssemblyInfo
    strip_width_mm: float
    strip_thickness_mm: float
    chip_length_mm: float
    instructions: List[str]
    difficulty: str
    estimated_time_hours: float
    notes: List[str]
    project_sheet: str = Field(description="Formatted printable project sheet")


class TraditionalProjectRequest(BaseModel):
    pattern_id: str = Field(..., description="Preset pattern ID (e.g. 'torres_diamond_7x9')")
    panel_length_mm: float = Field(default=300.0, ge=50.0, le=1000.0)


@router.get("/traditional/masters", response_model=Dict[str, List[str]])
def list_master_patterns() -> Dict[str, List[str]]:
    """List available traditional patterns grouped by master luthier."""
    builder = _get_builder()
    return builder.list_master_patterns()


@router.get("/traditional/patterns/{pattern_id}", response_model=PatternInfoResponse)
def get_traditional_pattern_info(pattern_id: str) -> PatternInfoResponse:
    """Get human-readable info about a traditional pattern preset."""
    builder = _get_builder()
    try:
        info = builder.get_pattern_info(pattern_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return PatternInfoResponse(**info)


@router.post("/traditional/project", response_model=TraditionalProjectResponse)
def create_traditional_project(req: TraditionalProjectRequest) -> TraditionalProjectResponse:
    """
    Generate a complete traditional rosette project.

    Returns cut lists, stick definitions, assembly sequence, step-by-step
    instructions, and a formatted printable project sheet — everything a
    craftsman needs for the shop.
    """
    builder = _get_builder()
    try:
        project = builder.create_project(
            pattern_id=req.pattern_id,
            panel_length_mm=req.panel_length_mm,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return TraditionalProjectResponse(
        name=project.name,
        master_attribution=project.master_attribution,
        description=project.description,
        cut_list=[
            CutListItem(
                species=c.species,
                num_strips=c.num_strips,
                strip_width_mm=c.strip_width_mm,
                strip_length_mm=c.strip_length_mm,
                strip_thickness_mm=c.strip_thickness_mm,
            )
            for c in project.cut_list
        ],
        stick_definitions=[
            StickItem(
                stick_number=s.stick_number,
                strips=[[sp, cnt] for sp, cnt in s.strips],
                total_strips=s.total_strips,
            )
            for s in project.stick_definitions
        ],
        assembly_sequence=AssemblyInfo(
            sequence=project.assembly_sequence.sequence,
            description=project.assembly_sequence.description,
            pattern_width_chips=project.assembly_sequence.pattern_width_chips,
        ),
        strip_width_mm=project.strip_width_mm,
        strip_thickness_mm=project.strip_thickness_mm,
        chip_length_mm=project.chip_length_mm,
        instructions=project.instructions,
        difficulty=project.difficulty,
        estimated_time_hours=project.estimated_time_hours,
        notes=project.notes,
        project_sheet=project.print_project_sheet(),
    )
