"""
RosetteProject — Unified envelope for rosette design + manufacturing.

Phase 3 Consolidation: bridges the two parallel type systems:
  - CAM side:  pattern_schemas.RingSpec  (dataclass, diameter-based)
  - API side:  rosette_pattern.RosetteRingBand (Pydantic, radius-based)

The RosetteProject is the single object a client sends to get back
design geometry, manufacturing plans, and CAM-ready data in one call.
"""

from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from .rosette_pattern import RosettePatternInDB, RosetteRingBand


# ── Type-bridge converters ──────────────────────────────────────────────────

def ring_band_to_cam_dict(band: RosetteRingBand) -> Dict:
    """
    Convert an API RosetteRingBand → dict accepted by RosettePatternEngine.generate_modern().

    Mapping:
        radius_mm + width_mm  →  inner/outer diameter (diameter = 2 × radius)
        strip_family_id       →  pattern_type (best-effort heuristic)
        slice_angle_deg       →  tile_angle_deg
        color_hint            →  primary_color
    """
    inner_d = 2.0 * (band.radius_mm - band.width_mm / 2.0)
    outer_d = 2.0 * (band.radius_mm + band.width_mm / 2.0)

    pattern_type = _family_to_pattern_type(band.strip_family_id)

    return {
        "ring_index": band.index,
        "inner_diameter_mm": round(max(inner_d, 0.0), 4),
        "outer_diameter_mm": round(outer_d, 4),
        "pattern_type": pattern_type,
        "primary_color": band.color_hint or "black",
        "secondary_color": "white",
        "tile_angle_deg": band.slice_angle_deg,
    }


def cam_ring_to_band(
    ring_dict: Dict,
    *,
    band_id: Optional[str] = None,
    strip_family_id: Optional[str] = None,
) -> RosetteRingBand:
    """
    Convert a CAM ring dict → API RosetteRingBand.

    Mapping:
        inner/outer diameter  →  radius_mm (midpoint), width_mm (difference / 2)
        pattern_type          →  strip_family_id
        primary_color         →  color_hint
        tile_angle_deg        →  slice_angle_deg
    """
    inner_d = float(ring_dict["inner_diameter_mm"])
    outer_d = float(ring_dict["outer_diameter_mm"])
    radius = (inner_d + outer_d) / 4.0  # midpoint radius
    width = (outer_d - inner_d) / 2.0

    idx = int(ring_dict.get("ring_index", 0))
    fam = strip_family_id or ring_dict.get("pattern_type", "solid")

    return RosetteRingBand(
        id=band_id or f"ring_{idx}",
        index=idx,
        radius_mm=round(radius, 4),
        width_mm=round(width, 4),
        color_hint=ring_dict.get("primary_color"),
        strip_family_id=fam,
        slice_angle_deg=float(ring_dict.get("tile_angle_deg", 0.0)),
    )


_FAMILY_PATTERN_MAP = {
    "checker": "checkerboard",
    "herring": "herringbone",
    "rope": "rope",
    "solid": "solid",
    "wave": "wave",
    "spanish": "spanish",
    "celtic": "celtic_knot",
}


def _family_to_pattern_type(family_id: str) -> str:
    """Best-effort map from strip_family_id → PatternType value."""
    lower = family_id.lower()
    for key, ptype in _FAMILY_PATTERN_MAP.items():
        if key in lower:
            return ptype
    return "solid"


# ── Project envelope ────────────────────────────────────────────────────────

class CamOverrides(BaseModel):
    """Optional per-project CAM parameter overrides."""

    tool_diameter_mm: float = Field(default=3.0, ge=0.5, le=25.0)
    stepover_pct: float = Field(default=0.45, ge=0.1, le=1.0)
    stepdown_mm: float = Field(default=0.5, ge=0.1, le=5.0)
    feed_xy_mm_min: float = Field(default=600.0, ge=50.0)
    safe_z_mm: float = Field(default=5.0, ge=1.0)


class RosetteProjectRequest(BaseModel):
    """
    Unified request to assemble a complete rosette project.

    Accepts a saved pattern (RosettePatternInDB) and returns
    design visuals, manufacturing plan, and CAM geometry together.
    """

    pattern: RosettePatternInDB = Field(
        ..., description="Full rosette pattern with ring bands"
    )
    guitars: int = Field(default=1, ge=1, le=500)
    tile_length_mm: float = Field(default=8.0, ge=1.0, le=50.0)
    scrap_factor: float = Field(default=0.12, ge=0.0, le=1.0)

    include_cam: bool = Field(
        default=False,
        description="Generate CAM toolpath geometry for the channel",
    )
    cam_overrides: Optional[CamOverrides] = None

    include_modern_preview: bool = Field(
        default=False,
        description="Generate modern parametric ring visuals (DXF/SVG)",
    )
    preview_formats: List[Literal["dxf", "svg"]] = Field(default_factory=lambda: ["svg"])


class ManufacturingPlanSummary(BaseModel):
    """Compact manufacturing plan included in project response."""

    guitars: int
    total_rings: int
    total_families: int
    total_tiles: int
    total_sticks: int
    strip_plans: List[Dict] = Field(default_factory=list)
    notes: Optional[str] = None


class CamSummary(BaseModel):
    """Compact CAM result included in project response."""

    rings_count: int
    z_passes: int
    move_count: int
    estimated_length_mm: float
    gcode_preview_lines: int = 0


class RosetteProjectResponse(BaseModel):
    """
    Unified project response — everything assembled in one payload.
    """

    project_name: str
    pattern_id: str
    soundhole_diameter_mm: float

    # Type-bridge metadata
    ring_count: int
    ring_mapping: List[Dict] = Field(
        default_factory=list,
        description="Per-ring mapping showing API band ↔ CAM ring correspondence",
    )

    # Manufacturing plan (always included)
    manufacturing: ManufacturingPlanSummary

    # CAM geometry (optional)
    cam: Optional[CamSummary] = None

    # Modern preview (optional)
    preview_svg: Optional[str] = None
    preview_dxf: Optional[str] = None
