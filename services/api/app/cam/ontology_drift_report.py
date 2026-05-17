"""
Ontology Drift Report

CAM Dev Order 7M: Drift classification and CI-visible reporting.

This module provides:
  - Report formatting
  - CI summary generation
  - Severity classification helpers
  - Drift trend analysis

7M invariants:
  - execution_authorized = false (always)
  - machine_output_allowed = false (always)

Guardrail:
  7M makes ontology drift visible. It does not automatically repair
  ontology drift.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.cam.ontology_reconciliation_engine import (
    OntologyConflict,
    OntologyReconciliationReport,
    SEVERITY_PENALTIES,
    list_reports,
    get_latest_report,
)


# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------

class DriftSeveritySummary(BaseModel):
    """Summary of drift by severity level."""

    critical: int = Field(default=0, description="Critical severity count")
    high: int = Field(default=0, description="High severity count")
    medium: int = Field(default=0, description="Medium severity count")
    low: int = Field(default=0, description="Low severity count")
    total_penalty: int = Field(default=0, description="Total severity penalty")


class DriftTypeSummary(BaseModel):
    """Summary of drift by conflict type."""

    duplicate_definition: int = Field(default=0)
    lifecycle_drift: int = Field(default=0)
    authority_collision: int = Field(default=0)
    runtime_reinterpretation: int = Field(default=0)
    semantic_alias_collision: int = Field(default=0)


class CISummary(BaseModel):
    """
    CI-visible summary for ontology integrity.

    Designed for quick pass/fail determination in CI pipelines.
    """

    status: Literal["pass", "warn", "fail"] = Field(
        ...,
        description="CI status: pass (no conflicts), warn (non-critical), fail (critical)"
    )
    alignment_score: float = Field(..., description="Alignment score (0.0-1.0)")
    conflicts_detected: int = Field(..., description="Total conflicts")
    critical_conflicts: int = Field(..., description="Critical conflicts (causes fail)")
    ontology_integrity_valid: bool = Field(..., description="Overall integrity")
    summary_message: str = Field(..., description="Human-readable summary")

    # 7M invariants
    execution_authorized: bool = Field(default=False)
    machine_output_allowed: bool = Field(default=False)

    @field_validator("execution_authorized", mode="before")
    @classmethod
    def enforce_no_execution(cls, v: Any) -> bool:
        return False

    @field_validator("machine_output_allowed", mode="before")
    @classmethod
    def enforce_no_machine_output(cls, v: Any) -> bool:
        return False


class OntologyDriftReport(BaseModel):
    """
    Comprehensive drift report with trend analysis.

    7M invariants (model-enforced):
      - execution_authorized = false (always)
      - machine_output_allowed = false (always)
    """

    report_id: str = Field(..., description="Source report ID")
    generated_at: datetime = Field(..., description="Generation timestamp")

    # Summaries
    severity_summary: DriftSeveritySummary = Field(
        ...,
        description="Breakdown by severity"
    )
    type_summary: DriftTypeSummary = Field(
        ...,
        description="Breakdown by conflict type"
    )
    ci_summary: CISummary = Field(
        ...,
        description="CI-visible summary"
    )

    # Affected domains
    affected_domains: List[str] = Field(
        default_factory=list,
        description="Domains with detected conflicts"
    )

    # Top conflicts
    top_conflicts: List[OntologyConflict] = Field(
        default_factory=list,
        description="Top conflicts by severity"
    )

    # Trend (if historical data available)
    trend_direction: Optional[Literal["improving", "stable", "degrading"]] = Field(
        None,
        description="Drift trend compared to previous report"
    )
    trend_delta: Optional[float] = Field(
        None,
        description="Alignment score delta from previous report"
    )

    # 7M invariants
    execution_authorized: bool = Field(default=False)
    machine_output_allowed: bool = Field(default=False)

    @field_validator("execution_authorized", mode="before")
    @classmethod
    def enforce_no_execution(cls, v: Any) -> bool:
        if v is True:
            raise ValueError(
                "7M invariant violation: execution_authorized must be false"
            )
        return False

    @field_validator("machine_output_allowed", mode="before")
    @classmethod
    def enforce_no_machine_output(cls, v: Any) -> bool:
        if v is True:
            raise ValueError(
                "7M invariant violation: machine_output_allowed must be false"
            )
        return False


# -----------------------------------------------------------------------------
# Severity Classification
# -----------------------------------------------------------------------------

def classify_severity_summary(
    conflicts: List[OntologyConflict],
) -> DriftSeveritySummary:
    """Classify conflicts by severity level."""
    critical = len([c for c in conflicts if c.severity == "critical"])
    high = len([c for c in conflicts if c.severity == "high"])
    medium = len([c for c in conflicts if c.severity == "medium"])
    low = len([c for c in conflicts if c.severity == "low"])

    total_penalty = sum(SEVERITY_PENALTIES.get(c.severity, 0) for c in conflicts)

    return DriftSeveritySummary(
        critical=critical,
        high=high,
        medium=medium,
        low=low,
        total_penalty=total_penalty,
    )


def classify_type_summary(
    conflicts: List[OntologyConflict],
) -> DriftTypeSummary:
    """Classify conflicts by type."""
    return DriftTypeSummary(
        duplicate_definition=len([
            c for c in conflicts if c.conflict_type == "duplicate_definition"
        ]),
        lifecycle_drift=len([
            c for c in conflicts if c.conflict_type == "lifecycle_drift"
        ]),
        authority_collision=len([
            c for c in conflicts if c.conflict_type == "authority_collision"
        ]),
        runtime_reinterpretation=len([
            c for c in conflicts if c.conflict_type == "runtime_reinterpretation"
        ]),
        semantic_alias_collision=len([
            c for c in conflicts if c.conflict_type == "semantic_alias_collision"
        ]),
    )


# -----------------------------------------------------------------------------
# CI Summary Generation
# -----------------------------------------------------------------------------

def generate_ci_summary(report: OntologyReconciliationReport) -> CISummary:
    """
    Generate CI-visible summary from a reconciliation report.

    Status determination:
      - pass: No conflicts detected
      - warn: Non-critical conflicts only
      - fail: Critical conflicts present
    """
    critical_count = len([
        c for c in report.conflicts if c.severity == "critical"
    ])

    if report.conflicts_detected == 0:
        status = "pass"
        message = "Ontology integrity verified. No conflicts detected."
    elif critical_count > 0:
        status = "fail"
        message = (
            f"Ontology integrity FAILED. {critical_count} critical conflicts "
            f"require immediate attention. Total: {report.conflicts_detected} conflicts."
        )
    else:
        status = "warn"
        message = (
            f"Ontology drift detected. {report.conflicts_detected} non-critical "
            f"conflicts found. Alignment score: {report.canonical_alignment_score:.2%}"
        )

    return CISummary(
        status=status,
        alignment_score=report.canonical_alignment_score,
        conflicts_detected=report.conflicts_detected,
        critical_conflicts=critical_count,
        ontology_integrity_valid=report.ontology_integrity_valid,
        summary_message=message,
        execution_authorized=False,
        machine_output_allowed=False,
    )


# -----------------------------------------------------------------------------
# Affected Domains
# -----------------------------------------------------------------------------

def get_affected_domains(conflicts: List[OntologyConflict]) -> List[str]:
    """Get list of domains affected by conflicts."""
    domains: set = set()
    for conflict in conflicts:
        domains.update(conflict.conflicting_sources)
    return sorted(domains)


# -----------------------------------------------------------------------------
# Trend Analysis
# -----------------------------------------------------------------------------

def analyze_trend(
    current_score: float,
    previous_reports: List[OntologyReconciliationReport],
) -> tuple[Optional[str], Optional[float]]:
    """
    Analyze drift trend compared to previous reports.

    Returns:
        (trend_direction, score_delta)
    """
    if not previous_reports:
        return None, None

    # Get most recent previous report
    previous = max(previous_reports, key=lambda r: r.generated_at)
    previous_score = previous.canonical_alignment_score

    delta = current_score - previous_score

    if delta > 0.05:
        direction = "improving"
    elif delta < -0.05:
        direction = "degrading"
    else:
        direction = "stable"

    return direction, round(delta, 4)


# -----------------------------------------------------------------------------
# Drift Report Generation
# -----------------------------------------------------------------------------

def generate_drift_report(
    reconciliation_report: OntologyReconciliationReport,
) -> OntologyDriftReport:
    """
    Generate comprehensive drift report from reconciliation report.

    Includes:
      - Severity breakdown
      - Type breakdown
      - CI summary
      - Affected domains
      - Top conflicts
      - Trend analysis
    """
    # Generate summaries
    severity_summary = classify_severity_summary(reconciliation_report.conflicts)
    type_summary = classify_type_summary(reconciliation_report.conflicts)
    ci_summary = generate_ci_summary(reconciliation_report)

    # Get affected domains
    affected_domains = get_affected_domains(reconciliation_report.conflicts)

    # Get top conflicts (sorted by severity)
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    sorted_conflicts = sorted(
        reconciliation_report.conflicts,
        key=lambda c: severity_order.get(c.severity, 4)
    )
    top_conflicts = sorted_conflicts[:10]  # Top 10

    # Analyze trend
    all_reports = list_reports()
    previous_reports = [
        r for r in all_reports
        if r.report_id != reconciliation_report.report_id
    ]
    trend_direction, trend_delta = analyze_trend(
        reconciliation_report.canonical_alignment_score,
        previous_reports,
    )

    return OntologyDriftReport(
        report_id=reconciliation_report.report_id,
        generated_at=reconciliation_report.generated_at,
        severity_summary=severity_summary,
        type_summary=type_summary,
        ci_summary=ci_summary,
        affected_domains=affected_domains,
        top_conflicts=top_conflicts,
        trend_direction=trend_direction,
        trend_delta=trend_delta,
        execution_authorized=False,
        machine_output_allowed=False,
    )


def generate_latest_drift_report() -> Optional[OntologyDriftReport]:
    """Generate drift report from the latest reconciliation report."""
    latest = get_latest_report()
    if latest is None:
        return None
    return generate_drift_report(latest)


# -----------------------------------------------------------------------------
# CI Output Formatting
# -----------------------------------------------------------------------------

def format_ci_output(ci_summary: CISummary) -> str:
    """
    Format CI summary as text output.

    Suitable for CI logs and status checks.
    """
    lines = [
        "=" * 60,
        "ONTOLOGY INTEGRITY CHECK",
        "=" * 60,
        f"Status: {ci_summary.status.upper()}",
        f"Alignment Score: {ci_summary.alignment_score:.2%}",
        f"Conflicts Detected: {ci_summary.conflicts_detected}",
        f"Critical Conflicts: {ci_summary.critical_conflicts}",
        f"Integrity Valid: {ci_summary.ontology_integrity_valid}",
        "-" * 60,
        ci_summary.summary_message,
        "=" * 60,
    ]
    return "\n".join(lines)


def format_drift_report_text(report: OntologyDriftReport) -> str:
    """
    Format drift report as text output.

    Suitable for detailed CI logs and developer review.
    """
    lines = [
        "=" * 70,
        "ONTOLOGY DRIFT REPORT",
        f"Report ID: {report.report_id}",
        f"Generated: {report.generated_at.isoformat()}",
        "=" * 70,
        "",
        "SEVERITY BREAKDOWN",
        "-" * 40,
        f"  Critical: {report.severity_summary.critical}",
        f"  High:     {report.severity_summary.high}",
        f"  Medium:   {report.severity_summary.medium}",
        f"  Low:      {report.severity_summary.low}",
        f"  Total Penalty: {report.severity_summary.total_penalty}",
        "",
        "CONFLICT TYPE BREAKDOWN",
        "-" * 40,
        f"  Duplicate Definition:     {report.type_summary.duplicate_definition}",
        f"  Lifecycle Drift:          {report.type_summary.lifecycle_drift}",
        f"  Authority Collision:      {report.type_summary.authority_collision}",
        f"  Runtime Reinterpretation: {report.type_summary.runtime_reinterpretation}",
        f"  Semantic Alias Collision: {report.type_summary.semantic_alias_collision}",
        "",
        "AFFECTED DOMAINS",
        "-" * 40,
    ]

    if report.affected_domains:
        for domain in report.affected_domains:
            lines.append(f"  - {domain}")
    else:
        lines.append("  (none)")

    lines.extend([
        "",
        "TREND",
        "-" * 40,
    ])

    if report.trend_direction:
        lines.append(f"  Direction: {report.trend_direction}")
        lines.append(f"  Delta: {report.trend_delta:+.2%}" if report.trend_delta else "  Delta: N/A")
    else:
        lines.append("  (no historical data)")

    lines.extend([
        "",
        "TOP CONFLICTS",
        "-" * 40,
    ])

    if report.top_conflicts:
        for conflict in report.top_conflicts[:5]:
            lines.append(f"  [{conflict.severity.upper()}] {conflict.term}")
            lines.append(f"    Type: {conflict.conflict_type}")
            lines.append(f"    {conflict.description}")
            lines.append("")
    else:
        lines.append("  (none)")

    lines.extend([
        "",
        format_ci_output(report.ci_summary),
    ])

    return "\n".join(lines)
