from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class DxfGuidedSlicePreviewRequest(BaseModel):
    """Preview a single saw slice derived from a DXF entity."""

    op_id: str = Field(..., description="Client op id")
    tool_id: str = Field(..., description="Saw tool id")
    dxf_path: str = Field(..., description="Server-side DXF path")
    layer: Optional[str] = Field(None, description="Optional layer filter")
    entity_index: Optional[int] = Field(
        None, description="Index of the DXF geometry to preview"
    )
    unit_scale: float = Field(1.0, description="DXF units to mm multiplier")

    slice_thickness_mm: float = 1.0
    passes: int = 1
    material: str = "hardwood"
    workholding: str = "vacuum"


class DxfGuidedBatchPreviewRequest(BaseModel):
    """Preview a batch of saw slices derived from a DXF file."""

    op_id: str = Field(..., description="Client batch id")
    tool_id: str = Field(..., description="Saw tool id")
    dxf_path: str = Field(..., description="Server-side DXF path")
    layer: Optional[str] = Field(None, description="Layer filter")
    max_entities: Optional[int] = Field(None, description="Limit extracted geometries")
    unit_scale: float = Field(1.0, description="DXF units to mm multiplier")

    slice_thickness_mm: float = 1.0
    passes: int = 1
    material: str = "hardwood"
    workholding: str = "vacuum"
