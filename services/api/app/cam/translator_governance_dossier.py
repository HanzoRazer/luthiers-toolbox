"""
Translator Governance Escalation Dossier

CAM Dev Order 7I: Governance review packaging for escalation.

This module creates the final non-executable governance preparation layer
that packages complete governance evidence for future human review.

A Governance Escalation Dossier packages:
  - Readiness evaluation (7G)
  - Provenance lineage (7F)
  - Authorization evaluation (7E)
  - Freeze manifest (7H)
  - Audit hashes
  - Promotion evidence hashes
  - Lifecycle hashes

Into a deterministic review artifact.

7I invariants:
  - execution_authorized: always false
  - machine_output_allowed: always false
  - immutable: always true

Key distinction:
  A Governance Escalation Dossier is a governance review package,
  NOT an execution authorization.

Guardrail:
  7I packages complete governance evidence for review.
  It does NOT create approval authority, execution authority,
  or mutation authority.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


# -----------------------------------------------------------------------------
# Type Definitions
# -----------------------------------------------------------------------------

DossierReviewState = Literal[
    "review_only",               # Baseline: review package only
    "non_executable",            # Stronger: explicitly non-executable
    "future_escalation_required",  # Strongest: escalation required for any execution
]


# -----------------------------------------------------------------------------
# In-Memory Index
# -----------------------------------------------------------------------------

DOSSIER_INDEX: Dict[str, "TranslatorGovernanceDossier"] = {}


# -----------------------------------------------------------------------------
# Governance Dossier Summary (for 7H integration)
# -----------------------------------------------------------------------------

class GovernanceDossierSummary(BaseModel):
    """
    Lightweight dossier summary for 7H quarantine integration.

    Contains only identification and review state — no detailed evidence.
    """

    dossier_id: str = Field(..., description="Dossier identifier")
    translator_id: str = Field(..., description="Translator identifier")
    readiness_gate: str = Field(..., description="Readiness gate from 7G")
    quarantine_state: str = Field(..., description="Quarantine state from 7H")
    deterministic_dossier_hash: str = Field(
        ..., description="Deterministic hash of governance evidence"
    )

    # 7I invariants — always enforced
    immutable: bool = Field(
        default=True,
        description="Always true — dossiers are immutable"
    )
    execution_authorized: bool = Field(
        default=False,
        description="Always false — no execution authorization"
    )


# -----------------------------------------------------------------------------
# Full Governance Dossier Model
# -----------------------------------------------------------------------------

class TranslatorGovernanceDossier(BaseModel):
    """
    Translator governance escalation dossier.

    Packages complete governance evidence for future human review.
    This is a review package, NOT an execution authorization.

    7I invariants (model-enforced):
      - execution_authorized: always false
      - machine_output_allowed: always false
      - immutable: always true
    """

    # --- Identity ---
    dossier_id: str = Field(
        default_factory=lambda: f"dossier-{uuid4().hex[:12]}",
        description="Unique dossier identifier"
    )
    translator_id: str = Field(..., description="Translator identifier")

    # --- Governance Gates ---
    readiness_gate: str = Field(..., description="Readiness gate from 7G")
    quarantine_state: str = Field(..., description="Quarantine state from 7H")
    authorization_gate: str = Field(..., description="Authorization gate from 7E")

    # --- Source Evidence Hashes ---
    provenance_hash: str = Field(
        ..., description="Hash from 7F provenance lineage"
    )
    readiness_hash: str = Field(
        ..., description="Hash from 7G readiness evaluation"
    )
    authorization_hash: str = Field(
        ..., description="Hash from 7E authorization evaluation"
    )
    freeze_manifest_hash: str = Field(
        ..., description="Hash from 7H freeze manifest"
    )

    # --- Governance Evidence Chains ---
    lifecycle_hashes: List[str] = Field(
        default_factory=list,
        description="Hashes from lifecycle reports"
    )
    audit_hashes: List[str] = Field(
        default_factory=list,
        description="Hashes from audit ledger"
    )
    promotion_evidence_hashes: List[str] = Field(
        default_factory=list,
        description="Hashes from promotion evidence"
    )

    # --- Governance Constraints ---
    governance_constraints: List[str] = Field(
        default_factory=list,
        description="Active governance constraints"
    )

    # --- Escalation Requirements ---
    required_escalation_layers: List[str] = Field(
        default_factory=list,
        description="Required escalation layers for execution"
    )

    # --- Review State ---
    review_state: DossierReviewState = Field(
        default="future_escalation_required",
        description="Current review state (default: strongest)"
    )

    # --- Deterministic Hash ---
    deterministic_dossier_hash: str = Field(
        ..., description="Deterministic hash of all governance evidence"
    )

    # --- 7I Invariants ---
    execution_authorized: bool = Field(
        default=False,
        description="Always false — no execution authorization in 7I"
    )
    machine_output_allowed: bool = Field(
        default=False,
        description="Always false — no machine output in 7I"
    )
    immutable: bool = Field(
        default=True,
        description="Always true — dossiers are immutable"
    )

    # --- Timestamps ---
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Dossier creation timestamp"
    )

    # --- Metadata ---
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional dossier metadata"
    )

    # --- Invariant Enforcement ---
    @model_validator(mode="after")
    def enforce_7i_invariants(self) -> "TranslatorGovernanceDossier":
        """
        Enforce 7I invariants:
        - execution_authorized must be False
        - machine_output_allowed must be False
        - immutable must be True
        """
        if self.execution_authorized:
            raise ValueError(
                f"Dossier '{self.dossier_id}': execution_authorized must be False — "
                f"dossiers do not authorize execution"
            )

        if self.machine_output_allowed:
            raise ValueError(
                f"Dossier '{self.dossier_id}': machine_output_allowed must be False — "
                f"dossiers do not allow machine output"
            )

        if not self.immutable:
            raise ValueError(
                f"Dossier '{self.dossier_id}': immutable must be True — "
                f"dossiers are always immutable"
            )

        return self

    def to_summary(self) -> GovernanceDossierSummary:
        """Create lightweight summary for 7H quarantine integration."""
        return GovernanceDossierSummary(
            dossier_id=self.dossier_id,
            translator_id=self.translator_id,
            readiness_gate=self.readiness_gate,
            quarantine_state=self.quarantine_state,
            deterministic_dossier_hash=self.deterministic_dossier_hash,
            immutable=True,
            execution_authorized=False,
        )


# -----------------------------------------------------------------------------
# Dossier Index Operations
# -----------------------------------------------------------------------------

def register_governance_dossier(dossier: TranslatorGovernanceDossier) -> None:
    """Register governance dossier in the in-memory index."""
    DOSSIER_INDEX[dossier.dossier_id] = dossier


def get_governance_dossier(dossier_id: str) -> Optional[TranslatorGovernanceDossier]:
    """Get governance dossier by ID from the index."""
    return DOSSIER_INDEX.get(dossier_id)


def list_governance_dossiers() -> List[TranslatorGovernanceDossier]:
    """List all registered governance dossiers."""
    return list(DOSSIER_INDEX.values())


def list_governance_dossiers_for_translator(
    translator_id: str,
) -> List[TranslatorGovernanceDossier]:
    """List all governance dossiers for a translator."""
    return [
        d for d in DOSSIER_INDEX.values()
        if d.translator_id == translator_id
    ]


def get_latest_dossier_for_translator(
    translator_id: str,
) -> Optional[TranslatorGovernanceDossier]:
    """Get most recent dossier for a translator."""
    dossiers = list_governance_dossiers_for_translator(translator_id)
    if not dossiers:
        return None
    return max(dossiers, key=lambda d: d.created_at)


def clear_governance_dossier_index() -> None:
    """Clear the dossier index (for testing)."""
    DOSSIER_INDEX.clear()


# -----------------------------------------------------------------------------
# Deterministic Dossier Hashing
# -----------------------------------------------------------------------------

def compute_deterministic_dossier_hash(
    provenance_hash: str,
    readiness_hash: str,
    authorization_hash: str,
    freeze_manifest_hash: str,
    lifecycle_hashes: List[str],
    audit_hashes: List[str],
    promotion_evidence_hashes: List[str],
    governance_constraints: List[str],
) -> str:
    """
    Compute deterministic hash of governance evidence.

    Same governance evidence → same dossier hash.

    Excludes:
    - Timestamps
    - UUIDs
    - Transient runtime metadata
    """
    hash_input = {
        "provenance_hash": provenance_hash,
        "readiness_hash": readiness_hash,
        "authorization_hash": authorization_hash,
        "freeze_manifest_hash": freeze_manifest_hash,
        "lifecycle_hashes": sorted(lifecycle_hashes),
        "audit_hashes": sorted(audit_hashes),
        "promotion_evidence_hashes": sorted(promotion_evidence_hashes),
        "governance_constraints": sorted(governance_constraints),
    }

    canonical_json = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


# -----------------------------------------------------------------------------
# Evidence Hash Extraction
# -----------------------------------------------------------------------------

def _extract_hash_from_object(obj: Any, hash_field: str) -> str:
    """Extract hash from object, trying multiple field names."""
    if obj is None:
        return ""

    # Try the specified field first
    if hasattr(obj, hash_field):
        return getattr(obj, hash_field) or ""

    # Try common hash field names
    for field in ["deterministic_hash", "hash", "compute_hash"]:
        if hasattr(obj, field):
            value = getattr(obj, field)
            if callable(value):
                try:
                    return value() or ""
                except Exception:
                    pass
            else:
                return value or ""

    # Try model_dump and hash the result
    if hasattr(obj, "model_dump"):
        try:
            data = obj.model_dump(mode="json")
            # Remove timestamps for determinism
            for key in ["created_at", "evaluated_at", "timestamp"]:
                data.pop(key, None)
            canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
            return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]
        except Exception:
            pass

    return ""


def _extract_provenance_hash(provenance: Any) -> str:
    """Extract hash from 7F provenance."""
    if provenance is None:
        return ""
    if hasattr(provenance, "deterministic_lineage_hash"):
        return provenance.deterministic_lineage_hash or ""
    return _extract_hash_from_object(provenance, "deterministic_lineage_hash")


def _extract_readiness_hash(readiness: Any) -> str:
    """Extract hash from 7G readiness evaluation."""
    return _extract_hash_from_object(readiness, "evaluation_hash")


def _extract_authorization_hash(authorization: Any) -> str:
    """Extract hash from 7E authorization evaluation."""
    return _extract_hash_from_object(authorization, "authorization_hash")


def _extract_freeze_manifest_hash(freeze_manifest: Any) -> str:
    """Extract hash from 7H freeze manifest."""
    if freeze_manifest is None:
        return ""
    if hasattr(freeze_manifest, "compute_manifest_hash"):
        try:
            return freeze_manifest.compute_manifest_hash()
        except Exception:
            pass
    return _extract_hash_from_object(freeze_manifest, "manifest_hash")


def _extract_audit_hashes(provenance: Any) -> List[str]:
    """Extract audit hashes from provenance."""
    if provenance is None:
        return []
    if hasattr(provenance, "parent_audit_hashes"):
        return list(provenance.parent_audit_hashes or [])
    return []


def _extract_promotion_evidence_hashes(provenance: Any) -> List[str]:
    """Extract promotion evidence hashes from provenance."""
    if provenance is None:
        return []
    if hasattr(provenance, "parent_promotion_evidence_hashes"):
        return list(provenance.parent_promotion_evidence_hashes or [])
    return []


def _extract_lifecycle_hashes(readiness: Any, provenance: Any) -> List[str]:
    """Extract lifecycle hashes from readiness/provenance metadata."""
    hashes = []

    # Try readiness metadata
    if readiness and hasattr(readiness, "metadata"):
        metadata = readiness.metadata or {}
        if "lifecycle_hash" in metadata:
            hashes.append(metadata["lifecycle_hash"])
        if "lifecycle_hashes" in metadata:
            hashes.extend(metadata["lifecycle_hashes"])

    # Try provenance metadata
    if provenance and hasattr(provenance, "metadata"):
        metadata = provenance.metadata or {}
        if "lifecycle_hash" in metadata:
            hashes.append(metadata["lifecycle_hash"])
        if "lifecycle_hashes" in metadata:
            hashes.extend(metadata["lifecycle_hashes"])

    # Try lifecycle_snapshot_hash from provenance
    if provenance and hasattr(provenance, "lifecycle_snapshot_hash"):
        if provenance.lifecycle_snapshot_hash:
            hashes.append(provenance.lifecycle_snapshot_hash)

    return list(set(hashes))  # Deduplicate


# -----------------------------------------------------------------------------
# Governance Constraints
# -----------------------------------------------------------------------------

CANONICAL_GOVERNANCE_CONSTRAINTS: List[str] = [
    "execution_runtime_absent",
    "serializer_invocation_prohibited",
    "machine_output_prohibited",
    "plugin_loading_prohibited",
    "human_approval_required",
    "governance_escalation_required",
]


# -----------------------------------------------------------------------------
# Dossier Builder
# -----------------------------------------------------------------------------

class DossierBuildError(Exception):
    """Error during dossier building due to missing required evidence."""
    pass


def build_governance_escalation_dossier(
    readiness_evaluation: Any,
    provenance: Any,
    authorization_evaluation: Any,
    freeze_manifest: Any,
    *,
    lifecycle_hashes: Optional[List[str]] = None,
    audit_hashes: Optional[List[str]] = None,
    promotion_evidence_hashes: Optional[List[str]] = None,
    additional_constraints: Optional[List[str]] = None,
) -> TranslatorGovernanceDossier:
    """
    Build a governance escalation dossier from complete governance evidence.

    Requires all four core inputs:
      - readiness_evaluation (7G)
      - provenance (7F)
      - authorization_evaluation (7E)
      - freeze_manifest (7H)

    Args:
        readiness_evaluation: 7G readiness evaluation (required)
        provenance: 7F provenance lineage (required)
        authorization_evaluation: 7E authorization evaluation (required)
        freeze_manifest: 7H freeze manifest (required)
        lifecycle_hashes: Optional override for lifecycle hashes
        audit_hashes: Optional override for audit hashes
        promotion_evidence_hashes: Optional override for promotion evidence hashes
        additional_constraints: Optional additional governance constraints

    Returns:
        TranslatorGovernanceDossier with complete governance evidence

    Raises:
        DossierBuildError: If any required evidence is missing

    Guardrail:
        7I packages complete governance evidence for review.
        It does NOT create approval authority, execution authority,
        or mutation authority.
    """
    # --- Validate required inputs ---
    if readiness_evaluation is None:
        raise DossierBuildError(
            "Missing required readiness_evaluation — cannot build dossier"
        )

    if provenance is None:
        raise DossierBuildError(
            "Missing required provenance — cannot build dossier"
        )

    if authorization_evaluation is None:
        raise DossierBuildError(
            "Missing required authorization_evaluation — cannot build dossier"
        )

    if freeze_manifest is None:
        raise DossierBuildError(
            "Missing required freeze_manifest — cannot build dossier"
        )

    # --- Extract translator_id ---
    translator_id = None
    for obj in [readiness_evaluation, provenance, authorization_evaluation, freeze_manifest]:
        if hasattr(obj, "translator_id"):
            translator_id = obj.translator_id
            break

    if translator_id is None:
        raise DossierBuildError(
            "Could not determine translator_id from evidence objects"
        )

    # --- Extract gates and states ---
    readiness_gate = "unknown"
    if hasattr(readiness_evaluation, "gate"):
        readiness_gate = readiness_evaluation.gate

    authorization_gate = "unknown"
    if hasattr(authorization_evaluation, "gate"):
        authorization_gate = authorization_evaluation.gate

    quarantine_state = "future_escalation_required"
    # Note: freeze_manifest doesn't have quarantine_state, but we can
    # derive it from the escalation requirements presence
    if hasattr(freeze_manifest, "required_escalation_layers"):
        if freeze_manifest.required_escalation_layers:
            quarantine_state = "future_escalation_required"

    # --- Extract hashes ---
    provenance_hash = _extract_provenance_hash(provenance)
    readiness_hash = _extract_readiness_hash(readiness_evaluation)
    authorization_hash = _extract_authorization_hash(authorization_evaluation)
    freeze_manifest_hash_val = _extract_freeze_manifest_hash(freeze_manifest)

    # --- Extract evidence chains (with overrides) ---
    final_lifecycle_hashes = lifecycle_hashes or _extract_lifecycle_hashes(
        readiness_evaluation, provenance
    )
    final_audit_hashes = audit_hashes or _extract_audit_hashes(provenance)
    final_promotion_evidence_hashes = (
        promotion_evidence_hashes or
        _extract_promotion_evidence_hashes(provenance)
    )

    # --- Build governance constraints ---
    governance_constraints = CANONICAL_GOVERNANCE_CONSTRAINTS.copy()
    if additional_constraints:
        governance_constraints.extend(additional_constraints)
    governance_constraints = list(set(governance_constraints))  # Deduplicate

    # --- Extract required escalation layers from freeze manifest ---
    required_escalation_layers: List[str] = []
    if hasattr(freeze_manifest, "required_escalation_layers"):
        required_escalation_layers = list(freeze_manifest.required_escalation_layers or [])

    # --- Compute deterministic dossier hash ---
    deterministic_dossier_hash = compute_deterministic_dossier_hash(
        provenance_hash=provenance_hash,
        readiness_hash=readiness_hash,
        authorization_hash=authorization_hash,
        freeze_manifest_hash=freeze_manifest_hash_val,
        lifecycle_hashes=final_lifecycle_hashes,
        audit_hashes=final_audit_hashes,
        promotion_evidence_hashes=final_promotion_evidence_hashes,
        governance_constraints=governance_constraints,
    )

    # --- Build dossier ---
    dossier = TranslatorGovernanceDossier(
        translator_id=translator_id,
        readiness_gate=readiness_gate,
        quarantine_state=quarantine_state,
        authorization_gate=authorization_gate,
        provenance_hash=provenance_hash,
        readiness_hash=readiness_hash,
        authorization_hash=authorization_hash,
        freeze_manifest_hash=freeze_manifest_hash_val,
        lifecycle_hashes=final_lifecycle_hashes,
        audit_hashes=final_audit_hashes,
        promotion_evidence_hashes=final_promotion_evidence_hashes,
        governance_constraints=governance_constraints,
        required_escalation_layers=required_escalation_layers,
        review_state="future_escalation_required",
        deterministic_dossier_hash=deterministic_dossier_hash,
        execution_authorized=False,
        machine_output_allowed=False,
        immutable=True,
        metadata={
            "builder": "build_governance_escalation_dossier",
            "dev_order": "7I",
            "review_package": True,
            "evidence_sources": {
                "readiness": type(readiness_evaluation).__name__,
                "provenance": type(provenance).__name__,
                "authorization": type(authorization_evaluation).__name__,
                "freeze_manifest": type(freeze_manifest).__name__,
            },
        },
    )

    # --- Register in index ---
    register_governance_dossier(dossier)

    return dossier


# -----------------------------------------------------------------------------
# RMOS Persistence (Optional)
# -----------------------------------------------------------------------------

DOSSIER_ARTIFACT_KIND = "translator_governance_dossier_json"


def persist_dossier_to_rmos(
    dossier: TranslatorGovernanceDossier,
    run_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Persist governance dossier to RMOS (optional).

    Returns artifact reference if successful, None otherwise.
    Supplemental to in-memory index.
    """
    try:
        from app.cam.export_rmos_artifacts import put_json_attachment

        dossier_dict = dossier.model_dump(mode="json")

        stat, path, sha256 = put_json_attachment(
            kind=DOSSIER_ARTIFACT_KIND,
            obj=dossier_dict,
            run_id=run_id,
        )

        return {
            "kind": DOSSIER_ARTIFACT_KIND,
            "sha256": sha256,
            "bytes": stat.size_bytes if stat else 0,
            "path": path,
            "dossier_id": dossier.dossier_id,
        }
    except ImportError:
        return None
    except Exception:
        return None
