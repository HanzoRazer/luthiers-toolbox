# services/api/app/cad/schemas/dxf_export.py
"""
Pydantic schemas for DXF export API endpoints.
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field

from ..geometry_models import DxfDocumentConfig, Polyline2D, Circle2D


class DxfExportPolylineRequest(BaseModel):
    """Request payload for polyline DXF export."""
    
    polylines: List[Polyline2D] = Field(..., min_length=1)
    layer: str = Field(default="OUTLINE", description="Target layer name")
    config: Optional[DxfDocumentConfig] = Field(
        default=None,
        description="Document configuration. Uses defaults if not provided."
    )


class DxfExportCircleRequest(BaseModel):
    """Request payload for circle DXF export."""
    
    circles: List[Circle2D] = Field(..., min_length=1)
    layer: str = Field(default="OUTLINE")
    config: Optional[DxfDocumentConfig] = None


class DxfExportMixedRequest(BaseModel):
    """Request payload for mixed geometry DXF export."""
    
    polylines: List[Polyline2D] = Field(default_factory=list)
    circles: List[Circle2D] = Field(default_factory=list)
    default_layer: str = Field(default="OUTLINE")
    config: Optional[DxfDocumentConfig] = None


class DxfExportResponse(BaseModel):
    """Metadata returned after a successful export."""
    
    bytes_length: int = Field(..., description="Size of generated DXF in bytes")
    entity_count: int = Field(..., description="Number of entities in document")
    filename: str = Field(..., description="Suggested filename")
    layers: List[str] = Field(default_factory=list, description="Layers used")


class DxfHealthResponse(BaseModel):
    """Health check response for DXF service."""
    
    status: str = "ok"
    dxf_export_enabled: bool = True
    offset_available: bool = False
    version: str = "1.0.0"


class DxfStatsResponse(BaseModel):
    """Document statistics response."""
    
    entity_count: int
    layer_count: int
    layers: List[str]
    units: str
    version: str
    max_entities: int
