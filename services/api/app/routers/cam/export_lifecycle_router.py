"""
Governed Export Lifecycle Router

CAM Dev Order 6E: End-to-end lifecycle validation endpoint.
CAM Dev Order 7Q: Runtime governance checkpoint integration.

This router orchestrates validation across all governed export layers:
  Preview → Export Object → Postprocessor → Translator

Core rule:
  - ORCHESTRATION, not EXECUTION
  - No output generation
  - No file persistence
  - No machine execution

7Q integration:
  - Runtime governance checkpoint before lifecycle validation
  - RED checkpoint blocks with HTTP 409
  - YELLOW/GREEN checkpoint proceeds with summary in response
"""

from typing import Optional

from fastapi import APIRouter
from pydantic import Field

from app.cam.export_lifecycle_orchestrator import (
    GovernedExportLifecycleRequest,
    GovernedExportLifecycleReport,
    run_governed_export_lifecycle,
)
from app.cam.runtime_checkpoint_response import (
    RuntimeCheckpointSummary,
    build_export_route_pathway,
    evaluate_runtime_pathway_checkpoint,
    raise_on_red_checkpoint,
    to_checkpoint_summary,
)

router = APIRouter(prefix="/export/lifecycle", tags=["cam-export-lifecycle"])


# Route path constant for checkpoint pathway
LIFECYCLE_VALIDATE_ROUTE = "/api/cam/export/lifecycle/validate"


class GovernedExportLifecycleReportWithCheckpoint(GovernedExportLifecycleReport):
    """
    Export lifecycle report with optional runtime checkpoint summary.

    Extends GovernedExportLifecycleReport with 7Q governance checkpoint.
    """

    runtime_checkpoint_summary: Optional[RuntimeCheckpointSummary] = Field(
        default=None,
        description="7Q runtime governance checkpoint summary (if evaluated)"
    )


@router.post(
    "/validate",
    response_model=GovernedExportLifecycleReportWithCheckpoint,
    summary="Validate complete governed export lifecycle",
    description="""
Run end-to-end validation across all governed export layers.

**Status:** Orchestration only (CAM Dev Order 6E)
**7Q Integration:** Runtime governance checkpoint before validation

**This endpoint validates without generating output.**

No DXF files are created. No G-code is generated.
No machine output is produced. No RMOS persistence.

**7Q Governance Checkpoint:**
- RED checkpoint → HTTP 409 Conflict (blocked)
- YELLOW checkpoint → proceeds with warning summary
- GREEN checkpoint → proceeds normally

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
    responses={
        409: {
            "description": "Runtime governance checkpoint blocked",
            "content": {
                "application/json": {
                    "example": {
                        "error": "runtime_governance_checkpoint_blocked",
                        "message": "Runtime governance checkpoint blocked route",
                        "checkpoint_summary": {
                            "checkpoint_gate": "red",
                            "blocking_issues": ["..."],
                        },
                    }
                }
            },
        },
    },
)
async def validate_export_lifecycle(
    request: GovernedExportLifecycleRequest,
) -> GovernedExportLifecycleReportWithCheckpoint:
    """
    Validate the complete governed export lifecycle.

    7Q: Evaluates runtime governance checkpoint before proceeding.
    RED checkpoint blocks with HTTP 409.

    Returns a lifecycle report — NOT machine or translator output.
    """
    # --- 7Q: Runtime governance checkpoint ---
    pathway = build_export_route_pathway(LIFECYCLE_VALIDATE_ROUTE)

    checkpoint_eval = evaluate_runtime_pathway_checkpoint(
        runtime_pathway=pathway,
        export_route=LIFECYCLE_VALIDATE_ROUTE,
    )

    # RED blocks with 409
    raise_on_red_checkpoint(checkpoint_eval, LIFECYCLE_VALIDATE_ROUTE)

    # --- Proceed with lifecycle validation ---
    base_report = run_governed_export_lifecycle(request)

    # --- Build response with checkpoint summary ---
    checkpoint_summary = to_checkpoint_summary(checkpoint_eval)

    return GovernedExportLifecycleReportWithCheckpoint(
        **base_report.model_dump(),
        runtime_checkpoint_summary=checkpoint_summary,
    )
