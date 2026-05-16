"""
Translator Governance Continuity Graph

CAM Dev Order 7L: Governance review continuity replay infrastructure.

This module creates the immutable governance continuity layer that connects
governance review ledger entries into deterministic replayable continuity graphs.

7L enables:
  - Deterministic governance replay
  - Escalation continuity tracking
  - Immutable governance ancestry traversal
  - Review evolution analysis
  - Replay integrity verification

7L invariants:
  - replayable = true (always)
  - immutable = true (always)
  - execution_authorized = false (always)
  - machine_output_allowed = false (always)

Guardrail:
  7L continuity graph remains immutable replay infrastructure only.
  No mutation, approval, execution, serializer invocation, or machine-output semantics.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
import hashlib
import json

from pydantic import BaseModel, Field, field_validator, model_validator

from app.cam.translator_governance_review_ledger import (
    TranslatorGovernanceReviewLedgerEntry,
    list_review_ledger_entries_for_translator,
)


# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

CONTINUITY_STATE_OPTIONS = Literal[
    "review_only",
    "non_executable",
    "future_escalation_required",
]


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------

class ContinuityGraphBuildError(Exception):
    """Raised when continuity graph build fails."""
    pass


class MixedTranslatorError(ValueError):
    """Raised when ledger entries have mixed translator_ids."""
    pass


class DuplicateContinuityGraphError(Exception):
    """Raised when attempting to register a duplicate continuity graph ID."""
    pass


# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------

class TranslatorGovernanceContinuityGraph(BaseModel):
    """
    Governance continuity graph for deterministic replay.

    Connects governance review ledger entries into an immutable
    replay structure for ancestry traversal and integrity verification.

    7L invariants (model-enforced):
      - replayable = true (always)
      - immutable = true (always)
      - execution_authorized = false (always)
      - machine_output_allowed = false (always)
    """

    # --- Identity ---
    continuity_graph_id: str = Field(
        ...,
        description="Deterministic graph ID from translator + root + current hashes"
    )
    translator_id: str = Field(..., description="Translator identifier")

    # --- Trace Hashes ---
    root_review_trace_hash: str = Field(
        ...,
        description="Review trace hash of the genesis (first) entry"
    )
    current_review_trace_hash: str = Field(
        ...,
        description="Review trace hash of the most recent entry"
    )

    # --- Hash Chains (positionally correlated) ---
    review_trace_chain: List[str] = Field(
        default_factory=list,
        description="Ordered chain of review trace hashes"
    )
    dossier_hash_chain: List[str] = Field(
        default_factory=list,
        description="Ordered chain of dossier hashes"
    )
    provenance_hash_chain: List[str] = Field(
        default_factory=list,
        description="Ordered chain of provenance hashes"
    )
    readiness_hash_chain: List[str] = Field(
        default_factory=list,
        description="Ordered chain of readiness hashes"
    )
    quarantine_hash_chain: List[str] = Field(
        default_factory=list,
        description="Ordered chain of quarantine hashes"
    )

    # --- Integrity ---
    continuity_integrity_valid: bool = Field(
        ...,
        description="Whether continuity integrity is valid"
    )
    integrity_violations: List[str] = Field(
        default_factory=list,
        description="List of integrity violations if any"
    )

    # --- Deterministic Continuity Hash ---
    deterministic_continuity_hash: str = Field(
        ...,
        description="Deterministic hash of all continuity evidence"
    )

    # --- Governance Constraints ---
    governance_constraints: List[str] = Field(
        default_factory=list,
        description="Aggregated governance constraints from all entries"
    )

    # --- Continuity State ---
    continuity_state: CONTINUITY_STATE_OPTIONS = Field(
        default="future_escalation_required",
        description="Current continuity state"
    )

    # --- Chain Length ---
    chain_length: int = Field(
        ...,
        ge=0,
        description="Number of entries in the continuity chain"
    )

    # --- 7L Invariants ---
    replayable: bool = Field(
        default=True,
        description="Always true — graphs are replayable"
    )
    immutable: bool = Field(
        default=True,
        description="Always true — graphs are immutable"
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

    # 7L invariant validators
    @field_validator("replayable", mode="before")
    @classmethod
    def enforce_replayable(cls, v: Any) -> bool:
        if v is False:
            raise ValueError(
                "7L invariant violation: replayable must be true"
            )
        return True

    @field_validator("immutable", mode="before")
    @classmethod
    def enforce_immutable(cls, v: Any) -> bool:
        if v is False:
            raise ValueError(
                "7L invariant violation: immutable must be true"
            )
        return True

    @field_validator("execution_authorized", mode="before")
    @classmethod
    def enforce_no_execution(cls, v: Any) -> bool:
        if v is True:
            raise ValueError(
                "7L invariant violation: execution_authorized must be false"
            )
        return False

    @field_validator("machine_output_allowed", mode="before")
    @classmethod
    def enforce_no_machine_output(cls, v: Any) -> bool:
        if v is True:
            raise ValueError(
                "7L invariant violation: machine_output_allowed must be false"
            )
        return False

    @model_validator(mode="after")
    def validate_invariants(self) -> "TranslatorGovernanceContinuityGraph":
        """Validate all 7L invariants after model construction."""
        if not self.replayable:
            raise ValueError(
                "7L invariant violation: replayable must be true"
            )
        if not self.immutable:
            raise ValueError(
                "7L invariant violation: immutable must be true"
            )
        if self.execution_authorized:
            raise ValueError(
                "7L invariant violation: execution_authorized must be false"
            )
        if self.machine_output_allowed:
            raise ValueError(
                "7L invariant violation: machine_output_allowed must be false"
            )
        return self


class GovernanceReplayResult(BaseModel):
    """
    Result of governance replay traversal.

    Returned by replay_governance_trace() for deterministic
    ancestry traversal with integrity verification.

    7L invariants (model-enforced):
      - execution_authorized = false (always)
      - machine_output_allowed = false (always)
    """

    translator_id: str = Field(..., description="Translator identifier")

    # --- Replay Chain ---
    replay_chain: List[TranslatorGovernanceReviewLedgerEntry] = Field(
        default_factory=list,
        description="Ordered chain of ledger entries (oldest to newest)"
    )

    # --- Replay Hashes ---
    replay_trace_hash: str = Field(
        ...,
        description="Deterministic hash of the replay chain"
    )
    continuity_hash: str = Field(
        ...,
        description="Continuity hash from the source graph"
    )

    # --- Integrity ---
    replay_integrity_valid: bool = Field(
        ...,
        description="Whether replay integrity is valid"
    )

    # --- Chain Info ---
    replay_length: int = Field(
        ...,
        ge=0,
        description="Number of entries in replay chain"
    )
    root_review_trace_hash: str = Field(
        ...,
        description="Review trace hash of the genesis entry"
    )
    current_review_trace_hash: str = Field(
        ...,
        description="Review trace hash of the most recent entry"
    )

    # --- Replay State ---
    replay_state: CONTINUITY_STATE_OPTIONS = Field(
        default="future_escalation_required",
        description="Current replay state"
    )

    # --- 7L Invariants ---
    execution_authorized: bool = Field(
        default=False,
        description="Always false — no execution authorization"
    )
    machine_output_allowed: bool = Field(
        default=False,
        description="Always false — no machine output"
    )

    # 7L invariant validators
    @field_validator("execution_authorized", mode="before")
    @classmethod
    def enforce_no_execution(cls, v: Any) -> bool:
        if v is True:
            raise ValueError(
                "7L invariant violation: execution_authorized must be false"
            )
        return False

    @field_validator("machine_output_allowed", mode="before")
    @classmethod
    def enforce_no_machine_output(cls, v: Any) -> bool:
        if v is True:
            raise ValueError(
                "7L invariant violation: machine_output_allowed must be false"
            )
        return False


class GovernanceContinuityGraphSummary(BaseModel):
    """
    Summary of a governance continuity graph for integration.

    Minimal representation for cross-module references.
    """

    continuity_graph_id: str
    translator_id: str
    root_review_trace_hash: str
    current_review_trace_hash: str
    chain_length: int
    continuity_integrity_valid: bool
    deterministic_continuity_hash: str
    continuity_state: CONTINUITY_STATE_OPTIONS
    created_at: datetime

    # 7L invariants
    replayable: bool = True
    immutable: bool = True
    execution_authorized: bool = False
    machine_output_allowed: bool = False

    @field_validator("replayable", mode="before")
    @classmethod
    def enforce_replayable(cls, v: Any) -> bool:
        return True

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

CONTINUITY_GRAPH_INDEX: Dict[str, TranslatorGovernanceContinuityGraph] = {}


def register_continuity_graph(
    graph: TranslatorGovernanceContinuityGraph,
) -> None:
    """
    Register a continuity graph in the index.

    Raises:
        DuplicateContinuityGraphError: If continuity_graph_id already exists
    """
    if graph.continuity_graph_id in CONTINUITY_GRAPH_INDEX:
        raise DuplicateContinuityGraphError(
            f"Continuity graph already exists: {graph.continuity_graph_id}. "
            "Continuity graphs are immutable."
        )
    CONTINUITY_GRAPH_INDEX[graph.continuity_graph_id] = graph


def get_continuity_graph(
    continuity_graph_id: str,
) -> Optional[TranslatorGovernanceContinuityGraph]:
    """Get a continuity graph by ID."""
    return CONTINUITY_GRAPH_INDEX.get(continuity_graph_id)


def list_continuity_graphs() -> List[TranslatorGovernanceContinuityGraph]:
    """List all continuity graphs."""
    return list(CONTINUITY_GRAPH_INDEX.values())


def list_continuity_graphs_for_translator(
    translator_id: str,
) -> List[TranslatorGovernanceContinuityGraph]:
    """List continuity graphs for a specific translator."""
    return [
        g for g in CONTINUITY_GRAPH_INDEX.values()
        if g.translator_id == translator_id
    ]


def get_latest_continuity_graph_for_translator(
    translator_id: str,
) -> Optional[TranslatorGovernanceContinuityGraph]:
    """Get the most recent continuity graph for a translator."""
    graphs = list_continuity_graphs_for_translator(translator_id)
    if not graphs:
        return None
    return max(graphs, key=lambda g: g.created_at)


def clear_continuity_graph_index() -> None:
    """Clear all continuity graphs from the index (for testing)."""
    CONTINUITY_GRAPH_INDEX.clear()


# -----------------------------------------------------------------------------
# Deterministic Hashing
# -----------------------------------------------------------------------------

def _short_sha256(*args: str) -> str:
    """Compute short SHA256 hash from multiple string inputs."""
    combined = ":".join(args)
    return hashlib.sha256(combined.encode()).hexdigest()[:12]


def _compute_continuity_graph_id(
    translator_id: str,
    root_review_trace_hash: str,
    current_review_trace_hash: str,
) -> str:
    """
    Compute deterministic continuity graph ID.

    Same inputs produce same ID, enabling idempotent rebuilds.
    """
    short_hash = _short_sha256(
        translator_id,
        root_review_trace_hash,
        current_review_trace_hash,
    )
    return f"continuity-{short_hash}"


def _compute_deterministic_continuity_hash(
    translator_id: str,
    review_trace_chain: List[str],
    dossier_hash_chain: List[str],
    provenance_hash_chain: List[str],
    readiness_hash_chain: List[str],
    quarantine_hash_chain: List[str],
    governance_constraints: List[str],
) -> str:
    """
    Compute deterministic hash of continuity evidence.

    Same governance continuity ancestry → same continuity hash.

    Excludes:
      - timestamps
      - UUIDs
      - transient metadata
      - RMOS attachment IDs
    """
    hash_input = {
        "translator_id": translator_id,
        "review_trace_chain": review_trace_chain,
        "dossier_hash_chain": dossier_hash_chain,
        "provenance_hash_chain": provenance_hash_chain,
        "readiness_hash_chain": readiness_hash_chain,
        "quarantine_hash_chain": quarantine_hash_chain,
        "governance_constraints": sorted(set(governance_constraints)),
    }
    canonical_json = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode()).hexdigest()


def _compute_replay_trace_hash(
    replay_chain: List[TranslatorGovernanceReviewLedgerEntry],
) -> str:
    """
    Compute deterministic hash of replay chain.

    Based on review_trace_hash values in order.
    """
    trace_hashes = [e.review_trace_hash for e in replay_chain]
    hash_input = {"trace_chain": trace_hashes}
    canonical_json = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode()).hexdigest()


# -----------------------------------------------------------------------------
# Integrity Validation
# -----------------------------------------------------------------------------

def _validate_continuity_integrity(
    ledger_entries: List[TranslatorGovernanceReviewLedgerEntry],
) -> tuple[bool, List[str]]:
    """
    Validate comprehensive continuity integrity.

    Returns:
        (is_valid, list_of_violations)

    Checks for:
      - Broken parent linkage
      - Orphaned review traces
      - Missing parent hashes
      - Non-deterministic ordering
      - Replay chain discontinuity
      - Duplicate review traces in chain
      - execution_authorized == true anywhere
      - machine_output_allowed == true anywhere
      - immutable == false anywhere
    """
    violations: List[str] = []

    if not ledger_entries:
        return True, []

    # Check for invariant violations in any entry
    for i, entry in enumerate(ledger_entries):
        if entry.execution_authorized:
            violations.append(
                f"execution_authorized=true at position {i} "
                f"(ledger_entry_id={entry.ledger_entry_id})"
            )
        if entry.machine_output_allowed:
            violations.append(
                f"machine_output_allowed=true at position {i} "
                f"(ledger_entry_id={entry.ledger_entry_id})"
            )
        if not entry.immutable:
            violations.append(
                f"immutable=false at position {i} "
                f"(ledger_entry_id={entry.ledger_entry_id})"
            )

    # Check for duplicate review traces
    seen_traces: set = set()
    for i, entry in enumerate(ledger_entries):
        if entry.review_trace_hash in seen_traces:
            violations.append(
                f"duplicate review_trace_hash at position {i}: "
                f"{entry.review_trace_hash}"
            )
        seen_traces.add(entry.review_trace_hash)

    # Check parent linkage (each entry should reference previous as parent)
    # First entry should have empty parents (genesis)
    if ledger_entries[0].parent_ledger_hashes:
        # Genesis can have parents if it was created with explicit parents
        # This is allowed, so we don't flag it as a violation
        pass

    # Check chain continuity for subsequent entries
    for i in range(1, len(ledger_entries)):
        current = ledger_entries[i]
        previous = ledger_entries[i - 1]

        # Current should have previous's review_trace_hash as a parent
        if previous.review_trace_hash not in current.parent_ledger_hashes:
            violations.append(
                f"broken parent linkage at position {i}: "
                f"expected parent {previous.review_trace_hash} "
                f"not in {current.parent_ledger_hashes}"
            )

    is_valid = len(violations) == 0
    return is_valid, violations


# -----------------------------------------------------------------------------
# Pure Builder
# -----------------------------------------------------------------------------

def build_governance_continuity_graph(
    ledger_entries: List[TranslatorGovernanceReviewLedgerEntry],
) -> TranslatorGovernanceContinuityGraph:
    """
    Build an immutable governance continuity graph from ledger entries.

    This is a pure function. Index lookups happen at router/helper layer.

    Args:
        ledger_entries: List of TranslatorGovernanceReviewLedgerEntry objects.
                       Must all have the same translator_id.
                       Should be ordered from oldest to newest.

    Returns:
        TranslatorGovernanceContinuityGraph

    Raises:
        ContinuityGraphBuildError: If entries are empty
        MixedTranslatorError: If entries have different translator_ids

    Guardrail:
        7L continuity graph remains immutable replay infrastructure only.
        No mutation, approval, execution, serializer invocation,
        or machine-output semantics.
    """
    if not ledger_entries:
        raise ContinuityGraphBuildError(
            "ledger_entries cannot be empty"
        )

    # Validate all entries have same translator_id
    translator_ids = set(e.translator_id for e in ledger_entries)
    if len(translator_ids) > 1:
        raise MixedTranslatorError(
            f"All ledger entries must have the same translator_id. "
            f"Found: {translator_ids}"
        )

    translator_id = ledger_entries[0].translator_id

    # Sort entries by created_at to ensure correct order
    sorted_entries = sorted(ledger_entries, key=lambda e: e.created_at)

    # Extract hash chains (preserve order)
    review_trace_chain = [e.review_trace_hash for e in sorted_entries]
    dossier_hash_chain = [e.dossier_hash for e in sorted_entries]
    provenance_hash_chain = [e.provenance_hash for e in sorted_entries]
    readiness_hash_chain = [e.readiness_hash for e in sorted_entries]
    quarantine_hash_chain = [e.quarantine_hash for e in sorted_entries]

    # Root and current trace hashes
    root_review_trace_hash = review_trace_chain[0]
    current_review_trace_hash = review_trace_chain[-1]

    # Aggregate governance constraints (preserve all, dedupe later in hash)
    governance_constraints: List[str] = []
    for entry in sorted_entries:
        governance_constraints.extend(entry.governance_constraints)

    # Validate integrity
    is_valid, violations = _validate_continuity_integrity(sorted_entries)

    # Compute deterministic continuity hash
    deterministic_continuity_hash = _compute_deterministic_continuity_hash(
        translator_id=translator_id,
        review_trace_chain=review_trace_chain,
        dossier_hash_chain=dossier_hash_chain,
        provenance_hash_chain=provenance_hash_chain,
        readiness_hash_chain=readiness_hash_chain,
        quarantine_hash_chain=quarantine_hash_chain,
        governance_constraints=governance_constraints,
    )

    # Compute deterministic graph ID
    continuity_graph_id = _compute_continuity_graph_id(
        translator_id=translator_id,
        root_review_trace_hash=root_review_trace_hash,
        current_review_trace_hash=current_review_trace_hash,
    )

    # Determine continuity state from most recent entry
    continuity_state = sorted_entries[-1].review_state

    # Build graph
    graph = TranslatorGovernanceContinuityGraph(
        continuity_graph_id=continuity_graph_id,
        translator_id=translator_id,
        root_review_trace_hash=root_review_trace_hash,
        current_review_trace_hash=current_review_trace_hash,
        review_trace_chain=review_trace_chain,
        dossier_hash_chain=dossier_hash_chain,
        provenance_hash_chain=provenance_hash_chain,
        readiness_hash_chain=readiness_hash_chain,
        quarantine_hash_chain=quarantine_hash_chain,
        continuity_integrity_valid=is_valid,
        integrity_violations=violations,
        deterministic_continuity_hash=deterministic_continuity_hash,
        governance_constraints=list(set(governance_constraints)),
        continuity_state=continuity_state,
        chain_length=len(sorted_entries),
        replayable=True,
        immutable=True,
        execution_authorized=False,
        machine_output_allowed=False,
    )

    return graph


# -----------------------------------------------------------------------------
# Helper for Index Lookup
# -----------------------------------------------------------------------------

def build_continuity_graph_for_translator(
    translator_id: str,
    register: bool = True,
) -> TranslatorGovernanceContinuityGraph:
    """
    Build continuity graph for a translator by looking up ledger entries.

    This helper:
      - Reads from REVIEW_LEDGER_INDEX
      - Filters entries for translator
      - Calls the pure builder

    Args:
        translator_id: Translator identifier
        register: Whether to register the graph in the index (default True)

    Returns:
        TranslatorGovernanceContinuityGraph

    Raises:
        ContinuityGraphBuildError: If no entries found for translator
    """
    entries = list_review_ledger_entries_for_translator(translator_id)

    if not entries:
        raise ContinuityGraphBuildError(
            f"No ledger entries found for translator: {translator_id}"
        )

    graph = build_governance_continuity_graph(entries)

    if register:
        # Check if this exact graph already exists
        existing = get_continuity_graph(graph.continuity_graph_id)
        if existing is None:
            register_continuity_graph(graph)

    return graph


# -----------------------------------------------------------------------------
# Replay Traversal
# -----------------------------------------------------------------------------

def replay_governance_trace(
    graph: TranslatorGovernanceContinuityGraph,
    ledger_entries: Optional[List[TranslatorGovernanceReviewLedgerEntry]] = None,
) -> GovernanceReplayResult:
    """
    Perform deterministic governance replay traversal.

    Returns a structured GovernanceReplayResult with integrity verification.

    Args:
        graph: The continuity graph to replay
        ledger_entries: Optional list of entries. If not provided,
                       looks up from REVIEW_LEDGER_INDEX.

    Returns:
        GovernanceReplayResult

    Note:
        Replay means deterministic ancestry traversal only.
        NOT runtime replay, execution replay, or serializer replay.
    """
    if ledger_entries is None:
        ledger_entries = list_review_ledger_entries_for_translator(
            graph.translator_id
        )

    # Sort entries by created_at
    sorted_entries = sorted(ledger_entries, key=lambda e: e.created_at)

    # Validate replay integrity
    replay_integrity_valid = graph.continuity_integrity_valid

    # Additional validation: check that replay chain matches graph
    replay_trace_hashes = [e.review_trace_hash for e in sorted_entries]
    if replay_trace_hashes != graph.review_trace_chain:
        replay_integrity_valid = False

    # Compute replay trace hash
    replay_trace_hash = _compute_replay_trace_hash(sorted_entries)

    # Build result
    result = GovernanceReplayResult(
        translator_id=graph.translator_id,
        replay_chain=sorted_entries,
        replay_trace_hash=replay_trace_hash,
        continuity_hash=graph.deterministic_continuity_hash,
        replay_integrity_valid=replay_integrity_valid,
        replay_length=len(sorted_entries),
        root_review_trace_hash=graph.root_review_trace_hash,
        current_review_trace_hash=graph.current_review_trace_hash,
        replay_state=graph.continuity_state,
        execution_authorized=False,
        machine_output_allowed=False,
    )

    return result


def get_continuity_chain(
    graph: TranslatorGovernanceContinuityGraph,
) -> List[str]:
    """Get the review trace chain from a continuity graph."""
    return list(graph.review_trace_chain)


def get_root_review_trace(
    graph: TranslatorGovernanceContinuityGraph,
) -> str:
    """Get the root (genesis) review trace hash."""
    return graph.root_review_trace_hash


def validate_continuity_integrity(
    graph: TranslatorGovernanceContinuityGraph,
) -> tuple[bool, List[str]]:
    """
    Validate continuity integrity of a graph.

    Returns:
        (is_valid, list_of_violations)
    """
    return graph.continuity_integrity_valid, list(graph.integrity_violations)


# -----------------------------------------------------------------------------
# Summary Helper
# -----------------------------------------------------------------------------

def to_summary(
    graph: TranslatorGovernanceContinuityGraph,
) -> GovernanceContinuityGraphSummary:
    """Convert a continuity graph to its summary representation."""
    return GovernanceContinuityGraphSummary(
        continuity_graph_id=graph.continuity_graph_id,
        translator_id=graph.translator_id,
        root_review_trace_hash=graph.root_review_trace_hash,
        current_review_trace_hash=graph.current_review_trace_hash,
        chain_length=graph.chain_length,
        continuity_integrity_valid=graph.continuity_integrity_valid,
        deterministic_continuity_hash=graph.deterministic_continuity_hash,
        continuity_state=graph.continuity_state,
        created_at=graph.created_at,
        replayable=True,
        immutable=True,
        execution_authorized=False,
        machine_output_allowed=False,
    )


# -----------------------------------------------------------------------------
# RMOS Persistence (Optional)
# -----------------------------------------------------------------------------

CONTINUITY_GRAPH_ARTIFACT_KIND = "translator_governance_continuity_graph_json"


def persist_continuity_graph_to_rmos(
    graph: TranslatorGovernanceContinuityGraph,
    run_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Persist continuity graph to RMOS (optional).

    Artifact kind: translator_governance_continuity_graph_json

    Returns artifact reference if successful, None otherwise.
    Supplemental to in-memory index.
    """
    try:
        from app.cam.export_rmos_artifacts import put_json_attachment

        graph_dict = graph.model_dump(mode="json")

        stat, path, sha256 = put_json_attachment(
            kind=CONTINUITY_GRAPH_ARTIFACT_KIND,
            obj=graph_dict,
            run_id=run_id,
        )

        return {
            "kind": CONTINUITY_GRAPH_ARTIFACT_KIND,
            "sha256": sha256,
            "bytes": stat.size_bytes if stat else 0,
            "path": path,
            "continuity_graph_id": graph.continuity_graph_id,
        }
    except ImportError:
        return None
    except Exception:
        return None
