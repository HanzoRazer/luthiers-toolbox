"""
Rosette Manufacturing Routes — Phase 2 + Phase 3 Consolidation

Wires the orphaned rosette_planner (manufacturing plan generator),
TraditionalBuilder (craftsman project sheets), and the unified
RosetteProject envelope to the Art Studio API.

Endpoints:
    POST /api/art/rosette/manufacturing-plan   — Generate multi-family manufacturing plan
    GET  /api/art/rosette/traditional/masters   — List patterns grouped by master luthier
    GET  /api/art/rosette/traditional/patterns/{pattern_id} — Get pattern info
    POST /api/art/rosette/traditional/project   — Generate full traditional rosette project
    POST /api/art/rosette/project               — Unified project envelope (Phase 3)
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


# ── Unified Project Envelope (Phase 3) ─────────────────────────────────────

from ...schemas.rosette_project import (
    RosetteProjectRequest,
    RosetteProjectResponse,
    ManufacturingPlanSummary,
    CamSummary,
    ring_band_to_cam_dict,
)

# Optional CAM modules — degrade gracefully
CAM_BRIDGE_AVAILABLE = False
try:
    from ...services.rosette_cam_bridge import (
        RosetteGeometry,
        CamParams,
        plan_rosette_toolpath,
    )
    CAM_BRIDGE_AVAILABLE = True
except ImportError:
    logger.warning("rosette_cam_bridge unavailable — CAM features disabled")

MODERN_GENERATOR_AVAILABLE = False
try:
    from ...cam.rosette.pattern_generator import RosettePatternEngine
    MODERN_GENERATOR_AVAILABLE = True
except ImportError:
    logger.warning("RosettePatternEngine unavailable — preview features disabled")


@router.post("/project", response_model=RosetteProjectResponse)
def assemble_rosette_project(req: RosetteProjectRequest) -> RosetteProjectResponse:
    """
    Assemble a unified rosette project from a pattern definition.

    Returns manufacturing plan, optional CAM geometry, and optional
    modern parametric ring previews — all in a single response.
    """
    pattern = req.pattern

    # ── 1. Manufacturing plan (always) ──────────────────────────────────
    try:
        plan = generate_manufacturing_plan(
            pattern=pattern,
            guitars=req.guitars,
            tile_length_mm=req.tile_length_mm,
            scrap_factor=req.scrap_factor,
        )
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    mfg_summary = ManufacturingPlanSummary(
        guitars=plan.guitars,
        total_rings=len(plan.ring_requirements),
        total_families=len(plan.strip_plans),
        total_tiles=sum(sp.total_tiles_needed for sp in plan.strip_plans),
        total_sticks=sum(sp.sticks_needed for sp in plan.strip_plans),
        strip_plans=[
            {
                "family": sp.strip_family_id,
                "tiles": sp.total_tiles_needed,
                "sticks": sp.sticks_needed,
                "strip_length_m": round(sp.total_strip_length_m, 2),
                "rings": sp.ring_indices,
            }
            for sp in plan.strip_plans
        ],
        notes=plan.notes,
    )

    # ── 2. Ring mapping (always) ────────────────────────────────────────
    ring_mapping = []
    for band in pattern.ring_bands:
        cam_dict = ring_band_to_cam_dict(band)
        ring_mapping.append({
            "band_id": band.id,
            "band_index": band.index,
            "strip_family_id": band.strip_family_id,
            "cam_pattern_type": cam_dict["pattern_type"],
            "radius_mm": band.radius_mm,
            "width_mm": band.width_mm,
            "inner_diameter_mm": cam_dict["inner_diameter_mm"],
            "outer_diameter_mm": cam_dict["outer_diameter_mm"],
        })

    # ── 3. CAM geometry (optional) ──────────────────────────────────────
    cam_summary = None
    if req.include_cam:
        if not CAM_BRIDGE_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail="CAM bridge module is not available",
            )

        overrides = req.cam_overrides
        if overrides is None:
            from ...schemas.rosette_project import CamOverrides
            overrides = CamOverrides()

        # Use outermost/innermost ring radii for channel geometry
        radii = [b.radius_mm for b in pattern.ring_bands]
        widths = [b.width_mm for b in pattern.ring_bands]
        if not radii:
            raise HTTPException(status_code=422, detail="Pattern has no ring bands")

        outer_r = max(r + w / 2 for r, w in zip(radii, widths))
        inner_r = min(r - w / 2 for r, w in zip(radii, widths))

        geom = RosetteGeometry(
            center_x_mm=pattern.center_x_mm,
            center_y_mm=pattern.center_y_mm,
            inner_radius_mm=max(inner_r, 0.0),
            outer_radius_mm=outer_r,
        )
        cam_params = CamParams(
            tool_diameter_mm=overrides.tool_diameter_mm,
            stepover_pct=overrides.stepover_pct,
            stepdown_mm=overrides.stepdown_mm,
            feed_xy_mm_min=overrides.feed_xy_mm_min,
            safe_z_mm=overrides.safe_z_mm,
            cut_depth_mm=pattern.default_slice_thickness_mm,
        )
        moves, stats = plan_rosette_toolpath(geom, cam_params)
        cam_summary = CamSummary(
            rings_count=stats.get("rings", 0),
            z_passes=stats.get("z_passes", 0),
            move_count=stats.get("move_count", len(moves)),
            estimated_length_mm=round(stats.get("length_mm", 0.0), 1),
        )

    # ── 4. Modern parametric preview (optional) ─────────────────────────
    preview_svg = None
    preview_dxf = None
    if req.include_modern_preview:
        if not MODERN_GENERATOR_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail="Pattern generator module is not available",
            )

        cam_rings = [ring_band_to_cam_dict(b) for b in pattern.ring_bands]
        engine = RosettePatternEngine()
        try:
            result = engine.generate_modern(
                rings=cam_rings,
                name=pattern.name,
                soundhole_diameter_mm=pattern.ring_bands[0].radius_mm * 2 if pattern.ring_bands else 100.0,
                include_dxf="dxf" in req.preview_formats,
                include_svg="svg" in req.preview_formats,
            )
            preview_svg = result.svg_content
            preview_dxf = result.dxf_content
        except (ValueError, TypeError) as exc:
            logger.warning("Modern preview generation failed: %s", exc)

    # ── Compute soundhole diameter from innermost ring ──────────────────
    if pattern.ring_bands:
        sh_diameter = min(b.radius_mm for b in pattern.ring_bands) * 2
    else:
        sh_diameter = 100.0

    return RosetteProjectResponse(
        project_name=pattern.name,
        pattern_id=pattern.id,
        soundhole_diameter_mm=round(sh_diameter, 2),
        ring_count=len(pattern.ring_bands),
        ring_mapping=ring_mapping,
        manufacturing=mfg_summary,
        cam=cam_summary,
        preview_svg=preview_svg,
        preview_dxf=preview_dxf,
    )
