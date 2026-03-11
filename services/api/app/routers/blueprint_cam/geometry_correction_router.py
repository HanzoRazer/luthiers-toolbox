"""
DXF Geometry Correction API Router
====================================

API endpoints for DXF dimension correction and centerline alignment.

Resolves: SG-GAP-01, SG-GAP-02
"""

from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from .dxf_geometry_correction import (
    analyze_dxf_geometry,
    correct_dxf_geometry,
    validate_correction,
    GeometryAnalysis,
)


router = APIRouter(prefix="/geometry-correction", tags=["DXF Geometry Correction"])


class AnalysisResponse(BaseModel):
    """Response from geometry analysis."""
    actual_width_mm: float
    actual_length_mm: float
    bounds_min_x: float
    bounds_min_y: float
    bounds_max_x: float
    bounds_max_y: float
    geometric_center_x: float
    geometric_center_y: float
    centerline_offset_mm: float
    total_points: int
    entity_count: int
    # Spec comparison (if provided)
    spec_width_mm: float = 0.0
    spec_length_mm: float = 0.0
    width_deviation_pct: float = 0.0
    length_deviation_pct: float = 0.0


class CorrectionResponse(BaseModel):
    """Response from geometry correction."""
    success: bool
    # Before
    original_width_mm: float
    original_length_mm: float
    original_centerline_offset_mm: float
    original_width_deviation_pct: float
    original_length_deviation_pct: float
    # After
    corrected_width_mm: float
    corrected_length_mm: float
    corrected_centerline_offset_mm: float
    corrected_width_deviation_pct: float
    corrected_length_deviation_pct: float
    # Transforms applied
    scale_x: float
    scale_y: float
    translate_x: float
    translate_y: float
    # Validation
    validation_passed: bool
    validation_issues: list
    warnings: list
    errors: list


@router.get("/info")
def get_geometry_correction_info():
    """Get geometry correction module info."""
    return {
        "module": "DXF Geometry Correction Pipeline",
        "version": "1.0.0",
        "resolves": ["SG-GAP-01", "SG-GAP-02"],
        "capabilities": {
            "dimension_scaling": "Scale DXF to match spec dimensions",
            "centerline_correction": "Translate DXF to center on X=0",
            "uniform_scale": "Preserve aspect ratio during scaling",
            "geometry_analysis": "Measure bounds, center, deviation from spec",
        },
        "supported_specs": [
            "smart_guitar_v1",
            "explorer",
            "les_paul",
            "stratocaster",
            "flying_v",
        ],
    }


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_geometry(
    file: UploadFile = File(..., description="DXF file to analyze"),
    spec_width_mm: Optional[float] = Form(None, description="Expected width in mm"),
    spec_length_mm: Optional[float] = Form(None, description="Expected length in mm"),
):
    """
    Analyze DXF geometry without modification.

    Returns measured dimensions, centerline offset, and deviation from spec.
    """
    content = await file.read()

    if len(content) == 0:
        raise HTTPException(400, "Empty file")

    analysis = analyze_dxf_geometry(content)

    if analysis.actual_width_mm == 0:
        raise HTTPException(400, "Could not determine DXF bounds")

    # Calculate deviations if spec provided
    width_dev = 0.0
    length_dev = 0.0

    if spec_width_mm:
        width_dev = (analysis.actual_width_mm - spec_width_mm) / spec_width_mm * 100

    if spec_length_mm:
        length_dev = (analysis.actual_length_mm - spec_length_mm) / spec_length_mm * 100

    return AnalysisResponse(
        actual_width_mm=analysis.actual_width_mm,
        actual_length_mm=analysis.actual_length_mm,
        bounds_min_x=analysis.bounds_min[0],
        bounds_min_y=analysis.bounds_min[1],
        bounds_max_x=analysis.bounds_max[0],
        bounds_max_y=analysis.bounds_max[1],
        geometric_center_x=analysis.geometric_center_x,
        geometric_center_y=analysis.geometric_center_y,
        centerline_offset_mm=analysis.centerline_offset_mm,
        total_points=analysis.total_points,
        entity_count=analysis.entity_count,
        spec_width_mm=spec_width_mm or 0.0,
        spec_length_mm=spec_length_mm or 0.0,
        width_deviation_pct=width_dev,
        length_deviation_pct=length_dev,
    )


@router.post("/correct", response_model=CorrectionResponse)
async def correct_geometry(
    file: UploadFile = File(..., description="DXF file to correct"),
    spec_width_mm: Optional[float] = Form(None, description="Target width in mm"),
    spec_length_mm: Optional[float] = Form(None, description="Target length in mm"),
    center_on_x: bool = Form(True, description="Center geometry on X=0"),
    center_on_y: bool = Form(False, description="Center geometry on Y=0"),
    uniform_scale: bool = Form(True, description="Use same scale for X and Y"),
    tolerance_pct: float = Form(2.0, ge=0.0, le=50.0, description="Skip scaling if within tolerance"),
    return_dxf: bool = Form(False, description="Return corrected DXF file"),
):
    """
    Correct DXF geometry to match spec dimensions and center alignment.

    Steps:
    1. Analyze current geometry
    2. Calculate scale factors to match spec dimensions
    3. Calculate translation to center on axis
    4. Apply transformations
    5. Validate result
    """
    content = await file.read()

    if len(content) == 0:
        raise HTTPException(400, "Empty file")

    result = correct_dxf_geometry(
        dxf_bytes=content,
        spec_width_mm=spec_width_mm,
        spec_length_mm=spec_length_mm,
        center_on_x=center_on_x,
        center_on_y=center_on_y,
        uniform_scale=uniform_scale,
        tolerance_pct=tolerance_pct,
    )

    if not result.success:
        raise HTTPException(500, f"Correction failed: {result.errors}")

    # Validate result
    passed, issues = validate_correction(result)

    if return_dxf:
        filename = file.filename or "corrected.dxf"
        if not filename.endswith("_corrected.dxf"):
            filename = filename.replace(".dxf", "_corrected.dxf")
        return Response(
            content=result.dxf_bytes,
            media_type="application/dxf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    orig = result.original_analysis
    corr = result.corrected_analysis

    return CorrectionResponse(
        success=result.success,
        original_width_mm=orig.actual_width_mm if orig else 0.0,
        original_length_mm=orig.actual_length_mm if orig else 0.0,
        original_centerline_offset_mm=orig.centerline_offset_mm if orig else 0.0,
        original_width_deviation_pct=orig.width_deviation_pct if orig else 0.0,
        original_length_deviation_pct=orig.length_deviation_pct if orig else 0.0,
        corrected_width_mm=corr.actual_width_mm if corr else 0.0,
        corrected_length_mm=corr.actual_length_mm if corr else 0.0,
        corrected_centerline_offset_mm=corr.centerline_offset_mm if corr else 0.0,
        corrected_width_deviation_pct=corr.width_deviation_pct if corr else 0.0,
        corrected_length_deviation_pct=corr.length_deviation_pct if corr else 0.0,
        scale_x=result.scale_applied[0],
        scale_y=result.scale_applied[1],
        translate_x=result.translation_applied[0],
        translate_y=result.translation_applied[1],
        validation_passed=passed,
        validation_issues=issues,
        warnings=result.warnings,
        errors=result.errors,
    )


@router.post("/correct-download")
async def correct_and_download(
    file: UploadFile = File(..., description="DXF file to correct"),
    spec_width_mm: Optional[float] = Form(None),
    spec_length_mm: Optional[float] = Form(None),
    center_on_x: bool = Form(True),
    uniform_scale: bool = Form(True),
):
    """
    Correct DXF geometry and return the corrected file.

    Convenience endpoint that always returns the corrected DXF.
    """
    content = await file.read()

    if len(content) == 0:
        raise HTTPException(400, "Empty file")

    result = correct_dxf_geometry(
        dxf_bytes=content,
        spec_width_mm=spec_width_mm,
        spec_length_mm=spec_length_mm,
        center_on_x=center_on_x,
        uniform_scale=uniform_scale,
    )

    if not result.success:
        raise HTTPException(500, f"Correction failed: {result.errors}")

    filename = file.filename or "corrected.dxf"
    if not filename.endswith("_corrected.dxf"):
        filename = filename.replace(".dxf", "_corrected.dxf")

    return Response(
        content=result.dxf_bytes,
        media_type="application/dxf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Scale-X": str(result.scale_applied[0]),
            "X-Scale-Y": str(result.scale_applied[1]),
            "X-Translate-X": str(result.translation_applied[0]),
            "X-Translate-Y": str(result.translation_applied[1]),
        },
    )
