"""
Inlay Pattern Schemas — Request / Response Models

Pydantic v2 models for the inlay pattern generation API.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Shared enums / literals
# ---------------------------------------------------------------------------

InlayShape = Literal[
    "herringbone", "diamond", "greek_key", "spiral", "sunburst", "feather"
]

ExportFormat = Literal["svg", "dxf", "layered_svg"]


# ---------------------------------------------------------------------------
# Generator list
# ---------------------------------------------------------------------------

class InlayGeneratorInfo(BaseModel):
    """Describes one available inlay pattern generator."""
    model_config = ConfigDict(extra="forbid")

    shape: str
    name: str
    description: str = ""
    is_linear: bool = True
    param_hints: Dict[str, Any] = Field(default_factory=dict)


class InlayGeneratorListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    generators: List[InlayGeneratorInfo]


# ---------------------------------------------------------------------------
# Generate request / response
# ---------------------------------------------------------------------------

class InlayGenerateRequest(BaseModel):
    """Request to generate an inlay pattern."""
    model_config = ConfigDict(extra="forbid")

    shape: InlayShape
    params: Dict[str, Any] = Field(default_factory=dict)
    materials: List[str] = Field(
        default=["mop", "ebony", "koa"],
        description="Material keys for element colouring (up to 3)",
    )
    bg_material: str = Field(default="ebony", description="Background material key")
    include_offsets: bool = Field(
        default=False,
        description="If true, response includes offset geometry for CNC",
    )
    male_offset_mm: float = Field(default=0.10, ge=0, description="Male inlay offset (mm)")
    pocket_offset_mm: float = Field(default=0.10, ge=0, description="Pocket offset (mm)")


class InlayGenerateResponse(BaseModel):
    """Response containing generated SVG and metadata."""
    model_config = ConfigDict(extra="forbid")

    shape: str
    svg: str = Field(description="Preview SVG string")
    width_mm: float
    height_mm: float
    element_count: int
    is_radial: bool = False
    warnings: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Export request / response
# ---------------------------------------------------------------------------

class InlayExportRequest(BaseModel):
    """Request to export an inlay pattern in a specific format."""
    model_config = ConfigDict(extra="forbid")

    shape: InlayShape
    params: Dict[str, Any] = Field(default_factory=dict)
    format: ExportFormat = "svg"
    materials: List[str] = Field(default=["mop", "ebony", "koa"])
    bg_material: str = "ebony"
    male_offset_mm: float = Field(default=0.10, ge=0)
    pocket_offset_mm: float = Field(default=0.10, ge=0)


# ---------------------------------------------------------------------------
# Import response
# ---------------------------------------------------------------------------

class InlayImportResponse(BaseModel):
    """Response after importing a DXF/SVG/CSV file."""
    model_config = ConfigDict(extra="forbid")

    format_detected: str
    element_count: int
    width_mm: float
    height_mm: float
    preview_svg: str = Field(description="SVG preview of imported geometry")
