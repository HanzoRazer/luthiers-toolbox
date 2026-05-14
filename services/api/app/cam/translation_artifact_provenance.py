"""
Translation Artifact Provenance + Immutable Governance Lineage

CAM Dev Order 7F: Provenance and lineage tracking for translation artifacts.

This module formalizes:
  Translation Artifact → Provenance Lineage → Governance Evidence Chain

Provenance represents governance context at evaluation time, NOT artifact
revision history. Same artifact + different governance context = different
provenance.

7F invariants:
  - immutable: always true
  - execution_authorized: always false
  - machine_output_present: always false

Key distinction:
  Governance ancestry ≠ artifact revision control
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from app.cam.translation_artifact import TranslationArtifact


# -----------------------------------------------------------------------------
# Type Definitions
# -----------------------------------------------------------------------------

ProvenanceLineageState = Literal[
    "validation_only",
    "non_executable",
]


# -----------------------------------------------------------------------------
# Provenance Index (In-Memory Registry)
# -----------------------------------------------------------------------------

PROVENANCE_INDEX: Dict[str, "TranslationArtifactProvenance"] = {}


# -----------------------------------------------------------------------------
# Provenance Summary (Lightweight)
# -----------------------------------------------------------------------------

class TranslationArtifactProvenanceSummary(BaseModel):
    """
    Lightweight provenance summary for artifact attachment.

    Contains only identification and immutability state.
    """

    provenance_id: str = Field(..., description="Provenance identifier")
    deterministic_lineage_hash: str = Field(
        ..., description="Deterministic hash of governance lineage"
    )
    lineage_state: ProvenanceLineageState = Field(
        ..., description="Provenance lineage state"
    )

    # 7F invariants — always enforced
    immutable: bool = Field(
        default=True,
        description="Always true — provenance is immutable"
    )
    execution_authorized: bool = Field(
        default=False,
        description="Always false — execution not authorized"
    )


# -----------------------------------------------------------------------------
# Full Provenance Model
# -----------------------------------------------------------------------------

class TranslationArtifactProvenance(BaseModel):
    """
    Translation artifact provenance with immutable governance lineage.

    Represents governance context at evaluation time:
    - Lifecycle ancestry
    - Policy state
    - Capability state
    - Audit/evidence hashes

    7F invariants (model-enforced):
      - immutable: always true
      - execution_authorized: always false
      - machine_output_present: always false
    """

    # --- Identity ---
    provenance_id: str = Field(
        default_factory=lambda: f"prov-{uuid4().hex[:12]}",
        description="Unique provenance identifier"
    )
    artifact_id: str = Field(..., description="Source artifact identifier")

    # --- Source Lineage ---
    source_export_object_hash: str = Field(
        ..., description="SHA256 hash of source export object"
    )

    # --- Governance Ancestry ---
    parent_audit_hashes: List[str] = Field(
        default_factory=list,
        description="Audit ledger hashes from current governance cycle"
    )
    parent_promotion_evidence_hashes: List[str] = Field(
        default_factory=list,
        description="Promotion evidence hashes from current governance state"
    )

    # --- Capability/Policy Hashes ---
    translator_capability_hash: str = Field(
        ..., description="Hash of translator capability at evaluation time"
    )
    policy_snapshot_hash: str = Field(
        default="",
        description="Hash of policy snapshot at evaluation time"
    )
    lifecycle_snapshot_hash: str = Field(
        default="",
        description="Hash of lifecycle report snapshot"
    )

    # --- Deterministic Lineage ---
    deterministic_lineage_hash: str = Field(
        ..., description="Deterministic hash of full governance lineage"
    )

    # --- State ---
    lineage_state: ProvenanceLineageState = Field(
        default="validation_only",
        description="Provenance lineage state"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Provenance creation timestamp"
    )

    # --- 7F Invariants ---
    immutable: bool = Field(
        default=True,
        description="Always true — provenance is immutable"
    )
    execution_authorized: bool = Field(
        default=False,
        description="Always false — execution not authorized in 7F"
    )
    machine_output_present: bool = Field(
        default=False,
        description="Always false — no machine output in 7F"
    )

    # --- Metadata ---
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional provenance metadata"
    )

    # --- Invariant Enforcement ---
    @model_validator(mode="after")
    def enforce_7f_invariants(self) -> "TranslationArtifactProvenance":
        """
        Enforce 7F invariants:
        - immutable must be True
        - execution_authorized must be False
        - machine_output_present must be False
        """
        if not self.immutable:
            raise ValueError(
                f"Provenance '{self.provenance_id}': immutable must be True — "
                f"provenance lineage is always immutable"
            )

        if self.execution_authorized:
            raise ValueError(
                f"Provenance '{self.provenance_id}': execution_authorized must be "
                f"False in 7F — no execution authorization"
            )

        if self.machine_output_present:
            raise ValueError(
                f"Provenance '{self.provenance_id}': machine_output_present must be "
                f"False in 7F — no machine output"
            )

        return self

    def to_summary(self) -> TranslationArtifactProvenanceSummary:
        """Create lightweight summary for artifact attachment."""
        return TranslationArtifactProvenanceSummary(
            provenance_id=self.provenance_id,
            deterministic_lineage_hash=self.deterministic_lineage_hash,
            lineage_state=self.lineage_state,
            immutable=self.immutable,
            execution_authorized=self.execution_authorized,
        )


# -----------------------------------------------------------------------------
# Deterministic Lineage Hashing
# -----------------------------------------------------------------------------

def _normalize_for_lineage_hash(obj: Any) -> Any:
    """Normalize object for deterministic lineage hashing."""
    if isinstance(obj, dict):
        return {
            k: _normalize_for_lineage_hash(v)
            for k, v in sorted(obj.items())
            if k not in ("created_at", "timestamp", "updated_at", "provenance_id")
        }
    elif isinstance(obj, list):
        return [_normalize_for_lineage_hash(item) for item in obj]
    elif isinstance(obj, datetime):
        return None  # Exclude timestamps
    else:
        return obj


def compute_deterministic_lineage_hash(
    source_export_object_hash: str,
    parent_audit_hashes: List[str],
    parent_promotion_evidence_hashes: List[str],
    translator_capability_hash: str,
    policy_snapshot_hash: str,
    lifecycle_snapshot_hash: str,
) -> str:
    """
    Compute deterministic lineage hash from governance ancestry.

    Same governance ancestry → same lineage hash.

    Excludes:
    - Timestamps
    - UUIDs
    - RMOS attachment IDs
    - Transient metadata
    """
    lineage_input = {
        "source_export_object_hash": source_export_object_hash,
        "parent_audit_hashes": sorted(parent_audit_hashes),
        "parent_promotion_evidence_hashes": sorted(parent_promotion_evidence_hashes),
        "translator_capability_hash": translator_capability_hash,
        "policy_snapshot_hash": policy_snapshot_hash,
        "lifecycle_snapshot_hash": lifecycle_snapshot_hash,
    }

    canonical_json = json.dumps(lineage_input, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def compute_snapshot_hash(snapshot: Dict[str, Any]) -> str:
    """Compute hash of a snapshot dict (policy, lifecycle, capability)."""
    if not snapshot:
        return ""
    normalized = _normalize_for_lineage_hash(snapshot)
    canonical_json = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


# -----------------------------------------------------------------------------
# Provenance Builder
# -----------------------------------------------------------------------------

def build_translation_artifact_provenance(
    artifact: TranslationArtifact,
    lifecycle_report: Optional[Dict[str, Any]] = None,
    audit_ledger: Optional[Dict[str, Any]] = None,
    promotion_evidence: Optional[Dict[str, Any]] = None,
) -> TranslationArtifactProvenance:
    """
    Build translation artifact provenance from governance context.

    Captures:
    - Governance ancestry
    - Deterministic lineage hash
    - Immutable semantics

    No artifact mutation. No execution authorization.

    Args:
        artifact: Source translation artifact
        lifecycle_report: Optional lifecycle report dict
        audit_ledger: Optional audit ledger dict
        promotion_evidence: Optional promotion evidence dict

    Returns:
        TranslationArtifactProvenance with immutable lineage
    """
    # Extract hashes from governance artifacts
    parent_audit_hashes: List[str] = []
    if audit_ledger:
        audit_hash = audit_ledger.get("deterministic_hash")
        if audit_hash:
            parent_audit_hashes.append(audit_hash)

    parent_promotion_evidence_hashes: List[str] = []
    if promotion_evidence:
        evidence_hash = promotion_evidence.get("evidence_hash")
        if evidence_hash:
            parent_promotion_evidence_hashes.append(evidence_hash)

    # Compute component hashes
    translator_capability_hash = compute_snapshot_hash(artifact.capability_snapshot)
    policy_snapshot_hash = compute_snapshot_hash(artifact.policy_snapshot)
    lifecycle_snapshot_hash = compute_snapshot_hash(lifecycle_report or {})

    # Compute deterministic lineage hash
    deterministic_lineage_hash = compute_deterministic_lineage_hash(
        source_export_object_hash=artifact.source_export_object_hash,
        parent_audit_hashes=parent_audit_hashes,
        parent_promotion_evidence_hashes=parent_promotion_evidence_hashes,
        translator_capability_hash=translator_capability_hash,
        policy_snapshot_hash=policy_snapshot_hash,
        lifecycle_snapshot_hash=lifecycle_snapshot_hash,
    )

    # Determine lineage state from artifact state
    lineage_state: ProvenanceLineageState = "validation_only"
    if artifact.artifact_state == "non_executable":
        lineage_state = "non_executable"

    # Build provenance
    provenance = TranslationArtifactProvenance(
        artifact_id=artifact.artifact_id,
        source_export_object_hash=artifact.source_export_object_hash,
        parent_audit_hashes=parent_audit_hashes,
        parent_promotion_evidence_hashes=parent_promotion_evidence_hashes,
        translator_capability_hash=translator_capability_hash,
        policy_snapshot_hash=policy_snapshot_hash,
        lifecycle_snapshot_hash=lifecycle_snapshot_hash,
        deterministic_lineage_hash=deterministic_lineage_hash,
        lineage_state=lineage_state,
        immutable=True,
        execution_authorized=False,
        machine_output_present=False,
        metadata={
            "builder": "build_translation_artifact_provenance",
            "dev_order": "7F",
            "artifact_state": artifact.artifact_state,
            "translator_id": artifact.translator_id,
        },
    )

    # Register in provenance index
    register_provenance(provenance)

    return provenance


# -----------------------------------------------------------------------------
# Provenance Index Operations
# -----------------------------------------------------------------------------

def register_provenance(provenance: TranslationArtifactProvenance) -> None:
    """Register provenance in the in-memory index."""
    PROVENANCE_INDEX[provenance.provenance_id] = provenance


def get_provenance(provenance_id: str) -> Optional[TranslationArtifactProvenance]:
    """Get provenance by ID from the index."""
    return PROVENANCE_INDEX.get(provenance_id)


def get_provenance_by_artifact(artifact_id: str) -> List[TranslationArtifactProvenance]:
    """
    Get all provenances for an artifact ID.

    Returns list because same artifact may have multiple provenances
    from different governance contexts.
    """
    return [
        p for p in PROVENANCE_INDEX.values()
        if p.artifact_id == artifact_id
    ]


def list_provenances() -> List[TranslationArtifactProvenance]:
    """List all registered provenances."""
    return list(PROVENANCE_INDEX.values())


def get_provenance_by_lineage_hash(
    lineage_hash: str,
) -> Optional[TranslationArtifactProvenance]:
    """Get provenance by deterministic lineage hash."""
    for provenance in PROVENANCE_INDEX.values():
        if provenance.deterministic_lineage_hash == lineage_hash:
            return provenance
    return None


def clear_provenance_index() -> None:
    """Clear the provenance index (for testing)."""
    PROVENANCE_INDEX.clear()


# -----------------------------------------------------------------------------
# RMOS Persistence (Optional)
# -----------------------------------------------------------------------------

PROVENANCE_ARTIFACT_KIND = "translation_artifact_provenance_json"


def persist_provenance_to_rmos(
    provenance: TranslationArtifactProvenance,
    run_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Persist provenance to RMOS (optional).

    Returns artifact reference if successful, None otherwise.

    This is supplemental to the in-memory index.
    """
    try:
        from app.cam.export_rmos_artifacts import put_json_attachment, RMOSArtifactRef

        provenance_dict = provenance.model_dump(mode="json")

        # Use existing RMOS infrastructure
        stat, path, sha256 = put_json_attachment(
            kind=PROVENANCE_ARTIFACT_KIND,
            obj=provenance_dict,
            run_id=run_id,
        )

        return {
            "kind": PROVENANCE_ARTIFACT_KIND,
            "sha256": sha256,
            "bytes": stat.size_bytes if stat else 0,
            "path": path,
            "provenance_id": provenance.provenance_id,
        }
    except ImportError:
        return None
    except Exception:
        return None
