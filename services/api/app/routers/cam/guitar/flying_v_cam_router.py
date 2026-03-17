"""Flying V CAM Router — CAM operations for 1958 Gibson Flying V.

Resolves FV-GAP-05 (pocket toolpath) and FV-GAP-10 (neck pocket depth validation).

Provides:
- GET /spec — Spec summary (variant, cavity dimensions)
- POST /toolpath/control_cavity — G-code for control cavity pocket (parametric placement)
- POST /toolpath/neck_pocket — G-code for neck pocket mortise
- POST /toolpath/pickup — G-code for pickup cavity (neck, bridge, or both)
- POST /validate — Depth validation (optionally with shared gcode_verify/preflight)

Uses cam.flying_v.pocket_generator (parametric from gibson_flying_v_1958.json)
and cam.flying_v.depth_validator with preflight_gate integration.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

router = APIRouter(tags=["Flying V", "CAM"])


# -----------------------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------------------


class FlyingVSpecSummary(BaseModel):
    """Summary of Flying V spec for API."""
    model_id: str
    variant: str
    body_thickness_mm: float
    scale_length_mm: float
    neck_pocket_depth_mm: float
    control_cavity_depth_mm: float
    pickup_depth_mm: float


class ToolpathResponse(BaseModel):
    """G-code toolpath response."""
    ok: bool
    gcode: str
    operation: str
    variant: str = "original_1958"
    line_count: int = 0


class ValidateRequest(BaseModel):
    """Request for depth validation."""
    gcode: str
    operation: str = Field(..., description="neck_pocket | control_cavity | pickup_neck | pickup_bridge")
    tolerance_mm: float = Field(0.5, ge=0.0, le=2.0)
    use_preflight: bool = Field(True, description="Run shared preflight (gcode_verify stack) before depth check")


class ValidateResponse(BaseModel):
    """Depth validation result."""
    ok: bool
    operation: str
    expected_depth_mm: float
    actual_depths: list
    min_depth: float
    max_depth: float
    tolerance_mm: float
    errors: list
    warnings: list
    preflight_ok: Optional[bool] = None
    preflight_errors: list = []
    preflight_warnings: list = []


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------


@router.get("/spec", response_model=FlyingVSpecSummary)
def get_flying_v_spec(
    variant: str = Query("original_1958", description="original_1958 | reissue_2023"),
) -> FlyingVSpecSummary:
    """Return Flying V spec summary (cavity dimensions from gibson_flying_v_1958.json)."""
    from app.cam.flying_v import load_flying_v_spec

    spec = load_flying_v_spec(variant)
    return FlyingVSpecSummary(
        model_id=spec.model_id,
        variant=spec.variant,
        body_thickness_mm=spec.body_thickness_mm,
        scale_length_mm=spec.scale_length_mm,
        neck_pocket_depth_mm=spec.neck_pocket.depth_mm,
        control_cavity_depth_mm=spec.control_cavity.depth_mm,
        pickup_depth_mm=spec.neck_pickup.depth_mm,
    )


@router.post("/toolpath/control_cavity", response_model=ToolpathResponse)
def generate_control_cavity_toolpath(
    variant: str = Query("original_1958", description="Spec variant"),
) -> ToolpathResponse:
    """Generate G-code for Flying V control cavity pocket (parametric placement from body outline)."""
    from app.cam.flying_v import load_flying_v_spec, generate_control_cavity_toolpath as gen

    spec = load_flying_v_spec(variant)
    gcode = gen(spec)
    return ToolpathResponse(
        ok=True,
        gcode=gcode,
        operation="control_cavity",
        variant=variant,
        line_count=len(gcode.strip().splitlines()),
    )


@router.post("/toolpath/neck_pocket", response_model=ToolpathResponse)
def generate_neck_pocket_toolpath(
    variant: str = Query("original_1958", description="Spec variant"),
) -> ToolpathResponse:
    """Generate G-code for Flying V neck pocket mortise (roughing + finishing)."""
    from app.cam.flying_v import load_flying_v_spec, generate_neck_pocket_toolpath as gen

    spec = load_flying_v_spec(variant)
    gcode = gen(spec)
    return ToolpathResponse(
        ok=True,
        gcode=gcode,
        operation="neck_pocket",
        variant=variant,
        line_count=len(gcode.strip().splitlines()),
    )


@router.post("/toolpath/pickup", response_model=ToolpathResponse)
def generate_pickup_toolpath(
    pickup: str = Query("both", description="neck | bridge | both"),
    variant: str = Query("original_1958", description="Spec variant"),
) -> ToolpathResponse:
    """Generate G-code for Flying V pickup cavity pocket(s)."""
    from app.cam.flying_v import load_flying_v_spec, generate_pickup_cavity_toolpath as gen

    if pickup not in ("neck", "bridge", "both"):
        pickup = "both"
    spec = load_flying_v_spec(variant)
    gcode = gen(spec, pickup=pickup)
    return ToolpathResponse(
        ok=True,
        gcode=gcode,
        operation=f"pickup_{pickup}",
        variant=variant,
        line_count=len(gcode.strip().splitlines()),
    )


@router.post("/validate", response_model=ValidateResponse)
def validate_flying_v_gcode(req: ValidateRequest) -> ValidateResponse:
    """
    Validate Flying V G-code depths against spec.

    When use_preflight is True, runs the shared preflight (same stack as
    scripts/utils/gcode_verify.py) before depth validation (FV-GAP-10).
    """
    from app.cam.flying_v import (
        load_flying_v_spec,
        validate_neck_pocket_depth,
        validate_control_cavity_depth,
    )
    from app.cam.flying_v.depth_validator import _extract_z_depths, DepthValidationResult

    spec = load_flying_v_spec()
    preflight_ok = None
    preflight_errors: list = []
    preflight_warnings: list = []

    if req.use_preflight:
        try:
            from app.cam.preflight_gate import preflight_validate, PreflightConfig

            config = PreflightConfig(
                stock_thickness_mm=spec.body_thickness_mm,
                require_units_mm=True,
                require_absolute=True,
                require_spindle_on=True,
                require_feed_on_cut=True,
            )
            preflight_result = preflight_validate(req.gcode, config=config)
            preflight_ok = preflight_result.ok
            preflight_errors = list(preflight_result.errors)
            preflight_warnings = list(preflight_result.warnings)
        except Exception as e:
            preflight_errors.append(f"Preflight unavailable: {e}")

    if req.operation == "neck_pocket":
        result = validate_neck_pocket_depth(req.gcode, spec=spec, tolerance_mm=req.tolerance_mm)
    elif req.operation == "control_cavity":
        result = validate_control_cavity_depth(req.gcode, spec=spec, tolerance_mm=req.tolerance_mm)
    elif req.operation in ("pickup_neck", "pickup_bridge"):
        expected = spec.neck_pickup.depth_mm if "neck" in req.operation else spec.bridge_pickup.depth_mm
        depths = _extract_z_depths(req.gcode)
        errors = []
        warnings = []
        if not depths:
            errors.append("No Z depth values found")
            positive_depths = []
            max_depth = min_depth = 0.0
        else:
            positive_depths = [abs(d) for d in depths]
            max_depth = max(positive_depths)
            min_depth = min(positive_depths)
            if abs(max_depth - expected) > req.tolerance_mm:
                errors.append(f"Depth mismatch: expected {expected:.2f}mm, got {max_depth:.2f}mm")
        result = DepthValidationResult(
            ok=len(errors) == 0,
            operation=req.operation,
            expected_depth_mm=expected,
            actual_depths=positive_depths,
            min_depth=min_depth if depths else 0.0,
            max_depth=max_depth if depths else 0.0,
            tolerance_mm=req.tolerance_mm,
            errors=errors,
            warnings=warnings,
        )
    else:
        result = validate_neck_pocket_depth(req.gcode, spec=spec, tolerance_mm=req.tolerance_mm)

    return ValidateResponse(
        ok=result.ok,
        operation=result.operation,
        expected_depth_mm=result.expected_depth_mm,
        actual_depths=result.actual_depths,
        min_depth=result.min_depth,
        max_depth=result.max_depth,
        tolerance_mm=result.tolerance_mm,
        errors=result.errors,
        warnings=result.warnings,
        preflight_ok=preflight_ok,
        preflight_errors=preflight_errors,
        preflight_warnings=preflight_warnings,
    )
