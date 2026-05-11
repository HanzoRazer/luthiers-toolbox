"""
Postprocessor Boundary Router

CAM Dev Order 6C: Compatibility validation endpoint.

This router provides postprocessor compatibility checking without
generating any machine output.

Core rule:
  - Returns compatibility REPORT only
  - No G-code generation
  - No DXF generation
  - No file output
  - No machine-executable instructions
"""

from fastapi import APIRouter

from app.cam.postprocessor_boundary import (
    PostprocessorCompatibilityReport,
    PostprocessorCompatibilityRequest,
    evaluate_postprocessor_compatibility,
)

router = APIRouter(prefix="/postprocessor", tags=["cam-postprocessor"])


@router.post(
    "/compatibility",
    response_model=PostprocessorCompatibilityReport,
    summary="Check export object compatibility with machine profile",
    description="""
Evaluate whether a governed export object is compatible with a machine profile.

**Status:** Validation only (CAM Dev Order 6C)

**This endpoint returns a REPORT, not machine output.**

No G-code is generated. No DXF is generated. No files are produced.

**Gate logic:**
- GREEN: All compatibility checks pass
- YELLOW: Compatible with warnings (tight margins, incomplete metadata)
- RED: Incompatible (unsupported operation, unit mismatch, bounds violation)

**Checks performed:**
1. Operation support — is the operation in machine_profile.supported_operations?
2. Unit compatibility — do export and machine units match?
3. Axis requirement — does machine have at least 3 axes?
4. Bounds check — do toolpath bounds fit within machine envelope?
5. Tooling block — is tooling block present and complete?
6. Arc support — if export uses arcs, does machine support them?

**Response guarantees:**
- machine_output_generated: always false
- postprocessor_output_generated: always false
- metadata.validation_only: always true
- metadata.machine_ready: always false
""",
)
async def check_compatibility(
    request: PostprocessorCompatibilityRequest,
) -> PostprocessorCompatibilityReport:
    """
    Check export object compatibility with machine profile.

    Returns a compatibility report — NOT machine output.
    """
    return evaluate_postprocessor_compatibility(
        export_object=request.export_object,
        machine_profile=request.machine_profile,
    )
