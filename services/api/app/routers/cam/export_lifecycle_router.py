"""
Governed Export Lifecycle Router

CAM Dev Order 6E: End-to-end lifecycle validation endpoint.

This router orchestrates validation across all governed export layers:
  Preview → Export Object → Postprocessor → Translator

Core rule:
  - ORCHESTRATION, not EXECUTION
  - No output generation
  - No file persistence
  - No machine execution
"""

from fastapi import APIRouter

from app.cam.export_lifecycle_orchestrator import (
    GovernedExportLifecycleRequest,
    GovernedExportLifecycleReport,
    run_governed_export_lifecycle,
)

router = APIRouter(prefix="/export/lifecycle", tags=["cam-export-lifecycle"])


@router.post(
    "/validate",
    response_model=GovernedExportLifecycleReport,
    summary="Validate complete governed export lifecycle",
    description="""
Run end-to-end validation across all governed export layers.

**Status:** Orchestration only (CAM Dev Order 6E)

**This endpoint validates without generating output.**

No DXF files are created. No G-code is generated.
No machine output is produced. No RMOS persistence.

**Pipeline stages:**
1. Preview generation — compute geometry and toolpaths
2. Export object creation — package manufacturing intent
3. Machine compatibility — validate postprocessor support
4. Translator compatibility — validate DXF translator support
5. Lifecycle gate aggregation — propagate RED > YELLOW > GREEN

**Gate logic:**
- GREEN: All stages pass, ready for export
- YELLOW: Compatible with warnings
- RED: Blocking issues, cannot proceed

**Response guarantees:**
- machine_output_generated: always false
- translator_output_generated: always false
- machine_ready: always false
- metadata.validation_only: always true
""",
)
async def validate_export_lifecycle(
    request: GovernedExportLifecycleRequest,
) -> GovernedExportLifecycleReport:
    """
    Validate the complete governed export lifecycle.

    Returns a lifecycle report — NOT machine or translator output.
    """
    return run_governed_export_lifecycle(request)
