"""
CAM Export Object Schema

CAM Dev Order 6B: Portable manufacturing representation.

This module defines the Export Object — the canonical portable
manufacturing representation that sits between governed preview
and machine-specific postprocessing.

Design principles:
  - Self-contained: all information needed to manufacture the part
  - Machine-agnostic: no controller-specific syntax
  - Traceable: links to source geometry and validation
  - Extensible: core schema with operation-specific extensions
  - Versionable: schema version for forward compatibility

This is NOT machine output. No G-code. No executable.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# Schema Version
# -----------------------------------------------------------------------------

EXPORT_SCHEMA_VERSION = "1.0.0"


# -----------------------------------------------------------------------------
# Export Types
# -----------------------------------------------------------------------------

class ExportType(str, Enum):
    """Type of export object."""
    TOOLPATH = "toolpath"   # Full toolpaths for postprocessing
    GEOMETRY = "geometry"   # Geometry only (DXF-equivalent)
    BUNDLE = "bundle"       # Both geometry and toolpaths


# -----------------------------------------------------------------------------
# Coordinate System
# -----------------------------------------------------------------------------

class ExportCoordinateSystem(BaseModel):
    """Complete coordinate system specification."""
    origin: str = Field(..., description="Origin definition (e.g., 'nut_left_face')")
    x_axis: str = Field(..., description="X axis definition (e.g., 'string_to_string')")
    y_axis: str = Field(..., description="Y axis definition (e.g., 'slot_length')")
    z_axis: str = Field(default="depth_into_stock", description="Z axis definition")
    z_zero: str = Field(..., description="Z datum definition (e.g., 'top_of_stock')")
    units: Literal["mm"] = Field(default="mm", description="Units (always mm)")
    handedness: Literal["right_handed", "left_handed"] = Field(
        default="right_handed", description="Coordinate system handedness"
    )
    frame: str = Field(default="local_workpiece", description="Reference frame")


# -----------------------------------------------------------------------------
# Geometry Block
# -----------------------------------------------------------------------------

class ExportBounds(BaseModel):
    """Bounding box in workpiece coordinates."""
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    z_min: float
    z_max: float


class GeometryEntity(BaseModel):
    """A geometric entity (operation-specific)."""
    type: str
    id: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class ExportGeometry(BaseModel):
    """Geometry block of export object."""
    coordinate_system: ExportCoordinateSystem
    bounds: ExportBounds
    entities: List[GeometryEntity] = Field(default_factory=list)


# -----------------------------------------------------------------------------
# Toolpath Block
# -----------------------------------------------------------------------------

class ExportMove(BaseModel):
    """A single toolpath move in neutral format."""
    type: Literal["rapid", "plunge", "linear", "retract", "arc_cw", "arc_ccw"]
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    f: Optional[float] = None  # Feed rate for cutting moves
    i: Optional[float] = None  # Arc center X offset
    j: Optional[float] = None  # Arc center Y offset


class ExportOperation(BaseModel):
    """A toolpath operation."""
    operation_id: str
    operation_type: str
    entity_ref: Optional[str] = None  # Reference to geometry entity
    sequence: int
    moves: List[ExportMove]


class ExportToolpathStatistics(BaseModel):
    """Toolpath statistics."""
    total_operations: int
    total_moves: int
    rapid_moves: int = 0
    cutting_moves: int = 0
    total_rapid_distance_mm: Optional[float] = None
    total_cutting_distance_mm: Optional[float] = None
    estimated_time_s: Optional[float] = None


class ExportToolpaths(BaseModel):
    """Toolpaths block of export object."""
    operations: List[ExportOperation]
    statistics: ExportToolpathStatistics


# -----------------------------------------------------------------------------
# Tooling Block
# -----------------------------------------------------------------------------

class ExportToolGeometry(BaseModel):
    """Tool geometry specification."""
    diameter_mm: float
    cutting_length_mm: Optional[float] = None
    shank_diameter_mm: Optional[float] = None
    overall_length_mm: Optional[float] = None
    flute_count: Optional[int] = None


class ExportTooling(BaseModel):
    """Tooling block of export object."""
    tool_id: str
    tool_type: str
    geometry: ExportToolGeometry
    material: Optional[str] = None
    coating: Optional[str] = None
    operation_class: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


# -----------------------------------------------------------------------------
# Material Block
# -----------------------------------------------------------------------------

class ExportMaterial(BaseModel):
    """Material block of export object."""
    material_type: str = Field(default="unknown", description="Material type")
    material_profile_id: Optional[str] = Field(
        default=None, description="Reference to material profile"
    )
    properties: Dict[str, Any] = Field(default_factory=dict)


# -----------------------------------------------------------------------------
# Stock Block
# -----------------------------------------------------------------------------

class ExportStockDimensions(BaseModel):
    """Stock dimensions."""
    length_mm: float
    width_mm: float
    thickness_mm: float


class ExportStockOrientation(BaseModel):
    """Stock orientation mapping."""
    length_axis: str = "x"
    width_axis: str = "y"
    thickness_axis: str = "z"


class ExportStock(BaseModel):
    """Stock block of export object."""
    stock_type: str = Field(default="rectangular", description="Stock geometry type")
    dimensions: ExportStockDimensions
    orientation: ExportStockOrientation = Field(default_factory=ExportStockOrientation)
    fixture: Optional[Dict[str, Any]] = None


# -----------------------------------------------------------------------------
# Validation Block
# -----------------------------------------------------------------------------

class ExportValidationCheck(BaseModel):
    """A validation check result."""
    check: str
    result: Literal["passed", "failed", "skipped"]
    details: Optional[str] = None


class ExportValidation(BaseModel):
    """Validation block of export object."""
    gate_status: Literal["green", "yellow", "red"]
    preview_gate: Literal["green", "yellow", "red"]
    export_gate: Literal["green", "yellow", "red"]
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    checks_performed: List[ExportValidationCheck] = Field(default_factory=list)
    source_preview_hash: Optional[str] = None


# -----------------------------------------------------------------------------
# Intent Block
# -----------------------------------------------------------------------------

class ExportIntent(BaseModel):
    """Intent block preserving manufacturing intent."""
    operation_type: str
    depth_strategy: Optional[str] = None
    finish_requirements: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


# -----------------------------------------------------------------------------
# Metadata Block
# -----------------------------------------------------------------------------

class ExportSource(BaseModel):
    """Source traceability."""
    preview_id: str
    preview_hash: Optional[str] = None
    generator_id: str
    generator_version: str


class ExportMetadata(BaseModel):
    """Metadata block of export object."""
    export_id: str
    schema_version: str = EXPORT_SCHEMA_VERSION
    created_at: datetime
    created_by: Optional[str] = None
    source: ExportSource
    operation_category: str
    description: Optional[str] = None


# -----------------------------------------------------------------------------
# Export Object (Top Level)
# -----------------------------------------------------------------------------

class ExportObject(BaseModel):
    """
    The canonical portable manufacturing representation.

    Sits between governed preview and machine-specific postprocessing.
    Contains all information needed to manufacture the part without
    any machine-specific syntax.
    """
    schema_version: str = EXPORT_SCHEMA_VERSION
    export_id: str
    export_type: ExportType

    metadata: ExportMetadata
    geometry: ExportGeometry
    toolpaths: ExportToolpaths
    tooling: ExportTooling
    material: ExportMaterial = Field(default_factory=lambda: ExportMaterial())
    stock: ExportStock
    validation: ExportValidation
    intent: ExportIntent


# -----------------------------------------------------------------------------
# Export Response (for endpoints)
# -----------------------------------------------------------------------------

class ExportObjectResponse(BaseModel):
    """Response wrapper for export object endpoint."""
    exportable: bool
    gate: Literal["green", "yellow", "red"]
    export_object: Optional[ExportObject] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
