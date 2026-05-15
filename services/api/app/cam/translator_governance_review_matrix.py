"""
Translator Governance Review Matrix

CAM Dev Order 7J: Governance review readiness consolidation layer.

This module transforms governance dossier evidence into a deterministic
human-review readiness matrix.

7J invariants:
  - execution_authorized = false (always)
  - machine_output_allowed = false (always)

Guardrail:
  7J determines review readiness only. It does not create approval
  authority, execution authority, or mutation authority.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
import hashlib
import json
import uuid

from pydantic import BaseModel, Field, field_validator, model_validator


# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

# Canonical required escalation layers (from 7I)
CANONICAL_ESCALATION_LAYERS: List[str] = [
    "governance_review",
    "translator_execution_architecture_review",
    "human_approval",
    "security_review",
    "artifact_generation_policy_review",
]

# Scoring weights
SCORING_WEIGHTS: Dict[str, int] = {
    "dossier_integrity": 20,
    "provenance_integrity": 20,
    "quarantine_integrity": 20,
    "authorization_integrity": 15,
    "readiness_integrity": 15,
    "governance_completeness": 10,
}

# Gate thresholds
GATE_THRESHOLDS: Dict[str, int] = {
    "green": 80,   # >= 80
    "yellow": 50,  # >= 50 and < 80
    "red": 0,      # < 50
}

# Blocker conditions (cause hard RED regardless of score)
BLOCKER_CONDITIONS: List[str] = [
    "dossier_integrity_failure",
    "provenance_integrity_failure",
    "quarantine_invariant_failure",
    "authorization_invariant_failure",
    "readiness_invariant_failure",
    "missing_required_escalation_layer",
    "execution_authorized_true",
    "machine_output_allowed_true",
    "immutable_false",
]


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------

class ReviewMatrixEvaluationError(Exception):
    """Raised when review matrix evaluation fails."""
    pass


# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------

class TranslatorGovernanceReviewMatrix(BaseModel):
    """
    Governance review readiness matrix.

    Aggregates governance evidence from a dossier into a deterministic
    review readiness evaluation.

    7J invariants (model-enforced):
      - execution_authorized = false (always)
      - machine_output_allowed = false (always)
    """

    review_matrix_id: str = Field(..., description="Unique review matrix ID")
    dossier_id: str = Field(..., description="Source dossier ID")
    translator_id: str = Field(..., description="Translator identifier")

    # Gate and scoring
    review_gate: Literal["green", "yellow", "red"] = Field(
        ...,
        description="Review readiness gate"
    )
    review_readiness_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Deterministic review readiness score (0-100)"
    )

    # Integrity checks
    dossier_integrity_valid: bool = Field(
        ...,
        description="Dossier evidence hash valid"
    )
    provenance_integrity_valid: bool = Field(
        ...,
        description="Provenance lineage intact"
    )
    quarantine_integrity_valid: bool = Field(
        ...,
        description="Quarantine invariants satisfied"
    )
    authorization_integrity_valid: bool = Field(
        ...,
        description="Authorization evaluation valid"
    )
    readiness_integrity_valid: bool = Field(
        ...,
        description="Readiness evaluation valid"
    )

    # Governance completeness
    governance_constraints_satisfied: bool = Field(
        ...,
        description="All governance constraints present"
    )
    escalation_layers_complete: bool = Field(
        ...,
        description="All required escalation layers present"
    )

    # Deficiency counts
    blocker_count: int = Field(
        ...,
        ge=0,
        description="Number of blocking deficiencies"
    )
    warning_count: int = Field(
        ...,
        ge=0,
        description="Number of warning deficiencies"
    )

    # Deficiency details
    blockers: List[str] = Field(
        default_factory=list,
        description="List of blocking deficiencies"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="List of warning deficiencies"
    )

    # Human review requirements
    required_human_reviews: List[str] = Field(
        default_factory=list,
        description="Required human review types"
    )

    # Review state
    review_state: Literal[
        "review_only",
        "non_executable",
        "future_escalation_required",
    ] = Field(
        default="future_escalation_required",
        description="Current review state"
    )

    # Eligibility
    eligible_for_human_governance_review: bool = Field(
        ...,
        description="Whether eligible for human governance review"
    )

    # 7J invariants (always false)
    execution_authorized: bool = Field(
        default=False,
        description="7J invariant: always false"
    )
    machine_output_allowed: bool = Field(
        default=False,
        description="7J invariant: always false"
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    evidence_hash: str = Field(
        default="",
        description="SHA256 hash of review evidence"
    )

    # 7J invariant validators
    @field_validator("execution_authorized", mode="before")
    @classmethod
    def enforce_no_execution(cls, v: Any) -> bool:
        if v is True:
            raise ValueError(
                "7J invariant violation: execution_authorized must be false"
            )
        return False

    @field_validator("machine_output_allowed", mode="before")
    @classmethod
    def enforce_no_machine_output(cls, v: Any) -> bool:
        if v is True:
            raise ValueError(
                "7J invariant violation: machine_output_allowed must be false"
            )
        return False

    @model_validator(mode="after")
    def validate_invariants(self) -> "TranslatorGovernanceReviewMatrix":
        """Validate all 7J invariants after model construction."""
        if self.execution_authorized:
            raise ValueError(
                "7J invariant violation: execution_authorized must be false"
            )
        if self.machine_output_allowed:
            raise ValueError(
                "7J invariant violation: machine_output_allowed must be false"
            )
        return self


class GovernanceReviewMatrixSummary(BaseModel):
    """
    Summary of a governance review matrix for integration.

    Minimal representation for cross-module references.
    """

    review_matrix_id: str
    dossier_id: str
    translator_id: str
    review_gate: Literal["green", "yellow", "red"]
    review_readiness_score: int
    blocker_count: int
    warning_count: int
    eligible_for_human_governance_review: bool
    created_at: datetime

    # 7J invariants
    execution_authorized: bool = False
    machine_output_allowed: bool = False

    @field_validator("execution_authorized", mode="before")
    @classmethod
    def enforce_no_execution(cls, v: Any) -> bool:
        return False

    @field_validator("machine_output_allowed", mode="before")
    @classmethod
    def enforce_no_machine_output(cls, v: Any) -> bool:
        return False


# -----------------------------------------------------------------------------
# In-Memory Index
# -----------------------------------------------------------------------------

REVIEW_MATRIX_INDEX: Dict[str, TranslatorGovernanceReviewMatrix] = {}


def register_review_matrix(
    matrix: TranslatorGovernanceReviewMatrix,
) -> None:
    """Register a review matrix in the index."""
    REVIEW_MATRIX_INDEX[matrix.review_matrix_id] = matrix


def get_review_matrix(
    review_matrix_id: str,
) -> Optional[TranslatorGovernanceReviewMatrix]:
    """Get a review matrix by ID."""
    return REVIEW_MATRIX_INDEX.get(review_matrix_id)


def list_review_matrices() -> List[TranslatorGovernanceReviewMatrix]:
    """List all review matrices."""
    return list(REVIEW_MATRIX_INDEX.values())


def list_review_matrices_for_translator(
    translator_id: str,
) -> List[TranslatorGovernanceReviewMatrix]:
    """List review matrices for a specific translator."""
    return [
        m for m in REVIEW_MATRIX_INDEX.values()
        if m.translator_id == translator_id
    ]


def get_latest_review_matrix_for_translator(
    translator_id: str,
) -> Optional[TranslatorGovernanceReviewMatrix]:
    """Get the most recent review matrix for a translator."""
    matrices = list_review_matrices_for_translator(translator_id)
    if not matrices:
        return None
    return max(matrices, key=lambda m: m.created_at)


def clear_review_matrix_index() -> None:
    """Clear all review matrices from the index (for testing)."""
    REVIEW_MATRIX_INDEX.clear()


# -----------------------------------------------------------------------------
# Scoring Engine
# -----------------------------------------------------------------------------

def _compute_integrity_score(
    dossier_valid: bool,
    provenance_valid: bool,
    quarantine_valid: bool,
    authorization_valid: bool,
    readiness_valid: bool,
    governance_complete: bool,
) -> int:
    """
    Compute deterministic review readiness score.

    Weights:
      - Dossier integrity: 20
      - Provenance integrity: 20
      - Quarantine integrity: 20
      - Authorization integrity: 15
      - Readiness integrity: 15
      - Governance completeness: 10

    Total: 100 points
    """
    score = 0

    if dossier_valid:
        score += SCORING_WEIGHTS["dossier_integrity"]
    if provenance_valid:
        score += SCORING_WEIGHTS["provenance_integrity"]
    if quarantine_valid:
        score += SCORING_WEIGHTS["quarantine_integrity"]
    if authorization_valid:
        score += SCORING_WEIGHTS["authorization_integrity"]
    if readiness_valid:
        score += SCORING_WEIGHTS["readiness_integrity"]
    if governance_complete:
        score += SCORING_WEIGHTS["governance_completeness"]

    return score


def _determine_gate(score: int, has_hard_red: bool) -> Literal["green", "yellow", "red"]:
    """
    Determine review gate from score and hard RED conditions.

    Thresholds:
      - >= 80: GREEN
      - >= 50 and < 80: YELLOW
      - < 50: RED

    Hard RED overrides score-based gate.
    """
    if has_hard_red:
        return "red"

    if score >= GATE_THRESHOLDS["green"]:
        return "green"
    elif score >= GATE_THRESHOLDS["yellow"]:
        return "yellow"
    else:
        return "red"


# -----------------------------------------------------------------------------
# Deficiency Classifier
# -----------------------------------------------------------------------------

def _classify_deficiencies(
    dossier_valid: bool,
    provenance_valid: bool,
    quarantine_valid: bool,
    authorization_valid: bool,
    readiness_valid: bool,
    escalation_complete: bool,
    missing_layers: List[str],
    dossier_execution_authorized: bool,
    dossier_machine_output: bool,
    dossier_immutable: bool,
    readiness_gate: Optional[str],
    authorization_eligible: Optional[bool],
) -> tuple[List[str], List[str]]:
    """
    Classify deficiencies into blockers and warnings.

    Returns:
        (blockers, warnings)
    """
    blockers: List[str] = []
    warnings: List[str] = []

    # Integrity blockers
    if not dossier_valid:
        blockers.append("dossier_integrity_failure")
    if not provenance_valid:
        blockers.append("provenance_integrity_failure")
    if not quarantine_valid:
        blockers.append("quarantine_invariant_failure")
    if not authorization_valid:
        blockers.append("authorization_invariant_failure")
    if not readiness_valid:
        blockers.append("readiness_invariant_failure")

    # Escalation layer blockers
    if not escalation_complete:
        for layer in missing_layers:
            blockers.append(f"missing_required_escalation_layer:{layer}")

    # Invariant violation blockers
    if dossier_execution_authorized:
        blockers.append("execution_authorized_true")
    if dossier_machine_output:
        blockers.append("machine_output_allowed_true")
    if not dossier_immutable:
        blockers.append("immutable_false")

    # Warnings (non-blocking issues)
    if readiness_gate and readiness_gate == "yellow":
        warnings.append("readiness_gate_yellow")
    if readiness_gate and readiness_gate == "red":
        warnings.append("readiness_gate_red")
    if authorization_eligible is False:
        warnings.append("authorization_not_eligible")

    return blockers, warnings


# -----------------------------------------------------------------------------
# Evidence Hash
# -----------------------------------------------------------------------------

def _compute_evidence_hash(
    dossier_id: str,
    translator_id: str,
    score: int,
    gate: str,
    blockers: List[str],
    warnings: List[str],
) -> str:
    """
    Compute deterministic SHA256 hash of review evidence.

    Excludes timestamps and UUIDs to ensure determinism.
    """
    evidence = {
        "dossier_id": dossier_id,
        "translator_id": translator_id,
        "score": score,
        "gate": gate,
        "blockers": sorted(blockers),
        "warnings": sorted(warnings),
    }
    evidence_json = json.dumps(evidence, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(evidence_json.encode()).hexdigest()


# -----------------------------------------------------------------------------
# Review Matrix Evaluator
# -----------------------------------------------------------------------------

def evaluate_governance_review_readiness(
    dossier: Any,
    persist_to_rmos: bool = False,
) -> TranslatorGovernanceReviewMatrix:
    """
    Evaluate governance review readiness from a dossier.

    Creates a deterministic review matrix from the dossier evidence.

    Args:
        dossier: TranslatorGovernanceDossier instance
        persist_to_rmos: Whether to persist to RMOS (default False)

    Returns:
        TranslatorGovernanceReviewMatrix

    Raises:
        ReviewMatrixEvaluationError: If evaluation fails

    Guardrail:
      7J determines review readiness only. It does not create approval
      authority, execution authority, or mutation authority.
    """
    if dossier is None:
        raise ReviewMatrixEvaluationError("Dossier is required")

    # Extract dossier metadata
    dossier_id = getattr(dossier, "dossier_id", None)
    translator_id = getattr(dossier, "translator_id", None)

    if not dossier_id or not translator_id:
        raise ReviewMatrixEvaluationError(
            "Dossier must have dossier_id and translator_id"
        )

    # Validate dossier integrity (deterministic hash present and non-empty)
    dossier_hash = getattr(dossier, "deterministic_dossier_hash", None)
    dossier_valid = bool(dossier_hash)

    # Validate provenance integrity (hash present)
    provenance_hash = getattr(dossier, "provenance_hash", None)
    provenance_valid = bool(provenance_hash)

    # Validate quarantine integrity (hash present)
    freeze_manifest_hash = getattr(dossier, "freeze_manifest_hash", None)
    quarantine_valid = bool(freeze_manifest_hash)

    # Validate authorization integrity (hash present)
    authorization_hash = getattr(dossier, "authorization_hash", None)
    authorization_valid = bool(authorization_hash)

    # Validate readiness integrity (hash present)
    readiness_hash = getattr(dossier, "readiness_hash", None)
    readiness_valid = bool(readiness_hash)

    # Check escalation layers completeness
    dossier_layers = getattr(dossier, "required_escalation_layers", []) or []
    missing_layers = [
        layer for layer in CANONICAL_ESCALATION_LAYERS
        if layer not in dossier_layers
    ]
    escalation_complete = len(missing_layers) == 0

    # Check governance constraints
    dossier_constraints = getattr(dossier, "governance_constraints", []) or []
    governance_complete = len(dossier_constraints) > 0

    # Check dossier invariants
    dossier_execution_authorized = getattr(
        dossier, "execution_authorized", False
    )
    dossier_machine_output = getattr(
        dossier, "machine_output_allowed", False
    )
    dossier_immutable = getattr(dossier, "immutable", True)

    # Extract gate values for warnings (direct fields on dossier)
    readiness_gate = getattr(dossier, "readiness_gate", None)
    authorization_gate = getattr(dossier, "authorization_gate", None)
    # Authorization eligible is inferred from authorization_gate
    authorization_eligible = authorization_gate == "green" if authorization_gate else None

    # Compute score
    score = _compute_integrity_score(
        dossier_valid=dossier_valid,
        provenance_valid=provenance_valid,
        quarantine_valid=quarantine_valid,
        authorization_valid=authorization_valid,
        readiness_valid=readiness_valid,
        governance_complete=governance_complete and escalation_complete,
    )

    # Classify deficiencies
    blockers, warnings = _classify_deficiencies(
        dossier_valid=dossier_valid,
        provenance_valid=provenance_valid,
        quarantine_valid=quarantine_valid,
        authorization_valid=authorization_valid,
        readiness_valid=readiness_valid,
        escalation_complete=escalation_complete,
        missing_layers=missing_layers,
        dossier_execution_authorized=dossier_execution_authorized,
        dossier_machine_output=dossier_machine_output,
        dossier_immutable=dossier_immutable,
        readiness_gate=readiness_gate,
        authorization_eligible=authorization_eligible,
    )

    # Check for hard RED conditions
    has_hard_red = len(blockers) > 0

    # Determine gate
    gate = _determine_gate(score, has_hard_red)

    # Determine eligibility
    # Eligible only if: gate != "red" AND blocker_count == 0
    # AND execution_authorized == false AND machine_output_allowed == false
    eligible = (
        gate != "red"
        and len(blockers) == 0
        # 7J invariants are always false, so these are always satisfied
    )

    # Derive required human reviews from dossier escalation layers
    required_human_reviews = list(dossier_layers) if dossier_layers else []

    # Determine review state
    review_state: Literal["review_only", "non_executable", "future_escalation_required"]
    if gate == "red":
        review_state = "future_escalation_required"
    elif gate == "yellow":
        review_state = "non_executable"
    else:
        review_state = "review_only"

    # Generate review matrix ID
    review_matrix_id = f"review-{uuid.uuid4().hex[:12]}"

    # Compute evidence hash
    evidence_hash = _compute_evidence_hash(
        dossier_id=dossier_id,
        translator_id=translator_id,
        score=score,
        gate=gate,
        blockers=blockers,
        warnings=warnings,
    )

    # Create review matrix
    matrix = TranslatorGovernanceReviewMatrix(
        review_matrix_id=review_matrix_id,
        dossier_id=dossier_id,
        translator_id=translator_id,
        review_gate=gate,
        review_readiness_score=score,
        dossier_integrity_valid=dossier_valid,
        provenance_integrity_valid=provenance_valid,
        quarantine_integrity_valid=quarantine_valid,
        authorization_integrity_valid=authorization_valid,
        readiness_integrity_valid=readiness_valid,
        governance_constraints_satisfied=governance_complete,
        escalation_layers_complete=escalation_complete,
        blocker_count=len(blockers),
        warning_count=len(warnings),
        blockers=blockers,
        warnings=warnings,
        required_human_reviews=required_human_reviews,
        review_state=review_state,
        eligible_for_human_governance_review=eligible,
        execution_authorized=False,
        machine_output_allowed=False,
        evidence_hash=evidence_hash,
    )

    # Register in index
    register_review_matrix(matrix)

    # Optional RMOS persistence
    if persist_to_rmos:
        _persist_to_rmos(matrix)

    return matrix


def evaluate_governance_review_readiness_by_dossier_id(
    dossier_id: str,
    persist_to_rmos: bool = False,
) -> TranslatorGovernanceReviewMatrix:
    """
    Evaluate governance review readiness by dossier ID.

    Looks up the dossier from the DOSSIER_INDEX and evaluates.

    Args:
        dossier_id: Dossier identifier
        persist_to_rmos: Whether to persist to RMOS (default False)

    Returns:
        TranslatorGovernanceReviewMatrix

    Raises:
        ReviewMatrixEvaluationError: If dossier not found or evaluation fails
    """
    # Import here to avoid circular dependency
    from app.cam.translator_governance_dossier import get_governance_dossier

    dossier = get_governance_dossier(dossier_id)
    if dossier is None:
        raise ReviewMatrixEvaluationError(
            f"Dossier not found: {dossier_id}"
        )

    return evaluate_governance_review_readiness(
        dossier=dossier,
        persist_to_rmos=persist_to_rmos,
    )


# -----------------------------------------------------------------------------
# RMOS Persistence (Optional)
# -----------------------------------------------------------------------------

def _persist_to_rmos(matrix: TranslatorGovernanceReviewMatrix) -> Optional[str]:
    """
    Persist review matrix to RMOS.

    Artifact kind: translator_governance_review_matrix_json

    Returns:
        RMOS artifact ID if successful, None otherwise
    """
    try:
        from app.rmos.runs_v2.run_artifact_manager import persist_run_artifact

        artifact_data = matrix.model_dump(mode="json")

        artifact_id = persist_run_artifact(
            artifact_kind="translator_governance_review_matrix_json",
            artifact_data=artifact_data,
            metadata={
                "review_matrix_id": matrix.review_matrix_id,
                "dossier_id": matrix.dossier_id,
                "translator_id": matrix.translator_id,
                "review_gate": matrix.review_gate,
                "review_readiness_score": matrix.review_readiness_score,
                "eligible_for_human_governance_review": matrix.eligible_for_human_governance_review,
            },
        )
        return artifact_id
    except ImportError:
        # RMOS not available
        return None
    except Exception:
        # Persistence failed, but don't block evaluation
        return None


# -----------------------------------------------------------------------------
# Summary Helper
# -----------------------------------------------------------------------------

def to_summary(
    matrix: TranslatorGovernanceReviewMatrix,
) -> GovernanceReviewMatrixSummary:
    """Convert a review matrix to its summary representation."""
    return GovernanceReviewMatrixSummary(
        review_matrix_id=matrix.review_matrix_id,
        dossier_id=matrix.dossier_id,
        translator_id=matrix.translator_id,
        review_gate=matrix.review_gate,
        review_readiness_score=matrix.review_readiness_score,
        blocker_count=matrix.blocker_count,
        warning_count=matrix.warning_count,
        eligible_for_human_governance_review=matrix.eligible_for_human_governance_review,
        created_at=matrix.created_at,
        execution_authorized=False,
        machine_output_allowed=False,
    )
