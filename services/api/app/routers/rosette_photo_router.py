# services/api/app/routers/rosette_photo_router.py
"""
Rosette Photo Import Router

Converts photographs/screenshots of rosette patterns into
CNC-ready vector files (DXF R12 + SVG).

Endpoints:
- POST /api/cam/rosette/import_photo - Convert uploaded photo
- POST /api/cam/rosette/import_photo_advanced - Convert with custom settings
"""

from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Literal
import tempfile
import os
from pathlib import Path

# Import converter (with graceful degradation if OpenCV not available)
try:
    from ..cam.rosette.photo_converter import (
        RosettePhotoConverter,
        ConversionSettings,
        convert_photo_to_svg,
    )
    CONVERTER_AVAILABLE = True
except ImportError as e:
    CONVERTER_AVAILABLE = False
    IMPORT_ERROR = str(e)


router = APIRouter(prefix="/cam/rosette", tags=["Rosette Photo Import"])


# ============================================================================
# Schemas
# ============================================================================


class PhotoImportRequest(BaseModel):
    """Basic photo import settings."""
    output_width_mm: float = Field(100.0, ge=10, le=500, description="Target width in mm")
    fit_to_ring: bool = Field(False, description="Warp to circular ring shape")
    ring_inner_mm: float = Field(45.0, ge=10, le=200, description="Inner ring diameter")
    ring_outer_mm: float = Field(55.0, ge=20, le=300, description="Outer ring diameter")
    simplify: float = Field(1.0, ge=0.1, le=10.0, description="Path simplification (higher = simpler)")
    invert: bool = Field(False, description="Invert black/white")


class AdvancedPhotoImportRequest(BaseModel):
    """Advanced photo import with full control."""
    # Preprocessing
    blur_kernel: int = Field(5, ge=1, le=31, description="Gaussian blur size (odd)")
    threshold_method: Literal["otsu", "adaptive", "manual"] = Field("adaptive")
    manual_threshold: int = Field(127, ge=0, le=255)
    invert: bool = Field(False)
    
    # Contour detection
    min_contour_area: float = Field(100, ge=1)
    max_contour_area: float = Field(1e8, ge=1000)
    simplify_epsilon: float = Field(1.0, ge=0.1, le=10.0)
    
    # Output
    output_width_mm: float = Field(100.0, ge=10, le=500)
    center_on_origin: bool = Field(True)
    fit_to_circle: bool = Field(False)
    circle_inner_mm: float = Field(45.0, ge=10, le=200)
    circle_outer_mm: float = Field(55.0, ge=20, le=300)
    
    # Cleanup
    remove_background: bool = Field(True)
    close_paths: bool = Field(True)


class PhotoImportResponse(BaseModel):
    """Photo import result."""
    success: bool
    svg_content: str
    dxf_content: str
    stats: dict


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/import_photo", response_model=PhotoImportResponse)
async def import_rosette_photo(
    file: UploadFile = File(...),
    output_width_mm: float = 100.0,
    fit_to_ring: bool = False,
    ring_inner_mm: float = 45.0,
    ring_outer_mm: float = 55.0,
    simplify: float = 1.0,
    invert: bool = False,
):
    """
    Convert uploaded rosette photo to DXF + SVG.
    
    Workflow:
    1. Upload image (JPG, PNG, etc.)
    2. Auto-detect contours via OpenCV
    3. Convert to vector paths
    4. Export DXF R12 + SVG
    
    Args:
        file: Image file (photo, screenshot, scan)
        output_width_mm: Target width in mm
        fit_to_ring: Warp pattern to circular ring
        ring_inner_mm: Inner ring diameter (if fitting)
        ring_outer_mm: Outer ring diameter (if fitting)
        simplify: Path simplification (higher = fewer points)
        invert: Invert black/white
    
    Returns:
        SVG and DXF content with conversion statistics
    """
    if not CONVERTER_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail=f"Photo converter not available. Missing dependency: {IMPORT_ERROR}"
        )
    
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Must be an image."
        )
    
    # Validate ring dimensions
    if fit_to_ring and ring_inner_mm >= ring_outer_mm:
        raise HTTPException(
            status_code=400,
            detail="ring_outer_mm must be greater than ring_inner_mm"
        )
    
    try:
        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_input:
            content = await file.read()
            tmp_input.write(content)
            tmp_input_path = tmp_input.name
        
        # Create temp output paths
        tmp_svg = tempfile.NamedTemporaryFile(delete=False, suffix='.svg')
        tmp_dxf = tempfile.NamedTemporaryFile(delete=False, suffix='.dxf')
        tmp_svg.close()
        tmp_dxf.close()
        
        # Convert
        settings = ConversionSettings(
            output_width_mm=output_width_mm,
            fit_to_circle=fit_to_ring,
            circle_inner_mm=ring_inner_mm,
            circle_outer_mm=ring_outer_mm,
            simplify_epsilon=simplify,
            invert=invert,
        )
        
        converter = RosettePhotoConverter(settings)
        result = converter.convert(tmp_input_path, tmp_svg.name, tmp_dxf.name)
        
        # Read outputs
        with open(tmp_svg.name, 'r') as f:
            svg_content = f.read()
        
        with open(tmp_dxf.name, 'r') as f:
            dxf_content = f.read()
        
        # Cleanup temp files
        os.unlink(tmp_input_path)
        os.unlink(tmp_svg.name)
        os.unlink(tmp_dxf.name)
        
        return PhotoImportResponse(
            success=True,
            svg_content=svg_content,
            dxf_content=dxf_content,
            stats={
                "contour_count": result["contour_count"],
                "total_points": result["total_points"],
                "input_filename": file.filename,
                "output_width_mm": output_width_mm,
                "fit_to_ring": fit_to_ring,
            }
        )
    
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(
            status_code=500,
            detail=f"Conversion failed: {str(e)}"
        )


@router.post("/import_photo_advanced", response_model=PhotoImportResponse)
async def import_rosette_photo_advanced(
    file: UploadFile = File(...),
    settings: AdvancedPhotoImportRequest = None,
):
    """
    Convert rosette photo with advanced control over all parameters.
    
    Provides full access to:
    - Preprocessing (blur, threshold method)
    - Contour detection (area filters, simplification)
    - Output formatting (dimensions, centering)
    - Cleanup options (background removal, path closing)
    
    Args:
        file: Image file
        settings: Advanced conversion settings
    
    Returns:
        SVG and DXF content with statistics
    """
    if not CONVERTER_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail=f"Photo converter not available. Missing dependency: {IMPORT_ERROR}"
        )
    
    if settings is None:
        settings = AdvancedPhotoImportRequest()
    
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Must be an image."
        )
    
    # Validate blur kernel (must be odd)
    if settings.blur_kernel % 2 == 0:
        settings.blur_kernel += 1
    
    try:
        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_input:
            content = await file.read()
            tmp_input.write(content)
            tmp_input_path = tmp_input.name
        
        # Create temp outputs
        tmp_svg = tempfile.NamedTemporaryFile(delete=False, suffix='.svg')
        tmp_dxf = tempfile.NamedTemporaryFile(delete=False, suffix='.dxf')
        tmp_svg.close()
        tmp_dxf.close()
        
        # Convert with advanced settings
        conv_settings = ConversionSettings(
            blur_kernel=settings.blur_kernel,
            threshold_method=settings.threshold_method,
            manual_threshold=settings.manual_threshold,
            invert=settings.invert,
            min_contour_area=settings.min_contour_area,
            max_contour_area=settings.max_contour_area,
            simplify_epsilon=settings.simplify_epsilon,
            output_width_mm=settings.output_width_mm,
            center_on_origin=settings.center_on_origin,
            fit_to_circle=settings.fit_to_circle,
            circle_inner_mm=settings.circle_inner_mm,
            circle_outer_mm=settings.circle_outer_mm,
            remove_background=settings.remove_background,
            close_paths=settings.close_paths,
        )
        
        converter = RosettePhotoConverter(conv_settings)
        result = converter.convert(tmp_input_path, tmp_svg.name, tmp_dxf.name)
        
        # Read outputs
        with open(tmp_svg.name, 'r') as f:
            svg_content = f.read()
        
        with open(tmp_dxf.name, 'r') as f:
            dxf_content = f.read()
        
        # Cleanup
        os.unlink(tmp_input_path)
        os.unlink(tmp_svg.name)
        os.unlink(tmp_dxf.name)
        
        return PhotoImportResponse(
            success=True,
            svg_content=svg_content,
            dxf_content=dxf_content,
            stats={
                "contour_count": result["contour_count"],
                "total_points": result["total_points"],
                "input_filename": file.filename,
                "settings": settings.dict(),
            }
        )
    
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(
            status_code=500,
            detail=f"Advanced conversion failed: {str(e)}"
        )


@router.get("/import_photo/status")
def check_photo_import_status():
    """
    Check if photo import functionality is available.
    
    Returns availability status and error details if unavailable.
    """
    return {
        "available": CONVERTER_AVAILABLE,
        "error": None if CONVERTER_AVAILABLE else IMPORT_ERROR,
        "dependencies": {
            "opencv": CONVERTER_AVAILABLE,
            "numpy": CONVERTER_AVAILABLE,
            "pillow": CONVERTER_AVAILABLE,
        }
    }
