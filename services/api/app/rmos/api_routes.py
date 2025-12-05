"""
RMOS 2.0 API Routes
FastAPI router for feasibility, BOM, and toolpath endpoints.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from .api_contracts import (
    RmosContext,
    RmosFeasibilityResult,
    RmosBomResult,
    RmosToolpathPlan,
    compute_feasibility_for_design,
    compute_bom_for_design,
    generate_toolpaths_for_design
)

try:
    from ..art_studio.schemas import RosetteParamSpec
except (ImportError, AttributeError, ModuleNotFoundError):
    from .api_contracts import RosetteParamSpec


router = APIRouter()


# ======================
# Request Models
# ======================

class FeasibilityRequest(BaseModel):
    """Request body for feasibility check"""
    design: RosetteParamSpec = Field(..., description="Rosette design parameters")
    context: Optional[RmosContext] = Field(None, description="Manufacturing context (optional)")


class BomRequest(BaseModel):
    """Request body for BOM generation"""
    design: RosetteParamSpec = Field(..., description="Rosette design parameters")
    context: Optional[RmosContext] = Field(None, description="Manufacturing context (optional)")


class ToolpathRequest(BaseModel):
    """Request body for toolpath generation"""
    design: RosetteParamSpec = Field(..., description="Rosette design parameters")
    context: Optional[RmosContext] = Field(None, description="Manufacturing context (optional)")


# ======================
# Endpoints
# ======================

@router.post("/feasibility", response_model=RmosFeasibilityResult, tags=["RMOS"])
async def check_feasibility(request: FeasibilityRequest):
    """
    Check manufacturing feasibility for rosette design.
    
    Returns:
        RmosFeasibilityResult with score, risk bucket, warnings, and estimates
    
    Example:
        POST /api/rmos/feasibility
        {
          "design": {
            "outer_diameter_mm": 100.0,
            "inner_diameter_mm": 20.0,
            "ring_count": 3,
            "pattern_type": "herringbone"
          },
          "context": {
            "material_id": "maple",
            "tool_id": "end_mill_6mm",
            "use_shapely_geometry": true
          }
        }
    """
    try:
        # Use provided context or create default
        ctx = request.context if request.context else RmosContext()
        
        # Compute feasibility
        result = compute_feasibility_for_design(request.design, ctx)
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Feasibility computation failed: {str(e)}"
        )


@router.post("/bom", response_model=RmosBomResult, tags=["RMOS"])
async def generate_bom(request: BomRequest):
    """
    Generate Bill of Materials for rosette design.
    
    Returns:
        RmosBomResult with material requirements, tool IDs, and waste estimate
    
    Example:
        POST /api/rmos/bom
        {
          "design": {
            "outer_diameter_mm": 100.0,
            "inner_diameter_mm": 20.0,
            "ring_count": 3,
            "pattern_type": "herringbone"
          }
        }
    """
    try:
        # Use provided context or create default
        ctx = request.context if request.context else RmosContext()
        
        # Compute BOM
        result = compute_bom_for_design(request.design, ctx)
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"BOM generation failed: {str(e)}"
        )


@router.post("/toolpaths", response_model=RmosToolpathPlan, tags=["RMOS"])
async def generate_toolpaths(request: ToolpathRequest):
    """
    Generate toolpath plan for rosette design.
    
    Returns:
        RmosToolpathPlan with toolpath segments, length, time estimate, and warnings
    
    Example:
        POST /api/rmos/toolpaths
        {
          "design": {
            "outer_diameter_mm": 100.0,
            "inner_diameter_mm": 20.0,
            "ring_count": 3,
            "pattern_type": "herringbone"
          },
          "context": {
            "use_shapely_geometry": true
          }
        }
    """
    try:
        # Use provided context or create default
        ctx = request.context if request.context else RmosContext()
        
        # Generate toolpaths
        result = generate_toolpaths_for_design(request.design, ctx)
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Toolpath generation failed: {str(e)}"
        )


@router.get("/health", tags=["RMOS"])
async def health_check():
    """
    RMOS health check endpoint.
    
    Returns:
        Status message confirming RMOS 2.0 is operational
    """
    return {
        "status": "ok",
        "module": "RMOS 2.0",
        "version": "2.0.0",
        "endpoints": ["/feasibility", "/bom", "/toolpaths"]
    }
