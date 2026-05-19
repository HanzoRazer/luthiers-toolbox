"""
Translation Artifact Authorization Router

CAM Dev Order 7E: Authorization validation endpoint for translation artifacts.

Provides validation-only endpoint to evaluate artifact eligibility
for future execution WITHOUT authorizing or performing execution.

7E invariants:
  - No execution
  - No artifact generation
  - No DXF/SVG/G-code output
  - No machine output
  - Human approval always required
  - Execution never authorized
"""

from fastapi import APIRouter

from app.cam.translation_artifact_authorization import (
    TranslationArtifactAuthorizationEvaluation,
    TranslationArtifactAuthorizationRequest,
    evaluate_translation_artifact_authorization,
)


router = APIRouter(
    prefix="/api/cam/translation-artifacts/authorize",
    tags=["CAM Translation Artifact Authorization"],
)


@router.post(
    "/validate",
    response_model=TranslationArtifactAuthorizationEvaluation,
    summary="Validate translation artifact authorization eligibility",
    description="""
Evaluates whether a translation artifact is eligible for future execution.

This is ELIGIBILITY EVALUATION only:
- Does NOT authorize execution
- Does NOT generate artifacts
- Does NOT produce DXF/SVG/G-code
- Does NOT produce machine output

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
)
def validate_translation_artifact_authorization(
    request: TranslationArtifactAuthorizationRequest,
) -> TranslationArtifactAuthorizationEvaluation:
    """
    Validate translation artifact authorization eligibility.

    Validation only. No execution. No output generation.
    """
    return evaluate_translation_artifact_authorization(request.artifact)
