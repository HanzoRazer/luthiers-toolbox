"""
CAM Lifecycle Audit Ledger — CAM Dev Order 6K

Deterministic audit snapshots for governed export lifecycle validation.
Metadata only — no machine output, no artifact payloads.
"""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from app.cam.cam_lifecycle_policy_engine import LifecyclePolicyEvaluation
    from app.cam.cam_operation_registry import CAMOperationCapability
    from app.cam.export_lifecycle_orchestrator import GovernedExportLifecycleReport


class AuditLedgerSummary(BaseModel):
    """Lightweight audit summary attached to lifecycle reports."""

    audit_id: str
    deterministic_hash: str
    lifecycle_gate: str
    operation: Optional[str] = None


class LifecycleAuditSnapshot(BaseModel):
    """Full audit snapshot persisted to RMOS when requested."""

    audit_id: str = Field(default_factory=lambda: f"audit-{uuid4().hex[:12]}")
    deterministic_hash: str
    lifecycle_gate: str
    operation: str
    exportability_class: Optional[str] = None
    maturity: Optional[str] = None
    policy_gate: Optional[str] = None
    export_ready: Optional[bool] = None
    machine_ready: Optional[bool] = None
    blocking_issue_count: int = 0
    warning_count: int = 0
    stage_snapshots: List[str] = Field(default_factory=list)


def _stable_hash(payload: Dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def generate_lifecycle_audit_snapshot(
    lifecycle_report: "GovernedExportLifecycleReport",
    policy_evaluation: "LifecyclePolicyEvaluation",
    operation_capability: Optional["CAMOperationCapability"] = None,
) -> LifecycleAuditSnapshot:
    """Build a deterministic audit snapshot from lifecycle + policy state."""
    operation = lifecycle_report.preview_operation or policy_evaluation.operation

    hash_payload: Dict[str, Any] = {
        "operation": operation,
        "lifecycle_gate": lifecycle_report.lifecycle_gate,
        "exportability_class": policy_evaluation.exportability_class,
        "maturity": policy_evaluation.maturity,
        "policy_gate": policy_evaluation.lifecycle_gate,
        "export_ready": lifecycle_report.export_ready,
        "machine_ready": lifecycle_report.machine_ready,
        "blocking_issues": sorted(lifecycle_report.blocking_issues),
        "warnings": sorted(lifecycle_report.warnings),
        "preview_gate": lifecycle_report.preview_gate,
        "machine_output_generated": lifecycle_report.machine_output_generated,
        "translator_output_generated": lifecycle_report.translator_output_generated,
    }

    if operation_capability is not None:
        hash_payload["capability_exportability"] = operation_capability.exportability_class
        hash_payload["capability_maturity"] = operation_capability.maturity

    return LifecycleAuditSnapshot(
        deterministic_hash=_stable_hash(hash_payload),
        lifecycle_gate=lifecycle_report.lifecycle_gate,
        operation=operation,
        exportability_class=policy_evaluation.exportability_class,
        maturity=policy_evaluation.maturity,
        policy_gate=policy_evaluation.lifecycle_gate,
        export_ready=lifecycle_report.export_ready,
        machine_ready=lifecycle_report.machine_ready,
        blocking_issue_count=len(lifecycle_report.blocking_issues),
        warning_count=len(lifecycle_report.warnings),
    )


def create_audit_summary(snapshot: LifecycleAuditSnapshot) -> AuditLedgerSummary:
    """Convert a full snapshot to the summary embedded in lifecycle reports."""
    return AuditLedgerSummary(
        audit_id=snapshot.audit_id,
        deterministic_hash=snapshot.deterministic_hash,
        lifecycle_gate=snapshot.lifecycle_gate,
        operation=snapshot.operation,
    )
