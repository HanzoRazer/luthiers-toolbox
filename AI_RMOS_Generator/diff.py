"""
RMOS Runs v2 Diff

Run comparison with severity classification for audit review.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .schemas import RunArtifact


def diff_runs(a: RunArtifact, b: RunArtifact) -> Dict[str, Any]:
    """
    Compare two run artifacts and return structured diff.

    Severity levels:
    - CRITICAL: Hash mismatch, status change to/from ERROR
    - WARNING: Risk level change, significant score drift
    - INFO: Metadata differences, minor changes
    """
    differences: List[Dict[str, Any]] = []
    severity = "INFO"

    def upgrade_severity(new_sev: str) -> None:
        nonlocal severity
        if new_sev == "CRITICAL":
            severity = "CRITICAL"
        elif new_sev == "WARNING" and severity != "CRITICAL":
            severity = "WARNING"

    # Identity check
    if a.run_id == b.run_id:
        differences.append({
            "field": "run_id",
            "note": "Comparing same run_id - likely version comparison",
            "severity": "INFO",
        })

    # Status comparison (CRITICAL if ERROR involved)
    if a.status != b.status:
        sev = "CRITICAL" if "ERROR" in (a.status, b.status) else "WARNING"
        differences.append({
            "field": "status",
            "a": a.status,
            "b": b.status,
            "severity": sev,
        })
        upgrade_severity(sev)

    # Risk level comparison
    if a.decision.risk_level != b.decision.risk_level:
        # RED involved = CRITICAL
        sev = "CRITICAL" if "RED" in (a.decision.risk_level, b.decision.risk_level) else "WARNING"
        differences.append({
            "field": "decision.risk_level",
            "a": a.decision.risk_level,
            "b": b.decision.risk_level,
            "severity": sev,
        })
        upgrade_severity(sev)

    # Score drift
    if a.decision.score is not None and b.decision.score is not None:
        drift = abs(a.decision.score - b.decision.score)
        if drift > 0.01:
            sev = "WARNING" if drift > 5.0 else "INFO"
            differences.append({
                "field": "decision.score",
                "a": a.decision.score,
                "b": b.decision.score,
                "drift": drift,
                "severity": sev,
            })
            upgrade_severity(sev)

    # Hash comparisons (CRITICAL if mismatch)
    if a.hashes.feasibility_sha256 != b.hashes.feasibility_sha256:
        differences.append({
            "field": "hashes.feasibility_sha256",
            "a": a.hashes.feasibility_sha256,
            "b": b.hashes.feasibility_sha256,
            "severity": "CRITICAL",
        })
        upgrade_severity("CRITICAL")

    if a.hashes.gcode_sha256 and b.hashes.gcode_sha256:
        if a.hashes.gcode_sha256 != b.hashes.gcode_sha256:
            differences.append({
                "field": "hashes.gcode_sha256",
                "a": a.hashes.gcode_sha256,
                "b": b.hashes.gcode_sha256,
                "severity": "WARNING",
            })
            upgrade_severity("WARNING")

    if a.hashes.toolpaths_sha256 and b.hashes.toolpaths_sha256:
        if a.hashes.toolpaths_sha256 != b.hashes.toolpaths_sha256:
            differences.append({
                "field": "hashes.toolpaths_sha256",
                "a": a.hashes.toolpaths_sha256,
                "b": b.hashes.toolpaths_sha256,
                "severity": "WARNING",
            })
            upgrade_severity("WARNING")

    # Tool/mode comparison
    if a.tool_id != b.tool_id:
        differences.append({
            "field": "tool_id",
            "a": a.tool_id,
            "b": b.tool_id,
            "severity": "INFO",
        })

    if a.mode != b.mode:
        differences.append({
            "field": "mode",
            "a": a.mode,
            "b": b.mode,
            "severity": "INFO",
        })

    # Block reason comparison
    if a.decision.block_reason != b.decision.block_reason:
        differences.append({
            "field": "decision.block_reason",
            "a": a.decision.block_reason,
            "b": b.decision.block_reason,
            "severity": "WARNING" if any([a.decision.block_reason, b.decision.block_reason]) else "INFO",
        })

    # Warnings comparison
    a_warnings = set(a.decision.warnings)
    b_warnings = set(b.decision.warnings)
    if a_warnings != b_warnings:
        added = list(b_warnings - a_warnings)
        removed = list(a_warnings - b_warnings)
        differences.append({
            "field": "decision.warnings",
            "added": added,
            "removed": removed,
            "severity": "INFO",
        })

    # Advisory count comparison
    if len(a.advisory_inputs) != len(b.advisory_inputs):
        differences.append({
            "field": "advisory_inputs.count",
            "a": len(a.advisory_inputs),
            "b": len(b.advisory_inputs),
            "severity": "INFO",
        })

    # Explanation status comparison
    if a.explanation_status != b.explanation_status:
        differences.append({
            "field": "explanation_status",
            "a": a.explanation_status,
            "b": b.explanation_status,
            "severity": "INFO",
        })

    return {
        "severity": severity,
        "run_a": a.run_id,
        "run_b": b.run_id,
        "differences": differences,
        "difference_count": len(differences),
    }


def summarize_diff(diff_result: Dict[str, Any]) -> str:
    """Generate human-readable summary of diff."""
    severity = diff_result["severity"]
    count = diff_result["difference_count"]
    
    if count == 0:
        return "Runs are identical"
    
    critical = sum(1 for d in diff_result["differences"] if d.get("severity") == "CRITICAL")
    warnings = sum(1 for d in diff_result["differences"] if d.get("severity") == "WARNING")
    
    parts = []
    if critical:
        parts.append(f"{critical} critical")
    if warnings:
        parts.append(f"{warnings} warnings")
    if count - critical - warnings:
        parts.append(f"{count - critical - warnings} info")
    
    return f"[{severity}] {count} differences: {', '.join(parts)}"
