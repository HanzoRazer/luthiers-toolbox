"""
Nut Slot CAM Router

CAM Dev Order 1: POST /api/cam/nut-slot/preview

Endpoint for generating nut slot CAM preview with toolpath JSON.
Software proof-of-concept only — not for shop use.
"""

from fastapi import APIRouter

from app.cam.nut_slot_cam import (
    NutSlotPreviewRequest,
    NutSlotPreviewResponse,
    generate_nut_slot_preview,
)

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
