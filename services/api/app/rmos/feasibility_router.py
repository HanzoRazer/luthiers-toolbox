"""
RMOS Feasibility Router

Wave 18: Phase D - Feasibility Fusion Endpoints

FastAPI endpoints for unified feasibility scoring across all risk dimensions.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

from .feasibility_fusion import (
    evaluate_feasibility,
    evaluate_feasibility_for_model,
    FeasibilityReport,
    RiskAssessment,
    RiskLevel,
)
from .context import RmosContext


router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class FeasibilityRequest(BaseModel):
    """Request body for feasibility evaluation."""
    design: Dict[str, Any] = Field(
        ...,
        description="Design parameters (tool_diameter_mm, feed_rate_mmpm, etc.)",
        example={
            "tool_diameter_mm": 6.0,
            "feed_rate_mmpm": 1200,
            "spindle_rpm": 18000,
            "depth_of_cut_mm": 3.0,
        }
    )
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="RMOS context dict (optional if using model_id endpoint)",
    )


class RiskAssessmentResponse(BaseModel):
    """Individual risk assessment response."""
    category: str
    score: float
    risk: str  # GREEN, YELLOW, RED, UNKNOWN
    warnings: List[str]
    details: Dict[str, Any]


class FeasibilityResponse(BaseModel):
    """Feasibility evaluation response."""
    overall_score: float = Field(..., description="Weighted aggregate score (0-100)")
    overall_risk: str = Field(..., description="Worst-case risk level")
    is_feasible: bool = Field(..., description="True if not RED")
    needs_review: bool = Field(..., description="True if YELLOW or RED")
    assessments: List[RiskAssessmentResponse]
    recommendations: List[str]
    pass_threshold: float = 70.0


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/evaluate", response_model=FeasibilityResponse)
async def evaluate_feasibility_endpoint(request: FeasibilityRequest):
    """
    Evaluate manufacturing feasibility with custom RMOS context.
    
    POST /api/rmos/feasibility/evaluate
    
    Request body:
    ```json
    {
      "design": {
        "tool_diameter_mm": 6.0,
        "feed_rate_mmpm": 1200,
        "spindle_rpm": 18000,
        "depth_of_cut_mm": 3.0
      },
      "context": {
        "model_id": "strat_25_5",
        "materials": {...},
        "safety_constraints": {...}
      }
    }
    ```
    
    Response:
    ```json
    {
      "overall_score": 85.3,
      "overall_risk": "GREEN",
      "is_feasible": true,
      "needs_review": false,
      "assessments": [
        {
          "category": "chipload",
          "score": 90.0,
          "risk": "GREEN",
          "warnings": [],
          "details": {...}
        },
        ...
      ],
      "recommendations": [
        "✅ All parameters within safe operating range."
      ]
    }
    ```
    """
    try:
        # Build or deserialize context
        if request.context:
            context = RmosContext.from_dict(request.context)
        else:
            raise HTTPException(
                status_code=400,
                detail="Either 'context' dict or use /evaluate/model/{model_id} endpoint"
            )
        
        # Evaluate feasibility
        report = evaluate_feasibility(request.design, context)
        
        # Convert to response format
        assessments_response = [
            RiskAssessmentResponse(
                category=a.category,
                score=a.score,
                risk=a.risk.value,
                warnings=a.warnings,
                details=a.details,
            )
            for a in report.assessments
        ]
        
        return FeasibilityResponse(
            overall_score=report.overall_score,
            overall_risk=report.overall_risk.value,
            is_feasible=report.is_feasible(),
            needs_review=report.needs_review(),
            assessments=assessments_response,
            recommendations=report.recommendations,
            pass_threshold=report.pass_threshold,
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feasibility evaluation failed: {str(e)}")


@router.post("/evaluate/model/{model_id}", response_model=FeasibilityResponse)
async def evaluate_feasibility_for_model_endpoint(
    model_id: str,
    request: FeasibilityRequest,
):
    """
    Evaluate manufacturing feasibility for a specific guitar model.
    
    POST /api/rmos/feasibility/evaluate/model/strat_25_5
    
    Request body:
    ```json
    {
      "design": {
        "tool_diameter_mm": 6.0,
        "feed_rate_mmpm": 1200,
        "spindle_rpm": 18000,
        "depth_of_cut_mm": 3.0
      }
    }
    ```
    
    Automatically creates RmosContext from model_id.
    Available models: strat_25_5, lp_24_75
    """
    try:
        # Evaluate with model_id
        report = evaluate_feasibility_for_model(model_id, request.design)
        
        # Convert to response format
        assessments_response = [
            RiskAssessmentResponse(
                category=a.category,
                score=a.score,
                risk=a.risk.value,
                warnings=a.warnings,
                details=a.details,
            )
            for a in report.assessments
        ]
        
        return FeasibilityResponse(
            overall_score=report.overall_score,
            overall_risk=report.overall_risk.value,
            is_feasible=report.is_feasible(),
            needs_review=report.needs_review(),
            assessments=assessments_response,
            recommendations=report.recommendations,
            pass_threshold=report.pass_threshold,
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feasibility evaluation failed: {str(e)}")


@router.get("/models")
async def list_available_models():
    """
    List available guitar models for feasibility evaluation.
    
    GET /api/rmos/feasibility/models
    
    Response:
    ```json
    {
      "models": [
        {"id": "strat_25_5", "display_name": "Strat-style 25.5\""},
        {"id": "lp_24_75", "display_name": "LP-style 24.75\""}
      ]
    }
    ```
    """
    from ..instrument_geometry.model_spec import PRESET_MODELS
    
    models = [
        {
            "id": model.id,
            "display_name": model.display_name,
            "scale_length_mm": model.scale_profile().scale_length_mm,
            "num_frets": model.scale_profile().num_frets,
        }
        for model in PRESET_MODELS.values()
    ]
    
    return {"models": models}


@router.get("/risk-levels")
async def list_risk_levels():
    """
    List available risk level values and their meanings.
    
    GET /api/rmos/feasibility/risk-levels
    
    Response:
    ```json
    {
      "levels": [
        {"value": "GREEN", "description": "Safe to proceed"},
        {"value": "YELLOW", "description": "Caution advised"},
        {"value": "RED", "description": "Not recommended"},
        {"value": "UNKNOWN", "description": "Insufficient data"}
      ]
    }
    ```
    """
    return {
        "levels": [
            {"value": "GREEN", "description": "Safe to proceed"},
            {"value": "YELLOW", "description": "Caution advised"},
            {"value": "RED", "description": "Not recommended"},
            {"value": "UNKNOWN", "description": "Insufficient data"},
        ]
    }


@router.get("/categories")
async def list_risk_categories():
    """
    List risk assessment categories and their weights.
    
    GET /api/rmos/feasibility/categories
    
    Response:
    ```json
    {
      "categories": [
        {"name": "chipload", "weight": 0.30, "description": "Tool chipload feasibility"},
        {"name": "heat", "weight": 0.25, "description": "Heat dissipation analysis"},
        ...
      ]
    }
    ```
    """
    return {
        "categories": [
            {
                "name": "chipload",
                "weight": 0.30,
                "description": "Tool chipload feasibility (critical for tool life)",
            },
            {
                "name": "heat",
                "weight": 0.25,
                "description": "Heat dissipation analysis (critical for finish quality)",
            },
            {
                "name": "deflection",
                "weight": 0.20,
                "description": "Tool deflection assessment (affects precision)",
            },
            {
                "name": "rimspeed",
                "weight": 0.15,
                "description": "Rim speed safety check (tool safety concern)",
            },
            {
                "name": "bom_efficiency",
                "weight": 0.10,
                "description": "Material efficiency optimization (cost reduction)",
            },
        ]
    }
