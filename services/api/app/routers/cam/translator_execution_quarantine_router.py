"""
Translator Execution Quarantine Router

CAM Dev Order 7H: REST endpoints for execution quarantine introspection.

Endpoints:
  GET  /api/cam/translators/quarantine              - List quarantine evaluations
  GET  /api/cam/translators/quarantine/{translator_id} - Get latest quarantine
  POST /api/cam/translators/quarantine/evaluate     - Evaluate quarantine
  GET  /api/cam/translators/freeze-manifests        - List freeze manifests
  GET  /api/cam/translators/freeze-manifests/{manifest_id} - Get freeze manifest

7H invariants:
  - All responses have execution_runtime_present=false
  - All responses have governance_escalation_required=true
  - No DXF, G-code, or machine output
  - No mutation endpoints (read/evaluate only)

Guardrail:
  7H creates freeze/quarantine evidence boundary.
  It does NOT create any execution pathway or approval workflow.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.cam.translator_execution_quarantine import (
    QuarantineState,
    TranslatorExecutionQuarantine,
    TranslatorGovernanceFreezeManifest,
    ExecutionQuarantineSummary,
    REQUIRED_ESCALATION_LAYERS,
    PROHIBITED_ACTIONS,
    evaluate_execution_quarantine,
    get_quarantine,
    get_latest_quarantine,
    list_quarantines,
    get_freeze_manifest,
    list_freeze_manifests,
)


router = APIRouter(tags=["Translator Quarantine"])


# -----------------------------------------------------------------------------
# Request Models
# -----------------------------------------------------------------------------

class QuarantineEvaluationRequest(BaseModel):
    """Request model for quarantine evaluation."""

    translator_id: str = Field(..., description="Translator identifier")
    readiness_evaluation_id: Optional[str] = Field(
        default=None,
        description="Optional readiness evaluation ID for context"
    )
    provenance_id: Optional[str] = Field(
        default=None,
        description="Optional provenance ID for context"
    )


# -----------------------------------------------------------------------------
# Response Models
# -----------------------------------------------------------------------------

class QuarantinePolicyInfo(BaseModel):
    """Information about quarantine policy."""

    required_escalation_layers: List[str] = Field(
        default_factory=lambda: REQUIRED_ESCALATION_LAYERS.copy()
    )
    prohibited_actions: List[str] = Field(
        default_factory=lambda: PROHIBITED_ACTIONS.copy()
    )
    quarantine_states: List[str] = Field(
        default_factory=lambda: [
            "execution_prohibited",
            "governance_freeze",
            "future_escalation_required",
        ]
    )
    default_state: str = "future_escalation_required"

    # 7H invariants
    execution_runtime_present: bool = False
    governance_escalation_required: bool = True


# -----------------------------------------------------------------------------
# Quarantine Endpoints
# -----------------------------------------------------------------------------

@router.get(
    "/translators/quarantine",
    response_model=List[ExecutionQuarantineSummary],
    summary="List quarantine evaluations",
    description="List all translator execution quarantine evaluations.",
)
async def list_quarantine_evaluations(
    translator_id: Optional[str] = None,
) -> List[ExecutionQuarantineSummary]:
    """List quarantine evaluations, optionally filtered by translator."""
    quarantines = list_quarantines()
    if translator_id:
        quarantines = [q for q in quarantines if q.translator_id == translator_id]
    return [q.to_summary() for q in quarantines]


@router.get(
    "/translators/quarantine/policy",
    response_model=QuarantinePolicyInfo,
    summary="Get quarantine policy",
    description="Get the current quarantine policy configuration.",
)
async def get_quarantine_policy() -> QuarantinePolicyInfo:
    """Get quarantine policy information."""
    return QuarantinePolicyInfo()


@router.get(
    "/translators/quarantine/{translator_id}",
    response_model=TranslatorExecutionQuarantine,
    summary="Get translator quarantine",
    description="Get the most recent quarantine evaluation for a translator.",
)
async def get_translator_quarantine(
    translator_id: str,
) -> TranslatorExecutionQuarantine:
    """Get latest quarantine evaluation for a specific translator."""
    quarantine = get_latest_quarantine(translator_id)

    if quarantine is None:
        # Generate a fresh quarantine evaluation
        quarantine = evaluate_execution_quarantine(translator_id=translator_id)

    return quarantine


@router.post(
    "/translators/quarantine/evaluate",
    response_model=TranslatorExecutionQuarantine,
    summary="Evaluate execution quarantine",
    description="Evaluate execution quarantine for a translator.",
)
async def evaluate_quarantine(
    request: QuarantineEvaluationRequest,
) -> TranslatorExecutionQuarantine:
    """
    Evaluate translator execution quarantine.

    This is QUARANTINE EVALUATION, not execution authorization.
    Creates freeze manifest and enforces runtime prohibition.

    Guardrail:
      7H creates freeze/quarantine evidence boundary.
      It does NOT create any execution pathway.
    """
    # Note: In a full implementation, we would fetch the readiness evaluation
    # and provenance from their indexes using the provided IDs. For now,
    # we evaluate without them (they're optional context).
    readiness_evaluation = None
    provenance = None

    if request.readiness_evaluation_id:
        try:
            from app.cam.translator_readiness_matrix import get_readiness_evaluation
            readiness_evaluation = get_readiness_evaluation(
                request.translator_id,
                request.readiness_evaluation_id,
            )
        except ImportError:
            pass

    if request.provenance_id:
        try:
            from app.cam.translation_artifact_provenance import get_provenance
            provenance = get_provenance(request.provenance_id)
        except ImportError:
            pass

    quarantine = evaluate_execution_quarantine(
        translator_id=request.translator_id,
        readiness_evaluation=readiness_evaluation,
        provenance=provenance,
    )

    return quarantine


# -----------------------------------------------------------------------------
# Freeze Manifest Endpoints
# -----------------------------------------------------------------------------

@router.get(
    "/translators/freeze-manifests",
    response_model=List[TranslatorGovernanceFreezeManifest],
    summary="List freeze manifests",
    description="List all governance freeze manifests.",
)
async def list_manifests(
    translator_id: Optional[str] = None,
) -> List[TranslatorGovernanceFreezeManifest]:
    """List freeze manifests, optionally filtered by translator."""
    manifests = list_freeze_manifests()
    if translator_id:
        manifests = [m for m in manifests if m.translator_id == translator_id]
    return manifests


@router.get(
    "/translators/freeze-manifests/{manifest_id}",
    response_model=TranslatorGovernanceFreezeManifest,
    summary="Get freeze manifest",
    description="Get a specific governance freeze manifest by ID.",
)
async def get_manifest(manifest_id: str) -> TranslatorGovernanceFreezeManifest:
    """Get freeze manifest by ID."""
    manifest = get_freeze_manifest(manifest_id)

    if manifest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Freeze manifest not found: {manifest_id}",
        )

    return manifest
