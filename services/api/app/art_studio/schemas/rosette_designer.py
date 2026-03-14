"""
Rosette Designer Schemas — Interactive wheel designer for concentric rosette layouts.

All geometry internally in mm. Inch conversions at API boundary only.
Ring radii stored in SVG units (1 unit = 0.01 inch for legacy compat).
"""
from __future__ import annotations

import math
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SymmetryMode(str, Enum):
    NONE = "none"
    ROTATIONAL = "rotational"
    BILATERAL = "bilateral"
    QUADRANT = "quadrant"


class MfgSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


# ---------------------------------------------------------------------------
# Ring definitions — locked from luthier_rosette_layout.svg audit
# ---------------------------------------------------------------------------

class RingDef(BaseModel):
    """Immutable ring zone geometry."""
    label: str
    r1: float = Field(description="Inner radius in SVG units (1 unit = 0.01 inch)")
    r2: float = Field(description="Outer radius in SVG units")
    color: str
    dot_color: str
    inch1: str
    inch2: str
    has_tabs: bool = False
    tab_inner_r: float = 0
    tab_outer_r: float = 0
    tab_ang_width: float = 0
    tab_fill_even: str = ""
    tab_fill_odd: str = ""


RING_DEFS: list[RingDef] = [
    RingDef(label="Soundhole Binding", r1=150, r2=190, color="#3d2e12",
            dot_color="#c8922a", inch1='1.50"', inch2='1.90"'),
    RingDef(label="Inner Purfling", r1=190, r2=210, color="#2e3512",
            dot_color="#7aaa50", inch1='1.90"', inch2='2.10"'),
    RingDef(label="Main Channel", r1=210, r2=300, color="#12282e",
            dot_color="#50aac8", inch1='2.10"', inch2='3.00"',
            has_tabs=True, tab_inner_r=200, tab_outer_r=312,
            tab_ang_width=10, tab_fill_even="#4a90d9", tab_fill_odd="#b0c8e8"),
    RingDef(label="Outer Purfling", r1=300, r2=320, color="#2e2212",
            dot_color="#c87a50", inch1='3.00"', inch2='3.20"'),
    RingDef(label="Outer Binding", r1=320, r2=350, color="#2e1812",
            dot_color="#c85050", inch1='3.20"', inch2='3.50"'),
]

SEG_OPTIONS: list[int] = [6, 8, 10, 12, 16, 20, 24]


# ---------------------------------------------------------------------------
# Tile catalog
# ---------------------------------------------------------------------------

class TileType(str, Enum):
    SOLID = "solid"
    ABALONE = "abalone"
    MOP = "mop"
    BURL = "burl"
    HERRINGBONE = "herringbone"
    CHECKER = "checker"
    CELTIC = "celtic"
    DIAGONAL = "diagonal"
    DOTS = "dots"
    STRIPES = "stripes"
    STRIPES2 = "stripes2"
    STRIPES3 = "stripes3"
    CLEAR = "clear"


class TileDef(BaseModel):
    id: str
    name: str
    tile_type: TileType = Field(alias="type")
    color: str = ""
    category: str = ""

    model_config = {"populate_by_name": True}


TILE_CATS: list[dict] = [
    {"label": "Tonewoods", "tiles": [
        {"id": "maple", "name": "Maple", "type": "solid", "color": "#D4B483"},
        {"id": "rosewood", "name": "Rosewood", "type": "solid", "color": "#6B2D1A"},
        {"id": "ebony", "name": "Ebony", "type": "solid", "color": "#1C1C1C"},
        {"id": "mahogany", "name": "Mahogany", "type": "solid", "color": "#8B4513"},
        {"id": "spruce", "name": "Spruce", "type": "solid", "color": "#EDD9A3"},
        {"id": "walnut", "name": "Walnut", "type": "solid", "color": "#5C3D2E"},
    ]},
    {"label": "Decorative", "tiles": [
        {"id": "abalone", "name": "Abalone", "type": "abalone"},
        {"id": "mop", "name": "Moth.Pearl", "type": "mop"},
        {"id": "burl", "name": "Burl", "type": "burl"},
        {"id": "cream", "name": "Cream", "type": "solid", "color": "#F5E6C8"},
    ]},
    {"label": "Purfling", "tiles": [
        {"id": "bwb", "name": "B/W/B", "type": "stripes"},
        {"id": "rbr", "name": "R/B/R", "type": "stripes2"},
        {"id": "wbw", "name": "W/B/W", "type": "stripes3"},
    ]},
    {"label": "Motifs", "tiles": [
        {"id": "herringbone", "name": "Herringbone", "type": "herringbone"},
        {"id": "checker", "name": "Checker", "type": "checker"},
        {"id": "celtic", "name": "Celtic", "type": "celtic"},
        {"id": "diagonal", "name": "Diagonal", "type": "diagonal"},
        {"id": "dots", "name": "Dot Inlay", "type": "dots"},
        {"id": "clear", "name": "Clear", "type": "clear"},
    ]},
]

TILE_MAP: dict[str, dict] = {}
for cat in TILE_CATS:
    for tile in cat["tiles"]:
        tile["category"] = cat["label"]
        TILE_MAP[tile["id"]] = tile


# ---------------------------------------------------------------------------
# API request / response models
# ---------------------------------------------------------------------------

class RosetteDesignState(BaseModel):
    """Complete serializable state of a rosette design."""
    version: str = "3"
    name: str = "Untitled Design"
    num_segs: int = Field(default=12, ge=4, le=48)
    sym_mode: SymmetryMode = SymmetryMode.ROTATIONAL
    grid: dict[str, str] = Field(default_factory=dict,
                                  description="Map of 'ringIdx-segIdx' -> tileId")
    ring_active: list[bool] = Field(default_factory=lambda: [True] * 5)
    show_tabs: bool = True
    show_annotations: bool = False
    saved_at: str = ""


class PlaceTileRequest(BaseModel):
    """Place a tile in one or more cells (respecting symmetry)."""
    ring_idx: int = Field(ge=0, le=4)
    seg_idx: int = Field(ge=0)
    tile_id: str
    sym_mode: SymmetryMode = SymmetryMode.ROTATIONAL
    num_segs: int = Field(ge=4, le=48)
    ring_active: list[bool] = Field(default_factory=lambda: [True] * 5)
    grid: dict[str, str] = Field(default_factory=dict)


class PlaceTileResponse(BaseModel):
    grid: dict[str, str]
    affected_cells: list[str]


class SymmetryCellsRequest(BaseModel):
    ring_idx: int = Field(ge=0, le=4)
    seg_idx: int = Field(ge=0)
    sym_mode: SymmetryMode = SymmetryMode.ROTATIONAL
    num_segs: int = Field(ge=4, le=48)


class SymmetryCellsResponse(BaseModel):
    cells: list[list[int]]


class CellInfoResponse(BaseModel):
    zone: str
    seg: str
    angle: str
    depth_inches: str
    arc_len_inches: str
    r1_inches: str
    r2_inches: str
    tile_name: Optional[str] = None
    tile_id: Optional[str] = None


# ---------------------------------------------------------------------------
# BOM models
# ---------------------------------------------------------------------------

class BomPerRingDetail(BaseModel):
    ring_label: str
    count: int
    arc_total_inches: float
    inner_arc_inches: float
    outer_arc_inches: float
    depth_inches: float
    mid_arc_inches: float


class BomMaterialEntry(BaseModel):
    tile_id: str
    tile_name: str
    tile_color_hex: str
    pieces: int
    arc_total_inches: float
    per_ring: list[BomPerRingDetail]
    procurement_strips: list[str]


class BomRingEntry(BaseModel):
    label: str
    dot_color: str
    depth_inches: float
    r1_inches: str
    r2_inches: str
    filled: int
    total_cells: int
    material_names: list[str]
    arc_total_inches: float


class BomResponse(BaseModel):
    filled_cells: int
    total_cells: int
    material_count: int
    total_pieces: int
    total_arc_inches: float
    fill_percent: float
    materials: list[BomMaterialEntry]
    rings: list[BomRingEntry]


class BomRequest(BaseModel):
    num_segs: int = Field(ge=4, le=48)
    grid: dict[str, str] = Field(default_factory=dict)
    ring_active: list[bool] = Field(default_factory=lambda: [True] * 5)
    show_tabs: bool = True


# ---------------------------------------------------------------------------
# Manufacturing Intelligence models
# ---------------------------------------------------------------------------

class MfgFlagCellRef(BaseModel):
    ri: int
    si: int
    key: str
    label: str
    val: float = 0.0


class MfgFlag(BaseModel):
    id: str
    sev: MfgSeverity
    title: str
    desc: str
    cells: list[MfgFlagCellRef] = Field(default_factory=list)
    fix: Optional[str] = None
    has_auto_fix: bool = False


class MfgCheckResponse(BaseModel):
    score: int = Field(ge=0, le=100)
    score_class: str  # "good", "ok", "bad"
    error_count: int
    warning_count: int
    info_count: int
    passing_count: int
    flags: list[MfgFlag]


class MfgCheckRequest(BaseModel):
    num_segs: int = Field(ge=4, le=48)
    sym_mode: SymmetryMode = SymmetryMode.ROTATIONAL
    grid: dict[str, str] = Field(default_factory=dict)
    ring_active: list[bool] = Field(default_factory=lambda: [True] * 5)
    show_tabs: bool = True


# ---------------------------------------------------------------------------
# Recipe models
# ---------------------------------------------------------------------------

class RecipePreset(BaseModel):
    id: str
    name: str
    desc: str
    tags: list[str]
    num_segs: int
    sym_mode: SymmetryMode
    ring_active: list[bool]
    grid: dict[str, str]


class RecipeListResponse(BaseModel):
    recipes: list[RecipePreset]


# ---------------------------------------------------------------------------
# Preview request/response
# ---------------------------------------------------------------------------

class PreviewRequest(BaseModel):
    num_segs: int = Field(default=12, ge=4, le=48)
    grid: dict[str, str] = Field(default_factory=dict)
    ring_active: list[bool] = Field(default_factory=lambda: [True] * 5)
    show_tabs: bool = True
    show_annotations: bool = False
    width: int = Field(default=620, ge=100, le=2000)
    height: int = Field(default=620, ge=100, le=2000)


class PreviewResponse(BaseModel):
    svg: str
    filled_count: int
    total_cells: int


# ---------------------------------------------------------------------------
# Export models
# ---------------------------------------------------------------------------

class ExportSvgRequest(BaseModel):
    num_segs: int = Field(default=12, ge=4, le=48)
    grid: dict[str, str] = Field(default_factory=dict)
    ring_active: list[bool] = Field(default_factory=lambda: [True] * 5)
    show_tabs: bool = True
    with_annotations: bool = False
    design_name: str = "Untitled Design"


class ExportBomCsvRequest(BaseModel):
    num_segs: int = Field(default=12, ge=4, le=48)
    grid: dict[str, str] = Field(default_factory=dict)
    ring_active: list[bool] = Field(default_factory=lambda: [True] * 5)
    show_tabs: bool = True
    design_name: str = "Untitled Design"


# ---------------------------------------------------------------------------
# Catalog response
# ---------------------------------------------------------------------------

class TileCatalogResponse(BaseModel):
    categories: list[dict]
    tile_map: dict[str, dict]
    ring_defs: list[dict]
    seg_options: list[int]
