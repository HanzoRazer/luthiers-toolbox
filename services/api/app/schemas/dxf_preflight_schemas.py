"""
Pydantic schemas for DXF preflight router.

Extracted from dxf_preflight_router.py (Phase 13 decomposition).
"""
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class ValidationIssue(BaseModel):
    """Single validation issue found in DXF"""
    severity: Literal["error", "warning", "info"]
    category: Literal["format", "geometry", "units", "layers", "compatibility"]
    message: str
    details: Optional[str] = None
    fix_available: bool = False
    fix_description: Optional[str] = None


class GeometrySummary(BaseModel):
    """Summary of geometry types in DXF"""
    lines: int = 0
    arcs: int = 0
    circles: int = 0
    polylines: int = 0
    lwpolylines: int = 0
    splines: int = 0
    ellipses: int = 0
    text: int = 0
    other: int = 0
    total: int = 0


class LayerInfo(BaseModel):
    """Information about a single layer"""
    name: str
    entity_count: int
    geometry_types: List[str]
    color: Optional[int] = None
    frozen: bool = False
    locked: bool = False


class ValidationReport(BaseModel):
    """Complete validation report for a DXF file"""
    filename: str
    filesize_bytes: int
    dxf_version: str
    units: Optional[str] = None
    issues: List[ValidationIssue]
    errors_count: int
    warnings_count: int
    info_count: int
    geometry: GeometrySummary
    layers: List[LayerInfo]
    cam_ready: bool
    recommended_actions: List[str]


class ValidateBase64Request(BaseModel):
    """Request to validate DXF from base64"""
    dxf_base64: str
    filename: str = "uploaded.dxf"


class AutoFixRequest(BaseModel):
    """Request to auto-fix common DXF issues"""
    dxf_base64: str
    filename: str
    fixes: List[Literal[
        "convert_to_r12", "close_open_polylines", "explode_splines",
        "merge_duplicate_layers", "set_units_mm"
    ]]


class CurvePoint(BaseModel):
    """Simple XY point used by CurveLab"""
    x: float
    y: float


class CurveBiarcEntity(BaseModel):
    """Optional bi-arc metadata from CurveLab client"""
    type: Literal["arc", "line"]
    radius: Optional[float] = None
    center: Optional[CurvePoint] = None
    start_angle: Optional[float] = None
    end_angle: Optional[float] = None
    a: Optional[CurvePoint] = Field(None, description="Line start point")
    b: Optional[CurvePoint] = Field(None, description="Line end point")


class CurvePreflightRequest(BaseModel):
    """Inline geometry payload sent by CurveLab.vue"""
    points: List[CurvePoint]
    units: Literal["mm", "inch"] = "mm"
    tolerance_mm: float = Field(0.1, description="Closure/duplicate tolerance in millimeters")
    layer: str = Field("CURVE", description="DXF layer name to preview")
    biarc_entities: Optional[List[CurveBiarcEntity]] = None


class PolylineMetrics(BaseModel):
    point_count: int
    length: float
    length_units: str
    closed: bool
    closure_gap: float
    closure_units: str
    duplicate_count: int
    duplicate_indices: List[int]
    bounding_box: Dict[str, float]


class BiarcMetrics(BaseModel):
    entity_count: int
    arcs: int
    lines: int
    min_radius: Optional[float]
    max_radius: Optional[float]
    radius_units: str = "mm"


class CurvePreflightResponse(BaseModel):
    """Response payload consumed by CurveLab Preflight modal"""
    units: str
    tolerance_mm: float
    issues: List[ValidationIssue]
    errors_count: int
    warnings_count: int
    info_count: int
    polyline: PolylineMetrics
    biarc: Optional[BiarcMetrics]
    cam_ready: bool
    recommended_actions: List[str]
