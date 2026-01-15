# services/api/app/rmos/runs_v2/diff.py
"""
Run Diff Engine (Stub)

Computes safe, text-only diffs between runs.
NEVER exposes toolpaths, gcode, or manufacturing secrets.

Contract: Only metadata and design-intent differences are surfaced.
"""

from __future__ import annotations

from typing import Any, Dict, List


def diff_runs(run_a: Any, run_b: Any) -> Dict[str, Any]:
    """
    Compute diff between two runs.

    Returns a safe diff structure with:
    - changed_paths: list of field paths that differ
    - diff_severity: INFO | WARN | CRITICAL
    - metadata_changes: dict of safe metadata diffs

    NEVER includes toolpath or gcode content.
    """
    changed_paths: List[str] = []
    severity = "INFO"

    # Compare safe metadata fields only
    safe_fields = ["status", "notes", "event_type", "batch_label", "parent_plan_id"]

    for field in safe_fields:
        val_a = getattr(run_a, field, None)
        val_b = getattr(run_b, field, None)
        if val_a != val_b:
            changed_paths.append(field)

    # Compare attachment counts (not content)
    att_a = getattr(run_a, "attachments", []) or []
    att_b = getattr(run_b, "attachments", []) or []
    if len(att_a) != len(att_b):
        changed_paths.append("attachments.count")

    # Determine severity
    if "status" in changed_paths:
        severity = "WARN"
    if len(changed_paths) > 5:
        severity = "WARN"

    return {
        "run_id_a": getattr(run_a, "run_id", "unknown"),
        "run_id_b": getattr(run_b, "run_id", "unknown"),
        "changed_paths": changed_paths,
        "diff_severity": severity,
        "change_count": len(changed_paths),
    }


def diff_summary(diff_result: Dict[str, Any]) -> str:
    """
    Generate human-readable summary of a diff result.

    Returns safe text only - no manufacturing data.
    """
    run_a = diff_result.get("run_id_a", "A")
    run_b = diff_result.get("run_id_b", "B")
    changed = diff_result.get("changed_paths", [])
    severity = diff_result.get("diff_severity", "INFO")

    if not changed:
        return f"No differences between {run_a} and {run_b}."

    changes_text = ", ".join(changed[:5])
    if len(changed) > 5:
        changes_text += f" (+{len(changed) - 5} more)"

    return f"[{severity}] {len(changed)} difference(s) between {run_a} and {run_b}: {changes_text}"


def build_diff(run_a: Any, run_b: Any) -> str:
    """
    Build a text diff between two runs.

    This is the main entry point used by the API.
    Returns a safe, text-only diff string.

    NEVER includes toolpath or gcode content.
    """
    diff_result = diff_runs(run_a, run_b)
    lines = [diff_summary(diff_result), ""]

    # Add field-by-field details for changed paths
    for path in diff_result.get("changed_paths", []):
        val_a = getattr(run_a, path, None) if not path.startswith("attachments") else None
        val_b = getattr(run_b, path, None) if not path.startswith("attachments") else None

        if path == "attachments.count":
            att_a = getattr(run_a, "attachments", []) or []
            att_b = getattr(run_b, "attachments", []) or []
            lines.append(f"  {path}: {len(att_a)} -> {len(att_b)}")
        else:
            # Truncate long values
            str_a = str(val_a)[:100] if val_a else "(none)"
            str_b = str(val_b)[:100] if val_b else "(none)"
            lines.append(f"  {path}: {str_a} -> {str_b}")

    return "\n".join(lines)
