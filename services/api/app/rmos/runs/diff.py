"""
RMOS Run Diff Engine

Provides authoritative diff between two run artifacts.
Used for:
- Comparing runs in the UI
- Detecting drift in replay
- Audit trail analysis
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List, Optional

from .schemas import RunArtifact


def _to_dict(obj: Any) -> Any:
    """Convert dataclass to dict if needed."""
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    return obj


def _diff_values(a: Any, b: Any) -> Optional[Dict[str, Any]]:
    """Diff two values. Returns None if equal."""
    if a == b:
        return None
    return {"a": a, "b": b}


def _diff_dict(a: Dict[str, Any] | None, b: Dict[str, Any] | None) -> Dict[str, Any]:
    """Diff two dicts, returning changed keys."""
    a = a or {}
    b = b or {}
    keys = sorted(set(a.keys()) | set(b.keys()))
    out: Dict[str, Any] = {}
    for k in keys:
        if a.get(k) != b.get(k):
            out[k] = {"a": a.get(k), "b": b.get(k)}
    return out


def _severity_from_diff(diff: Dict[str, Any]) -> str:
    """
    Determine severity from diff.
    
    - CRITICAL: gcode/toolpaths hash changed, risk bucket changed, status changed
    - WARNING: feasibility score changed, request hash changed
    - INFO: notes/errors-only changes
    """
    critical_keys = {
        "hashes.gcode_hash",
        "hashes.toolpaths_hash",
        "feasibility.risk_bucket",
        "status",
    }
    warning_keys = {
        "hashes.request_hash",
        "feasibility.score",
    }

    changed_paths = set(diff.get("changed_paths", []))

    if any(p in changed_paths for p in critical_keys):
        return "CRITICAL"
    if any(p in changed_paths for p in warning_keys):
        return "WARNING"
    if changed_paths:
        return "INFO"
    return "INFO"


def diff_runs(a: RunArtifact, b: RunArtifact) -> Dict[str, Any]:
    """
    Compute authoritative diff between two run artifacts.
    
    Returns structured diff with:
    - a/b run identifiers
    - diff_severity: CRITICAL | WARNING | INFO
    - changed_paths: list of dotted paths that changed
    - diff: structured diff data
    """
    A = _to_dict(a)
    B = _to_dict(b)

    diffs: Dict[str, Any] = {}
    changed_paths: List[str] = []

    def set_diff(path: str, d: Optional[Dict[str, Any]]):
        if d is None:
            return
        diffs[path] = d
        changed_paths.append(path)

    # Top-level identity
    set_diff("event_type", _diff_values(A.get("event_type"), B.get("event_type")))
    set_diff("status", _diff_values(A.get("status"), B.get("status")))

    # Context group
    ctx_fields = ["tool_id", "material_id", "machine_id", "workflow_mode", "workflow_session_id"]
    ctx = {}
    for f in ctx_fields:
        d = _diff_values(A.get(f), B.get(f))
        if d:
            ctx[f] = d
            changed_paths.append(f"context.{f}")
    if ctx:
        diffs["context"] = ctx

    # Hashes group
    hashes = {}
    for f in ["request_hash", "toolpaths_hash", "gcode_hash", "geometry_hash"]:
        d = _diff_values(A.get(f), B.get(f))
        if d:
            hashes[f] = d
            changed_paths.append(f"hashes.{f}")
    if hashes:
        diffs["hashes"] = hashes

    # Feasibility diff
    feas_diff = _diff_dict(A.get("feasibility"), B.get("feasibility"))
    if feas_diff:
        diffs["feasibility"] = feas_diff
        if "risk_bucket" in feas_diff:
            changed_paths.append("feasibility.risk_bucket")
        if "score" in feas_diff:
            changed_paths.append("feasibility.score")

    # Attachments diff
    a_atts = A.get("attachments") or []
    b_atts = B.get("attachments") or []

    def norm_atts(atts):
        out = []
        for x in atts:
            if isinstance(x, dict):
                out.append({
                    "sha256": x.get("sha256"),
                    "kind": x.get("kind"),
                    "filename": x.get("filename"),
                })
        return sorted(out, key=lambda z: (z.get("kind") or "", z.get("sha256") or ""))

    na = norm_atts(a_atts)
    nb = norm_atts(b_atts)
    if na != nb:
        diffs["attachments"] = {"a": na, "b": nb}
        changed_paths.append("attachments")

    # Notes / errors
    set_diff("notes", _diff_values(A.get("notes"), B.get("notes")))
    set_diff("errors", _diff_values(A.get("errors"), B.get("errors")))

    severity = _severity_from_diff({"changed_paths": changed_paths})

    return {
        "a": {"run_id": a.run_id, "created_at_utc": a.created_at_utc},
        "b": {"run_id": b.run_id, "created_at_utc": b.created_at_utc},
        "diff_severity": severity,
        "changed_paths": sorted(set(changed_paths)),
        "diff": diffs,
    }
