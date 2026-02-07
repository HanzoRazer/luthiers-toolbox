"""
Saw Blade Validator API - Safety validation endpoints.

Endpoints:
- POST /api/saw/validate/operation  - Validate complete operation
- POST /api/saw/validate/contour    - Validate contour radius only
- POST /api/saw/validate/doc        - Validate depth of cut only
- POST /api/saw/validate/feeds      - Validate RPM and feed rate only
- GET  /api/saw/validate/limits     - Get safety limit constants
"""

from fastapi import APIRouter, HTTPException, status
from typing import Optional
from pydantic import BaseModel

from ..cam_core.saw_lab.saw_blade_validator import (
    get_validator,
    ValidationLevel,
    OperationValidation,
    SafetyLimits
)


router = APIRouter(prefix="/saw/validate", tags=["Saw Lab", "Validation"])


# ============================================================================
# Request Models
# ============================================================================

class ValidateOperationRequest(BaseModel):
    """Request to validate complete operation."""
    blade_id: str
    operation_type: str  # "slice", "batch", "contour"
    doc_mm: Optional[float] = None
    rpm: Optional[float] = None
    feed_ipm: Optional[float] = None
    contour_radius_mm: Optional[float] = None
    material_family: Optional[str] = None


class ValidateContourRequest(BaseModel):
    """Request to validate contour radius."""
    blade_id: str
    radius_mm: float


class ValidateDOCRequest(BaseModel):
    """Request to validate depth of cut."""
    blade_id: str
    doc_mm: float


class ValidateFeedsRequest(BaseModel):
    """Request to validate RPM and feed rate."""
    blade_id: str
    rpm: float
    feed_ipm: float


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/operation", response_model=OperationValidation)
def validate_operation(req: ValidateOperationRequest):
    """
    Validate complete saw operation.
    
    Runs all applicable safety checks:
    - Contour radius (if provided)
    - Depth of cut (if provided)
    - RPM (if provided)
    - Feed rate (if provided)
    - Blade design (kerf vs plate)
    - Material compatibility (if provided)
    
    Returns:
        OperationValidation with overall status and individual check results
    """
    validator = get_validator()
    
    try:
        result = validator.validate_operation(
            blade_id=req.blade_id,
            operation_type=req.operation_type,
            doc_mm=req.doc_mm,
            rpm=req.rpm,
            feed_ipm=req.feed_ipm,
            contour_radius_mm=req.contour_radius_mm,
            material_family=req.material_family
        )
        return result
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation error: {str(e)}"
        )


@router.post("/contour", response_model=OperationValidation)
def validate_contour(req: ValidateContourRequest):
    """
    Validate contour radius only.
    
    Quick check: Is radius safe for blade diameter?
    Rule: min_radius >= blade_diameter / 2
    
    Returns:
        OperationValidation with contour radius check
    """
    validator = get_validator()
    
    try:
        result = validator.validate_operation(
            blade_id=req.blade_id,
            operation_type="contour",
            contour_radius_mm=req.radius_mm
        )
        return result
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation error: {str(e)}"
        )


@router.post("/doc", response_model=OperationValidation)
def validate_doc(req: ValidateDOCRequest):
    """
    Validate depth of cut only.
    
    Quick check: Is DOC within safe range?
    Rule: kerf × 1 <= DOC <= kerf × 10
    
    Returns:
        OperationValidation with DOC check
    """
    validator = get_validator()
    
    try:
        result = validator.validate_operation(
            blade_id=req.blade_id,
            operation_type="slice",
            doc_mm=req.doc_mm
        )
        return result
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation error: {str(e)}"
        )


@router.post("/feeds", response_model=OperationValidation)
def validate_feeds(req: ValidateFeedsRequest):
    """
    Validate RPM and feed rate.
    
    Checks:
    - RPM within safe range (2000-6000 typical)
    - Feed rate within safe range (10-300 IPM)
    - Chipload within safe range (0.001-0.020" per tooth)
    
    Returns:
        OperationValidation with RPM and feed checks
    """
    validator = get_validator()
    
    try:
        result = validator.validate_operation(
            blade_id=req.blade_id,
            operation_type="slice",
            rpm=req.rpm,
            feed_ipm=req.feed_ipm
        )
        return result
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation error: {str(e)}"
        )


@router.get("/limits")
def get_safety_limits():
    """
    Get safety limit constants.
    
    Returns:
        Dictionary of safety thresholds used by validator
    """
    limits = SafetyLimits()
    
    return {
        "contour": {
            "min_radius_safety_factor": limits.MIN_RADIUS_SAFETY_FACTOR,
            "description": "min_radius = blade_diameter / 2 * factor"
        },
        "depth_of_cut": {
            "min_kerf_multiple": limits.DOC_MIN_KERF_MULTIPLE,
            "max_kerf_multiple": limits.DOC_MAX_KERF_MULTIPLE,
            "warn_kerf_multiple": limits.DOC_WARN_KERF_MULTIPLE,
            "description": "DOC range = kerf × [min, max]"
        },
        "rpm": {
            "min_universal": limits.RPM_MIN_UNIVERSAL,
            "max_universal": limits.RPM_MAX_UNIVERSAL,
            "warn_high": limits.RPM_WARN_HIGH,
            "description": "Typical saw blade RPM range"
        },
        "feed_rate": {
            "min_ipm": limits.FEED_MIN_IPM,
            "max_ipm": limits.FEED_MAX_IPM,
            "warn_high_ipm": limits.FEED_WARN_HIGH_IPM,
            "description": "Feed rate in inches per minute"
        },
        "chipload": {
            "min": limits.CHIPLOAD_MIN,
            "max": limits.CHIPLOAD_MAX,
            "warn_high": limits.CHIPLOAD_WARN_HIGH,
            "description": "Inches per tooth (feed / (rpm × teeth))"
        },
        "kerf_plate_ratio": {
            "min": limits.KERF_PLATE_RATIO_MIN,
            "max": limits.KERF_PLATE_RATIO_MAX,
            "warn": limits.KERF_PLATE_RATIO_WARN,
            "description": "Kerf width / plate thickness"
        }
    }
