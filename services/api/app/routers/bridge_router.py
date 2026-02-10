"""
Bridge Calculator Router
API endpoints for acoustic guitar bridge saddle compensation calculations and DXF export.

Endpoints:
- POST /cam/bridge/export_dxf: Generate DXF from bridge geometry JSON
- GET /cam/bridge/presets: List available family/gauge/action presets
- GET /cam/bridge/health: Health check
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

router = APIRouter(prefix="/cam/bridge", tags=["Bridge Calculator", "CAM"])

IN_TO_MM = 25.4

def inches_to_mm(value: float) -> float:
    """Convert inches to millimeters with 2 decimal precision."""
    return round(value * IN_TO_MM, 2)

# ============================================================================
# Pydantic Models
# ============================================================================

class Point(BaseModel):
    """2D point coordinates."""

    x: float
    y: float

class BridgeEndpoints(BaseModel):
    """Saddle line endpoints (treble and bass sides)."""

    treble: Point
    bass: Point

class BridgeGeometry(BaseModel):
    """Bridge saddle compensation geometry."""

    units: str = Field(..., description="Units: 'mm' or 'in'")
    scaleLength: float = Field(..., description="Scale length from nut to saddle")
    stringSpread: float = Field(..., description="String spread (E-to-E) at bridge")
    compTreble: float = Field(
        ..., description="Compensation offset for treble side (mm or in)"
    )
    compBass: float = Field(
        ..., description="Compensation offset for bass side (mm or in)"
    )
    slotWidth: float = Field(
        ..., description="Saddle slot width (perpendicular to saddle line)"
    )
    slotLength: float = Field(..., description="Saddle slot length (along saddle line)")
    angleDeg: Optional[float] = Field(
        None, description="Saddle angle in degrees (calculated)"
    )
    endpoints: BridgeEndpoints = Field(..., description="Saddle line endpoints")
    slotPolygon: List[Point] = Field(
        ..., description="Slot rectangle polygon (4 vertices)"
    )

class BridgeExportRequest(BaseModel):
    """Request body for DXF export."""

    geometry: BridgeGeometry
    filename: Optional[str] = Field(
        None, description="Optional output filename (without extension)"
    )

class PresetFamily(BaseModel):
    """Guitar family preset definition."""

    id: str
    label: str
    scaleLength: float  # mm
    stringSpread: float  # mm (E-to-E spacing)
    compTreble: float  # mm compensation guide
    compBass: float  # mm compensation guide
    slotWidth: float  # mm slot width
    slotLength: float  # mm slot length

class PresetGauge(BaseModel):
    """String gauge preset."""

    id: str
    label: str
    compAdjust: float  # Legacy aggregate adjustment (mm)
    trebleAdjust: float  # mm delta applied to treble compensation
    bassAdjust: float  # mm delta applied to bass compensation

class PresetAction(BaseModel):
    """Action height preset."""

    id: str
    label: str
    compAdjust: float  # Legacy aggregate adjustment (mm)
    trebleAdjust: float  # mm delta applied to treble compensation
    bassAdjust: float  # mm delta applied to bass compensation

class PresetsResponse(BaseModel):
    """Available presets for bridge calculator."""

    families: List[PresetFamily]
    gauges: List[PresetGauge]
    actions: List[PresetAction]

# ============================================================================
# Preset Data
# ============================================================================

FAMILY_PRESETS = [
    {
        "id": "les_paul",
        "label": 'Les Paul (24.75")',
        "scaleLength": inches_to_mm(24.75),
        "stringSpread": 52.0,
        "compTreble": 1.5,
        "compBass": 3.0,
        "slotWidth": 3.0,
        "slotLength": 75.0,
    },
    {
        "id": "strat_tele",
        "label": 'Strat/Tele (25.5")',
        "scaleLength": inches_to_mm(25.5),
        "stringSpread": 52.5,
        "compTreble": 2.0,
        "compBass": 3.5,
        "slotWidth": 3.0,
        "slotLength": 75.0,
    },
    {
        "id": "om",
        "label": 'OM Acoustic (25.4")',
        "scaleLength": inches_to_mm(25.4),
        "stringSpread": 54.0,
        "compTreble": 2.0,
        "compBass": 4.2,
        "slotWidth": 3.2,
        "slotLength": 80.0,
    },
    {
        "id": "dread",
        "label": 'Dreadnought (25.4")',
        "scaleLength": inches_to_mm(25.4),
        "stringSpread": 54.0,
        "compTreble": 2.0,
        "compBass": 4.5,
        "slotWidth": 3.2,
        "slotLength": 80.0,
    },
    {
        "id": "archtop",
        "label": 'Archtop (25.0")',
        "scaleLength": inches_to_mm(25.0),
        "stringSpread": 52.0,
        "compTreble": 1.8,
        "compBass": 3.2,
        "slotWidth": 3.0,
        "slotLength": 75.0,
    },
]

GAUGE_PRESETS = [
    {
        "id": "light",
        "label": "Light (.010-.046)",
        "compAdjust": -0.3,
        "trebleAdjust": -0.3,
        "bassAdjust": -0.3,
    },
    {
        "id": "medium",
        "label": "Medium (.011-.049)",
        "compAdjust": 0.0,
        "trebleAdjust": 0.0,
        "bassAdjust": 0.0,
    },
    {
        "id": "heavy",
        "label": "Heavy (.012-.053)",
        "compAdjust": 0.35,
        "trebleAdjust": 0.3,
        "bassAdjust": 0.4,
    },
]

ACTION_PRESETS = [
    {
        "id": "low",
        "label": "Low Action",
        "compAdjust": -0.2,
        "trebleAdjust": -0.2,
        "bassAdjust": -0.2,
    },
    {
        "id": "standard",
        "label": "Standard Action",
        "compAdjust": 0.0,
        "trebleAdjust": 0.0,
        "bassAdjust": 0.0,
    },
    {
        "id": "high",
        "label": "High Action",
        "compAdjust": 0.35,
        "trebleAdjust": 0.3,
        "bassAdjust": 0.4,
    },
]

# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/export_dxf", response_class=Response)
def export_bridge_dxf(request: BridgeExportRequest) -> Response:
    """
    Generate a minimal R12 DXF file from bridge geometry.

    Notes:
    - Generates DXF inline to avoid subprocess/script dependencies.
    - Outputs ASCII DXF (latin-1 compatible).
    - Entities:
        * SADDLE_LINE as a LINE
        * SLOT_RECTANGLE as LINE segments following slotPolygon (closed)
    """
    geom = request.geometry

    # ---- Validation (return 422 instead of 500) ----
    units = (geom.units or "").lower().strip()
    if units not in {"mm", "in"}:
        raise HTTPException(status_code=422, detail="units must be 'mm' or 'in'")

    if geom.scaleLength is None or geom.scaleLength <= 0:
        raise HTTPException(status_code=422, detail="scaleLength must be > 0")

    if geom.slotPolygon is None or len(geom.slotPolygon) < 3:
        raise HTTPException(
            status_code=422, detail="slotPolygon must have at least 3 points"
        )

    pts = [(p.x, p.y) for p in geom.slotPolygon]
    if any(x is None or y is None for x, y in pts):
        raise HTTPException(
            status_code=422, detail="slotPolygon points must include x and y"
        )

    # ---- Minimal DXF (R12 / AC1009) ----
    def _dxf_pair(code: int, value: Any) -> str:
        return f"{code}\n{value}\n"

    def _line_entity(layer: str, x1: float, y1: float, x2: float, y2: float) -> str:
        return (
            "0\nLINE\n"
            + _dxf_pair(8, layer)
            + _dxf_pair(10, float(x1))
            + _dxf_pair(20, float(y1))
            + _dxf_pair(11, float(x2))
            + _dxf_pair(21, float(y2))
        )

    # Saddle line from endpoints
    x1, y1 = geom.endpoints.treble.x, geom.endpoints.treble.y
    x2, y2 = geom.endpoints.bass.x, geom.endpoints.bass.y

    entities = []
    entities.append(_line_entity("SADDLE_LINE", x1, y1, x2, y2))

    # Slot polygon as line segments (closed)
    for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1]):
        entities.append(_line_entity("SLOT_RECTANGLE", ax, ay, bx, by))

    dxf_content = (
        "0\nSECTION\n2\nHEADER\n"
        + _dxf_pair(9, "$ACADVER")
        + _dxf_pair(1, "AC1009")
        + "0\nENDSEC\n"
        + "0\nSECTION\n2\nENTITIES\n"
        + "".join(entities)
        + "0\nENDSEC\n0\nEOF\n"
    )

    scale = geom.scaleLength
    comp_t = geom.compTreble
    comp_b = geom.compBass

    if request.filename:
        filename = f"{request.filename}.dxf"
    else:
        filename = f"bridge_{scale:.1f}{units}_ct{comp_t:.1f}_cb{comp_b:.1f}.dxf"

    return Response(
        content=dxf_content.encode("latin-1"),
        media_type="application/dxf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

@router.get("/presets", response_model=PresetsResponse)
def get_bridge_presets() -> Dict[str, Any]:
    """
    Get available presets for bridge calculator.

    Returns family presets (guitar types), gauge presets (string weights),
    and action presets (height adjustments).
    """
    return {
        "families": FAMILY_PRESETS,
        "gauges": GAUGE_PRESETS,
        "actions": ACTION_PRESETS,
    }

