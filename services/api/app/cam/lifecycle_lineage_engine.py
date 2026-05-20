"""
Lifecycle Lineage Engine

CAM Dev Order 7R: Lineage verification and replay infrastructure.

Provides:
  - Parent lineage verification
  - Replay continuity validation
  - Deterministic ancestry reconstruction
  - Lifecycle integrity evaluation
  - Checkpoint continuity verification

7R invariants:
  - Replay = integrity verification + determinism check + timeline view
  - Replay does NOT re-execute operations
  - No machine output generation
  - No execution authorization
  - Immutable once recorded
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import hashlib
import json

from .cam_lifecycle_audit_ledger import (
    CAMLifecycleAuditLedgerEntry,
    AuditCheckpointSummary,
    LIFECYCLE_AUDIT_LEDGER_INDEX,
    register_audit_entry,
)


class LineageIntegrityStatus(str, Enum):
    """Integrity status for lineage verification."""
    VALID = "valid"
    BROKEN_CHAIN = "broken_chain"
    HASH_MISMATCH = "hash_mismatch"
    MISSING_PARENT = "missing_parent"
    ORPHANED = "orphaned"
    UNKNOWN = "unknown"


class ReplayContinuityStatus(str, Enum):
    """Continuity status for replay verification."""
    CONTINUOUS = "continuous"
    GAP_DETECTED = "gap_detected"
    DIVERGENT = "divergent"
    INCOMPLETE = "incomplete"


@dataclass
class LineageVerificationResult:
    """Result of lineage verification."""
    entry_id: str
    status: LineageIntegrityStatus
    parent_verified: bool
    chain_depth: int
    broken_at: Optional[str] = None
    reason: Optional[str] = None
    verified_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


@dataclass
class ReplayContinuityResult:
    """Result of replay continuity verification."""
    export_id: str
    status: ReplayContinuityStatus
    entries_verified: int
    entries_total: int
    gaps: List[Tuple[str, str]] = field(default_factory=list)
    divergence_point: Optional[str] = None
    timeline: List[str] = field(default_factory=list)
    verified_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


@dataclass
class AncestryReconstruction:
    """Reconstructed ancestry chain for an entry."""
    entry_id: str
    ancestry_chain: List[str]
    root_entry_id: Optional[str] = None
    chain_length: int = 0
    complete: bool = False
    missing_links: List[str] = field(default_factory=list)
    reconstructed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


@dataclass
class CheckpointContinuityResult:
    """Result of checkpoint continuity verification."""
    checkpoint_pathway: str
    entries_with_checkpoint: int
    entries_without_checkpoint: int
    continuity_maintained: bool
    first_checkpoint_entry: Optional[str] = None
    last_checkpoint_entry: Optional[str] = None


def build_lifecycle_audit_hash(
    lifecycle_report_hash: str,
    policy_evaluation_hash: str,
    operation_capability_hash: str,
    checkpoint_evaluation_hash: Optional[str] = None,
    parent_hashes: Optional[List[str]] = None,
) -> str:
    """
    Build deterministic hash for lifecycle audit entry.

    Hash incorporates:
      - Lifecycle report hash
      - Policy evaluation hash
      - Operation capability hash
      - Optional checkpoint evaluation hash
      - Parent hash chain for continuity

    Returns: SHA-256 hex digest (64 chars)
    """
    components = [
        f"lifecycle:{lifecycle_report_hash}",
        f"policy:{policy_evaluation_hash}",
        f"capability:{operation_capability_hash}",
    ]

    if checkpoint_evaluation_hash:
        components.append(f"checkpoint:{checkpoint_evaluation_hash}")

    if parent_hashes:
        for i, ph in enumerate(parent_hashes):
            components.append(f"parent_{i}:{ph}")

    canonical = "|".join(sorted(components))
    return hashlib.sha256(canonical.encode()).hexdigest()


def verify_lifecycle_continuity(
    entry_id: str,
    ledger_index: Optional[Dict[str, CAMLifecycleAuditLedgerEntry]] = None,
) -> LineageVerificationResult:
    """
    Verify lineage continuity for a specific entry.

    Checks:
      - Entry exists in ledger
      - Parent hashes point to valid entries
      - Hash chain is unbroken
      - No orphaned references

    Args:
        entry_id: ID of entry to verify (ledger_entry_id)
        ledger_index: Optional ledger index (defaults to global)

    Returns: LineageVerificationResult with status and details
    """
    index = ledger_index or LIFECYCLE_AUDIT_LEDGER_INDEX

    if entry_id not in index:
        return LineageVerificationResult(
            entry_id=entry_id,
            status=LineageIntegrityStatus.UNKNOWN,
            parent_verified=False,
            chain_depth=0,
            reason=f"Entry {entry_id} not found in ledger",
        )

    entry = index[entry_id]

    if not entry.parent_lifecycle_hashes:
        return LineageVerificationResult(
            entry_id=entry_id,
            status=LineageIntegrityStatus.VALID,
            parent_verified=True,
            chain_depth=1,
            reason="Root entry with no parents",
        )

    chain_depth = 1
    current_parents = entry.parent_lifecycle_hashes
    verified_parents = []

    for parent_hash in current_parents:
        parent_found = False
        for pid, pentry in index.items():
            if pentry.deterministic_hash == parent_hash:
                parent_found = True
                verified_parents.append(pid)
                chain_depth += 1
                break

        if not parent_found:
            return LineageVerificationResult(
                entry_id=entry_id,
                status=LineageIntegrityStatus.MISSING_PARENT,
                parent_verified=False,
                chain_depth=chain_depth,
                broken_at=parent_hash,
                reason=f"Parent hash {parent_hash[:16]}... not found in ledger",
            )

    return LineageVerificationResult(
        entry_id=entry_id,
        status=LineageIntegrityStatus.VALID,
        parent_verified=True,
        chain_depth=chain_depth,
        reason=f"All {len(verified_parents)} parent(s) verified",
    )


def build_lifecycle_replay(
    export_id: str,
    ledger_index: Optional[Dict[str, CAMLifecycleAuditLedgerEntry]] = None,
) -> ReplayContinuityResult:
    """
    Build replay timeline for an export.

    Replay is integrity verification + determinism check + timeline view.
    It does NOT re-execute operations.

    Args:
        export_id: Export ID to replay lifecycle for
        ledger_index: Optional ledger index (defaults to global)

    Returns: ReplayContinuityResult with timeline and status
    """
    index = ledger_index or LIFECYCLE_AUDIT_LEDGER_INDEX

    export_entries = [
        (eid, entry) for eid, entry in index.items()
        if entry.export_id == export_id
    ]

    if not export_entries:
        return ReplayContinuityResult(
            export_id=export_id,
            status=ReplayContinuityStatus.INCOMPLETE,
            entries_verified=0,
            entries_total=0,
            timeline=[],
        )

    export_entries.sort(key=lambda x: x[1].created_at)

    timeline = [eid for eid, _ in export_entries]
    gaps = []

    for i in range(1, len(export_entries)):
        prev_id, prev_entry = export_entries[i - 1]
        curr_id, curr_entry = export_entries[i]

        if curr_entry.parent_lifecycle_hashes:
            if prev_entry.deterministic_hash not in curr_entry.parent_lifecycle_hashes:
                gaps.append((prev_id, curr_id))

    if gaps:
        return ReplayContinuityResult(
            export_id=export_id,
            status=ReplayContinuityStatus.GAP_DETECTED,
            entries_verified=len(export_entries) - len(gaps),
            entries_total=len(export_entries),
            gaps=gaps,
            timeline=timeline,
        )

    return ReplayContinuityResult(
        export_id=export_id,
        status=ReplayContinuityStatus.CONTINUOUS,
        entries_verified=len(export_entries),
        entries_total=len(export_entries),
        timeline=timeline,
    )


def reconstruct_ancestry(
    entry_id: str,
    max_depth: int = 100,
    ledger_index: Optional[Dict[str, CAMLifecycleAuditLedgerEntry]] = None,
) -> AncestryReconstruction:
    """
    Reconstruct full ancestry chain for an entry.

    Walks parent hash chain backward to find root.

    Args:
        entry_id: Starting entry ID (ledger_entry_id)
        max_depth: Maximum chain depth to traverse
        ledger_index: Optional ledger index (defaults to global)

    Returns: AncestryReconstruction with full chain
    """
    index = ledger_index or LIFECYCLE_AUDIT_LEDGER_INDEX

    if entry_id not in index:
        return AncestryReconstruction(
            entry_id=entry_id,
            ancestry_chain=[],
            complete=False,
            missing_links=[entry_id],
        )

    ancestry_chain = [entry_id]
    missing_links = []
    current_entry = index[entry_id]
    depth = 0

    while depth < max_depth:
        if not current_entry.parent_lifecycle_hashes:
            break

        parent_hash = current_entry.parent_lifecycle_hashes[0]
        parent_found = False

        for pid, pentry in index.items():
            if pentry.deterministic_hash == parent_hash:
                ancestry_chain.append(pid)
                current_entry = pentry
                parent_found = True
                break

        if not parent_found:
            missing_links.append(parent_hash)
            break

        depth += 1

    root_entry_id = ancestry_chain[-1] if ancestry_chain else None
    complete = len(missing_links) == 0

    return AncestryReconstruction(
        entry_id=entry_id,
        ancestry_chain=ancestry_chain,
        root_entry_id=root_entry_id,
        chain_length=len(ancestry_chain),
        complete=complete,
        missing_links=missing_links,
    )


def append_checkpoint_to_lifecycle(
    entry_id: str,
    checkpoint_pathway: str,
    checkpoint_severity: str,
    checkpoint_hash: str,
    ledger_index: Optional[Dict[str, CAMLifecycleAuditLedgerEntry]] = None,
) -> bool:
    """
    Append checkpoint reference to an existing lifecycle entry.

    NOTE: This creates a new entry with checkpoint, preserving immutability
    of original entry. The new entry references the original as parent.

    Args:
        entry_id: Entry to augment with checkpoint (ledger_entry_id)
        checkpoint_pathway: Checkpoint pathway (e.g., "translator_dispatch:dxf_r12")
        checkpoint_severity: red/yellow/green
        checkpoint_hash: Hash of checkpoint evaluation
        ledger_index: Optional ledger index (defaults to global)

    Returns: True if successful, False if entry not found
    """
    index = ledger_index or LIFECYCLE_AUDIT_LEDGER_INDEX

    if entry_id not in index:
        return False

    original = index[entry_id]

    checkpoint_summary = AuditCheckpointSummary(
        checkpoint_gate=checkpoint_severity.lower(),
        checkpoint_passed=checkpoint_severity.lower() != "red",
        blocking_issues=[],
        warnings=[],
        enforcement_hash=checkpoint_hash,
        pathway=checkpoint_pathway,
    )

    continuity_valid = checkpoint_severity.lower() != "red"

    new_entry = CAMLifecycleAuditLedgerEntry(
        export_id=original.export_id,
        operation=original.operation,
        translator_id=original.translator_id,
        lifecycle_gate=original.lifecycle_gate,
        entry_state=original.entry_state,
        runtime_pathway=checkpoint_pathway,
        runtime_enforcement_hash=checkpoint_hash,
        checkpoint_summary=checkpoint_summary,
        parent_lifecycle_hashes=[original.deterministic_hash],
        continuity_integrity_valid=continuity_valid,
        blocking_issues=original.blocking_issues.copy(),
        warnings=original.warnings.copy(),
        policy_snapshot=original.policy_snapshot.copy(),
        metadata={
            "dev_order": "7R",
            "audit_type": "checkpoint_append",
            "original_entry_id": entry_id,
        },
    )

    new_entry.deterministic_hash = new_entry.compute_deterministic_hash()
    register_audit_entry(new_entry)

    return True


def is_valid_lifecycle_transition(
    from_entry_id: str,
    to_entry_id: str,
    ledger_index: Optional[Dict[str, CAMLifecycleAuditLedgerEntry]] = None,
) -> Tuple[bool, str]:
    """
    Check if transition between two entries is valid.

    Valid transitions:
      - to_entry references from_entry in parent_lifecycle_hashes
      - Both entries exist in ledger
      - to_entry created_at >= from_entry created_at

    Args:
        from_entry_id: Source entry ID (ledger_entry_id)
        to_entry_id: Target entry ID (ledger_entry_id)
        ledger_index: Optional ledger index (defaults to global)

    Returns: (is_valid, reason)
    """
    index = ledger_index or LIFECYCLE_AUDIT_LEDGER_INDEX

    if from_entry_id not in index:
        return False, f"Source entry {from_entry_id} not found"

    if to_entry_id not in index:
        return False, f"Target entry {to_entry_id} not found"

    from_entry = index[from_entry_id]
    to_entry = index[to_entry_id]

    if to_entry.created_at < from_entry.created_at:
        return False, "Target entry recorded before source entry"

    if not to_entry.parent_lifecycle_hashes:
        return False, "Target entry has no parent references"

    if from_entry.deterministic_hash not in to_entry.parent_lifecycle_hashes:
        return False, "Target entry does not reference source entry as parent"

    return True, "Valid transition: parent hash chain verified"


def verify_checkpoint_continuity(
    checkpoint_pathway: str,
    ledger_index: Optional[Dict[str, CAMLifecycleAuditLedgerEntry]] = None,
) -> CheckpointContinuityResult:
    """
    Verify checkpoint continuity across all entries for a pathway.

    Args:
        checkpoint_pathway: Pathway to verify (e.g., "translator_dispatch:dxf_r12")
        ledger_index: Optional ledger index (defaults to global)

    Returns: CheckpointContinuityResult with continuity status
    """
    index = ledger_index or LIFECYCLE_AUDIT_LEDGER_INDEX

    entries_with = []
    entries_without = []

    for eid, entry in index.items():
        if entry.checkpoint_summary is not None:
            entries_with.append((eid, entry.created_at))
        else:
            entries_without.append((eid, entry.created_at))

    entries_with.sort(key=lambda x: x[1])

    first_entry = entries_with[0][0] if entries_with else None
    last_entry = entries_with[-1][0] if entries_with else None

    continuity_maintained = len(entries_without) == 0 or len(entries_with) == 0

    return CheckpointContinuityResult(
        checkpoint_pathway=checkpoint_pathway,
        entries_with_checkpoint=len(entries_with),
        entries_without_checkpoint=len(entries_without),
        continuity_maintained=continuity_maintained,
        first_checkpoint_entry=first_entry,
        last_checkpoint_entry=last_entry,
    )


def generate_lineage_report(
    ledger_index: Optional[Dict[str, CAMLifecycleAuditLedgerEntry]] = None,
) -> Dict[str, Any]:
    """
    Generate comprehensive lineage report for all entries.

    Returns summary statistics and integrity status.
    """
    index = ledger_index or LIFECYCLE_AUDIT_LEDGER_INDEX

    total_entries = len(index)
    valid_entries = 0
    broken_chains = 0
    orphaned_entries = 0
    root_entries = 0

    for eid in index:
        result = verify_lifecycle_continuity(eid, index)
        if result.status == LineageIntegrityStatus.VALID:
            valid_entries += 1
            if result.chain_depth == 1:
                root_entries += 1
        elif result.status == LineageIntegrityStatus.BROKEN_CHAIN:
            broken_chains += 1
        elif result.status == LineageIntegrityStatus.ORPHANED:
            orphaned_entries += 1

    return {
        "total_entries": total_entries,
        "valid_entries": valid_entries,
        "broken_chains": broken_chains,
        "orphaned_entries": orphaned_entries,
        "root_entries": root_entries,
        "integrity_percentage": (valid_entries / total_entries * 100) if total_entries > 0 else 100.0,
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
