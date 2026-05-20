"""
CAM Lifecycle Audit Ledger

CAM Dev Order 7R: Lifecycle governance lineage and audit continuity.

This module provides:
  - CAMLifecycleAuditLedgerEntry model for audit records
  - AuditLedgerSummary for lightweight response embedding
  - Deterministic lifecycle hashing
  - Parent lineage verification
  - Replay continuity helpers
  - In-memory audit indexes

7R follows the 7O structural pattern but with narrower semantic scope:
  - 7O = runtime semantic consumption lineage
  - 7R = export lifecycle governance lineage

7R invariants (always enforced):
  - immutable = True
  - execution_authorized = False
  - machine_output_allowed = False

Guardrail:
  7R records and replays lifecycle governance lineage.
  It does not rerun lifecycle execution, invoke serializers,
  generate machine output, or authorize runtime behavior.
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

LifecycleGate = Literal["green", "yellow", "red"]

AuditEntryState = Literal[
    "validation_complete",
    "validation_failed",
    "checkpoint_blocked",
    "early_return",
]


# -----------------------------------------------------------------------------
# In-Memory Indexes
# -----------------------------------------------------------------------------

LIFECYCLE_AUDIT_LEDGER_INDEX: Dict[str, "CAMLifecycleAuditLedgerEntry"] = {}
LIFECYCLE_AUDIT_BY_EXPORT_INDEX: Dict[str, List[str]] = {}  # export_id -> [entry_ids]


# -----------------------------------------------------------------------------
# Checkpoint Summary (denormalized for audit readability)
# -----------------------------------------------------------------------------

class AuditCheckpointSummary(BaseModel):
    """
    Denormalized checkpoint summary stored in audit entry.

    Preserves audit readability even if runtime indexes are cleared.
    """

    checkpoint_gate: LifecycleGate = Field(
        ..., description="Checkpoint gate status"
    )
    checkpoint_passed: bool = Field(
        ..., description="Whether checkpoint allowed proceeding"
    )
    blocking_issues: List[str] = Field(
        default_factory=list, description="RED blocking issues"
    )
    warnings: List[str] = Field(
        default_factory=list, description="YELLOW warnings"
    )
    enforcement_hash: str = Field(
        default="", description="Deterministic enforcement hash from 7P"
    )
    pathway: str = Field(
        default="", description="Evaluated runtime pathway"
    )


# -----------------------------------------------------------------------------
# Audit Ledger Summary (for response embedding)
# -----------------------------------------------------------------------------

class AuditLedgerSummary(BaseModel):
    """
    Lightweight audit summary for lifecycle report embedding.

    Contains essential audit state without full lineage detail.
    """

    audit_id: str = Field(..., description="Audit entry identifier")
    export_id: str = Field(..., description="Governed lifecycle subject identifier")
    operation: str = Field(default="", description="CAM operation type")

    lifecycle_gate: LifecycleGate = Field(..., description="Lifecycle gate result")
    entry_state: AuditEntryState = Field(..., description="Audit entry state")

    continuity_integrity_valid: bool = Field(
        ..., description="Whether lineage continuity is valid"
    )

    has_checkpoint: bool = Field(
        default=False, description="Whether runtime checkpoint was evaluated"
    )
    checkpoint_gate: Optional[LifecycleGate] = Field(
        default=None, description="Runtime checkpoint gate if evaluated"
    )

    deterministic_hash: str = Field(
        ..., description="Deterministic audit hash"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Audit creation timestamp"
    )


# -----------------------------------------------------------------------------
# Full Audit Ledger Entry
# -----------------------------------------------------------------------------

class CAMLifecycleAuditLedgerEntry(BaseModel):
    """
    Full lifecycle audit ledger entry.

    Records lifecycle governance lineage with parent ancestry,
    checkpoint integration, and deterministic hashing.

    7R invariants (model-enforced):
      - immutable = True (always)
      - execution_authorized = False (always)
      - machine_output_allowed = False (always)

    Continuity rule:
      - checkpoint_gate == "red" → continuity_integrity_valid = False
    """

    # --- Identity ---
    ledger_entry_id: str = Field(
        default_factory=lambda: f"lifecycle-audit-{uuid4().hex[:12]}",
        description="Unique audit entry identifier"
    )
    audit_id: str = Field(
        default_factory=lambda: f"audit-{uuid4().hex[:12]}",
        description="Audit identifier (alias for compatibility)"
    )

    # --- Lifecycle Subject ---
    export_id: str = Field(
        ..., description="Governed lifecycle subject identifier"
    )
    operation: str = Field(
        default="", description="CAM operation type"
    )
    translator_id: Optional[str] = Field(
        default=None, description="Translator identifier if applicable"
    )

    # --- Lifecycle Result ---
    lifecycle_gate: LifecycleGate = Field(
        ..., description="Lifecycle validation gate result"
    )
    entry_state: AuditEntryState = Field(
        default="validation_complete",
        description="Audit entry state"
    )

    # --- Runtime Checkpoint Integration ---
    runtime_pathway: str = Field(
        default="", description="Runtime governance pathway evaluated"
    )
    runtime_enforcement_evaluation_id: Optional[str] = Field(
        default=None, description="Reference to 7P enforcement evaluation"
    )
    runtime_enforcement_hash: Optional[str] = Field(
        default=None, description="Deterministic enforcement hash from 7P"
    )
    checkpoint_summary: Optional[AuditCheckpointSummary] = Field(
        default=None, description="Denormalized checkpoint summary"
    )

    # --- Lineage ---
    parent_lifecycle_hashes: List[str] = Field(
        default_factory=list,
        description="Parent audit entry hashes for lineage chain"
    )

    # --- Integrity ---
    continuity_integrity_valid: bool = Field(
        default=True,
        description="Whether lineage continuity is valid"
    )

    # --- Issues ---
    blocking_issues: List[str] = Field(
        default_factory=list, description="RED blocking issues"
    )
    warnings: List[str] = Field(
        default_factory=list, description="YELLOW warnings"
    )

    # --- RMOS Integration ---
    rmos_summary: Optional[Dict[str, Any]] = Field(
        default=None, description="RMOS persistence summary if persisted"
    )

    # --- Policy Snapshot ---
    policy_snapshot: Dict[str, Any] = Field(
        default_factory=dict,
        description="Policy evaluation snapshot at audit time"
    )

    # --- 7R Invariants ---
    immutable: bool = Field(
        default=True,
        description="Always True — audit entries are immutable"
    )
    execution_authorized: bool = Field(
        default=False,
        description="Always False — 7R does not authorize execution"
    )
    machine_output_allowed: bool = Field(
        default=False,
        description="Always False — 7R does not allow machine output"
    )

    # --- Deterministic Hash ---
    deterministic_hash: str = Field(
        default="",
        description="Deterministic hash of audit state"
    )

    # --- Timestamps ---
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Audit entry creation timestamp"
    )

    # --- Metadata ---
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional audit metadata"
    )

    # --- Invariant Enforcement ---
    @model_validator(mode="after")
    def enforce_7r_invariants(self) -> "CAMLifecycleAuditLedgerEntry":
        """
        Enforce 7R invariants:
        - immutable must be True
        - execution_authorized must be False
        - machine_output_allowed must be False
        - RED checkpoint implies continuity_integrity_valid = False
        """
        if not self.immutable:
            raise ValueError(
                "7R invariant violation: immutable must be True — "
                "audit entries are immutable"
            )

        if self.execution_authorized:
            raise ValueError(
                "7R invariant violation: execution_authorized must be False — "
                "7R does not authorize execution"
            )

        if self.machine_output_allowed:
            raise ValueError(
                "7R invariant violation: machine_output_allowed must be False — "
                "7R does not allow machine output"
            )

        # RED checkpoint/lifecycle implies invalid continuity
        if self.checkpoint_summary and self.checkpoint_summary.checkpoint_gate == "red":
            if self.continuity_integrity_valid:
                raise ValueError(
                    "7R invariant violation: RED checkpoint requires "
                    "continuity_integrity_valid = False"
                )

        if self.lifecycle_gate == "red" and self.continuity_integrity_valid:
            # RED lifecycle can still have valid continuity if it's just a validation failure
            # Only checkpoint RED forces continuity invalid
            pass

        return self

    def compute_deterministic_hash(self) -> str:
        """Compute deterministic hash of audit state."""
        hash_input = {
            "export_id": self.export_id,
            "operation": self.operation,
            "translator_id": self.translator_id,
            "lifecycle_gate": self.lifecycle_gate,
            "entry_state": self.entry_state,
            "runtime_pathway": self.runtime_pathway,
            "runtime_enforcement_hash": self.runtime_enforcement_hash,
            "parent_lifecycle_hashes": sorted(self.parent_lifecycle_hashes),
            "continuity_integrity_valid": self.continuity_integrity_valid,
            "blocking_issues": sorted(self.blocking_issues),
            "warnings": sorted(self.warnings),
            "checkpoint_gate": (
                self.checkpoint_summary.checkpoint_gate
                if self.checkpoint_summary else None
            ),
        }
        canonical_json = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    def to_summary(self) -> AuditLedgerSummary:
        """Convert to lightweight summary for response embedding."""
        return AuditLedgerSummary(
            audit_id=self.audit_id,
            export_id=self.export_id,
            operation=self.operation,
            lifecycle_gate=self.lifecycle_gate,
            entry_state=self.entry_state,
            continuity_integrity_valid=self.continuity_integrity_valid,
            has_checkpoint=self.checkpoint_summary is not None,
            checkpoint_gate=(
                self.checkpoint_summary.checkpoint_gate
                if self.checkpoint_summary else None
            ),
            deterministic_hash=self.deterministic_hash,
            created_at=self.created_at,
        )


# -----------------------------------------------------------------------------
# Index Operations
# -----------------------------------------------------------------------------

def register_audit_entry(entry: CAMLifecycleAuditLedgerEntry) -> None:
    """Register audit entry in the in-memory indexes."""
    LIFECYCLE_AUDIT_LEDGER_INDEX[entry.ledger_entry_id] = entry

    # Index by export_id
    if entry.export_id not in LIFECYCLE_AUDIT_BY_EXPORT_INDEX:
        LIFECYCLE_AUDIT_BY_EXPORT_INDEX[entry.export_id] = []
    LIFECYCLE_AUDIT_BY_EXPORT_INDEX[entry.export_id].append(entry.ledger_entry_id)


def get_audit_entry(entry_id: str) -> Optional[CAMLifecycleAuditLedgerEntry]:
    """Get audit entry by ID."""
    return LIFECYCLE_AUDIT_LEDGER_INDEX.get(entry_id)


def get_audit_entries_for_export(export_id: str) -> List[CAMLifecycleAuditLedgerEntry]:
    """Get all audit entries for an export, ordered by creation time."""
    entry_ids = LIFECYCLE_AUDIT_BY_EXPORT_INDEX.get(export_id, [])
    entries = [LIFECYCLE_AUDIT_LEDGER_INDEX[eid] for eid in entry_ids if eid in LIFECYCLE_AUDIT_LEDGER_INDEX]
    return sorted(entries, key=lambda e: e.created_at)


def get_latest_audit_for_export(export_id: str) -> Optional[CAMLifecycleAuditLedgerEntry]:
    """Get most recent audit entry for an export."""
    entries = get_audit_entries_for_export(export_id)
    return entries[-1] if entries else None


def list_audit_entries() -> List[CAMLifecycleAuditLedgerEntry]:
    """List all audit entries."""
    return list(LIFECYCLE_AUDIT_LEDGER_INDEX.values())


def clear_audit_indexes() -> None:
    """Clear audit indexes (for testing)."""
    LIFECYCLE_AUDIT_LEDGER_INDEX.clear()
    LIFECYCLE_AUDIT_BY_EXPORT_INDEX.clear()


# -----------------------------------------------------------------------------
# Snapshot Generation (for orchestrator integration)
# -----------------------------------------------------------------------------

def generate_lifecycle_audit_snapshot(
    lifecycle_report: Any,
    policy_evaluation: Any,
    operation_capability: Any,
    checkpoint_evaluation: Optional[Any] = None,
) -> CAMLifecycleAuditLedgerEntry:
    """
    Generate lifecycle audit snapshot from orchestrator state.

    This is the primary entry point for the orchestrator to create audit entries.

    Args:
        lifecycle_report: GovernedExportLifecycleReport from orchestrator
        policy_evaluation: LifecyclePolicyEvaluation from policy engine
        operation_capability: CAMOperationCapability from registry
        checkpoint_evaluation: Optional 7P enforcement evaluation

    Returns:
        CAMLifecycleAuditLedgerEntry with computed hash
    """
    # Extract export_id from report or generate fallback
    export_id = _extract_export_id(lifecycle_report)

    # Extract operation
    operation = ""
    if operation_capability and hasattr(operation_capability, "operation"):
        operation = operation_capability.operation

    # Extract translator_id if present
    translator_id = None
    if hasattr(lifecycle_report, "translation_artifact_summary"):
        artifact = lifecycle_report.translation_artifact_summary
        if artifact and hasattr(artifact, "translator_id"):
            translator_id = artifact.translator_id

    # Determine lifecycle gate
    lifecycle_gate: LifecycleGate = "green"
    if hasattr(lifecycle_report, "lifecycle_gate"):
        lifecycle_gate = lifecycle_report.lifecycle_gate

    # Determine entry state
    entry_state = _determine_entry_state(lifecycle_report, checkpoint_evaluation)

    # Build checkpoint summary if evaluation provided
    checkpoint_summary = None
    runtime_enforcement_id = None
    runtime_enforcement_hash = None
    runtime_pathway = ""

    if checkpoint_evaluation:
        checkpoint_summary = AuditCheckpointSummary(
            checkpoint_gate=checkpoint_evaluation.severity,
            checkpoint_passed=checkpoint_evaluation.governance_checkpoint_passed,
            blocking_issues=checkpoint_evaluation.blocking_issues,
            warnings=checkpoint_evaluation.warnings,
            enforcement_hash=checkpoint_evaluation.deterministic_enforcement_hash,
            pathway=checkpoint_evaluation.runtime_pathway,
        )
        runtime_enforcement_id = checkpoint_evaluation.evaluation_id
        runtime_enforcement_hash = checkpoint_evaluation.deterministic_enforcement_hash
        runtime_pathway = checkpoint_evaluation.runtime_pathway

    # Get parent hashes from previous entries for this export
    parent_hashes = _get_parent_hashes(export_id)

    # Determine continuity validity
    continuity_valid = True
    if checkpoint_summary and checkpoint_summary.checkpoint_gate == "red":
        continuity_valid = False

    # Extract issues
    blocking_issues = []
    warnings = []
    if hasattr(lifecycle_report, "blocking_issues"):
        blocking_issues = list(lifecycle_report.blocking_issues)
    if hasattr(lifecycle_report, "warnings"):
        warnings = list(lifecycle_report.warnings)

    # Build policy snapshot
    policy_snapshot = {}
    if policy_evaluation:
        policy_snapshot = {
            "lifecycle_gate": policy_evaluation.lifecycle_gate if hasattr(policy_evaluation, "lifecycle_gate") else None,
            "preview_allowed": policy_evaluation.preview_allowed if hasattr(policy_evaluation, "preview_allowed") else None,
            "export_allowed": policy_evaluation.export_allowed if hasattr(policy_evaluation, "export_allowed") else None,
        }

    # Create entry
    entry = CAMLifecycleAuditLedgerEntry(
        export_id=export_id,
        operation=operation,
        translator_id=translator_id,
        lifecycle_gate=lifecycle_gate,
        entry_state=entry_state,
        runtime_pathway=runtime_pathway,
        runtime_enforcement_evaluation_id=runtime_enforcement_id,
        runtime_enforcement_hash=runtime_enforcement_hash,
        checkpoint_summary=checkpoint_summary,
        parent_lifecycle_hashes=parent_hashes,
        continuity_integrity_valid=continuity_valid,
        blocking_issues=blocking_issues,
        warnings=warnings,
        policy_snapshot=policy_snapshot,
        metadata={
            "dev_order": "7R",
            "audit_type": "lifecycle_governance",
        },
    )

    # Compute deterministic hash
    entry.deterministic_hash = entry.compute_deterministic_hash()

    # Register in index
    register_audit_entry(entry)

    return entry


def create_audit_summary(entry: CAMLifecycleAuditLedgerEntry) -> AuditLedgerSummary:
    """
    Create lightweight summary from full audit entry.

    Convenience function for orchestrator integration.
    """
    return entry.to_summary()


# -----------------------------------------------------------------------------
# Internal Helpers
# -----------------------------------------------------------------------------

def _extract_export_id(lifecycle_report: Any) -> str:
    """Extract export_id from lifecycle report or generate fallback."""
    # Try to get from export object summary
    if hasattr(lifecycle_report, "export_object_summary"):
        summary = lifecycle_report.export_object_summary
        if summary and hasattr(summary, "export_id"):
            return summary.export_id

    # Try to get from preview
    if hasattr(lifecycle_report, "preview"):
        preview = lifecycle_report.preview
        if preview and hasattr(preview, "export_id"):
            return preview.export_id

    # Generate fallback
    return f"lifecycle-export-{uuid4().hex[:12]}"


def _determine_entry_state(
    lifecycle_report: Any,
    checkpoint_evaluation: Optional[Any],
) -> AuditEntryState:
    """Determine audit entry state from report and checkpoint."""
    # Check for checkpoint block
    if checkpoint_evaluation:
        if hasattr(checkpoint_evaluation, "severity") and checkpoint_evaluation.severity == "red":
            return "checkpoint_blocked"

    # Check lifecycle gate
    if hasattr(lifecycle_report, "lifecycle_gate"):
        if lifecycle_report.lifecycle_gate == "red":
            return "validation_failed"

    # Check for early return indicators
    if hasattr(lifecycle_report, "metadata"):
        meta = lifecycle_report.metadata
        if isinstance(meta, dict) and meta.get("early_return"):
            return "early_return"

    return "validation_complete"


def _get_parent_hashes(export_id: str) -> List[str]:
    """Get parent hashes from previous audit entries for this export."""
    entries = get_audit_entries_for_export(export_id)
    if not entries:
        return []

    # Return hash of most recent entry as parent
    latest = entries[-1]
    if latest.deterministic_hash:
        return [latest.deterministic_hash]

    return []
