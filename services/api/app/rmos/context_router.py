# services/api/app/rmos/context_router.py
"""
RMOS Context Router: FastAPI Endpoints for Context Management

Phase B - Wave 17→18 Integration (Optional)

Provides REST API endpoints for:
- Listing available instrument models
- Retrieving RmosContext for a specific model
- Creating custom contexts from JSON payloads
- Validating context integrity

Usage:
    # In main.py:
    from rmos.context_router import router as rmos_context_router
    app.include_router(rmos_context_router, prefix="/api/rmos", tags=["RMOS"])
    
    # Client usage:
    GET  /api/rmos/models                    -> List all model IDs
    GET  /api/rmos/context/{model_id}        -> Get context for model
    POST /api/rmos/context                   -> Create custom context
    POST /api/rmos/context/validate          -> Validate context payload
"""

from __future__ import annotations

from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from .context import RmosContext
from .context_adapter import (
    build_rmos_context_for_model,
    build_rmos_context_from_dict,
    export_context_to_dict,
    get_context_summary,
)


# ---------------------------------------------------------------------------
# Pydantic Models (Request/Response)
# ---------------------------------------------------------------------------

class ModelListResponse(BaseModel):
    """Response model for listing available instrument models."""
    models: List[str] = Field(description="List of model IDs")
    count: int = Field(description="Total number of models")


class ContextResponse(BaseModel):
    """Response model for RmosContext retrieval."""
    context: Dict[str, Any] = Field(description="Full RmosContext as dictionary")
    summary: Dict[str, Any] = Field(description="Human-readable summary")


class ContextCreateRequest(BaseModel):
    """Request model for creating custom RmosContext."""
    model_id: str = Field(description="Instrument model identifier")
    material_species: str = Field(default="maple", description="Wood species")
    material_thickness_mm: float = Field(default=25.4, ge=1.0, le=100.0, description="Stock thickness (mm)")
    include_default_cuts: bool = Field(default=False, description="Add typical cut operations")


class ContextValidateRequest(BaseModel):
    """Request model for validating RmosContext payload."""
    context: Dict[str, Any] = Field(description="RmosContext payload to validate")


class ContextValidateResponse(BaseModel):
    """Response model for context validation."""
    valid: bool = Field(description="Whether context is valid")
    errors: List[str] = Field(description="List of validation errors (empty if valid)")


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter()


@router.get("/models", response_model=ModelListResponse)
def get_available_models():
    """
    List all available instrument model IDs.
    
    Returns:
        ModelListResponse with list of model IDs
    
    Example:
        ```bash
        curl http://localhost:8000/api/rmos/models
        ```
        
        Response:
        ```json
        {
          "models": ["strat_25_5", "lp_24_75", "benedetto_17", ...],
          "count": 6
        }
        ```
    """
    # Import here to avoid circular dependencies
    from ..instrument_geometry.model_spec import PRESET_MODELS
    
    model_ids = list(PRESET_MODELS.keys())
    
    return ModelListResponse(
        models=model_ids,
        count=len(model_ids),
    )


@router.get("/context/{model_id}", response_model=ContextResponse)
def get_context_for_model(
    model_id: str,
    material_species: str = Query(default="maple", description="Wood species"),
    material_thickness_mm: float = Query(default=25.4, ge=1.0, le=100.0, description="Stock thickness (mm)"),
    include_default_cuts: bool = Query(default=False, description="Add typical cut operations"),
):
    """
    Retrieve RmosContext for a specific instrument model.
    
    Args:
        model_id: Instrument model identifier (e.g., "benedetto_17")
        material_species: Wood species (default: "maple")
        material_thickness_mm: Stock thickness in mm (default: 25.4 = 1 inch)
        include_default_cuts: Whether to add typical cut operations
    
    Returns:
        ContextResponse with full context and summary
    
    Raises:
        HTTPException 404: If model_id not found
    
    Example:
        ```bash
        curl "http://localhost:8000/api/rmos/context/benedetto_17?material_species=mahogany&material_thickness_mm=44.45"
        ```
        
        Response:
        ```json
        {
          "context": {
            "model_id": "benedetto_17",
            "model_spec": {...},
            "materials": {...},
            ...
          },
          "summary": {
            "model_id": "benedetto_17",
            "scale_length_in": 25.5,
            "material_species": "mahogany",
            ...
          }
        }
        ```
    """
    try:
        context = build_rmos_context_for_model(
            model_id=model_id,
            material_species=material_species,
            material_thickness_mm=material_thickness_mm,
            include_default_cuts=include_default_cuts,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    return ContextResponse(
        context=export_context_to_dict(context),
        summary=get_context_summary(context),
    )


@router.post("/context", response_model=ContextResponse)
def create_custom_context(request: ContextCreateRequest):
    """
    Create custom RmosContext from request parameters.
    
    Args:
        request: ContextCreateRequest with model_id, material, etc.
    
    Returns:
        ContextResponse with full context and summary
    
    Raises:
        HTTPException 404: If model_id not found
        HTTPException 400: If parameters invalid
    
    Example:
        ```bash
        curl -X POST http://localhost:8000/api/rmos/context \
          -H "Content-Type: application/json" \
          -d '{
            "model_id": "strat_25_5",
            "material_species": "ash",
            "material_thickness_mm": 44.45,
            "include_default_cuts": true
          }'
        ```
        
        Response:
        ```json
        {
          "context": {...},
          "summary": {...}
        }
        ```
    """
    try:
        context = build_rmos_context_for_model(
            model_id=request.model_id,
            material_species=request.material_species,
            material_thickness_mm=request.material_thickness_mm,
            include_default_cuts=request.include_default_cuts,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create context: {str(e)}")
    
    return ContextResponse(
        context=export_context_to_dict(context),
        summary=get_context_summary(context),
    )


@router.post("/context/validate", response_model=ContextValidateResponse)
def validate_context(request: ContextValidateRequest):
    """
    Validate RmosContext payload for integrity.
    
    Args:
        request: ContextValidateRequest with context payload
    
    Returns:
        ContextValidateResponse with validation result
    
    Example:
        ```bash
        curl -X POST http://localhost:8000/api/rmos/context/validate \
          -H "Content-Type: application/json" \
          -d '{
            "context": {
              "model_id": "strat_25_5",
              "model_spec": {...},
              "materials": {...}
            }
          }'
        ```
        
        Response:
        ```json
        {
          "valid": true,
          "errors": []
        }
        ```
        
        Or if invalid:
        ```json
        {
          "valid": false,
          "errors": [
            "Invalid material thickness: -5.0mm",
            "Cut #2 has invalid feed rate: -1000.0"
          ]
        }
        ```
    """
    try:
        context = build_rmos_context_from_dict(request.context)
        errors = context.validate()
        
        return ContextValidateResponse(
            valid=len(errors) == 0,
            errors=errors,
        )
    except Exception as e:
        return ContextValidateResponse(
            valid=False,
            errors=[f"Failed to parse context: {str(e)}"],
        )


@router.get("/context/{model_id}/summary")
def get_context_summary_only(model_id: str):
    """
    Get quick summary of context without full payload (faster endpoint).
    
    Args:
        model_id: Instrument model identifier
    
    Returns:
        Summary dictionary
    
    Example:
        ```bash
        curl http://localhost:8000/api/rmos/context/benedetto_17/summary
        ```
        
        Response:
        ```json
        {
          "model_id": "benedetto_17",
          "display_name": "Benedetto 17\" Archtop",
          "scale_length_in": 25.5,
          "num_strings": 6,
          "material_species": "maple",
          ...
        }
        ```
    """
    try:
        context = build_rmos_context_for_model(model_id)
        return get_context_summary(context)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
