"""
Woodworking calculators API — floating bridge, joinery, panels, bandsaw rim speed.

Prefix: /api/woodworking
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.cam_core.saw_lab.bandsaw import (
    Bandsaw,
    BandsawBladeSpec,
    compute_blade_tension,
    compute_drift_angle,
    compute_feed_rate,
    get_blade_by_id,
    load_blade_library,
    plan_curve_cut,
    plan_resaw_cut,
    validate_resaw_setup,
)
from app.woodworking.archtop_floating_bridge import (
    BENEDETTO_17,
    build_archtop_bridge_report,
    generate_dxf,
    resolve_arch_radius_from_sagitta,
)
from app.woodworking.archtop_bridge import (
    ArchtopBridgeSpec,
    compute_foot_arch,
    compute_post_holes,
)
from app.woodworking import (
    board_feet,
    compute_biscuit_layout,
    compute_box_joint,
    compute_break_angle_deg,
    compute_dovetail_angle_from_slope,
    compute_floating_panel_gaps,
    compute_mortise_tenon,
    compute_panel_blank_oversize,
    compute_saddle_height_from_twelfth_action,
    movement_budget_for_species,
    seasonal_movement,
    wood_weight,
)

router = APIRouter(tags=["woodworking"])


# ─── Floating bridge ──────────────────────────────────────────────────────────


class FloatingBridgeActionRequest(BaseModel):
    scale_length_mm: float = Field(..., gt=0)
    action_12th_mm: float = Field(..., ge=0)


class BreakAngleRequest(BaseModel):
    height_delta_mm: float = Field(..., ge=0)
    horizontal_run_mm: float = Field(..., gt=0)


@router.post("/floating-bridge/from-12th-action", summary="Saddle height from 12th-fret action")
def post_floating_bridge_action(req: FloatingBridgeActionRequest) -> Dict[str, Any]:
    r = compute_saddle_height_from_twelfth_action(req.scale_length_mm, req.action_12th_mm)
    return {
        "scale_length_mm": r.scale_length_mm,
        "action_12th_mm": r.action_12th_mm,
        "saddle_height_above_plane_mm": r.saddle_height_above_plane_mm,
        "distance_12th_to_bridge_mm": r.distance_12th_to_bridge_mm,
        "notes": r.notes,
    }


@router.post("/floating-bridge/break-angle", summary="String break angle behind bridge")
def post_break_angle(req: BreakAngleRequest) -> Dict[str, float]:
    return {"break_angle_deg": compute_break_angle_deg(req.height_delta_mm, req.horizontal_run_mm)}


class ArchtopBridgeGeometryRequest(BaseModel):
    """Measured top arch: chord span (mm) and sagitta (mm). Prefer over nominal 3048."""

    span_mm: float = Field(..., gt=0, description="Chord span along arch (measured)")
    sagitta_mm: float = Field(..., gt=0, description="Rise from chord to arc (measured)")
    base_length_mm: float = Field(default=BENEDETTO_17.base_length_mm)
    base_width_mm: float = Field(default=BENEDETTO_17.base_width_mm)
    e_to_e_string_spacing_mm: float = Field(default=BENEDETTO_17.e_to_e_string_spacing_mm)
    post_spacing_mm: float = Field(default=BENEDETTO_17.post_spacing_mm)
    saddle_radius_mm: float = Field(default=BENEDETTO_17.saddle_radius_mm)


@router.post(
    "/floating-bridge/archtop/geometry",
    summary="Benedetto-style archtop floating bridge (sagitta arch, foot, posts, saddle slots)",
)
def post_archtop_geometry(req: ArchtopBridgeGeometryRequest) -> Dict[str, Any]:
    rep = build_archtop_bridge_report(
        span_mm=req.span_mm,
        sagitta_mm=req.sagitta_mm,
        base_length_mm=req.base_length_mm,
        base_width_mm=req.base_width_mm,
        e_to_e_string_spacing_mm=req.e_to_e_string_spacing_mm,
        post_spacing_mm=req.post_spacing_mm,
        saddle_radius_mm=req.saddle_radius_mm,
    )
    return {
        "arch_radius_mm": rep.arch_radius_mm,
        "span_mm": rep.span_mm,
        "sagitta_mm": rep.sagitta_mm,
        "foot": rep.foot,
        "posts": rep.posts,
        "saddle_slots": rep.saddle_slots,
        "defaults": rep.defaults,
    }


class ArchtopBridgeDxfRequest(ArchtopBridgeGeometryRequest):
    """Same as geometry; DXF uses resolved arch radius from span + sagitta."""


@router.post(
    "/floating-bridge/archtop/dxf",
    summary="DXF R2000 (BRIDGE_OUTLINE, FOOT_PROFILE, SADDLE_SLOT, POST_HOLES, CENTERLINE)",
    response_class=Response,
)
def post_archtop_dxf(req: ArchtopBridgeDxfRequest) -> Response:
    r_arch = resolve_arch_radius_from_sagitta(req.span_mm, req.sagitta_mm)
    try:
        raw = generate_dxf(
            arch_radius_mm=r_arch,
            base_length_mm=req.base_length_mm,
            base_width_mm=req.base_width_mm,
            foot_thickness_mm=BENEDETTO_17.foot_thickness_mm,
            saddle_radius_mm=req.saddle_radius_mm,
            post_spacing_mm=req.post_spacing_mm,
            post_hole_diameter_mm=BENEDETTO_17.post_hole_diameter_mm,
            e_to_e_string_spacing_mm=req.e_to_e_string_spacing_mm,
        )
    except ImportError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    return Response(
        content=raw,
        media_type="application/dxf",
        headers={"Content-Disposition": 'attachment; filename="archtop_floating_bridge.dxf"'},
    )





class ArchtopBridgeComputeRequest(BaseModel):
    """ArchtopBridgeSpec fields for compute endpoint."""

    style: str = Field(default="benedetto")
    body_arch_radius_mm: Optional[float] = Field(default=3048.0, description="Nominal 120 inch")
    arch_span_mm: Optional[float] = Field(default=None, description="Measured footprint width")
    arch_height_mm: Optional[float] = Field(default=None, description="Measured sagitta")
    base_length_mm: float = Field(default=155.0)
    foot_width_mm: float = Field(default=4.5)
    saddle_radius_mm: float = Field(default=381.0)
    post_spacing_mm: float = Field(default=74.6)
    post_diameter_mm: float = Field(default=4.0)
    string_spacing_ee_mm: float = Field(default=52.0)
    material: str = Field(default="ebony")


@router.post(
    "/archtop-bridge/compute",
    summary="Archtop bridge foot arch + post holes (measured arch wins over nominal)",
)
def post_archtop_bridge_compute(req: ArchtopBridgeComputeRequest) -> Dict[str, Any]:
    spec = ArchtopBridgeSpec(
        style=req.style,
        body_arch_radius_mm=req.body_arch_radius_mm,
        arch_span_mm=req.arch_span_mm,
        arch_height_mm=req.arch_height_mm,
        base_length_mm=req.base_length_mm,
        foot_width_mm=req.foot_width_mm,
        saddle_radius_mm=req.saddle_radius_mm,
        post_spacing_mm=req.post_spacing_mm,
        post_diameter_mm=req.post_diameter_mm,
        string_spacing_ee_mm=req.string_spacing_ee_mm,
        material=req.material,
    )
    return {
        "foot_arch": compute_foot_arch(spec),
        "post_holes": compute_post_holes(spec),
        "spec": {
            "style": spec.style,
            "material": spec.material,
            "resolved_arch_radius_mm": spec.resolved_arch_radius(),
        },
    }

# ─── Joinery ─────────────────────────────────────────────────────────────────


class DovetailRequest(BaseModel):
    ratio_run_to_rise: float = Field(..., gt=0, description="1:X dovetail (e.g. 6 for 1:6)")


class BoxJointRequest(BaseModel):
    stock_width_mm: float = Field(..., gt=0)
    num_fingers: int = Field(..., ge=1)
    kerf_mm: float = Field(..., ge=0)


class MortiseTenonRequest(BaseModel):
    stock_thickness_mm: float = Field(..., gt=0)
    shoulder_mm: float = Field(default=3.0, ge=0)
    tenon_fraction: float = Field(default=0.33, ge=0.1, le=0.6)


class BiscuitRequest(BaseModel):
    joint_length_mm: float = Field(..., gt=0)
    biscuit_size: str = Field(default="20")
    end_margin_mm: float = Field(default=50.0, ge=0)


@router.post("/joinery/dovetail-angle", summary="Dovetail angles from 1:X ratio")
def post_dovetail(req: DovetailRequest) -> Dict[str, float]:
    r = compute_dovetail_angle_from_slope(req.ratio_run_to_rise)
    return {
        "ratio_run_to_rise": r.ratio_run_to_rise,
        "included_angle_deg": r.angle_deg,
        "half_angle_from_vertical_deg": r.half_angle_from_vertical_deg,
    }


@router.post("/joinery/box-joint", summary="Equal finger widths for box joints")
def post_box_joint(req: BoxJointRequest) -> Dict[str, Any]:
    r = compute_box_joint(req.stock_width_mm, req.num_fingers, req.kerf_mm)
    return {
        "stock_width_mm": r.stock_width_mm,
        "num_fingers": r.num_fingers,
        "kerf_mm": r.kerf_mm,
        "finger_width_mm": r.finger_width_mm,
        "usable_width_mm": r.usable_width_mm,
        "notes": r.notes,
    }


@router.post("/joinery/mortise-tenon", summary="Nominal mortise/tenon thickness")
def post_mortise_tenon(req: MortiseTenonRequest) -> Dict[str, Any]:
    r = compute_mortise_tenon(req.stock_thickness_mm, req.shoulder_mm, req.tenon_fraction)
    return {
        "stock_thickness_mm": r.stock_thickness_mm,
        "tenon_thickness_mm": r.tenon_thickness_mm,
        "shoulder_mm": r.shoulder_mm,
        "mortise_width_mm": r.mortise_width_mm,
        "notes": r.notes,
    }


@router.post("/joinery/biscuits", summary="Biscuit positions along a joint")
def post_biscuits(req: BiscuitRequest) -> Dict[str, Any]:
    r = compute_biscuit_layout(req.joint_length_mm, req.biscuit_size, req.end_margin_mm)
    return {
        "joint_length_mm": r.joint_length_mm,
        "biscuit_pitch_mm": r.biscuit_pitch_mm,
        "count": r.count,
        "positions_mm_from_end": r.positions_mm_from_end,
        "notes": r.notes,
    }


# ─── Panels ───────────────────────────────────────────────────────────────────


class FloatingPanelGapsRequest(BaseModel):
    panel_width_across_grain_mm: float = Field(..., gt=0)
    species: str = Field(default="maple")
    rh_from: float = Field(..., ge=0, le=100)
    rh_to: float = Field(..., ge=0, le=100)
    num_capture_edges: int = Field(default=4, ge=1)


class PanelBlankRequest(BaseModel):
    opening_width_mm: float = Field(..., ge=0)
    opening_height_mm: float = Field(..., ge=0)
    oversize_mm_each_side: float = Field(default=3.0, ge=0)
    width_is_across_grain: bool = True


@router.post("/panels/floating-gaps", summary="Panel expansion and per-edge gap")
def post_floating_gaps(req: FloatingPanelGapsRequest) -> Dict[str, Any]:
    r = compute_floating_panel_gaps(
        req.panel_width_across_grain_mm,
        req.species,
        req.rh_from,
        req.rh_to,
        req.num_capture_edges,
    )
    return {
        "panel_width_across_grain_mm": r.panel_width_across_grain_mm,
        "species": r.species,
        "rh_from": r.rh_from,
        "rh_to": r.rh_to,
        "total_movement_mm": r.total_movement_mm,
        "gap_per_edge_mm": r.gap_per_edge_mm,
        "num_edges": r.num_edges,
        "notes": r.notes,
    }


@router.post("/panels/blank-oversize", summary="Rough panel blank from opening")
def post_panel_blank(req: PanelBlankRequest) -> Dict[str, Any]:
    r = compute_panel_blank_oversize(
        req.opening_width_mm,
        req.opening_height_mm,
        req.oversize_mm_each_side,
        req.width_is_across_grain,
    )
    return {
        "opening_width_mm": r.opening_width_mm,
        "opening_height_mm": r.opening_height_mm,
        "oversize_mm_each_side": r.oversize_mm_each_side,
        "blank_width_mm": r.blank_width_mm,
        "blank_height_mm": r.blank_height_mm,
        "grain_note": r.grain_note,
    }


class PanelBoardFeetRequest(BaseModel):
    thickness_in: float = Field(..., gt=0)
    width_in: float = Field(..., gt=0)
    length_in: float = Field(..., gt=0)
    quantity: int = Field(default=1, ge=0)
    species: str = Field(default="maple", description="For weight estimate")


@router.post("/panel/board-feet", summary="Board feet and optional wood weight")
def post_panel_board_feet(req: PanelBoardFeetRequest) -> Dict[str, Any]:
    bf = board_feet(req.thickness_in, req.width_in, req.length_in, req.quantity)
    wt = wood_weight(req.thickness_in, req.width_in, req.length_in, req.species)
    return {
        "board_feet": round(bf, 4),
        "quantity": req.quantity,
        "weight": wt,
    }


class PanelMovementBudgetRequest(BaseModel):
    dimension_mm: float = Field(..., gt=0, description="Across-grain dimension for movement")
    species: str
    rh_from: float = Field(..., ge=0, le=100)
    rh_to: float = Field(..., ge=0, le=100)
    grain_direction: str = Field(default="tangential")
    include_coefficient: bool = Field(
        default=True,
        description="Include shrinkage coefficient from registry (no duplicate tables)",
    )


@router.post("/panel/movement-budget", summary="Seasonal movement + optional coefficient")
def post_panel_movement_budget(req: PanelMovementBudgetRequest) -> Dict[str, Any]:
    movement = seasonal_movement(
        req.dimension_mm,
        req.species,
        req.rh_from,
        req.rh_to,
        req.grain_direction,
    )
    out: Dict[str, Any] = {"movement": movement}
    if req.include_coefficient:
        out["coefficient"] = movement_budget_for_species(req.species, req.grain_direction)
    return out


# ─── Bandsaw ──────────────────────────────────────────────────────────────────


class BandsawGeometryRequest(BaseModel):
    wheel_diameter_mm: float = Field(..., gt=0)
    wheel_center_distance_mm: float = Field(..., gt=0)
    kerf_mm: float = Field(default=0.6, ge=0)
    rpm: float = Field(..., gt=0)


class BandsawFeedRequest(BandsawGeometryRequest):
    stock_thickness_mm: float = Field(..., gt=0)
    aggressive: float = Field(default=0.5, gt=0, le=1.0)


@router.post("/bandsaw/rim-speed", summary="Bandsaw rim speed and blade length")
def post_bandsaw_rim(req: BandsawGeometryRequest) -> Dict[str, Any]:
    bs = Bandsaw(
        wheel_diameter_mm=req.wheel_diameter_mm,
        wheel_center_distance_mm=req.wheel_center_distance_mm,
        kerf_mm=req.kerf_mm,
    )
    mps = bs.surface_speed_m_per_s(req.rpm)
    return {
        **bs.to_dict(),
        "rpm": req.rpm,
        "rim_speed_m_per_s": round(mps, 4),
        "rim_speed_m_per_min": round(bs.surface_speed_m_per_min(req.rpm), 3),
        "rim_speed_sfpm": round(bs.surface_speed_sfpm(req.rpm), 2),
    }


@router.post("/bandsaw/resaw-feed-hint", summary="Heuristic resaw feed rate (mm/s)")
def post_bandsaw_feed(req: BandsawFeedRequest) -> Dict[str, Any]:
    bs = Bandsaw(
        wheel_diameter_mm=req.wheel_diameter_mm,
        wheel_center_distance_mm=req.wheel_center_distance_mm,
        kerf_mm=req.kerf_mm,
    )
    sfpm = bs.surface_speed_sfpm(req.rpm)
    feed = bs.resaw_feed_mm_s(
        req.stock_thickness_mm,
        sfpm=sfpm,
        aggressive=req.aggressive,
    )
    return {
        "rim_speed_sfpm": round(sfpm, 2),
        "resaw_feed_mm_s": feed,
        "stock_thickness_mm": req.stock_thickness_mm,
    }


def _resolve_blade(
    blade_id: Optional[str],
    width_mm: float,
    thickness_mm: float,
    tpi: float,
    blade_family: str,
    kerf_mm: float,
) -> BandsawBladeSpec:
    if blade_id:
        b = get_blade_by_id(blade_id.strip())
        if b is None:
            raise HTTPException(status_code=404, detail=f"Unknown blade id: {blade_id}")
        return b
    return BandsawBladeSpec(
        id="inline",
        width_mm=width_mm,
        thickness_mm=thickness_mm,
        tpi=tpi,
        blade_family=blade_family,
        kerf_mm=kerf_mm,
    )


@router.get("/bandsaw/blades", summary="Bandsaw blade library (JSON)")
def get_bandsaw_blades() -> Dict[str, Any]:
    blades = load_blade_library()
    return {"blades": [b.raw if b.raw else {"id": b.id, "width_mm": b.width_mm} for b in blades]}


class BandsawBladeInline(BaseModel):
    blade_id: Optional[str] = None
    width_mm: float = Field(default=19.05, gt=0)
    thickness_mm: float = Field(default=0.9, gt=0)
    tpi: float = Field(default=14, gt=0)
    blade_family: str = Field(default="carbon_steel")
    kerf_mm: float = Field(default=0.65, ge=0)


class BandsawTensionRequest(BandsawBladeInline):
    stress_fraction: float = Field(default=0.5, ge=0, le=1)


@router.post("/bandsaw/tension", summary="Blade tension T = σ × A (carbon vs bi-metal σ band)")
def post_bandsaw_tension(req: BandsawTensionRequest) -> Dict[str, Any]:
    blade = _resolve_blade(
        req.blade_id,
        req.width_mm,
        req.thickness_mm,
        req.tpi,
        req.blade_family,
        req.kerf_mm,
    )
    return compute_blade_tension(blade, stress_fraction=req.stress_fraction)


class BandsawDriftRequest(BandsawGeometryRequest, BandsawBladeInline):
    pass


@router.post("/bandsaw/drift", summary="Empirical drift angle (Duginske-style)")
def post_bandsaw_drift(req: BandsawDriftRequest) -> Dict[str, Any]:
    blade = _resolve_blade(
        req.blade_id,
        req.width_mm,
        req.thickness_mm,
        req.tpi,
        req.blade_family,
        req.kerf_mm,
    )
    return compute_drift_angle(
        blade.width_mm,
        req.wheel_diameter_mm,
        req.rpm,
        blade.tpi,
    )


class BandsawFeedPhysicsRequest(BandsawGeometryRequest, BandsawBladeInline):
    stock_thickness_mm: float = Field(..., gt=0)
    gullet_fill_efficiency: float = Field(default=0.35, gt=0, le=1)


@router.post("/bandsaw/feed-rate", summary="Gullet-capacity feed rate (mm/s)")
def post_bandsaw_feed_physics(req: BandsawFeedPhysicsRequest) -> Dict[str, Any]:
    blade = _resolve_blade(
        req.blade_id,
        req.width_mm,
        req.thickness_mm,
        req.tpi,
        req.blade_family,
        req.kerf_mm,
    )
    bs = Bandsaw(
        wheel_diameter_mm=req.wheel_diameter_mm,
        wheel_center_distance_mm=req.wheel_center_distance_mm,
        kerf_mm=req.kerf_mm,
    )
    sfpm = bs.surface_speed_sfpm(req.rpm)
    out = compute_feed_rate(
        blade,
        sfpm,
        req.stock_thickness_mm,
        gullet_fill_efficiency=req.gullet_fill_efficiency,
    )
    out["rim_speed_sfpm"] = round(sfpm, 2)
    return out


class BandsawValidateResawRequest(BandsawGeometryRequest, BandsawBladeInline):
    stock_thickness_mm: float = Field(..., gt=0)
    max_resaw_height_mm: Optional[float] = None


@router.post("/bandsaw/validate-resaw", summary="Resaw feasibility and warnings")
def post_bandsaw_validate_resaw(req: BandsawValidateResawRequest) -> Dict[str, Any]:
    blade = _resolve_blade(
        req.blade_id,
        req.width_mm,
        req.thickness_mm,
        req.tpi,
        req.blade_family,
        req.kerf_mm,
    )
    bs = Bandsaw(
        wheel_diameter_mm=req.wheel_diameter_mm,
        wheel_center_distance_mm=req.wheel_center_distance_mm,
        kerf_mm=req.kerf_mm,
        max_resaw_height_mm=req.max_resaw_height_mm,
    )
    return validate_resaw_setup(bs, blade, req.stock_thickness_mm, req.rpm)


class BandsawPlanCurveRequest(BandsawBladeInline):
    planned_curve_radius_mm: float = Field(..., gt=0)


@router.post("/bandsaw/plan-curve", summary="Curve cut vs min radius (blade width)")
def post_bandsaw_plan_curve(req: BandsawPlanCurveRequest) -> Dict[str, Any]:
    blade = _resolve_blade(
        req.blade_id,
        req.width_mm,
        req.thickness_mm,
        req.tpi,
        req.blade_family,
        req.kerf_mm,
    )
    return plan_curve_cut(blade, req.planned_curve_radius_mm)


class BandsawPlanResawRequest(BaseModel):
    plate_width_mm: float = Field(..., gt=0)
    plate_thickness_mm: float = Field(..., gt=0)
    kerf_mm: float = Field(default=0.65, ge=0)
    target_thickness_mm: float = Field(..., gt=0)
    bookmatch: bool = True


@router.post("/bandsaw/plan-resaw", summary="Bookmatch layout and thinning passes")
def post_bandsaw_plan_resaw(req: BandsawPlanResawRequest) -> Dict[str, Any]:
    return plan_resaw_cut(
        req.plate_width_mm,
        req.plate_thickness_mm,
        req.kerf_mm,
        req.target_thickness_mm,
        bookmatch=req.bookmatch,
    )


__all__ = ["router"]
