"""
Translator Governance Dossier Router

CAM Dev Order 7I: REST endpoints for governance escalation dossier.

Endpoints:
  POST /api/cam/translators/governance-dossier/build   - Build dossier
  GET  /api/cam/translators/governance-dossiers        - List dossiers
  GET  /api/cam/translators/governance-dossiers/{id}   - Get dossier
  GET  /api/cam/translators/governance-dossiers/by-translator/{id} - By translator

7I invariants:
  - All responses have execution_authorized=false
  - All responses have machine_output_allowed=false
  - All responses have immutable=true
  - No mutation endpoints
  - No approval endpoints

Guardrail:
  7I packages complete governance evidence for review.
  It does NOT create approval authority, execution authority,
  or mutation authority.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.cam.translator_governance_dossier import (
    TranslatorGovernanceDossier,
    GovernanceDossierSummary,
    CANONICAL_GOVERNANCE_CONSTRAINTS,
    build_governance_escalation_dossier,
    get_governance_dossier,
    list_governance_dossiers,
    list_governance_dossiers_for_translator,
    get_latest_dossier_for_translator,
    DossierBuildError,
)


router = APIRouter(tags=["Translator Governance Dossier"])


# -----------------------------------------------------------------------------
# Request Models
# -----------------------------------------------------------------------------

class DossierBuildRequest(BaseModel):
    """Request model for building a governance escalation dossier."""

    translator_id: str = Field(..., description="Translator identifier")

    # Evidence IDs — used to fetch from indexes
    readiness_evaluation_id: Optional[str] = Field(
        default=None,
        description="7G readiness evaluation ID"
    )
    provenance_id: Optional[str] = Field(
        default=None,
        description="7F provenance ID"
    )
    authorization_artifact_id: Optional[str] = Field(
        default=None,
        description="7E authorization artifact ID"
    )
    freeze_manifest_id: Optional[str] = Field(
        default=None,
        description="7H freeze manifest ID"
    )

    # Optional hash overrides
    lifecycle_hashes: Optional[List[str]] = Field(
        default=None,
        description="Optional lifecycle hashes override"
    )
    audit_hashes: Optional[List[str]] = Field(
        default=None,
        description="Optional audit hashes override"
    )
    promotion_evidence_hashes: Optional[List[str]] = Field(
        default=None,
        description="Optional promotion evidence hashes override"
    )


# -----------------------------------------------------------------------------
# Response Models
# -----------------------------------------------------------------------------

class DossierPolicyInfo(BaseModel):
    """Information about dossier governance policy."""

    governance_constraints: List[str] = Field(
        default_factory=lambda: CANONICAL_GOVERNANCE_CONSTRAINTS.copy()
    )
    review_states: List[str] = Field(
        default_factory=lambda: [
            "review_only",
            "non_executable",
            "future_escalation_required",
        ]
    )
    default_review_state: str = "future_escalation_required"

    # 7I invariants
    execution_authorized: bool = False
    machine_output_allowed: bool = False
    immutable: bool = True


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.post(
    "/translators/governance-dossier/build",
    response_model=TranslatorGovernanceDossier,
    summary="Build governance escalation dossier",
    description="Build a governance escalation dossier from complete governance evidence.",
)
async def build_dossier(request: DossierBuildRequest) -> TranslatorGovernanceDossier:
    """
    Build governance escalation dossier.

    Requires all four core evidence objects:
    - readiness_evaluation (7G)
    - provenance (7F)
    - authorization_evaluation (7E)
    - freeze_manifest (7H)

    Guardrail:
      7I packages complete governance evidence for review.
      It does NOT create approval authority.
    """
    # Fetch evidence objects from their respective indexes
    readiness_evaluation = None
    provenance = None
    authorization_evaluation = None
    freeze_manifest = None

    # Fetch readiness evaluation from 7G
    if request.readiness_evaluation_id:
        try:
            from app.cam.translator_readiness_matrix import get_readiness_evaluation
            readiness_evaluation = get_readiness_evaluation(
                request.translator_id,
                request.readiness_evaluation_id,
            )
        except ImportError:
            pass
    else:
        # Try to get latest for translator
        try:
            from app.cam.translator_readiness_matrix import (
                evaluate_translator_readiness,
            )
            readiness_evaluation = evaluate_translator_readiness(request.translator_id)
        except ImportError:
            pass

    # Fetch provenance from 7F
    if request.provenance_id:
        try:
            from app.cam.translation_artifact_provenance import get_provenance
            provenance = get_provenance(request.provenance_id)
        except ImportError:
            pass
    else:
        # Try to get latest for translator via artifact
        try:
            from app.cam.translation_artifact_provenance import get_provenance_by_artifact
            # We need an artifact ID, which we don't have directly
            # For now, provenance must be explicitly provided
            pass
        except ImportError:
            pass

    # Fetch authorization evaluation — need to evaluate
    try:
        from app.cam.translation_artifact import TranslationArtifact
        from app.cam.translation_artifact_authorization import (
            evaluate_translation_artifact_authorization,
        )
        from app.cam.translator_capability_registry import get_translator_capability

        # Create a minimal artifact for authorization evaluation
        capability = get_translator_capability(request.translator_id)
        if capability:
            artifact = TranslationArtifact(
                translator_id=request.translator_id,
                translator_category=capability.translator_category,
                output_class=capability.output_class,
                artifact_state="validation_only",
                source_export_object_id="dossier-build",
                source_export_object_hash="dossier-build-hash",
                capability_snapshot=capability.model_dump(mode="json"),
                policy_snapshot={},
                execution_supported=False,
                executable_payload_present=False,
                machine_output_present=False,
            )
            authorization_evaluation = evaluate_translation_artifact_authorization(artifact)

            # Also create provenance if not provided
            if provenance is None:
                try:
                    from app.cam.translation_artifact_provenance import (
                        build_translation_artifact_provenance,
                    )
                    provenance = build_translation_artifact_provenance(artifact)
                except ImportError:
                    pass
    except ImportError:
        pass

    # Fetch or create freeze manifest from 7H
    if request.freeze_manifest_id:
        try:
            from app.cam.translator_execution_quarantine import get_freeze_manifest
            freeze_manifest = get_freeze_manifest(request.freeze_manifest_id)
        except ImportError:
            pass
    else:
        # Try to get latest quarantine and its manifest
        try:
            from app.cam.translator_execution_quarantine import (
                evaluate_execution_quarantine,
                get_freeze_manifest,
            )
            quarantine = evaluate_execution_quarantine(
                request.translator_id,
                readiness_evaluation=readiness_evaluation,
                provenance=provenance,
            )
            freeze_manifest = get_freeze_manifest(quarantine.freeze_manifest_id)
        except ImportError:
            pass

    # Validate we have all required evidence
    missing = []
    if readiness_evaluation is None:
        missing.append("readiness_evaluation")
    if provenance is None:
        missing.append("provenance")
    if authorization_evaluation is None:
        missing.append("authorization_evaluation")
    if freeze_manifest is None:
        missing.append("freeze_manifest")

    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required governance evidence: {', '.join(missing)}",
        )

    # Build dossier
    try:
        dossier = build_governance_escalation_dossier(
            readiness_evaluation=readiness_evaluation,
            provenance=provenance,
            authorization_evaluation=authorization_evaluation,
            freeze_manifest=freeze_manifest,
            lifecycle_hashes=request.lifecycle_hashes,
            audit_hashes=request.audit_hashes,
            promotion_evidence_hashes=request.promotion_evidence_hashes,
        )
        return dossier
    except DossierBuildError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/translators/governance-dossiers",
    response_model=List[GovernanceDossierSummary],
    summary="List governance dossiers",
    description="List all governance escalation dossiers.",
)
async def list_dossiers(
    translator_id: Optional[str] = None,
) -> List[GovernanceDossierSummary]:
    """List governance dossiers, optionally filtered by translator."""
    if translator_id:
        dossiers = list_governance_dossiers_for_translator(translator_id)
    else:
        dossiers = list_governance_dossiers()
    return [d.to_summary() for d in dossiers]


@router.get(
    "/translators/governance-dossiers/policy",
    response_model=DossierPolicyInfo,
    summary="Get dossier policy",
    description="Get the current dossier governance policy configuration.",
)
async def get_dossier_policy() -> DossierPolicyInfo:
    """Get dossier policy information."""
    return DossierPolicyInfo()


@router.get(
    "/translators/governance-dossiers/by-translator/{translator_id}",
    response_model=List[TranslatorGovernanceDossier],
    summary="Get dossiers by translator",
    description="Get all governance dossiers for a specific translator.",
)
async def get_dossiers_by_translator(
    translator_id: str,
) -> List[TranslatorGovernanceDossier]:
    """Get all governance dossiers for a translator."""
    return list_governance_dossiers_for_translator(translator_id)


@router.get(
    "/translators/governance-dossiers/{dossier_id}",
    response_model=TranslatorGovernanceDossier,
    summary="Get governance dossier",
    description="Get a specific governance escalation dossier by ID.",
)
async def get_dossier(dossier_id: str) -> TranslatorGovernanceDossier:
    """Get governance dossier by ID."""
    dossier = get_governance_dossier(dossier_id)

    if dossier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Governance dossier not found: {dossier_id}",
        )

    return dossier
