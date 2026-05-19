"""
Translator Governance Review Ledger

CAM Dev Order 7K: Immutable governance review trace chain.

This module creates the permanent governance trace chain for:
  - Review readiness evaluations
  - Escalation review evidence
  - Governance review lineage
  - Review deficiency history
  - Review-state evolution snapshots

7K invariants:
  - immutable = true (always)
  - execution_authorized = false (always)
  - machine_output_allowed = false (always)

Guardrail:
  7K records governance review trace ancestry. It must not mutate
  prior entries, approval state, or execution authority.
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

UNRESOLVED_HASH_PLACEHOLDER = "unresolved"


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------

class LedgerBuildError(Exception):
    """Raised when ledger entry build fails."""
    pass


class DuplicateLedgerEntryError(Exception):
    """Raised when attempting to register a duplicate ledger entry ID."""
    pass


# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------

class TranslatorGovernanceReviewLedgerEntry(BaseModel):
    """
    Immutable governance review ledger entry.

    Records deterministic review-readiness evaluations and preserves
    governance trace ancestry.

    7K invariants (model-enforced):
      - immutable = true (always)
      - execution_authorized = false (always)
      - machine_output_allowed = false (always)
    """

    # --- Identity ---
    ledger_entry_id: str = Field(..., description="Unique ledger entry ID")
    review_matrix_id: str = Field(..., description="Source review matrix ID")
    dossier_id: str = Field(..., description="Source dossier ID")
    translator_id: str = Field(..., description="Translator identifier")

    # --- Review State ---
    review_gate: str = Field(..., description="Review gate from matrix")
    review_readiness_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Review readiness score"
    )
    review_state: Literal[
        "review_only",
        "non_executable",
        "future_escalation_required",
    ] = Field(
        default="future_escalation_required",
        description="Current review state"
    )

    # --- Source Evidence Hashes ---
    provenance_hash: str = Field(..., description="Hash from provenance lineage")
    readiness_hash: str = Field(..., description="Hash from readiness evaluation")
    quarantine_hash: str = Field(..., description="Hash from quarantine/freeze manifest")
    authorization_hash: str = Field(..., description="Hash from authorization evaluation")
    dossier_hash: str = Field(..., description="Hash from governance dossier")
    review_matrix_hash: str = Field(..., description="Hash from review matrix")

    # --- Lineage ---
    parent_ledger_hashes: List[str] = Field(
        default_factory=list,
        description="Parent ledger entry hashes (ancestry chain)"
    )

    # --- Governance Constraints ---
    governance_constraints: List[str] = Field(
        default_factory=list,
        description="Active governance constraints"
    )

    # --- Deterministic Trace Hash ---
    review_trace_hash: str = Field(
        ...,
        description="Deterministic hash of all governance review ancestry"
    )

    # --- 7K Invariants ---
    immutable: bool = Field(
        default=True,
        description="Always true — ledger entries are immutable"
    )
    execution_authorized: bool = Field(
        default=False,
        description="Always false — no execution authorization"
    )
    machine_output_allowed: bool = Field(
        default=False,
        description="Always false — no machine output"
    )

    # --- Metadata ---
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    unresolved_hashes: List[str] = Field(
        default_factory=list,
        description="List of hash fields that could not be resolved"
    )

    # 7K invariant validators
    @field_validator("immutable", mode="before")
    @classmethod
    def enforce_immutable(cls, v: Any) -> bool:
        if v is False:
            raise ValueError(
                "7K invariant violation: immutable must be true"
            )
        return True

    @field_validator("execution_authorized", mode="before")
    @classmethod
    def enforce_no_execution(cls, v: Any) -> bool:
        if v is True:
            raise ValueError(
                "7K invariant violation: execution_authorized must be false"
            )
        return False

    @field_validator("machine_output_allowed", mode="before")
    @classmethod
    def enforce_no_machine_output(cls, v: Any) -> bool:
        if v is True:
            raise ValueError(
                "7K invariant violation: machine_output_allowed must be false"
            )
        return False

    @model_validator(mode="after")
    def validate_invariants(self) -> "TranslatorGovernanceReviewLedgerEntry":
        """Validate all 7K invariants after model construction."""
        if not self.immutable:
            raise ValueError(
                "7K invariant violation: immutable must be true"
            )
        if self.execution_authorized:
            raise ValueError(
                "7K invariant violation: execution_authorized must be false"
            )
        if self.machine_output_allowed:
            raise ValueError(
                "7K invariant violation: machine_output_allowed must be false"
            )
        return self


class GovernanceReviewLedgerSummary(BaseModel):
    """
    Summary of a governance review ledger entry for integration.

    Minimal representation for cross-module references.
    """

    ledger_entry_id: str
    review_matrix_id: str
    dossier_id: str
    translator_id: str
    review_gate: str
    review_readiness_score: int
    review_trace_hash: str
    parent_count: int
    created_at: datetime

    # 7K invariants
    immutable: bool = True
    execution_authorized: bool = False
    machine_output_allowed: bool = False

    @field_validator("immutable", mode="before")
    @classmethod
    def enforce_immutable(cls, v: Any) -> bool:
        return True

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

REVIEW_LEDGER_INDEX: Dict[str, TranslatorGovernanceReviewLedgerEntry] = {}


def register_review_ledger_entry(
    entry: TranslatorGovernanceReviewLedgerEntry,
) -> None:
    """
    Register a ledger entry in the index.

    Raises:
        DuplicateLedgerEntryError: If ledger_entry_id already exists
    """
    if entry.ledger_entry_id in REVIEW_LEDGER_INDEX:
        raise DuplicateLedgerEntryError(
            f"Ledger entry already exists: {entry.ledger_entry_id}. "
            "Ledger entries are append-only and immutable."
        )
    REVIEW_LEDGER_INDEX[entry.ledger_entry_id] = entry


def get_review_ledger_entry(
    ledger_entry_id: str,
) -> Optional[TranslatorGovernanceReviewLedgerEntry]:
    """Get a ledger entry by ID."""
    return REVIEW_LEDGER_INDEX.get(ledger_entry_id)


def list_review_ledger_entries() -> List[TranslatorGovernanceReviewLedgerEntry]:
    """List all ledger entries."""
    return list(REVIEW_LEDGER_INDEX.values())


def list_review_ledger_entries_for_translator(
    translator_id: str,
) -> List[TranslatorGovernanceReviewLedgerEntry]:
    """List ledger entries for a specific translator."""
    return [
        e for e in REVIEW_LEDGER_INDEX.values()
        if e.translator_id == translator_id
    ]


def get_latest_ledger_entry_for_translator(
    translator_id: str,
) -> Optional[TranslatorGovernanceReviewLedgerEntry]:
    """Get the most recent ledger entry for a translator."""
    entries = list_review_ledger_entries_for_translator(translator_id)
    if not entries:
        return None
    return max(entries, key=lambda e: e.created_at)


def clear_review_ledger_index() -> None:
    """Clear all ledger entries from the index (for testing)."""
    REVIEW_LEDGER_INDEX.clear()


# -----------------------------------------------------------------------------
# Hash Extraction Helpers
# -----------------------------------------------------------------------------

def _extract_hash(
    obj: Any,
    field_names: List[str],
    fallback_fields: Optional[List[str]] = None,
) -> str:
    """
    Extract hash from object using preferred field names.

    Args:
        obj: Object to extract hash from
        field_names: Preferred field names to try
        fallback_fields: Additional fallback field names

    Returns:
        Hash string or UNRESOLVED_HASH_PLACEHOLDER
    """
    if obj is None:
        return UNRESOLVED_HASH_PLACEHOLDER

    all_fields = field_names + (fallback_fields or [])

    for field in all_fields:
        value = getattr(obj, field, None)
        if value and isinstance(value, str):
            return value

    # Try to derive a stable hash from object contents as fallback
    try:
        if hasattr(obj, "model_dump"):
            data = obj.model_dump(mode="json", exclude={"created_at"})
            data_json = json.dumps(data, sort_keys=True, separators=(",", ":"))
            return hashlib.sha256(data_json.encode()).hexdigest()
    except Exception:
        pass

    return UNRESOLVED_HASH_PLACEHOLDER


def _extract_provenance_hash(provenance: Any) -> str:
    """Extract hash from provenance object."""
    return _extract_hash(
        provenance,
        ["deterministic_lineage_hash", "lineage_hash", "evidence_hash"],
        ["provenance_hash", "hash"],
    )


def _extract_readiness_hash(readiness: Any) -> str:
    """Extract hash from readiness evaluation object."""
    return _extract_hash(
        readiness,
        ["deterministic_readiness_hash", "readiness_hash", "evidence_hash"],
        ["evaluation_hash", "hash"],
    )


def _extract_quarantine_hash(quarantine: Any) -> str:
    """Extract hash from quarantine/freeze manifest object."""
    return _extract_hash(
        quarantine,
        ["freeze_manifest_hash", "quarantine_hash", "evidence_hash"],
        ["manifest_hash", "hash"],
    )


def _extract_authorization_hash(authorization: Any) -> str:
    """Extract hash from authorization evaluation object."""
    return _extract_hash(
        authorization,
        ["deterministic_authorization_hash", "authorization_hash", "evidence_hash"],
        ["evaluation_hash", "hash"],
    )


def _extract_dossier_hash(dossier: Any) -> str:
    """Extract hash from dossier object."""
    return _extract_hash(
        dossier,
        ["deterministic_dossier_hash", "dossier_hash", "evidence_hash"],
        ["hash"],
    )


def _extract_review_matrix_hash(review_matrix: Any) -> str:
    """Extract hash from review matrix object."""
    return _extract_hash(
        review_matrix,
        ["evidence_hash", "deterministic_review_hash", "review_hash"],
        ["matrix_hash", "hash"],
    )


# -----------------------------------------------------------------------------
# Deterministic Review Trace Hash
# -----------------------------------------------------------------------------

def _compute_review_trace_hash(
    review_matrix_hash: str,
    dossier_hash: str,
    provenance_hash: str,
    readiness_hash: str,
    quarantine_hash: str,
    authorization_hash: str,
    governance_constraints: List[str],
    parent_ledger_hashes: List[str],
) -> str:
    """
    Compute deterministic review trace hash from governance ancestry.

    Excludes:
      - timestamps
      - UUIDs
      - transient metadata
      - RMOS attachment IDs

    Goal: same governance review ancestry → same review trace hash
    """
    trace_data = {
        "review_matrix_hash": review_matrix_hash,
        "dossier_hash": dossier_hash,
        "provenance_hash": provenance_hash,
        "readiness_hash": readiness_hash,
        "quarantine_hash": quarantine_hash,
        "authorization_hash": authorization_hash,
        "governance_constraints": sorted(governance_constraints),
        "parent_ledger_hashes": sorted(parent_ledger_hashes),
    }
    trace_json = json.dumps(trace_data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(trace_json.encode()).hexdigest()


# -----------------------------------------------------------------------------
# Parent Detection
# -----------------------------------------------------------------------------

def _auto_detect_parent_hashes(translator_id: str) -> List[str]:
    """
    Auto-detect parent ledger hashes for a translator.

    Returns the review_trace_hash of the most recent entry, or empty list
    if this is the genesis entry.
    """
    latest = get_latest_ledger_entry_for_translator(translator_id)
    if latest is None:
        return []  # Genesis entry
    return [latest.review_trace_hash]


# -----------------------------------------------------------------------------
# Index Lookup Helpers
# -----------------------------------------------------------------------------

def _lookup_dossier(dossier_id: str) -> Any:
    """Look up dossier from DOSSIER_INDEX."""
    try:
        from app.cam.translator_governance_dossier import get_governance_dossier
        return get_governance_dossier(dossier_id)
    except ImportError:
        return None


def _lookup_review_matrix(review_matrix_id: str) -> Any:
    """Look up review matrix from REVIEW_MATRIX_INDEX."""
    try:
        from app.cam.translator_governance_review_matrix import get_review_matrix
        return get_review_matrix(review_matrix_id)
    except ImportError:
        return None


# -----------------------------------------------------------------------------
# Ledger Builder
# -----------------------------------------------------------------------------

def build_governance_review_ledger_entry(
    review_matrix: Any,
    dossier: Optional[Any] = None,
    provenance: Optional[Any] = None,
    readiness: Optional[Any] = None,
    quarantine: Optional[Any] = None,
    authorization: Optional[Any] = None,
    parent_ledger_hashes: Optional[List[str]] = None,
    persist_to_rmos: bool = False,
) -> TranslatorGovernanceReviewLedgerEntry:
    """
    Build an immutable governance review ledger entry.

    Args:
        review_matrix: TranslatorGovernanceReviewMatrix (required)
        dossier: TranslatorGovernanceDossier (optional, fallback to index)
        provenance: Provenance object (optional)
        readiness: Readiness evaluation (optional)
        quarantine: Quarantine/freeze manifest (optional)
        authorization: Authorization evaluation (optional)
        parent_ledger_hashes: Explicit parent hashes (optional, auto-detect if None)
        persist_to_rmos: Whether to persist to RMOS (default False)

    Returns:
        TranslatorGovernanceReviewLedgerEntry

    Raises:
        LedgerBuildError: If review_matrix is missing or invalid

    Guardrail:
      7K records governance review trace ancestry. It must not mutate
      prior entries, approval state, or execution authority.
    """
    if review_matrix is None:
        raise LedgerBuildError("review_matrix is required")

    # Extract core identifiers from review matrix
    review_matrix_id = getattr(review_matrix, "review_matrix_id", None)
    dossier_id = getattr(review_matrix, "dossier_id", None)
    translator_id = getattr(review_matrix, "translator_id", None)

    if not review_matrix_id or not translator_id:
        raise LedgerBuildError(
            "review_matrix must have review_matrix_id and translator_id"
        )

    # Extract review state from matrix
    review_gate = getattr(review_matrix, "review_gate", "red")
    review_readiness_score = getattr(review_matrix, "review_readiness_score", 0)
    review_state = getattr(review_matrix, "review_state", "future_escalation_required")

    # Look up dossier if not provided
    if dossier is None and dossier_id:
        dossier = _lookup_dossier(dossier_id)

    # Track unresolved hashes
    unresolved_hashes: List[str] = []

    # Extract hashes from input objects
    provenance_hash = _extract_provenance_hash(provenance)
    if provenance_hash == UNRESOLVED_HASH_PLACEHOLDER:
        unresolved_hashes.append("provenance_hash")

    readiness_hash = _extract_readiness_hash(readiness)
    if readiness_hash == UNRESOLVED_HASH_PLACEHOLDER:
        unresolved_hashes.append("readiness_hash")

    quarantine_hash = _extract_quarantine_hash(quarantine)
    if quarantine_hash == UNRESOLVED_HASH_PLACEHOLDER:
        unresolved_hashes.append("quarantine_hash")

    authorization_hash = _extract_authorization_hash(authorization)
    if authorization_hash == UNRESOLVED_HASH_PLACEHOLDER:
        unresolved_hashes.append("authorization_hash")

    dossier_hash = _extract_dossier_hash(dossier)
    if dossier_hash == UNRESOLVED_HASH_PLACEHOLDER:
        unresolved_hashes.append("dossier_hash")

    review_matrix_hash = _extract_review_matrix_hash(review_matrix)
    if review_matrix_hash == UNRESOLVED_HASH_PLACEHOLDER:
        unresolved_hashes.append("review_matrix_hash")

    # Extract governance constraints from dossier or matrix
    governance_constraints: List[str] = []
    if dossier:
        governance_constraints = getattr(dossier, "governance_constraints", []) or []
    if not governance_constraints and review_matrix:
        # Try to get from matrix blockers as fallback
        blockers = getattr(review_matrix, "blockers", []) or []
        if blockers:
            governance_constraints = blockers[:5]  # Limit to 5

    # Determine parent ledger hashes
    if parent_ledger_hashes is None:
        parent_ledger_hashes = _auto_detect_parent_hashes(translator_id)

    # Compute deterministic review trace hash
    review_trace_hash = _compute_review_trace_hash(
        review_matrix_hash=review_matrix_hash,
        dossier_hash=dossier_hash,
        provenance_hash=provenance_hash,
        readiness_hash=readiness_hash,
        quarantine_hash=quarantine_hash,
        authorization_hash=authorization_hash,
        governance_constraints=governance_constraints,
        parent_ledger_hashes=parent_ledger_hashes,
    )

    # Generate ledger entry ID
    ledger_entry_id = f"ledger-{uuid.uuid4().hex[:12]}"

    # Create ledger entry
    entry = TranslatorGovernanceReviewLedgerEntry(
        ledger_entry_id=ledger_entry_id,
        review_matrix_id=review_matrix_id,
        dossier_id=dossier_id or "unknown",
        translator_id=translator_id,
        review_gate=review_gate,
        review_readiness_score=review_readiness_score,
        review_state=review_state,
        provenance_hash=provenance_hash,
        readiness_hash=readiness_hash,
        quarantine_hash=quarantine_hash,
        authorization_hash=authorization_hash,
        dossier_hash=dossier_hash,
        review_matrix_hash=review_matrix_hash,
        parent_ledger_hashes=parent_ledger_hashes,
        governance_constraints=governance_constraints,
        review_trace_hash=review_trace_hash,
        unresolved_hashes=unresolved_hashes,
        immutable=True,
        execution_authorized=False,
        machine_output_allowed=False,
    )

    # Register in index
    register_review_ledger_entry(entry)

    # Optional RMOS persistence
    if persist_to_rmos:
        _persist_to_rmos(entry)

    return entry


def build_governance_review_ledger_entry_by_matrix_id(
    review_matrix_id: str,
    parent_ledger_hashes: Optional[List[str]] = None,
    persist_to_rmos: bool = False,
) -> TranslatorGovernanceReviewLedgerEntry:
    """
    Build ledger entry by looking up review matrix from index.

    Args:
        review_matrix_id: Review matrix ID to look up
        parent_ledger_hashes: Explicit parent hashes (optional)
        persist_to_rmos: Whether to persist to RMOS (default False)

    Returns:
        TranslatorGovernanceReviewLedgerEntry

    Raises:
        LedgerBuildError: If review matrix not found
    """
    review_matrix = _lookup_review_matrix(review_matrix_id)
    if review_matrix is None:
        raise LedgerBuildError(f"Review matrix not found: {review_matrix_id}")

    return build_governance_review_ledger_entry(
        review_matrix=review_matrix,
        parent_ledger_hashes=parent_ledger_hashes,
        persist_to_rmos=persist_to_rmos,
    )


# -----------------------------------------------------------------------------
# RMOS Persistence (Optional)
# -----------------------------------------------------------------------------

def _persist_to_rmos(entry: TranslatorGovernanceReviewLedgerEntry) -> Optional[str]:
    """
    Persist ledger entry to RMOS.

    Artifact kind: translator_governance_review_ledger_json

    Returns:
        RMOS artifact ID if successful, None otherwise
    """
    try:
        from app.rmos.runs_v2.run_artifact_manager import persist_run_artifact

        artifact_data = entry.model_dump(mode="json")

        artifact_id = persist_run_artifact(
            artifact_kind="translator_governance_review_ledger_json",
            artifact_data=artifact_data,
            metadata={
                "ledger_entry_id": entry.ledger_entry_id,
                "review_matrix_id": entry.review_matrix_id,
                "dossier_id": entry.dossier_id,
                "translator_id": entry.translator_id,
                "review_gate": entry.review_gate,
                "review_trace_hash": entry.review_trace_hash,
                "parent_count": len(entry.parent_ledger_hashes),
            },
        )
        return artifact_id
    except ImportError:
        return None
    except Exception:
        return None


# -----------------------------------------------------------------------------
# Summary Helper
# -----------------------------------------------------------------------------

def to_summary(
    entry: TranslatorGovernanceReviewLedgerEntry,
) -> GovernanceReviewLedgerSummary:
    """Convert a ledger entry to its summary representation."""
    return GovernanceReviewLedgerSummary(
        ledger_entry_id=entry.ledger_entry_id,
        review_matrix_id=entry.review_matrix_id,
        dossier_id=entry.dossier_id,
        translator_id=entry.translator_id,
        review_gate=entry.review_gate,
        review_readiness_score=entry.review_readiness_score,
        review_trace_hash=entry.review_trace_hash,
        parent_count=len(entry.parent_ledger_hashes),
        created_at=entry.created_at,
        immutable=True,
        execution_authorized=False,
        machine_output_allowed=False,
    )


# -----------------------------------------------------------------------------
# Lineage Helpers
# -----------------------------------------------------------------------------

def get_lineage_chain(
    ledger_entry_id: str,
    max_depth: int = 10,
) -> List[TranslatorGovernanceReviewLedgerEntry]:
    """
    Get the lineage chain for a ledger entry.

    Walks parent_ledger_hashes to build ancestry chain.

    Args:
        ledger_entry_id: Starting ledger entry ID
        max_depth: Maximum ancestry depth to traverse

    Returns:
        List of ledger entries from newest to oldest
    """
    chain: List[TranslatorGovernanceReviewLedgerEntry] = []
    visited: set = set()

    entry = get_review_ledger_entry(ledger_entry_id)
    if entry is None:
        return chain

    chain.append(entry)
    visited.add(entry.review_trace_hash)

    depth = 0
    current_hashes = entry.parent_ledger_hashes

    while current_hashes and depth < max_depth:
        depth += 1
        next_hashes: List[str] = []

        for parent_hash in current_hashes:
            if parent_hash in visited:
                continue

            # Find entry by review_trace_hash
            for e in REVIEW_LEDGER_INDEX.values():
                if e.review_trace_hash == parent_hash:
                    chain.append(e)
                    visited.add(parent_hash)
                    next_hashes.extend(e.parent_ledger_hashes)
                    break

        current_hashes = next_hashes

    return chain
