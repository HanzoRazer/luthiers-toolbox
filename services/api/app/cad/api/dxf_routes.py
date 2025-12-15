# services/api/app/cad/api/dxf_routes.py
"""
FastAPI routes for DXF export operations.

These routes provide HTTP access to the DXF engine with proper
validation, error handling, and feature flags.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Optional
import logging

from fastapi import APIRouter, HTTPException, Response, status

from ..dxf_engine import DxfEngine
from ..exceptions import CadEngineError, DxfValidationError
from ..offset_engine import is_offset_available
from ..schemas.dxf_export import (
    DxfExportPolylineRequest,
    DxfExportCircleRequest,
    DxfExportMixedRequest,
    DxfExportResponse,
    DxfHealthResponse,
    DxfStatsResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dxf", tags=["cad-dxf"])


# =============================================================================
# FEATURE FLAG
# =============================================================================

DXF_EXPORT_ENABLED = os.getenv("DXF_EXPORT_ENABLED", "1").lower() not in {"0", "false", "no"}


def _ensure_enabled() -> None:
    """Check if DXF export is enabled."""
    if not DXF_EXPORT_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DXF export is currently disabled by configuration.",
        )


def _generate_filename(prefix: str = "export") -> str:
    """Generate timestamped filename."""
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{ts}.dxf"


# =============================================================================
# HEALTH / STATUS
# =============================================================================

@router.get(
    "/health",
    response_model=DxfHealthResponse,
    summary="DXF service health check",
)
def health_check() -> DxfHealthResponse:
    """Check DXF service status and capabilities."""
    return DxfHealthResponse(
        status="ok" if DXF_EXPORT_ENABLED else "disabled",
        dxf_export_enabled=DXF_EXPORT_ENABLED,
        offset_available=is_offset_available(),
        version="1.0.0",
    )


# =============================================================================
# POLYLINE EXPORT
# =============================================================================

@router.post(
    "/polylines",
    response_model=DxfExportResponse,
    summary="Generate DXF metadata from polylines",
)
def export_polylines_meta(request: DxfExportPolylineRequest) -> DxfExportResponse:
    """
    Generate DXF from polylines and return metadata.
    
    Use /polylines/download to get the actual file.
    """
    _ensure_enabled()
    
    try:
        engine = DxfEngine(config=request.config)
        for poly in request.polylines:
            engine.add_polyline(poly, layer=request.layer)
        data = engine.to_bytes()
        
        return DxfExportResponse(
            bytes_length=len(data),
            entity_count=engine.entity_count,
            filename=_generate_filename("polylines"),
            layers=engine.layers,
        )
        
    except DxfValidationError as exc:
        logger.warning(f"DXF validation error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.to_dict(),
        ) from exc
    except CadEngineError as exc:
        logger.error(f"DXF engine error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=exc.to_dict(),
        ) from exc


@router.post(
    "/polylines/download",
    responses={200: {"content": {"application/dxf": {}}}},
    summary="Download DXF from polylines",
)
def export_polylines_download(request: DxfExportPolylineRequest) -> Response:
    """Generate and download DXF from polylines."""
    _ensure_enabled()
    
    try:
        engine = DxfEngine(config=request.config)
        for poly in request.polylines:
            engine.add_polyline(poly, layer=request.layer)
        data = engine.to_bytes()
        
        filename = _generate_filename("polylines")
        
        return Response(
            content=data,
            media_type="application/dxf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
        
    except DxfValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.to_dict(),
        ) from exc
    except CadEngineError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=exc.to_dict(),
        ) from exc


# =============================================================================
# CIRCLE EXPORT
# =============================================================================

@router.post(
    "/circles",
    response_model=DxfExportResponse,
    summary="Generate DXF metadata from circles",
)
def export_circles_meta(request: DxfExportCircleRequest) -> DxfExportResponse:
    """Generate DXF from circles and return metadata."""
    _ensure_enabled()
    
    try:
        engine = DxfEngine(config=request.config)
        for circle in request.circles:
            engine.add_circle(circle, layer=request.layer)
        data = engine.to_bytes()
        
        return DxfExportResponse(
            bytes_length=len(data),
            entity_count=engine.entity_count,
            filename=_generate_filename("circles"),
            layers=engine.layers,
        )
        
    except DxfValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.to_dict(),
        ) from exc
    except CadEngineError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=exc.to_dict(),
        ) from exc


@router.post(
    "/circles/download",
    responses={200: {"content": {"application/dxf": {}}}},
    summary="Download DXF from circles",
)
def export_circles_download(request: DxfExportCircleRequest) -> Response:
    """Generate and download DXF from circles."""
    _ensure_enabled()
    
    try:
        engine = DxfEngine(config=request.config)
        for circle in request.circles:
            engine.add_circle(circle, layer=request.layer)
        data = engine.to_bytes()
        
        filename = _generate_filename("circles")
        
        return Response(
            content=data,
            media_type="application/dxf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
        
    except (DxfValidationError, CadEngineError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


# =============================================================================
# MIXED GEOMETRY EXPORT
# =============================================================================

@router.post(
    "/mixed",
    response_model=DxfExportResponse,
    summary="Generate DXF metadata from mixed geometry",
)
def export_mixed_meta(request: DxfExportMixedRequest) -> DxfExportResponse:
    """Generate DXF from mixed geometry types and return metadata."""
    _ensure_enabled()
    
    try:
        engine = DxfEngine(config=request.config)
        
        for poly in request.polylines:
            engine.add_polyline(poly, layer=request.default_layer)
        
        for circle in request.circles:
            engine.add_circle(circle, layer=request.default_layer)
        
        data = engine.to_bytes()
        
        return DxfExportResponse(
            bytes_length=len(data),
            entity_count=engine.entity_count,
            filename=_generate_filename("mixed"),
            layers=engine.layers,
        )
        
    except (DxfValidationError, CadEngineError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post(
    "/mixed/download",
    responses={200: {"content": {"application/dxf": {}}}},
    summary="Download DXF from mixed geometry",
)
def export_mixed_download(request: DxfExportMixedRequest) -> Response:
    """Generate and download DXF from mixed geometry."""
    _ensure_enabled()
    
    try:
        engine = DxfEngine(config=request.config)
        
        for poly in request.polylines:
            engine.add_polyline(poly, layer=request.default_layer)
        
        for circle in request.circles:
            engine.add_circle(circle, layer=request.default_layer)
        
        data = engine.to_bytes()
        filename = _generate_filename("mixed")
        
        return Response(
            content=data,
            media_type="application/dxf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
        
    except (DxfValidationError, CadEngineError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
