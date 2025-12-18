"""
RMOS Run Diff Engine v2 - Governance Compliant

Provides authoritative diff between two run artifacts.
Adapted for Pydantic-based RunArtifact models.

Used for:
- Comparing runs in the UI
- Detecting drift in replay
- Audit trail analysis
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .schemas import RunArtifact


def _to_dict(obj: Any) -> Any:
    """Convert Pydantic model to dict if needed."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
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

    CRITICAL: gcode/toolpaths hash changed, risk_level changed, status changed
    WARNING: feasibility_sha256 changed, score changed
    INFO: notes/errors-only changes
    """
    critical_keys = {
        "hashes.gcode_sha256",
        "hashes.toolpaths_sha256",
        "decision.risk_level",
        "status",
    }
    warning_keys = {
        "hashes.feasibility_sha256",
        "decision.score",
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
    set_diff("mode", _diff_values(A.get("mode"), B.get("mode")))

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

    # Hashes group (v2 uses nested Hashes model)
    a_hashes = A.get("hashes") or {}
    b_hashes = B.get("hashes") or {}
    hashes = {}
    for f in ["feasibility_sha256", "toolpaths_sha256", "gcode_sha256", "opplan_sha256"]:
        d = _diff_values(a_hashes.get(f), b_hashes.get(f))
        if d:
            hashes[f] = d
            changed_paths.append(f"hashes.{f}")
    if hashes:
        diffs["hashes"] = hashes

    # Decision group (v2 uses nested RunDecision model)
    a_decision = A.get("decision") or {}
    b_decision = B.get("decision") or {}
    decision_diff = {}
    for f in ["risk_level", "score", "block_reason"]:
        d = _diff_values(a_decision.get(f), b_decision.get(f))
        if d:
            decision_diff[f] = d
            changed_paths.append(f"decision.{f}")
    if decision_diff:
        diffs["decision"] = decision_diff

    # Feasibility diff
    feas_diff = _diff_dict(A.get("feasibility"), B.get("feasibility"))
    if feas_diff:
        diffs["feasibility"] = feas_diff
        for k in feas_diff:
            changed_paths.append(f"feasibility.{k}")

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

    # Advisory inputs diff
    a_advisory = A.get("advisory_inputs") or []
    b_advisory = B.get("advisory_inputs") or []

    def norm_advisory(advs):
        out = []
        for x in advs:
            if isinstance(x, dict):
                out.append({
                    "advisory_id": x.get("advisory_id"),
                    "kind": x.get("kind"),
                })
        return sorted(out, key=lambda z: z.get("advisory_id") or "")

    na_adv = norm_advisory(a_advisory)
    nb_adv = norm_advisory(b_advisory)
    if na_adv != nb_adv:
        diffs["advisory_inputs"] = {"a": na_adv, "b": nb_adv}
        changed_paths.append("advisory_inputs")

    # Notes / errors
    set_diff("notes", _diff_values(A.get("notes"), B.get("notes")))
    set_diff("errors", _diff_values(A.get("errors"), B.get("errors")))

    # Meta diff
    meta_diff = _diff_dict(A.get("meta"), B.get("meta"))
    if meta_diff:
        diffs["meta"] = meta_diff
        for k in meta_diff:
            changed_paths.append(f"meta.{k}")

    severity = _severity_from_diff({"changed_paths": changed_paths})

    # Format created_at for output
    a_created = A.get("created_at_utc")
    b_created = B.get("created_at_utc")
    if hasattr(a_created, "isoformat"):
        a_created = a_created.isoformat()
    if hasattr(b_created, "isoformat"):
        b_created = b_created.isoformat()

    return {
        "a": {"run_id": A.get("run_id"), "created_at_utc": a_created},
        "b": {"run_id": B.get("run_id"), "created_at_utc": b_created},
        "diff_severity": severity,
        "changed_paths": sorted(set(changed_paths)),
        "diff": diffs,
    }


def diff_summary(diff_result: Dict[str, Any]) -> str:
    """
    Generate a human-readable summary of a diff result.

    Args:
        diff_result: Output from diff_runs()

    Returns:
        Brief summary string
    """
    severity = diff_result.get("diff_severity", "INFO")
    changed = diff_result.get("changed_paths", [])

    if not changed:
        return "No differences detected."

    return f"[{severity}] {len(changed)} field(s) changed: {', '.join(changed[:5])}{'...' if len(changed) > 5 else ''}"
