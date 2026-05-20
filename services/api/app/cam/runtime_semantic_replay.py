"""
Runtime Semantic Replay

CAM Dev Order 7O: Deterministic replay continuity for runtime semantic
consumption lineage.

This module provides:
  - RuntimeSemanticReplayResult model
  - Replay continuity verification
  - Deterministic chain replay
  - Integrity validation

Replay semantics:
  - Fetch ordered ledger entries for a consumer
  - Verify parent hash continuity
  - Recompute/revalidate replay chain hash
  - Report drift progression
  - Report escalation progression
  - Confirm invariants remain false

Does NOT:
  - Re-run 7N validation
  - Execute runtime behavior

7O invariants (always enforced):
  - immutable = true
  - execution_authorized = false (implicit, not stored in replay)
  - machine_output_allowed = false (implicit, not stored in replay)

Guardrail:
  7O records how runtimes consume ontology over time. It does not permit
  runtime execution, ontology mutation, semantic reinterpretation, or
  machine authority.
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.cam.runtime_semantic_consumption_ledger import (
    RuntimeSemanticConsumptionLedgerEntry,
    list_ledger_entries_for_consumer,
)


# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------

class RuntimeSemanticReplayResult(BaseModel):
    """
    Result of replaying runtime semantic consumption lineage.

    7O invariants (model-enforced):
      - immutable = true (always)
    """

    replay_id: str = Field(..., description="Unique replay ID")
    consumer_id: str = Field(..., description="Consumer being replayed")
    replayed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Replay timestamp"
    )

    # Replay analysis
    replay_entry_count: int = Field(
        ...,
        ge=0,
        description="Number of entries replayed"
    )
    replay_chain_hash: str = Field(
        ...,
        description="Hash of the entire replay chain"
    )

    # Progression detection
    drift_progression_detected: bool = Field(
        default=False,
        description="Whether drift increased over time"
    )
    escalation_progression_detected: bool = Field(
        default=False,
        description="Whether escalation severity increased"
    )

    # Integrity
    replay_integrity_valid: bool = Field(
        ...,
        description="Whether lineage hash chain is valid"
    )
    broken_links: List[str] = Field(
        default_factory=list,
        description="Entry IDs with broken parent links"
    )

    # Invariant verification
    invariants_verified: bool = Field(
        default=True,
        description="Whether all invariants remain false"
    )
    invariant_violations: List[str] = Field(
        default_factory=list,
        description="Any invariant violations found"
    )

    # 7O invariant
    immutable: bool = Field(default=True)

    @field_validator("immutable", mode="before")
    @classmethod
    def enforce_immutable(cls, v: Any) -> bool:
        if v is False:
            raise ValueError("7O invariant violation: immutable must be true")
        return True


# -----------------------------------------------------------------------------
# Replay Index (in-memory)
# -----------------------------------------------------------------------------

_RUNTIME_SEMANTIC_REPLAY_INDEX: Dict[str, RuntimeSemanticReplayResult] = {}
_REPLAY_BY_CONSUMER: Dict[str, List[str]] = {}


def _rebuild_replay_consumer_index() -> None:
    """Rebuild consumer index for replays."""
    global _REPLAY_BY_CONSUMER
    _REPLAY_BY_CONSUMER = {}
    for replay_id, replay in _RUNTIME_SEMANTIC_REPLAY_INDEX.items():
        consumer_id = replay.consumer_id
        if consumer_id not in _REPLAY_BY_CONSUMER:
            _REPLAY_BY_CONSUMER[consumer_id] = []
        _REPLAY_BY_CONSUMER[consumer_id].append(replay_id)


def store_replay_result(result: RuntimeSemanticReplayResult) -> None:
    """Store a replay result."""
    _RUNTIME_SEMANTIC_REPLAY_INDEX[result.replay_id] = result
    _rebuild_replay_consumer_index()


def get_replay_result(replay_id: str) -> Optional[RuntimeSemanticReplayResult]:
    """Get a replay result by ID."""
    return _RUNTIME_SEMANTIC_REPLAY_INDEX.get(replay_id)


def list_replay_results() -> List[RuntimeSemanticReplayResult]:
    """List all replay results."""
    return list(_RUNTIME_SEMANTIC_REPLAY_INDEX.values())


def list_replays_for_consumer(
    consumer_id: str,
) -> List[RuntimeSemanticReplayResult]:
    """List replay results for a specific consumer."""
    replay_ids = _REPLAY_BY_CONSUMER.get(consumer_id, [])
    replays = [_RUNTIME_SEMANTIC_REPLAY_INDEX[rid] for rid in replay_ids]
    return sorted(replays, key=lambda r: r.replayed_at)


def get_latest_replay_for_consumer(
    consumer_id: str,
) -> Optional[RuntimeSemanticReplayResult]:
    """Get the most recent replay result for a consumer."""
    replays = list_replays_for_consumer(consumer_id)
    if not replays:
        return None
    return replays[-1]


def clear_replays_for_tests() -> None:
    """Clear all replay results. For testing only."""
    global _RUNTIME_SEMANTIC_REPLAY_INDEX, _REPLAY_BY_CONSUMER
    _RUNTIME_SEMANTIC_REPLAY_INDEX = {}
    _REPLAY_BY_CONSUMER = {}


# -----------------------------------------------------------------------------
# Lineage Verification
# -----------------------------------------------------------------------------

def verify_parent_hash_continuity(
    entries: List[RuntimeSemanticConsumptionLedgerEntry],
) -> tuple[bool, List[str]]:
    """
    Verify that parent hash links are valid.

    For each entry after the first, its parent_ledger_hashes should
    contain the deterministic_ledger_hash of the previous entry.

    Returns:
        (is_valid, broken_link_entry_ids)
    """
    if len(entries) <= 1:
        return True, []

    broken_links: List[str] = []

    for i in range(1, len(entries)):
        current = entries[i]
        previous = entries[i - 1]

        # Check if previous hash is in parent hashes
        if previous.deterministic_ledger_hash not in current.parent_ledger_hashes:
            broken_links.append(current.ledger_entry_id)

    return len(broken_links) == 0, broken_links


def verify_invariants(
    entries: List[RuntimeSemanticConsumptionLedgerEntry],
) -> tuple[bool, List[str]]:
    """
    Verify that all invariants remain false across entries.

    Checks:
      - immutable = true
      - execution_authorized = false
      - machine_output_allowed = false

    Returns:
        (all_valid, violation_descriptions)
    """
    violations: List[str] = []

    for entry in entries:
        if entry.immutable is not True:
            violations.append(
                f"Entry {entry.ledger_entry_id}: immutable is not True"
            )
        if entry.execution_authorized is not False:
            violations.append(
                f"Entry {entry.ledger_entry_id}: execution_authorized is not False"
            )
        if entry.machine_output_allowed is not False:
            violations.append(
                f"Entry {entry.ledger_entry_id}: machine_output_allowed is not False"
            )

    return len(violations) == 0, violations


# -----------------------------------------------------------------------------
# Progression Detection
# -----------------------------------------------------------------------------

def detect_drift_progression(
    entries: List[RuntimeSemanticConsumptionLedgerEntry],
) -> bool:
    """
    Detect if drift increased over time.

    Returns True if drift type count increased from first to last entry.
    """
    if len(entries) < 2:
        return False

    first_drift_count = len(entries[0].detected_drift_types)
    last_drift_count = len(entries[-1].detected_drift_types)

    return last_drift_count > first_drift_count


def detect_escalation_progression(
    entries: List[RuntimeSemanticConsumptionLedgerEntry],
) -> bool:
    """
    Detect if escalation severity increased over time.

    Returns True if escalation_recommended went from False to True.
    """
    if len(entries) < 2:
        return False

    first_escalation = entries[0].escalation_recommended
    last_escalation = entries[-1].escalation_recommended

    return (not first_escalation) and last_escalation


# -----------------------------------------------------------------------------
# Replay Chain Hash
# -----------------------------------------------------------------------------

def compute_replay_chain_hash(
    entries: List[RuntimeSemanticConsumptionLedgerEntry],
) -> str:
    """
    Compute a hash representing the entire replay chain.

    This is a hash of all entry hashes in order.
    """
    if not entries:
        return hashlib.sha256(b"empty_chain").hexdigest()

    chain_data = {
        "entry_hashes": [e.deterministic_ledger_hash for e in entries],
    }

    json_str = json.dumps(chain_data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(json_str.encode()).hexdigest()


# -----------------------------------------------------------------------------
# Replay Execution
# -----------------------------------------------------------------------------

def replay_runtime_semantic_lineage(
    consumer_id: str,
) -> RuntimeSemanticReplayResult:
    """
    Replay the runtime semantic consumption lineage for a consumer.

    This performs deterministic governance lineage replay:
      - Fetches ordered ledger entries for the consumer
      - Verifies parent hash continuity
      - Recomputes/revalidates replay chain hash
      - Reports drift progression
      - Reports escalation progression
      - Confirms invariants remain false

    Does NOT:
      - Re-run 7N validation
      - Execute runtime behavior

    Returns:
        RuntimeSemanticReplayResult (also stored in index)
    """
    # Get ordered entries
    entries = list_ledger_entries_for_consumer(consumer_id)

    # Verify parent hash continuity
    continuity_valid, broken_links = verify_parent_hash_continuity(entries)

    # Verify invariants
    invariants_valid, invariant_violations = verify_invariants(entries)

    # Detect progressions
    drift_progression = detect_drift_progression(entries)
    escalation_progression = detect_escalation_progression(entries)

    # Compute chain hash
    chain_hash = compute_replay_chain_hash(entries)

    # Overall integrity
    replay_integrity_valid = continuity_valid and invariants_valid

    # Create result
    result = RuntimeSemanticReplayResult(
        replay_id=f"replay-{uuid.uuid4().hex[:12]}",
        consumer_id=consumer_id,
        replay_entry_count=len(entries),
        replay_chain_hash=chain_hash,
        drift_progression_detected=drift_progression,
        escalation_progression_detected=escalation_progression,
        replay_integrity_valid=replay_integrity_valid,
        broken_links=broken_links,
        invariants_verified=invariants_valid,
        invariant_violations=invariant_violations,
        immutable=True,
    )

    # Store result
    store_replay_result(result)

    return result
