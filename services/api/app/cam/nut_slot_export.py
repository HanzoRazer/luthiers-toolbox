"""
Nut Slot Export Object Generator

CAM Dev Order 6B: Export object prototype for nut slot CAM.

This module creates Export Objects from governed preview responses.
It proves the export object architecture can exist as running code
before implementing postprocessors or machine output.

No G-code. No machine-specific output. No RMOS persistence.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import List, Optional
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
    ExportObjectResponse,
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
from app.cam.nut_slot_cam import (
    CamGate,
    NutSlotPreviewRequest,
    NutSlotPreviewResponse,
    generate_nut_slot_preview,
)


# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

GENERATOR_ID = "nut_slot_cam"
GENERATOR_VERSION = "1.0.0"
OPERATION_CATEGORY = "slot_cutting"


# -----------------------------------------------------------------------------
# Hash Utilities
# -----------------------------------------------------------------------------

def compute_preview_hash(preview: NutSlotPreviewResponse) -> str:
    """Compute SHA256 hash of preview response for traceability."""
    preview_json = preview.model_dump_json(exclude_none=True)
    return f"sha256:{hashlib.sha256(preview_json.encode()).hexdigest()[:16]}"


def generate_export_id(operation_type: str = "NUT") -> str:
    """Generate unique export ID following pattern EXP-{type}-{date}-{hash}."""
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    unique_hash = uuid4().hex[:8]
    return f"EXP-{operation_type}-{date_str}-{unique_hash}"


# -----------------------------------------------------------------------------
# Coordinate System Mapping
# -----------------------------------------------------------------------------

def map_coordinate_system(preview: NutSlotPreviewResponse) -> ExportCoordinateSystem:
    """Map preview coordinate system to export format."""
    cs = preview.coordinate_system
    return ExportCoordinateSystem(
        origin=cs.origin,
        x_axis=cs.x_axis,
        y_axis=cs.y_axis,
        z_axis="depth_into_stock",
        z_zero=cs.z_zero,
        units="mm",
        handedness="right_handed",
        frame="local_workpiece",
    )


# -----------------------------------------------------------------------------
# Geometry Extraction
# -----------------------------------------------------------------------------

def extract_geometry(
    preview: NutSlotPreviewResponse,
    request: NutSlotPreviewRequest,
) -> ExportGeometry:
    """Extract geometry block from preview."""
    coord_sys = map_coordinate_system(preview)

    # Calculate bounds from toolpaths
    all_x = []
    all_y = []
    all_z = []
    for tp in preview.toolpaths:
        for move in tp.moves:
            all_x.append(move.x)
            all_y.append(move.y)
            all_z.append(move.z)

    bounds = ExportBounds(
        x_min=min(all_x) if all_x else 0.0,
        x_max=max(all_x) if all_x else 0.0,
        y_min=min(all_y) if all_y else 0.0,
        y_max=max(all_y) if all_y else 0.0,
        z_min=min(all_z) if all_z else 0.0,
        z_max=max(all_z) if all_z else 0.0,
    )

    # Create geometry entities for each slot
    entities = []
    for tp in preview.toolpaths:
        entity = GeometryEntity(
            type="slot",
            id=f"slot_{tp.slot_index}",
            properties={
                "x_mm": tp.x_mm,
                "y_start_mm": 0.0,
                "y_end_mm": request.slot_length_mm,
                "width_mm": tp.slot_width_mm,
                "depth_mm": tp.slot_depth_mm,
                "string_number": tp.string_number,
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

def extract_toolpaths(preview: NutSlotPreviewResponse) -> ExportToolpaths:
    """Extract toolpaths block from preview."""
    operations = []

    for tp in preview.toolpaths:
        moves = []
        for move in tp.moves:
            export_move = ExportMove(
                type=move.type,
                x=move.x,
                y=move.y,
                z=move.z,
                f=None,  # Feed rates not in preview yet
            )
            moves.append(export_move)

        operation = ExportOperation(
            operation_id=f"slot_{tp.slot_index}_cut",
            operation_type="slot_cut",
            entity_ref=f"slot_{tp.slot_index}",
            sequence=tp.slot_index,
            moves=moves,
        )
        operations.append(operation)

    # Build statistics
    stats = preview.statistics
    statistics = ExportToolpathStatistics(
        total_operations=stats.total_slots,
        total_moves=stats.cutting_move_count + stats.rapid_move_count,
        rapid_moves=stats.rapid_move_count,
        cutting_moves=stats.cutting_move_count,
        estimated_time_s=stats.estimated_time_s,
    )

    return ExportToolpaths(
        operations=operations,
        statistics=statistics,
    )


# -----------------------------------------------------------------------------
# Tooling Extraction
# -----------------------------------------------------------------------------

def extract_tooling(
    preview: NutSlotPreviewResponse,
    request: NutSlotPreviewRequest,
) -> ExportTooling:
    """Extract tooling block from preview and request."""
    tool = preview.tool

    # Derive tool ID from diameter
    diameter_str = f"{tool.diameter_mm:.2f}".replace(".", "")
    tool_id = f"nut_slot_saw_{diameter_str}"

    return ExportTooling(
        tool_id=tool_id,
        tool_type="slot_saw",
        geometry=ExportToolGeometry(
            diameter_mm=tool.diameter_mm,
            cutting_length_mm=5.0,  # Default for nut slot saws
            shank_diameter_mm=3.175,  # 1/8" standard
        ),
        operation_class=["slot_cutting", "grooving"],
        notes=f"Nut slot saw for {request.num_strings}-string instrument",
    )


# -----------------------------------------------------------------------------
# Stock Extraction
# -----------------------------------------------------------------------------

def extract_stock(request: NutSlotPreviewRequest) -> ExportStock:
    """Extract stock block from request."""
    return ExportStock(
        stock_type="rectangular",
        dimensions=ExportStockDimensions(
            length_mm=request.nut_width_mm,
            width_mm=request.slot_length_mm * 2,  # Estimate
            thickness_mm=request.stock_thickness_mm,
        ),
        fixture={"method": "jig_clamped", "notes": "Nut slot cutting jig"},
    )


# -----------------------------------------------------------------------------
# Validation Extraction
# -----------------------------------------------------------------------------

def extract_validation(
    preview: NutSlotPreviewResponse,
    preview_hash: str,
) -> ExportValidation:
    """Extract validation block from preview."""
    gate_str = preview.gate.value

    # Build checks performed list
    checks = [
        ExportValidationCheck(
            check="tool_diameter_vs_slot_width",
            result="passed" if preview.gate != CamGate.RED else "failed",
        ),
        ExportValidationCheck(
            check="depth_vs_stock_thickness",
            result="passed" if preview.gate != CamGate.RED else "failed",
        ),
        ExportValidationCheck(
            check="position_bounds",
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

def extract_intent(request: NutSlotPreviewRequest) -> ExportIntent:
    """Extract intent block from request context."""
    return ExportIntent(
        operation_type="nut_slot_cutting",
        depth_strategy="full_depth_single_pass",
        finish_requirements={
            "surface_finish": "functional",
            "tolerance_mm": 0.05,
        },
        notes=f"Standard nut slots for {request.num_strings}-string instrument",
    )


# -----------------------------------------------------------------------------
# Metadata Construction
# -----------------------------------------------------------------------------

def build_metadata(
    export_id: str,
    preview_hash: str,
    request: NutSlotPreviewRequest,
) -> ExportMetadata:
    """Build metadata block."""
    return ExportMetadata(
        export_id=export_id,
        schema_version=EXPORT_SCHEMA_VERSION,
        created_at=datetime.now(timezone.utc),
        source=ExportSource(
            preview_id="nut_slot_preview",
            preview_hash=preview_hash,
            generator_id=GENERATOR_ID,
            generator_version=GENERATOR_VERSION,
        ),
        operation_category=OPERATION_CATEGORY,
        description=f"Nut slot toolpaths for {request.num_strings}-string instrument",
    )


# -----------------------------------------------------------------------------
# Pure Function: Create Export Object
# -----------------------------------------------------------------------------

def create_nut_slot_export_object(
    preview: NutSlotPreviewResponse,
    request: NutSlotPreviewRequest,
) -> ExportObject:
    """
    Create export object from validated preview response.

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
    export_id = generate_export_id("NUT")
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


# -----------------------------------------------------------------------------
# Endpoint Function: Generate Export Object Response
# -----------------------------------------------------------------------------

def generate_nut_slot_export_object(
    request: NutSlotPreviewRequest,
) -> ExportObjectResponse:
    """
    Generate export object from request.

    This function:
    1. Generates preview internally (reproducible from source inputs)
    2. Evaluates gate status
    3. Returns export object if GREEN or YELLOW
    4. Returns error response if RED

    Args:
        request: Nut slot preview request

    Returns:
        ExportObjectResponse with export object or error details
    """
    # Generate preview internally (reproducible)
    preview = generate_nut_slot_preview(request)

    # Check gate status
    if preview.gate == CamGate.RED:
        return ExportObjectResponse(
            exportable=False,
            gate="red",
            export_object=None,
            errors=preview.errors,
            warnings=preview.warnings,
        )

    # Create export object
    export_obj = create_nut_slot_export_object(preview, request)

    return ExportObjectResponse(
        exportable=True,
        gate=preview.gate.value,
        export_object=export_obj,
        errors=[],
        warnings=preview.warnings,
    )
