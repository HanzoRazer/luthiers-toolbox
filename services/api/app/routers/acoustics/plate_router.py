"""Plate design acoustics router - PORT-001 from tap-tone-pi."""
from __future__ import annotations
from dataclasses import asdict
from typing import Any, Dict, List, Literal, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

try:
    from app.calculators.plate_design import (
        analyze_plate,
        analyze_coupled_system,
        get_material_preset,
        get_body_calibration,
        list_materials,
        list_body_styles,
        BodyStyle,
        PlateThicknessResult,
        CoupledSystemResult,
    )
    from app.calculators.plate_design.archtop_graduation import (
        graduation_from_wood_and_target,
        GraduationResult,
    )
    PLATE_DESIGN_AVAILABLE = True
except ImportError as e:
    PLATE_DESIGN_AVAILABLE = False
    _import_error = str(e)

router = APIRouter(tags=["acoustics-plate"])


# Request/Response Models
class PlateAnalyzeRequest(BaseModel):
    material: str = Field(..., description="Material preset name (e.g., 'sitka_spruce')")
    body_style: str = Field(..., description="Body style (e.g., 'om', 'dreadnought')")
    target_hz: float = Field(..., description="Target frequency in Hz")
    plate: Literal["top", "back"] = Field("top", description="Plate to analyze (top or back)")


class CoupledAnalyzeRequest(BaseModel):
    top_material: str = Field(..., description="Top plate material")
    back_material: str = Field(..., description="Back plate material")
    body_style: str = Field(..., description="Body style")
    top_thickness_mm: Optional[float] = Field(None, description="Top thickness (mm)")
    back_thickness_mm: Optional[float] = Field(None, description="Back thickness (mm)")


class MaterialInfo(BaseModel):
    name: str
    description: str
    E_L_GPa: float
    E_C_GPa: float
    density_kg_m3: float


class BodyStyleInfo(BaseModel):
    name: str
    description: str
    volume_m3: float
    f_monopole_target: float
    f_air_target: float


@router.get("/status")
def get_status() -> Dict[str, Any]:
    """Check if plate design module is available."""
    if PLATE_DESIGN_AVAILABLE:
        return {"available": True, "error": ""}
    return {"available": False, "error": _import_error}


@router.post("/analyze")
def analyze_plate_endpoint(req: PlateAnalyzeRequest) -> Dict[str, Any]:
    """Analyze plate thickness for target frequency. Returns PlateThicknessResult as dict."""
    if not PLATE_DESIGN_AVAILABLE:
        raise HTTPException(503, detail="Plate design module not available")

    material = get_material_preset(req.material)
    if material is None:
        raise HTTPException(400, detail=f"Unknown material: {req.material}")

    try:
        body_style_enum = BodyStyle(req.body_style.lower())
    except ValueError:
        raise HTTPException(400, detail=f"Unknown body style: {req.body_style}")

    calibration = get_body_calibration(body_style_enum)
    if calibration is None:
        raise HTTPException(400, detail=f"No calibration for body style: {req.body_style}")

    if req.plate == "top":
        length_mm = calibration.top_a_m * 1000.0
        width_mm = calibration.top_b_m * 1000.0
    else:
        length_mm = calibration.back_a_m * 1000.0
        width_mm = calibration.back_b_m * 1000.0

    result = analyze_plate(
        E_L_GPa=material.E_L_GPa,
        E_C_GPa=material.E_C_GPa,
        density_kg_m3=material.density_kg_m3,
        length_mm=length_mm,
        width_mm=width_mm,
        target_f_Hz=req.target_hz,
        material_name=req.material,
    )
    return asdict(result)


@router.post("/coupled")
def analyze_coupled_endpoint(req: CoupledAnalyzeRequest) -> Dict[str, Any]:
    """Analyze coupled top/back/air system. Returns CoupledSystemResult as dict."""
    if not PLATE_DESIGN_AVAILABLE:
        raise HTTPException(503, detail="Plate design module not available")

    top_mat = get_material_preset(req.top_material)
    back_mat = get_material_preset(req.back_material)
    if top_mat is None:
        raise HTTPException(400, detail=f"Unknown material: {req.top_material}")
    if back_mat is None:
        raise HTTPException(400, detail=f"Unknown material: {req.back_material}")

    try:
        body_style_enum = BodyStyle(req.body_style.lower())
    except ValueError:
        raise HTTPException(400, detail=f"Unknown body style: {req.body_style}")

    calibration = get_body_calibration(body_style_enum)
    if calibration is None:
        raise HTTPException(400, detail=f"No calibration for body style: {req.body_style}")

    top_h_mm = req.top_thickness_mm if req.top_thickness_mm is not None else 2.8
    back_h_mm = req.back_thickness_mm if req.back_thickness_mm is not None else 2.5

    result = analyze_coupled_system(
        body=calibration,
        top_E_L_GPa=top_mat.E_L_GPa,
        top_E_C_GPa=top_mat.E_C_GPa,
        top_rho=top_mat.density_kg_m3,
        top_h_mm=top_h_mm,
        back_E_L_GPa=back_mat.E_L_GPa,
        back_E_C_GPa=back_mat.E_C_GPa,
        back_rho=back_mat.density_kg_m3,
        back_h_mm=back_h_mm,
    )
    return asdict(result)


@router.get("/materials")
def list_materials_endpoint() -> List[MaterialInfo]:
    """List available material presets."""
    if not PLATE_DESIGN_AVAILABLE:
        raise HTTPException(503, detail="Plate design module not available")
    
    materials = list_materials()
    return [
        MaterialInfo(
            name=m["name"],
            description=m.get("notes", m.get("species", "")),
            E_L_GPa=m["E_L_GPa"],
            E_C_GPa=m["E_C_GPa"],
            density_kg_m3=m["density_kg_m3"],
        )
        for m in materials
    ]


@router.get("/body-styles")
def list_body_styles_endpoint() -> List[BodyStyleInfo]:
    """List available body style calibrations."""
    if not PLATE_DESIGN_AVAILABLE:
        raise HTTPException(503, detail="Plate design module not available")

    styles = list_body_styles()
    return [
        BodyStyleInfo(
            name=s["style"],
            description=s["description"],
            volume_m3=s.get("volume_m3", s.get("volume_liters", 0) * 0.001),
            f_monopole_target=s["f_monopole_target"],
            f_air_target=s.get("f_air_target", s["f_monopole_target"] * 1.1),
        )
        for s in styles
    ]


class ArchtopGraduationRequest(BaseModel):
    """Request for archtop graduation calculation."""
    material: str = Field(..., description="Material preset name (e.g., 'maple')")
    body_style: str = Field(..., description="Body style (e.g., 'archtop')")
    target_hz: float = Field(..., description="Target frequency in Hz (e.g., 120.0)")
    lower_bout_width_mm: float = Field(255.0, description="Lower bout width for arch height calc")
    arch_height_ratio: float = Field(0.062, description="Arch height as ratio of bout width")
    plate: Literal["top", "back"] = Field("top", description="Plate to analyze")


@router.post("/archtop-graduation")
def archtop_graduation_endpoint(req: ArchtopGraduationRequest) -> Dict[str, Any]:
    """
    Compute archtop graduation endpoints from wood properties and target frequency.

    Returns edge_mm, apex_mm, arch_height_mm derived from physics model.
    The normalized graduation template shape is universal — this provides the scale.
    """
    if not PLATE_DESIGN_AVAILABLE:
        raise HTTPException(503, detail="Plate design module not available")

    try:
        result = graduation_from_wood_and_target(
            material=req.material,
            body_style=req.body_style,
            target_hz=req.target_hz,
            lower_bout_width_mm=req.lower_bout_width_mm,
            arch_height_ratio=req.arch_height_ratio,
            plate=req.plate,
        )
        return result.to_dict()
    except ValueError as e:
        raise HTTPException(400, detail=str(e))
