"""
Pipeline to CAM Adapter Router
==============================

API endpoint for converting Phase 4 PipelineResult to CAM-ready format.

Resolves: VEC-GAP-03 (Phase 4 PipelineResult has no consumer)

Endpoints:
    POST /from-pipeline  - Convert PipelineResult JSON to CAM spec
    GET  /info           - Adapter info
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ...services.pipeline_cam_adapter import adapt_dict_to_cam, CamReadySpec

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pipeline-adapter", tags=["Pipeline CAM Adapter"])


class PipelineResultInput(BaseModel):
    """Input: Phase 4 PipelineResult as JSON dict."""
    source_file: str = ""
    extraction: Dict[str, Any] = {}
    linking: Dict[str, Any] = {}
    linked_dimensions: Dict[str, Any] = {}


class CamSpecResponse(BaseModel):
    """Response: CAM-ready specification."""
    success: bool
    geometry: Dict[str, Any] = {}
    dimensions: Dict[str, Any] = {}
    suggested_params: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
    warnings: list = []


@router.get("/info")
def get_adapter_info() -> Dict[str, Any]:
    """Get pipeline adapter information."""
    return {
        "module": "pipeline_cam_adapter",
        "description": "Converts Phase 4 PipelineResult to CAM-ready specification",
        "resolves": ["VEC-GAP-03"],
        "input": "PipelineResult JSON from /blueprint/phase4/link-json",
        "output": "CamReadySpec with loops, dimensions, suggested params",
    }


@router.post("/from-pipeline", response_model=CamSpecResponse)
def convert_pipeline_to_cam(data: PipelineResultInput) -> CamSpecResponse:
    """
    Convert Phase 4 PipelineResult to CAM-ready specification.
    
    Takes the JSON output from /blueprint/phase4/link-json and produces
    a CAM-ready spec with:
    - Geometry loops for toolpath generation
    - Extracted dimensions (body size, pocket depths)
    - Suggested CAM parameters based on dimensions
    """
    try:
        result_dict = data.model_dump()
        spec = adapt_dict_to_cam(result_dict)
        
        return CamSpecResponse(
            success=True,
            **spec.to_dict()
        )
    except Exception as e:  # WP-2: API endpoint catch-all
        logger.exception("Pipeline to CAM conversion failed")
        raise HTTPException(500, f"Conversion failed: {e}")


@router.post("/from-pipeline-raw")
def convert_pipeline_raw(data: Dict[str, Any]) -> JSONResponse:
    """
    Convert raw PipelineResult dict to CAM spec.
    
    Accepts any JSON dict and attempts to extract CAM-relevant data.
    """
    try:
        spec = adapt_dict_to_cam(data)
        return JSONResponse(content=spec.to_dict())
    except Exception as e:  # WP-2: API endpoint catch-all
        logger.exception("Pipeline to CAM conversion failed")
        raise HTTPException(500, f"Conversion failed: {e}")
