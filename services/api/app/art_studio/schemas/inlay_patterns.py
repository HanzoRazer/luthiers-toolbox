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
    "herringbone", "diamond", "greek_key", "spiral", "sunburst", "feather",
    "celtic_motif", "vine_scroll", "girih_rosette", "binding_flow",
    "hex_chain", "chevron_panel", "parquet_panel", "nested_diamond",
    "rope_border_motif", "twisted_rope", "compose_band",
    "checker_chevron", "block_pin", "amsterdam_flower", "spiro_arc", "sq_floral",
    "oak_medallion", "floral_spray", "open_flower_oval",
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

class ComposeBandRequest(BaseModel):
    """Request to generate a composite multi-layer band."""
    model_config = ConfigDict(extra="forbid")

    preset: Optional[str] = Field(default=None, description="Preset name")
    layers: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Layer dicts: [{shape, params, weight}, ...]",
    )
    band_width_mm: float = Field(default=150, gt=0)
    band_height_mm: float = Field(default=25, gt=0)
    gap_mm: float = Field(default=0.5, ge=0)
    repeats: int = Field(default=1, ge=1)
    mirror: bool = False
    materials: List[str] = Field(default=["mop", "ebony", "koa"])
    bg_material: str = "ebony"
    include_offsets: bool = False
    male_offset_mm: float = Field(default=0.10, ge=0)
    pocket_offset_mm: float = Field(default=0.10, ge=0)


class InlayImportResponse(BaseModel):
    """Response after importing a DXF/SVG/CSV file."""
    model_config = ConfigDict(extra="forbid")

    format_detected: str
    element_count: int
    width_mm: float
    height_mm: float
    preview_svg: str = Field(description="SVG preview of imported geometry")


# ---------------------------------------------------------------------------
# BOM response
# ---------------------------------------------------------------------------

class InlayBomEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    shape_type: str
    material_key: str
    count: int
    area_mm2: float


class InlayBomResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    shape: str
    entries: List[InlayBomEntry]
    total_pieces: int
    total_area_mm2: float


# ---------------------------------------------------------------------------
# Blueprint bridge request
# ---------------------------------------------------------------------------

class BlueprintToInlayRequest(BaseModel):
    """Request to import geometry from a Blueprint Reader vectorisation result."""
    model_config = ConfigDict(extra="forbid")

    dxf_path: Optional[str] = Field(
        default=None,
        description="Server-side path to vectorised DXF from Blueprint Reader",
    )
    svg_path: Optional[str] = Field(
        default=None,
        description="Server-side path to vectorised SVG from Blueprint Reader",
    )
    layer_filter: Optional[str] = Field(
        default=None,
        description="DXF layer name to extract (e.g. 'ROSETTE', 'BODY_OUTLINE')",
    )
