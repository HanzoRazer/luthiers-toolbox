"""
DXF Translator Boundary Router

CAM Dev Order 6D: Translator alignment validation endpoint.

This router provides DXF translator compatibility checking without
generating any DXF output.

Core rule:
  - DXF is a translator TARGET, not the manufacturing representation
  - Returns compatibility REPORT only
  - No DXF generation
  - No file output
  - No serialization
"""

from fastapi import APIRouter

from app.cam.dxf_translator_boundary import (
    DXFTranslatorCompatibilityReport,
    DXFTranslatorValidationRequest,
)
from app.cam.export_object_to_dxf_adapter import evaluate_dxf_translator_compatibility

router = APIRouter(prefix="/dxf/translator", tags=["cam-dxf-translator"])


@router.post(
    "/validate",
    response_model=DXFTranslatorCompatibilityReport,
    summary="Validate export object compatibility with DXF translator",
    description="""
Evaluate whether a governed export object is compatible with a DXF translator profile.

**Status:** Validation only (CAM Dev Order 6D)

**This endpoint returns a REPORT, not DXF output.**

No DXF is generated. No files are produced. No serialization occurs.

**Core principle:**
DXF is a translator target, NOT the manufacturing representation.
The Export Object owns manufacturing intent.
The DXF translator owns serialization adaptation.

**Gate logic:**
- GREEN: All compatibility checks pass, translation ready
- YELLOW: Compatible with warnings (missing optional features)
- RED: Incompatible (unsupported geometry, unit mismatch)

**Checks performed:**
1. Unit compatibility — do export and translator units match?
2. Geometry support — does translator support all detected geometry types?
3. Feature support — does translator support required features?

**Response guarantees:**
- translator_output_generated: always false
- dxf_generated: always false
- metadata.validation_only: always true
- metadata.machine_ready: always false
""",
)
async def validate_dxf_translator(
    request: DXFTranslatorValidationRequest,
) -> DXFTranslatorCompatibilityReport:
    """
    Validate export object compatibility with DXF translator.

    Returns a compatibility report — NOT DXF output.
    """
    return evaluate_dxf_translator_compatibility(
        export_object=request.export_object,
        translator_profile=request.translator_profile,
    )
