"""
DXF Preprocessor API Router
============================

API endpoints for DXF preprocessing pipeline.

Resolves: EX-GAP-01, EX-GAP-02, EX-GAP-03
"""

from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from .dxf_preprocessor import (
    preprocess_dxf,
    validate_dimensions,
    INSTRUMENT_SPECS,
    MIN_PRODUCTION_POINTS,
    MAX_SEGMENT_LENGTH_MM,
)


router = APIRouter(prefix="/preprocess", tags=["DXF Preprocessor"])


class PreprocessResponse(BaseModel):
    """Response from DXF preprocessing."""
    success: bool
    original_version: str = ""
    normalized_version: str = ""
    original_point_count: int = 0
    densified_point_count: int = 0
    original_bounds_mm: tuple = (0.0, 0.0)
    dimension_validation: Optional[dict] = None
    warnings: list = []
    errors: list = []


class ValidationResponse(BaseModel):
    """Response from dimension validation."""
    valid: bool
    instrument_type: str = ""
    actual_width_mm: float = 0.0
    actual_height_mm: float = 0.0
    expected_width_range: tuple = (0.0, 0.0)
    expected_height_range: tuple = (0.0, 0.0)
    width_deviation_pct: float = 0.0
    height_deviation_pct: float = 0.0
    message: str = ""


@router.get("/info")
def get_preprocessor_info():
    """Get preprocessor configuration and supported instruments."""
    return {
        "module": "DXF Preprocessor Pipeline",
        "version": "1.0.0",
        "resolves": ["EX-GAP-01", "EX-GAP-02", "EX-GAP-03"],
        "capabilities": {
            "format_normalization": "Convert any DXF version to R2000 (AC1015)",
            "curve_densification": f"Add points for min {MIN_PRODUCTION_POINTS} points per curve",
            "dimension_validation": "Validate bounds against instrument specs",
        },
        "supported_instruments": list(INSTRUMENT_SPECS.keys()),
        "config": {
            "min_production_points": MIN_PRODUCTION_POINTS,
            "max_segment_length_mm": MAX_SEGMENT_LENGTH_MM,
        },
    }


@router.post("/full", response_model=PreprocessResponse)
async def preprocess_full(
    file: UploadFile = File(..., description="DXF file to preprocess"),
    instrument_type: Optional[str] = Form(None, description="Instrument type for validation"),
    normalize_format: bool = Form(True, description="Normalize to R2000 format"),
    densify_curves: bool = Form(True, description="Densify coarse polylines"),
    validate_dims: bool = Form(True, description="Validate dimensions"),
    min_points: int = Form(MIN_PRODUCTION_POINTS, ge=10, le=10000),
    return_dxf: bool = Form(False, description="Return processed DXF file"),
):
    """
    Full DXF preprocessing pipeline.

    Applies:
    1. Format normalization (any version → R2000)
    2. Curve densification (coarse → 200+ points)
    3. Dimension validation (bounds vs spec)
    """
    content = await file.read()

    if len(content) == 0:
        raise HTTPException(400, "Empty file")

    result = preprocess_dxf(
        dxf_bytes=content,
        normalize_format=normalize_format,
        densify_curves=densify_curves,
        validate_dims=validate_dims,
        instrument_type=instrument_type,
        min_points=min_points,
    )

    if return_dxf and result.success:
        filename = file.filename or "processed.dxf"
        if not filename.endswith("_processed.dxf"):
            filename = filename.replace(".dxf", "_processed.dxf")
        return Response(
            content=result.dxf_bytes,
            media_type="application/dxf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    return PreprocessResponse(
        success=result.success,
        original_version=result.original_version,
        normalized_version=result.normalized_version,
        original_point_count=result.original_point_count,
        densified_point_count=result.densified_point_count,
        original_bounds_mm=result.original_bounds_mm,
        dimension_validation=result.dimension_validation,
        warnings=result.warnings,
        errors=result.errors,
    )


@router.post("/validate", response_model=ValidationResponse)
async def validate_dxf_dimensions(
    file: UploadFile = File(..., description="DXF file to validate"),
    instrument_type: Optional[str] = Form(None, description="Instrument type for validation"),
):
    """
    Validate DXF dimensions against instrument spec.

    Returns deviation percentages if dimensions are outside expected range.
    """
    content = await file.read()

    if len(content) == 0:
        raise HTTPException(400, "Empty file")

    result = validate_dimensions(content, instrument_type)

    return ValidationResponse(
        valid=result.valid,
        instrument_type=result.instrument_type,
        actual_width_mm=result.actual_width,
        actual_height_mm=result.actual_height,
        expected_width_range=result.expected_width_range,
        expected_height_range=result.expected_height_range,
        width_deviation_pct=result.width_deviation_pct,
        height_deviation_pct=result.height_deviation_pct,
        message=result.message,
    )


@router.post("/normalize")
async def normalize_dxf_format_endpoint(
    file: UploadFile = File(..., description="DXF file to normalize"),
):
    """
    Normalize DXF to R2000 format only.

    Returns the normalized DXF file.
    """
    from .dxf_preprocessor import normalize_dxf_format

    content = await file.read()

    if len(content) == 0:
        raise HTTPException(400, "Empty file")

    normalized_bytes, orig_ver, new_ver, warnings = normalize_dxf_format(content)

    filename = file.filename or "normalized.dxf"
    if not filename.endswith("_r2000.dxf"):
        filename = filename.replace(".dxf", "_r2000.dxf")

    return Response(
        content=normalized_bytes,
        media_type="application/dxf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Original-Version": orig_ver,
            "X-Normalized-Version": new_ver,
            "X-Warnings": "; ".join(warnings) if warnings else "none",
        },
    )


@router.post("/densify")
async def densify_dxf_endpoint(
    file: UploadFile = File(..., description="DXF file to densify"),
    min_points: int = Form(MIN_PRODUCTION_POINTS, ge=10, le=10000),
    max_segment_mm: float = Form(MAX_SEGMENT_LENGTH_MM, ge=0.1, le=50.0),
):
    """
    Densify coarse polylines to production quality.

    Returns the densified DXF file.
    """
    from .dxf_preprocessor import densify_dxf

    content = await file.read()

    if len(content) == 0:
        raise HTTPException(400, "Empty file")

    densified_bytes, orig_pts, new_pts, warnings = densify_dxf(
        content, min_points, max_segment_mm
    )

    filename = file.filename or "densified.dxf"
    if not filename.endswith("_dense.dxf"):
        filename = filename.replace(".dxf", "_dense.dxf")

    return Response(
        content=densified_bytes,
        media_type="application/dxf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Original-Points": str(orig_pts),
            "X-Densified-Points": str(new_pts),
            "X-Warnings": "; ".join(warnings) if warnings else "none",
        },
    )
