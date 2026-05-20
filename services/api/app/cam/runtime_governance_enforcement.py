"""
Runtime Governance Enforcement Layer

CAM Dev Order 7P: Runtime governance enforcement checkpoints and evaluation.

This module operationalizes runtime governance by validating declared
runtime-adjacent pathways against governance state from 7H/7N/7O.

7P creates:
  - RuntimeGovernanceEnforcementEvaluation model
  - Pathway parsing and classification
  - Governance linkage validation
  - Checkpoint evaluation against 7H quarantine, 7N consumption, 7O ledger
  - Enforcement severity classification

7P does NOT:
  - Execute runtime systems
  - Intercept live router traffic
  - Generate DXF/SVG/G-code
  - Invoke serializers
  - Produce machine output
  - Mutate 7H/7N/7O state

7P invariants (always enforced):
  - execution_authorized = False
  - machine_output_allowed = False
  - serializer_execution_allowed = False
  - runtime_self_authorized = False

Guardrail:
  7P evaluates declared runtime-adjacent pathways for governance compliance.
  It does not intercept live traffic, invoke serializers, execute runtimes,
  or authorize machine output.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


# -----------------------------------------------------------------------------
# Type Definitions
# -----------------------------------------------------------------------------

EnforcementSeverity = Literal["green", "yellow", "red"]

PathwayType = Literal[
    "translator_dispatch",
    "export_route",
    "serializer_boundary",
    "postprocessor_boundary",
    "geometry_consumption",
    "runtime_dispatch",
    "machine_output_boundary",
    "unknown",
]

CheckpointType = Literal[
    "quarantine_enforcement",
    "consumption_discipline",
    "ledger_lineage",
    "pathway_classification",
    "invariant_verification",
]


# -----------------------------------------------------------------------------
# Canonical Pathway Types
# -----------------------------------------------------------------------------

CANONICAL_PATHWAY_TYPES: List[str] = [
    "translator_dispatch",
    "export_route",
    "serializer_boundary",
    "postprocessor_boundary",
    "geometry_consumption",
    "runtime_dispatch",
    "machine_output_boundary",
]

# Pathway types that imply execution authority (always RED if unrecognized)
EXECUTION_IMPLYING_PREFIXES: List[str] = [
    "serializer",
    "machine",
    "runtime",
    "execute",
    "subprocess",
    "plugin",
]


# -----------------------------------------------------------------------------
# In-Memory Indexes
# -----------------------------------------------------------------------------

ENFORCEMENT_EVALUATION_INDEX: Dict[str, "RuntimeGovernanceEnforcementEvaluation"] = {}
ENFORCEMENT_REPORT_INDEX: Dict[str, "EnforcementCheckpointReport"] = {}


# -----------------------------------------------------------------------------
# Pathway Parsing
# -----------------------------------------------------------------------------

class ParsedPathway(BaseModel):
    """Parsed runtime pathway declaration."""

    raw_pathway: str = Field(..., description="Original pathway string")
    pathway_type: PathwayType = Field(..., description="Classified pathway type")
    pathway_target: str = Field(..., description="Target portion of pathway")
    is_canonical_type: bool = Field(
        default=False,
        description="Whether pathway_type is a canonical governance type"
    )
    implies_execution: bool = Field(
        default=False,
        description="Whether pathway implies execution authority"
    )
    parse_valid: bool = Field(default=True, description="Whether parse succeeded")
    parse_error: Optional[str] = Field(default=None, description="Parse error if any")


def parse_runtime_pathway(pathway: str) -> ParsedPathway:
    """
    Parse a runtime pathway declaration.

    Format: <pathway_type>:<pathway_target>

    Examples:
      - translator_dispatch:dxf_r12
      - export_route:/api/cam/export/lifecycle/validate
      - serializer_boundary:dxf_compat

    Returns ParsedPathway with classification.
    """
    if not pathway or not isinstance(pathway, str):
        return ParsedPathway(
            raw_pathway=pathway or "",
            pathway_type="unknown",
            pathway_target="",
            is_canonical_type=False,
            implies_execution=False,
            parse_valid=False,
            parse_error="Empty or invalid pathway string",
        )

    if ":" not in pathway:
        return ParsedPathway(
            raw_pathway=pathway,
            pathway_type="unknown",
            pathway_target=pathway,
            is_canonical_type=False,
            implies_execution=False,
            parse_valid=False,
            parse_error="Missing ':' separator in pathway format",
        )

    parts = pathway.split(":", 1)
    pathway_type_str = parts[0].strip().lower()
    pathway_target = parts[1].strip() if len(parts) > 1 else ""

    # Classify pathway type
    is_canonical = pathway_type_str in CANONICAL_PATHWAY_TYPES
    implies_execution = any(
        prefix in pathway_type_str for prefix in EXECUTION_IMPLYING_PREFIXES
    )

    # Map to PathwayType
    if pathway_type_str in CANONICAL_PATHWAY_TYPES:
        classified_type: PathwayType = pathway_type_str  # type: ignore
    else:
        classified_type = "unknown"

    return ParsedPathway(
        raw_pathway=pathway,
        pathway_type=classified_type,
        pathway_target=pathway_target,
        is_canonical_type=is_canonical,
        implies_execution=implies_execution,
        parse_valid=True,
        parse_error=None,
    )


# -----------------------------------------------------------------------------
# Governance Linkage
# -----------------------------------------------------------------------------

class GovernanceLinkage(BaseModel):
    """References to 7H/7N/7O governance state."""

    quarantine_id: Optional[str] = Field(
        default=None,
        description="Reference to 7H quarantine evaluation"
    )
    consumer_id: Optional[str] = Field(
        default=None,
        description="Reference to 7N semantic consumer"
    )
    ledger_entry_id: Optional[str] = Field(
        default=None,
        description="Reference to 7O ledger entry"
    )
    translator_id: Optional[str] = Field(
        default=None,
        description="Translator identifier"
    )
    export_route: Optional[str] = Field(
        default=None,
        description="Export route path"
    )

    # Lookup results
    quarantine_found: bool = Field(default=False)
    consumer_found: bool = Field(default=False)
    ledger_entry_found: bool = Field(default=False)

    # Governance state summaries (populated during lookup)
    quarantine_state: Optional[str] = Field(default=None)
    consumer_alignment_score: Optional[float] = Field(default=None)
    ledger_escalation_severity: Optional[str] = Field(default=None)


def lookup_governance_linkage(linkage: GovernanceLinkage) -> GovernanceLinkage:
    """
    Look up governance references in 7H/7N/7O indexes.

    Does NOT mutate those indexes — read-only lookup.
    """
    result = linkage.model_copy()

    # 7H Quarantine lookup
    if linkage.quarantine_id:
        try:
            from app.cam.translator_execution_quarantine import get_quarantine
            quarantine = get_quarantine(linkage.quarantine_id)
            if quarantine:
                result.quarantine_found = True
                result.quarantine_state = quarantine.quarantine_state
        except ImportError:
            pass

    # 7N Consumer lookup
    if linkage.consumer_id:
        try:
            from app.cam.runtime_semantic_consumption import get_consumer
            consumer = get_consumer(linkage.consumer_id)
            if consumer:
                result.consumer_found = True
        except ImportError:
            pass

    # 7O Ledger lookup
    if linkage.ledger_entry_id:
        try:
            from app.cam.runtime_semantic_consumption_ledger import get_ledger_entry
            entry = get_ledger_entry(linkage.ledger_entry_id)
            if entry:
                result.ledger_entry_found = True
                # Check for escalation
                try:
                    from app.cam.runtime_drift_escalation_engine import (
                        get_latest_escalation_for_consumer,
                    )
                    if entry.consumer_id:
                        escalation = get_latest_escalation_for_consumer(entry.consumer_id)
                        if escalation:
                            result.ledger_escalation_severity = escalation.escalation_severity
                except ImportError:
                    pass
        except ImportError:
            pass

    return result


# -----------------------------------------------------------------------------
# Enforcement Checkpoint
# -----------------------------------------------------------------------------

class EnforcementCheckpoint(BaseModel):
    """A single enforcement checkpoint evaluation."""

    checkpoint_type: CheckpointType = Field(..., description="Type of checkpoint")
    checkpoint_passed: bool = Field(..., description="Whether checkpoint passed")
    severity: EnforcementSeverity = Field(..., description="Severity if failed")
    message: str = Field(..., description="Checkpoint result message")
    blocking: bool = Field(default=False, description="Whether this blocks enforcement")


# -----------------------------------------------------------------------------
# Enforcement Evaluation Request
# -----------------------------------------------------------------------------

class RuntimeEnforcementRequest(BaseModel):
    """Request to evaluate runtime governance enforcement."""

    runtime_pathway: str = Field(
        ...,
        description="Runtime pathway declaration (format: type:target)"
    )

    # Optional governance linkage references
    quarantine_id: Optional[str] = Field(default=None)
    consumer_id: Optional[str] = Field(default=None)
    ledger_entry_id: Optional[str] = Field(default=None)
    translator_id: Optional[str] = Field(default=None)
    export_route: Optional[str] = Field(default=None)

    # Request metadata
    request_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context for evaluation"
    )


# -----------------------------------------------------------------------------
# Enforcement Evaluation Result
# -----------------------------------------------------------------------------

class RuntimeGovernanceEnforcementEvaluation(BaseModel):
    """
    Runtime governance enforcement evaluation result.

    7P invariants (model-enforced):
      - execution_authorized = False (always)
      - machine_output_allowed = False (always)
      - serializer_execution_allowed = False (always)
      - runtime_self_authorized = False (always)
    """

    # --- Identity ---
    evaluation_id: str = Field(
        default_factory=lambda: f"enforce-{uuid4().hex[:12]}",
        description="Unique evaluation identifier"
    )

    # --- Pathway ---
    runtime_pathway: str = Field(..., description="Evaluated runtime pathway")
    parsed_pathway: ParsedPathway = Field(..., description="Parsed pathway result")

    # --- Governance Linkage ---
    translator_id: Optional[str] = Field(default=None)
    export_route: Optional[str] = Field(default=None)
    governance_linkage: GovernanceLinkage = Field(
        default_factory=GovernanceLinkage,
        description="Governance references and lookup results"
    )

    # --- Checkpoint Results ---
    checkpoints: List[EnforcementCheckpoint] = Field(
        default_factory=list,
        description="Checkpoint evaluation results"
    )
    governance_checkpoint_passed: bool = Field(
        default=False,
        description="Overall governance checkpoint result"
    )
    runtime_quarantine_respected: bool = Field(
        default=True,
        description="Whether 7H quarantine is respected"
    )

    # --- Detection Results ---
    serializer_path_detected: bool = Field(
        default=False,
        description="Whether serializer invocation pathway detected"
    )
    runtime_bypass_detected: bool = Field(
        default=False,
        description="Whether runtime bypass attempt detected"
    )
    authority_leak_detected: bool = Field(
        default=False,
        description="Whether authority leak detected"
    )

    # --- Severity ---
    severity: EnforcementSeverity = Field(
        default="green",
        description="Overall enforcement severity"
    )
    blocking_issues: List[str] = Field(
        default_factory=list,
        description="RED blocking issues"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="YELLOW warnings"
    )

    # --- 7P Invariants (Always False/True) ---
    execution_authorized: bool = Field(
        default=False,
        description="Always False — 7P does not authorize execution"
    )
    machine_output_allowed: bool = Field(
        default=False,
        description="Always False — 7P does not allow machine output"
    )
    serializer_execution_allowed: bool = Field(
        default=False,
        description="Always False — 7P does not allow serializer execution"
    )
    runtime_self_authorized: bool = Field(
        default=False,
        description="Always False — 7P does not allow runtime self-authorization"
    )

    # --- Deterministic Hash ---
    deterministic_enforcement_hash: str = Field(
        default="",
        description="Deterministic hash of enforcement state"
    )

    # --- Timestamps ---
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Evaluation timestamp"
    )

    # --- Metadata ---
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional evaluation metadata"
    )

    # --- Invariant Enforcement ---
    @model_validator(mode="after")
    def enforce_7p_invariants(self) -> "RuntimeGovernanceEnforcementEvaluation":
        """
        Enforce 7P invariants:
        - All execution/authorization flags must be False
        """
        if self.execution_authorized:
            raise ValueError(
                "7P invariant violation: execution_authorized must be False — "
                "7P does not authorize execution"
            )

        if self.machine_output_allowed:
            raise ValueError(
                "7P invariant violation: machine_output_allowed must be False — "
                "7P does not allow machine output"
            )

        if self.serializer_execution_allowed:
            raise ValueError(
                "7P invariant violation: serializer_execution_allowed must be False — "
                "7P does not allow serializer execution"
            )

        if self.runtime_self_authorized:
            raise ValueError(
                "7P invariant violation: runtime_self_authorized must be False — "
                "7P does not allow runtime self-authorization"
            )

        return self

    def compute_enforcement_hash(self) -> str:
        """Compute deterministic hash of enforcement state."""
        hash_input = {
            "runtime_pathway": self.runtime_pathway,
            "pathway_type": self.parsed_pathway.pathway_type,
            "pathway_target": self.parsed_pathway.pathway_target,
            "translator_id": self.translator_id,
            "export_route": self.export_route,
            "governance_checkpoint_passed": self.governance_checkpoint_passed,
            "runtime_quarantine_respected": self.runtime_quarantine_respected,
            "serializer_path_detected": self.serializer_path_detected,
            "runtime_bypass_detected": self.runtime_bypass_detected,
            "authority_leak_detected": self.authority_leak_detected,
            "severity": self.severity,
            "blocking_issues": sorted(self.blocking_issues),
            "warnings": sorted(self.warnings),
            "checkpoint_results": [
                {
                    "type": c.checkpoint_type,
                    "passed": c.checkpoint_passed,
                    "severity": c.severity,
                }
                for c in self.checkpoints
            ],
        }
        canonical_json = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


# -----------------------------------------------------------------------------
# Enforcement Checkpoint Report (CI Summary)
# -----------------------------------------------------------------------------

class EnforcementCheckpointReport(BaseModel):
    """Aggregated enforcement report for CI integration."""

    report_id: str = Field(
        default_factory=lambda: f"enforce-report-{uuid4().hex[:12]}",
        description="Report identifier"
    )
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Report generation timestamp"
    )

    # --- Aggregated Results ---
    evaluations_count: int = Field(default=0)
    evaluations_passed: int = Field(default=0)
    evaluations_failed: int = Field(default=0)
    evaluations_warned: int = Field(default=0)

    # --- Detection Counts ---
    serializer_paths_detected: int = Field(default=0)
    runtime_bypasses_detected: int = Field(default=0)
    authority_leaks_detected: int = Field(default=0)
    quarantine_violations: int = Field(default=0)

    # --- Severity Distribution ---
    red_count: int = Field(default=0)
    yellow_count: int = Field(default=0)
    green_count: int = Field(default=0)

    # --- CI Status ---
    ci_status: Literal["pass", "warn", "fail"] = Field(
        default="pass",
        description="CI evaluation status"
    )
    summary_message: str = Field(default="")

    # --- Blocking Issues (Aggregated) ---
    all_blocking_issues: List[str] = Field(default_factory=list)
    all_warnings: List[str] = Field(default_factory=list)

    # --- 7P Invariants ---
    execution_authorized: bool = Field(default=False)
    machine_output_allowed: bool = Field(default=False)

    # --- Deterministic Hash ---
    deterministic_report_hash: str = Field(default="")

    def compute_report_hash(self) -> str:
        """Compute deterministic hash of report."""
        hash_input = {
            "evaluations_count": self.evaluations_count,
            "evaluations_passed": self.evaluations_passed,
            "evaluations_failed": self.evaluations_failed,
            "red_count": self.red_count,
            "yellow_count": self.yellow_count,
            "green_count": self.green_count,
            "serializer_paths_detected": self.serializer_paths_detected,
            "runtime_bypasses_detected": self.runtime_bypasses_detected,
            "authority_leaks_detected": self.authority_leaks_detected,
            "quarantine_violations": self.quarantine_violations,
            "ci_status": self.ci_status,
        }
        canonical_json = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


# -----------------------------------------------------------------------------
# Index Operations
# -----------------------------------------------------------------------------

def register_enforcement_evaluation(
    evaluation: RuntimeGovernanceEnforcementEvaluation,
) -> None:
    """Register enforcement evaluation in the in-memory index."""
    ENFORCEMENT_EVALUATION_INDEX[evaluation.evaluation_id] = evaluation


def get_enforcement_evaluation(
    evaluation_id: str,
) -> Optional[RuntimeGovernanceEnforcementEvaluation]:
    """Get enforcement evaluation by ID."""
    return ENFORCEMENT_EVALUATION_INDEX.get(evaluation_id)


def list_enforcement_evaluations() -> List[RuntimeGovernanceEnforcementEvaluation]:
    """List all enforcement evaluations."""
    return list(ENFORCEMENT_EVALUATION_INDEX.values())


def get_enforcement_evaluations_by_severity(
    severity: EnforcementSeverity,
) -> List[RuntimeGovernanceEnforcementEvaluation]:
    """Get evaluations by severity."""
    return [e for e in ENFORCEMENT_EVALUATION_INDEX.values() if e.severity == severity]


def clear_enforcement_index() -> None:
    """Clear enforcement index (for testing)."""
    ENFORCEMENT_EVALUATION_INDEX.clear()


def register_enforcement_report(report: EnforcementCheckpointReport) -> None:
    """Register enforcement report in the index."""
    ENFORCEMENT_REPORT_INDEX[report.report_id] = report


def get_enforcement_report(report_id: str) -> Optional[EnforcementCheckpointReport]:
    """Get enforcement report by ID."""
    return ENFORCEMENT_REPORT_INDEX.get(report_id)


def get_latest_enforcement_report() -> Optional[EnforcementCheckpointReport]:
    """Get most recent enforcement report."""
    if not ENFORCEMENT_REPORT_INDEX:
        return None
    return max(ENFORCEMENT_REPORT_INDEX.values(), key=lambda r: r.generated_at)


def list_enforcement_reports() -> List[EnforcementCheckpointReport]:
    """List all enforcement reports."""
    return list(ENFORCEMENT_REPORT_INDEX.values())


def clear_enforcement_report_index() -> None:
    """Clear enforcement report index (for testing)."""
    ENFORCEMENT_REPORT_INDEX.clear()
