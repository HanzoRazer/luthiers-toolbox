"""
Translation Artifact Authorization Router

CAM Dev Order 7E: Authorization validation endpoint for translation artifacts.
CAM Dev Order 7Q: Runtime governance checkpoint integration.

Provides validation-only endpoint to evaluate artifact eligibility
for future execution WITHOUT authorizing or performing execution.

7E invariants:
  - No execution
  - No artifact generation
  - No DXF/SVG/G-code output
  - No machine output
  - Human approval always required
  - Execution never authorized

7Q integration:
  - Runtime governance checkpoint before authorization validation
  - RED checkpoint blocks with HTTP 409
  - YELLOW/GREEN checkpoint proceeds with summary in response
"""

from typing import Optional

from fastapi import APIRouter
from pydantic import Field

from app.cam.translation_artifact_authorization import (
    TranslationArtifactAuthorizationEvaluation,
    TranslationArtifactAuthorizationRequest,
    evaluate_translation_artifact_authorization,
)
from app.cam.runtime_checkpoint_response import (
    RuntimeCheckpointSummary,
    build_translator_dispatch_pathway,
    evaluate_runtime_pathway_checkpoint,
    raise_on_red_checkpoint,
    to_checkpoint_summary,
)


router = APIRouter(
    prefix="/api/cam/translation-artifacts/authorize",
    tags=["CAM Translation Artifact Authorization"],
)


# Route path constant for checkpoint pathway
AUTHORIZATION_VALIDATE_ROUTE = "/api/cam/translation-artifacts/authorize/validate"


class TranslationArtifactAuthorizationEvaluationWithCheckpoint(
    TranslationArtifactAuthorizationEvaluation
):
    """
    Authorization evaluation with optional runtime checkpoint summary.

    Extends TranslationArtifactAuthorizationEvaluation with 7Q governance checkpoint.
    """

    runtime_checkpoint_summary: Optional[RuntimeCheckpointSummary] = Field(
        default=None,
        description="7Q runtime governance checkpoint summary (if evaluated)"
    )


@router.post(
    "/validate",
    response_model=TranslationArtifactAuthorizationEvaluationWithCheckpoint,
    summary="Validate translation artifact authorization eligibility",
    description="""
Evaluates whether a translation artifact is eligible for future execution.

**7Q Integration:** Runtime governance checkpoint before validation

This is ELIGIBILITY EVALUATION only:
- Does NOT authorize execution
- Does NOT generate artifacts
- Does NOT produce DXF/SVG/G-code
- Does NOT produce machine output

**7Q Governance Checkpoint:**
- RED checkpoint → HTTP 409 Conflict (blocked)
- YELLOW checkpoint → proceeds with warning summary
- GREEN checkpoint → proceeds normally

Returns:
- gate: green/yellow/red
- eligible_for_future_execution: true if gate != red
- authorized_for_execution: always false
- human_approval_required: always true
- blocking_issues: RED conditions
- warnings: YELLOW conditions

Checks performed:
1. Artifact 7D invariants (no execution_supported, no payload, no machine output)
2. Translator exists in registry
3. Category/output class match current registry
4. Capability snapshot comparison (detect drift)
5. Artifact state validity

Gate rules:
- RED: blocking issues present
- YELLOW: warnings present but no blocking issues
- GREEN: no issues
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
def validate_translation_artifact_authorization(
    request: TranslationArtifactAuthorizationRequest,
) -> TranslationArtifactAuthorizationEvaluationWithCheckpoint:
    """
    Validate translation artifact authorization eligibility.

    7Q: Evaluates runtime governance checkpoint before proceeding.
    RED checkpoint blocks with HTTP 409.

    Validation only. No execution. No output generation.
    """
    # --- 7Q: Runtime governance checkpoint ---
    # Use translator_id from artifact for pathway
    translator_id = request.artifact.translator_id
    pathway = build_translator_dispatch_pathway(translator_id)

    checkpoint_eval = evaluate_runtime_pathway_checkpoint(
        runtime_pathway=pathway,
        translator_id=translator_id,
        export_route=AUTHORIZATION_VALIDATE_ROUTE,
    )

    # RED blocks with 409
    raise_on_red_checkpoint(checkpoint_eval, AUTHORIZATION_VALIDATE_ROUTE)

    # --- Proceed with authorization validation ---
    base_evaluation = evaluate_translation_artifact_authorization(request.artifact)

    # --- Build response with checkpoint summary ---
    checkpoint_summary = to_checkpoint_summary(checkpoint_eval)

    return TranslationArtifactAuthorizationEvaluationWithCheckpoint(
        **base_evaluation.model_dump(),
        runtime_checkpoint_summary=checkpoint_summary,
    )
