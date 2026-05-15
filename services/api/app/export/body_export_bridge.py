"""
MRP-2A/2B Bridge: BOE Approved Geometry → Export Object

Transforms BOE-approved body geometry into a DXF-agnostic Export Object
candidate suitable for downstream translators.

Sprint: MRP-2B
Updated: MRP-5C (added cad_semantics extension)
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .cad_semantics import CadSemantics


# ─── Input Schemas (BOE Output) ──────────────────────────────────────────────


class ContourData(BaseModel):
    """Contour geometry from BOE export."""
    id: str
    role: str
    closed: bool = True
    winding: str  # "ccw" for outer, "cw" for voids
    points: List[List[float]]  # [[x, y], ...]


class BOEMetadata(BaseModel):
    """Metadata from BOE export."""
    name: str = "untitled"
    source: str = "body_outline_editor"
    created_at: Optional[str] = None


class IBGContext(BaseModel):
    """Optional IBG session context for enrichment."""
    session_id: str
    confidence: float
    dimensions: Dict[str, float]
    instrument_spec: str
    side_heights_mm: Optional[List[float]] = None
    radii_by_zone: Optional[Dict[str, float]] = None
    missing_landmarks: Optional[List[str]] = None
    recovery_mode: Optional[str] = None


class BOEApprovedGeometry(BaseModel):
    """
    BOE-approved body geometry.

    This is the JSON structure exported by body-outline-editor.html
    via the "Export JSON" button.
    """
    schema_version: int = 1
    units: str = "mm"
    origin: str = "body_center_y_positive_toward_neck"
    metadata: BOEMetadata = Field(default_factory=BOEMetadata)
    outer: ContourData
    voids: List[ContourData] = Field(default_factory=list)
    ibg_context: Optional[IBGContext] = None


# ─── Output Schemas (Export Object) ──────────────────────────────────────────


class CoordinateSystem(BaseModel):
    """Export Object coordinate system specification."""
    origin: str = "body_center"
    x_axis: str = "width"
    y_axis: str = "length_toward_neck"
    z_axis: str = "thickness"
    z_zero: str = "top_face"
    units: str = "mm"
    handedness: str = "right_handed"
    frame: str = "local_workpiece"


class Bounds(BaseModel):
    """Bounding box in workpiece coordinates."""
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    z_min: float = 0.0
    z_max: float = 0.0


class GeometryEntity(BaseModel):
    """Geometry entity in Export Object."""
    type: str = "closed_contour"
    id: str
    role: str
    winding: str
    points: List[List[float]]


class ExportGeometry(BaseModel):
    """Export Object geometry block."""
    coordinate_system: CoordinateSystem
    bounds: Bounds
    entities: List[GeometryEntity]


class ValidationCheck(BaseModel):
    """Single validation check result."""
    check: str
    result: str  # "passed" | "warning" | "failed"
    detail: Optional[str] = None


class ExportValidation(BaseModel):
    """Export Object validation block."""
    gate_status: str  # "green" | "yellow" | "red"
    preview_gate: str
    export_gate: str
    issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    checks_performed: List[ValidationCheck] = Field(default_factory=list)
    source_preview_hash: Optional[str] = None


class FinishRequirements(BaseModel):
    """Manufacturing finish requirements."""
    surface_finish: str = "router_quality"
    tolerance_mm: float = 0.5


class ExportIntent(BaseModel):
    """Export Object intent block."""
    operation_type: str = "body_profiling"
    depth_strategy: str = "full_thickness"
    finish_requirements: FinishRequirements = Field(default_factory=FinishRequirements)


class ExportSource(BaseModel):
    """Export Object source metadata."""
    preview_id: str
    preview_hash: str
    generator_id: str = "boe_export"
    generator_version: str = "3.5.0"
    ibg_session_id: Optional[str] = None
    ibg_confidence: Optional[float] = None
    instrument_spec: Optional[str] = None


class ExportMetadata(BaseModel):
    """Export Object metadata block."""
    export_id: str
    schema_version: str = "1.0.0"
    created_at: str
    source: ExportSource
    operation_category: str = "body_profiling"
    description: str = "Body outline"


class IBGMorphologyExtension(BaseModel):
    """IBG morphology extension for Export Object."""
    session_id: str
    confidence: float
    dimensions: Dict[str, float]
    instrument_spec: str
    side_heights_mm: Optional[List[float]] = None
    radii_by_zone: Optional[Dict[str, float]] = None
    missing_landmarks: Optional[List[str]] = None
    recovery_mode: Optional[str] = None


class ExportExtensions(BaseModel):
    """Export Object extensions block."""
    ibg_morphology: Optional[IBGMorphologyExtension] = None
    cad_semantics: Optional["CadSemantics"] = None  # MRP-5C: CAD semantic extension


class BodyExportObject(BaseModel):
    """
    DXF-agnostic Export Object for body geometry.

    Conforms to CAM_EXPORT_OBJECT_MODEL.md schema with export_type="geometry".
    """
    schema_version: str = "1.0.0"
    export_id: str
    export_type: str = "geometry"
    metadata: ExportMetadata
    geometry: ExportGeometry
    validation: ExportValidation
    intent: ExportIntent = Field(default_factory=ExportIntent)
    extensions: Optional[ExportExtensions] = None


# ─── Bridge Functions ────────────────────────────────────────────────────────


def compute_bounds(points: List[List[float]]) -> Bounds:
    """Compute bounding box from point array."""
    if not points:
        return Bounds(x_min=0, x_max=0, y_min=0, y_max=0)

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]

    return Bounds(
        x_min=min(xs),
        x_max=max(xs),
        y_min=min(ys),
        y_max=max(ys),
        z_min=0.0,
        z_max=0.0,
    )


def generate_export_id(points: List[List[float]]) -> str:
    """Generate unique export ID from content hash."""
    content = str(points).encode()
    content_hash = hashlib.sha256(content).hexdigest()[:8]
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"EXP-BODY-{date_str}-{content_hash}"


def compute_preview_hash(points: List[List[float]]) -> str:
    """Compute SHA256 hash of geometry for provenance tracking."""
    content = str(points).encode()
    return hashlib.sha256(content).hexdigest()


def validate_body_geometry(
    outer: ContourData,
    voids: List[ContourData],
) -> ExportValidation:
    """
    Run validation checks on body geometry.

    Returns ExportValidation with gate status and check results.
    """
    checks: List[ValidationCheck] = []
    issues: List[str] = []
    warnings: List[str] = []

    # Check 1: Contour has points
    has_points = len(outer.points) > 0
    checks.append(ValidationCheck(
        check="has_points",
        result="passed" if has_points else "failed",
        detail=f"{len(outer.points)} points" if has_points else "No points",
    ))
    if not has_points:
        issues.append("Outer contour has no points")

    # Check 2: Contour closed (first ≈ last)
    is_closed = False
    if len(outer.points) >= 2:
        first = outer.points[0]
        last = outer.points[-1]
        is_closed = (
            abs(first[0] - last[0]) < 0.01 and
            abs(first[1] - last[1]) < 0.01
        )
    checks.append(ValidationCheck(
        check="contour_closed",
        result="passed" if is_closed else "failed",
        detail="First point matches last" if is_closed else "Contour not closed",
    ))
    if not is_closed and has_points:
        issues.append("Outer contour not closed")

    # Check 3: Winding direction
    is_ccw = outer.winding == "ccw"
    checks.append(ValidationCheck(
        check="winding_ccw",
        result="passed" if is_ccw else "warning",
        detail=f"winding={outer.winding}",
    ))
    if not is_ccw:
        warnings.append(f"Outer contour winding is '{outer.winding}', expected 'ccw'")

    # Check 4: Minimum point count (10+ for reasonable shape)
    enough_points = len(outer.points) >= 10
    checks.append(ValidationCheck(
        check="minimum_points",
        result="passed" if enough_points else "warning",
        detail=f"{len(outer.points)} points (minimum 10)",
    ))
    if not enough_points and has_points:
        warnings.append(f"Only {len(outer.points)} points, may be low resolution")

    # Check 5: Void winding consistency
    void_winding_ok = all(v.winding == "cw" for v in voids)
    if voids:
        checks.append(ValidationCheck(
            check="void_winding_cw",
            result="passed" if void_winding_ok else "warning",
            detail="All voids have cw winding" if void_winding_ok else "Some voids not cw",
        ))
        if not void_winding_ok:
            warnings.append("Some voids do not have clockwise winding")

    # Check 6: Units specified
    # (This is always true for BOE export, but we check anyway)
    checks.append(ValidationCheck(
        check="units_specified",
        result="passed",
        detail="mm",
    ))

    # Determine gate status
    has_failures = any(c.result == "failed" for c in checks)
    has_warnings = any(c.result == "warning" for c in checks)

    if has_failures:
        gate_status = "red"
    elif has_warnings:
        gate_status = "yellow"
    else:
        gate_status = "green"

    preview_hash = compute_preview_hash(outer.points)

    return ExportValidation(
        gate_status=gate_status,
        preview_gate=gate_status,
        export_gate=gate_status,
        issues=issues,
        warnings=warnings,
        checks_performed=checks,
        source_preview_hash=preview_hash,
    )


def create_body_export_object(
    approved: BOEApprovedGeometry,
    ibg_context: Optional[IBGContext] = None,
) -> BodyExportObject:
    """
    Transform BOE-approved geometry to Export Object.

    Args:
        approved: BOE JSON export structure
        ibg_context: Optional IBG session data for enrichment

    Returns:
        Valid BodyExportObject ready for downstream translators
    """
    # Use provided IBG context or extract from approved geometry
    ctx = ibg_context or approved.ibg_context

    # Generate identifiers
    export_id = generate_export_id(approved.outer.points)
    preview_hash = compute_preview_hash(approved.outer.points)

    # Compute bounds
    bounds = compute_bounds(approved.outer.points)

    # Run validation
    validation = validate_body_geometry(approved.outer, approved.voids)

    # Build geometry entities
    entities = [
        GeometryEntity(
            type="closed_contour",
            id=approved.outer.id,
            role=approved.outer.role,
            winding=approved.outer.winding,
            points=approved.outer.points,
        )
    ]
    for void in approved.voids:
        entities.append(GeometryEntity(
            type="closed_contour",
            id=void.id,
            role=void.role,
            winding=void.winding,
            points=void.points,
        ))

    # Build source metadata
    source = ExportSource(
        preview_id=approved.metadata.source,
        preview_hash=preview_hash,
        generator_id="boe_export",
        generator_version="3.5.0",
    )

    # Add IBG context to source if available
    if ctx:
        source.ibg_session_id = ctx.session_id
        source.ibg_confidence = ctx.confidence
        source.instrument_spec = ctx.instrument_spec

    # Build metadata
    metadata = ExportMetadata(
        export_id=export_id,
        schema_version="1.0.0",
        created_at=datetime.now(timezone.utc).isoformat(),
        source=source,
        operation_category="body_profiling",
        description=approved.metadata.name or "Body outline",
    )

    # Build geometry block
    geometry = ExportGeometry(
        coordinate_system=CoordinateSystem(units=approved.units),
        bounds=bounds,
        entities=entities,
    )

    # Build extensions if IBG context available
    extensions = None
    if ctx:
        extensions = ExportExtensions(
            ibg_morphology=IBGMorphologyExtension(
                session_id=ctx.session_id,
                confidence=ctx.confidence,
                dimensions=ctx.dimensions,
                instrument_spec=ctx.instrument_spec,
                side_heights_mm=ctx.side_heights_mm,
                radii_by_zone=ctx.radii_by_zone,
                missing_landmarks=ctx.missing_landmarks,
                recovery_mode=ctx.recovery_mode,
            )
        )

    return BodyExportObject(
        schema_version="1.0.0",
        export_id=export_id,
        export_type="geometry",
        metadata=metadata,
        geometry=geometry,
        validation=validation,
        intent=ExportIntent(),
        extensions=extensions,
    )


def is_export_ready(validation: ExportValidation) -> bool:
    """Check if geometry is approved for export (green or yellow gate)."""
    return validation.gate_status in ("green", "yellow")


# MRP-5C: Resolve forward reference to CadSemantics
# This must be done after the module is loaded to resolve the TYPE_CHECKING import
def _rebuild_models():
    """Rebuild Pydantic models to resolve forward references."""
    from .cad_semantics import CadSemantics  # noqa: F401
    ExportExtensions.model_rebuild()
    BodyExportObject.model_rebuild()


_rebuild_models()
