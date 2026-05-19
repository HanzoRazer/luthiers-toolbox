"""
Nut Slot CAM Router

CAM Dev Order 1: POST /api/cam/nut-slot/preview
CAM Dev Order 6B: POST /api/cam/nut-slot/export-object

Endpoints for generating nut slot CAM preview and export objects.
Software proof-of-concept only — not for shop use.
"""

from fastapi import APIRouter

from app.cam.export_object import ExportObjectResponse
from app.cam.nut_slot_cam import (
    NutSlotPreviewRequest,
    NutSlotPreviewResponse,
    generate_nut_slot_preview,
)
from app.cam.nut_slot_export import generate_nut_slot_export_object

router = APIRouter(prefix="/nut-slot", tags=["cam-nut-slot"])


@router.post(
    "/preview",
    response_model=NutSlotPreviewResponse,
    summary="Generate nut slot CAM preview",
    description="""
Generate toolpath JSON preview for nut slot cutting.

**Status:** Experimental (software proof-of-concept only)

**Gate logic:**
- GREEN: All parameters within safe bounds
- YELLOW: Marginal parameters (warnings present)
- RED: Unsafe parameters (would block export)

**Coordinate system:**
- Origin: Left face of nut
- X axis: String-to-string direction
- Y axis: Slot length direction
- Z-zero: Top of stock

No G-code output. No machine-specific postprocessing.
""",
)
async def preview_nut_slots(request: NutSlotPreviewRequest) -> NutSlotPreviewResponse:
    """Generate nut slot CAM preview with toolpath JSON."""
    return generate_nut_slot_preview(request)


@router.post(
    "/export-object",
    response_model=ExportObjectResponse,
    summary="Generate nut slot export object",
    description="""
Generate portable manufacturing representation for nut slot cutting.

**Status:** Experimental (CAM Dev Order 6B)

**Export Object:**
The export object is a self-contained, machine-agnostic representation
that can be consumed by downstream postprocessors or CAM systems.

**Gate logic:**
- GREEN/YELLOW: Export object created successfully
- RED: Export blocked, returns exportable=false with errors

**Response shape:**
- exportable: boolean indicating if export succeeded
- gate: preview gate status (green/yellow/red)
- export_object: the portable manufacturing representation (if exportable)
- errors: list of blocking errors (if not exportable)
- warnings: list of non-blocking warnings

This is NOT machine output. No G-code. No executable.
""",
)
async def export_nut_slot_object(request: NutSlotPreviewRequest) -> ExportObjectResponse:
    """Generate nut slot export object from request."""
    return generate_nut_slot_export_object(request)
