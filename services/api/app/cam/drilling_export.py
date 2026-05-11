"""
Drilling Export Object Generator

CAM Dev Order 6G: Export object for drilling operations.

This module creates Export Objects from governed drilling preview responses.
It proves the export object architecture is operation-extensible.

No G-code. No machine-specific output. No RMOS persistence.
No peck cycles. No canned cycles.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import List
from uuid import uuid4

from app.cam.export_object import (
    EXPORT_SCHEMA_VERSION,
    ExportBounds,
    ExportCoordinateSystem,
    ExportGeometry,
    ExportIntent,
    ExportMaterial,
    ExportMetadata,
    ExportMove,
    ExportObject,
    ExportOperation,
    ExportSource,
    ExportStock,
    ExportStockDimensions,
    ExportToolGeometry,
    ExportTooling,
    ExportToolpaths,
    ExportToolpathStatistics,
    ExportType,
    ExportValidation,
    ExportValidationCheck,
    GeometryEntity,
)
from app.cam.routers.drilling.drilling_preview_router import (
    DrillingPreviewRequest,
    DrillingPreviewResponse,
    CamGate,
)


# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

GENERATOR_ID = "drilling_preview"
GENERATOR_VERSION = "1.0.0"
OPERATION_CATEGORY = "drilling"


# -----------------------------------------------------------------------------
# Hash Utilities
# -----------------------------------------------------------------------------

def compute_preview_hash(preview: DrillingPreviewResponse) -> str:
    """Compute SHA256 hash of preview response for traceability."""
    preview_json = preview.model_dump_json(exclude_none=True)
    return f"sha256:{hashlib.sha256(preview_json.encode()).hexdigest()[:16]}"


def generate_export_id(operation_type: str = "DRILL") -> str:
    """Generate unique export ID following pattern EXP-{type}-{date}-{hash}."""
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    unique_hash = uuid4().hex[:8]
    return f"EXP-{operation_type}-{date_str}-{unique_hash}"


# -----------------------------------------------------------------------------
# Coordinate System Mapping
# -----------------------------------------------------------------------------

def map_coordinate_system(preview: DrillingPreviewResponse) -> ExportCoordinateSystem:
    """Map preview coordinate system to export format."""
    cs = preview.coordinate_system
    return ExportCoordinateSystem(
        origin=cs.origin,
        x_axis=cs.x_axis,
        y_axis=cs.y_axis,
        z_axis=cs.z_axis,
        z_zero=cs.z_zero,
        units=cs.units,
        handedness=cs.handedness,
        frame=cs.frame,
    )


# -----------------------------------------------------------------------------
# Geometry Extraction
# -----------------------------------------------------------------------------

def extract_geometry(
    preview: DrillingPreviewResponse,
    request: DrillingPreviewRequest,
) -> ExportGeometry:
    """Extract geometry block from preview."""
    coord_sys = map_coordinate_system(preview)

    # Get holes from canonical toolpath
    holes = preview.canonical_toolpath.get("holes", [])

    # Calculate bounds from holes
    if holes:
        x_coords = [h["x_mm"] for h in holes]
        y_coords = [h["y_mm"] for h in holes]
        max_radius = max(h["radius_mm"] for h in holes)
        max_depth = max(h["depth_mm"] for h in holes)

        bounds = ExportBounds(
            x_min=min(x_coords) - max_radius,
            x_max=max(x_coords) + max_radius,
            y_min=min(y_coords) - max_radius,
            y_max=max(y_coords) + max_radius,
            z_min=0.0,
            z_max=max_depth,
        )
    else:
        bounds = ExportBounds(
            x_min=0.0, x_max=0.0,
            y_min=0.0, y_max=0.0,
            z_min=0.0, z_max=0.0,
        )

    # Create geometry entities for each hole
    entities: List[GeometryEntity] = []
    for i, hole in enumerate(holes):
        label = hole.get("label") or f"hole_{i + 1}"
        entity = GeometryEntity(
            type="hole",
            id=label,
            properties={
                "x_mm": hole["x_mm"],
                "y_mm": hole["y_mm"],
                "diameter_mm": hole["diameter_mm"],
                "radius_mm": hole["radius_mm"],
                "depth_mm": hole["depth_mm"],
            },
        )
        entities.append(entity)

    return ExportGeometry(
        coordinate_system=coord_sys,
        bounds=bounds,
        entities=entities,
    )


# -----------------------------------------------------------------------------
# Toolpath Extraction
# -----------------------------------------------------------------------------

def extract_toolpaths(preview: DrillingPreviewResponse) -> ExportToolpaths:
    """Extract toolpaths block from preview."""
    holes = preview.canonical_toolpath.get("holes", [])
    operations: List[ExportOperation] = []

    for i, hole in enumerate(holes):
        label = hole.get("label") or f"hole_{i + 1}"

        # Drilling toolpath: rapid to position, plunge, retract
        moves = [
            ExportMove(type="rapid", x=hole["x_mm"], y=hole["y_mm"], z=0.0),
            ExportMove(type="plunge", x=hole["x_mm"], y=hole["y_mm"], z=hole["depth_mm"]),
            ExportMove(type="retract", x=hole["x_mm"], y=hole["y_mm"], z=0.0),
        ]

        operation = ExportOperation(
            operation_id=f"{label}_drill",
            operation_type="drill",
            entity_ref=label,
            sequence=i,
            moves=moves,
        )
        operations.append(operation)

    # Build statistics from preview
    stats = preview.statistics
    statistics = ExportToolpathStatistics(
        total_operations=stats.get("hole_count", len(holes)),
        total_moves=stats.get("move_count", len(holes) * 3),
        rapid_moves=len(holes),
        cutting_moves=len(holes) * 2,  # plunge + retract per hole
        estimated_time_s=None,
    )

    return ExportToolpaths(
        operations=operations,
        statistics=statistics,
    )


# -----------------------------------------------------------------------------
# Tooling Extraction
# -----------------------------------------------------------------------------

def extract_tooling(
    preview: DrillingPreviewResponse,
    request: DrillingPreviewRequest,
) -> ExportTooling:
    """Extract tooling block from preview."""
    holes = preview.canonical_toolpath.get("holes", [])

    # Get unique diameters
    diameters = sorted(set(h["diameter_mm"] for h in holes))
    primary_diameter = diameters[0] if diameters else 3.0

    # Generate tool ID from primary diameter
    diameter_str = f"{primary_diameter:.2f}".replace(".", "")
    tool_id = f"drill_bit_{diameter_str}"

    return ExportTooling(
        tool_id=tool_id,
        tool_type="drill_bit",
        geometry=ExportToolGeometry(
            diameter_mm=primary_diameter,
            cutting_length_mm=primary_diameter * 5,  # Standard 5x diameter flute
            shank_diameter_mm=primary_diameter,
        ),
        operation_class=["drilling", "hole_making"],
        notes=f"Drill bit for {len(holes)} hole(s), primary diameter {primary_diameter}mm",
    )


# -----------------------------------------------------------------------------
# Stock Extraction
# -----------------------------------------------------------------------------

def extract_stock(request: DrillingPreviewRequest) -> ExportStock:
    """Extract stock block from request."""
    return ExportStock(
        stock_type="rectangular",
        dimensions=ExportStockDimensions(
            length_mm=request.stock_width_mm or 100.0,
            width_mm=request.stock_height_mm or 100.0,
            thickness_mm=request.stock_thickness_mm or 20.0,
        ),
        fixture={"method": "clamped", "notes": "Drilling fixture"},
    )


# -----------------------------------------------------------------------------
# Validation Extraction
# -----------------------------------------------------------------------------

def extract_validation(
    preview: DrillingPreviewResponse,
    preview_hash: str,
) -> ExportValidation:
    """Extract validation block from preview."""
    gate_str = preview.gate.value

    # Build checks performed list
    checks = [
        ExportValidationCheck(
            check="hole_overlap",
            result="passed" if preview.gate != CamGate.RED else "failed",
        ),
        ExportValidationCheck(
            check="depth_vs_stock",
            result="passed" if preview.gate != CamGate.RED else "failed",
        ),
        ExportValidationCheck(
            check="bounds_check",
            result="passed" if preview.gate != CamGate.RED else "failed",
        ),
    ]

    # Convert issues to dict format
    issues = [issue.model_dump() for issue in preview.issues]

    return ExportValidation(
        gate_status=gate_str,
        preview_gate=gate_str,
        export_gate=gate_str,
        issues=issues,
        warnings=preview.warnings,
        checks_performed=checks,
        source_preview_hash=preview_hash,
    )


# -----------------------------------------------------------------------------
# Intent Extraction
# -----------------------------------------------------------------------------

def extract_intent(request: DrillingPreviewRequest) -> ExportIntent:
    """Extract intent block from request context."""
    hole_count = len(request.holes)
    return ExportIntent(
        operation_type="drilling",
        depth_strategy="single_plunge",
        finish_requirements={
            "surface_finish": "functional",
            "tolerance_mm": 0.1,
        },
        notes=f"Drilling operation with {hole_count} hole(s)",
    )


# -----------------------------------------------------------------------------
# Metadata Construction
# -----------------------------------------------------------------------------

def build_metadata(
    export_id: str,
    preview_hash: str,
    request: DrillingPreviewRequest,
) -> ExportMetadata:
    """Build metadata block."""
    hole_count = len(request.holes)
    return ExportMetadata(
        export_id=export_id,
        schema_version=EXPORT_SCHEMA_VERSION,
        created_at=datetime.now(timezone.utc),
        source=ExportSource(
            preview_id="drilling_preview",
            preview_hash=preview_hash,
            generator_id=GENERATOR_ID,
            generator_version=GENERATOR_VERSION,
        ),
        operation_category=OPERATION_CATEGORY,
        description=f"Drilling toolpaths for {hole_count} hole(s)",
    )


# -----------------------------------------------------------------------------
# Pure Function: Create Export Object
# -----------------------------------------------------------------------------

def create_drilling_export_object(
    preview: DrillingPreviewResponse,
    request: DrillingPreviewRequest,
) -> ExportObject:
    """
    Create export object from validated drilling preview response.

    Pure function that transforms a governed preview into
    a portable manufacturing representation.

    Args:
        preview: Validated preview response (gate GREEN or YELLOW)
        request: Original request for context

    Returns:
        ExportObject ready for downstream consumption

    Note:
        Caller must verify gate is not RED before calling.
        This function does not check gate status.
    """
    export_id = generate_export_id("DRILL")
    preview_hash = compute_preview_hash(preview)

    return ExportObject(
        schema_version=EXPORT_SCHEMA_VERSION,
        export_id=export_id,
        export_type=ExportType.TOOLPATH,
        metadata=build_metadata(export_id, preview_hash, request),
        geometry=extract_geometry(preview, request),
        toolpaths=extract_toolpaths(preview),
        tooling=extract_tooling(preview, request),
        material=ExportMaterial(
            material_type="unknown",
            material_profile_id=None,
        ),
        stock=extract_stock(request),
        validation=extract_validation(preview, preview_hash),
        intent=extract_intent(request),
    )
