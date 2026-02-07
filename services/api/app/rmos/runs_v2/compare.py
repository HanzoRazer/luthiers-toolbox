from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple, Union


JsonDict = Dict[str, Any]


def _as_dict(obj: Any) -> JsonDict:
    """
    Normalize pydantic models / dicts into dict.
    """
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        try:
            return obj.model_dump()
        except (ValueError, TypeError, AttributeError):  # WP-1: narrowed from except Exception
            return {}
    return {}


def _as_list(obj: Any) -> List[Any]:
    if obj is None:
        return []
    if isinstance(obj, list):
        return obj
    # pydantic list-like
    try:
        return list(obj)
    except (ValueError, TypeError):  # WP-1: narrowed from except Exception
        return []


def _safe_str(x: Any) -> str:
    try:
        return str(x)
    except (ValueError, TypeError):  # WP-1: narrowed from except Exception
        return ""


def _dict_diff(a: JsonDict, b: JsonDict) -> JsonDict:
    keys = set(a.keys()) | set(b.keys())
    out: JsonDict = {}
    for k in sorted(keys):
        va = a.get(k)
        vb = b.get(k)
        if va != vb:
            out[k] = {"a": va, "b": vb}
    return out


def _rules_from_feasibility(feas: JsonDict) -> Set[str]:
    rt = feas.get("rules_triggered") or []
    if not isinstance(rt, list):
        return set()
    return {(_safe_str(x).strip().upper()) for x in rt if _safe_str(x).strip()}


def _attachments_index(atts: List[JsonDict]) -> Set[Tuple[str, str]]:
    """
    Identify attachments by (kind, sha256). Filename can change; sha is canonical.
    """
    out: Set[Tuple[str, str]] = set()
    for a in atts:
        if not isinstance(a, dict):
            continue
        kind = _safe_str(a.get("kind")).strip()
        sha = _safe_str(a.get("sha256")).strip()
        if kind and sha:
            out.add((kind, sha))
    return out


def _param_diff_from_request_summary(a_req: JsonDict, b_req: JsonDict) -> JsonDict:
    """
    Param-focused diff: only surface simple scalar changes from request_summary.
    (We intentionally avoid huge nested diffs for operator UX.)
    """
    out: JsonDict = {}
    keys = set(a_req.keys()) | set(b_req.keys())
    for k in sorted(keys):
        va = a_req.get(k)
        vb = b_req.get(k)
        if va == vb:
            continue
        # Keep scalar-ish values. If nested, still include but under "request_diff".
        scalar = isinstance(va, (str, int, float, bool, type(None))) and isinstance(vb, (str, int, float, bool, type(None)))
        if scalar:
            out[k] = [va, vb]
    return out


@dataclass(frozen=True)
class CompareSummary:
    risk_changed: bool
    blocking_changed: bool
    feasibility_changed: bool
    cam_changed: bool
    gcode_changed: bool
    attachments_changed: bool
    override_changed: bool


def compare_run_artifacts(run_a: Any, run_b: Any) -> JsonDict:
    """
    Produce a structured, deterministic comparison between two RunArtifacts.
    No timestamps, no prose, just facts.
    """
    ra = run_a
    rb = run_b

    a_req = _as_dict(getattr(ra, "request_summary", None) if hasattr(ra, "request_summary") else _as_dict(ra).get("request_summary"))
    b_req = _as_dict(getattr(rb, "request_summary", None) if hasattr(rb, "request_summary") else _as_dict(rb).get("request_summary"))

    a_feat = _as_dict(getattr(ra, "feasibility", None) if hasattr(ra, "feasibility") else _as_dict(ra).get("feasibility"))
    b_feat = _as_dict(getattr(rb, "feasibility", None) if hasattr(rb, "feasibility") else _as_dict(rb).get("feasibility"))

    a_dec = _as_dict(getattr(ra, "decision", None) if hasattr(ra, "decision") else _as_dict(ra).get("decision"))
    b_dec = _as_dict(getattr(rb, "decision", None) if hasattr(rb, "decision") else _as_dict(rb).get("decision"))

    a_hash = _as_dict(getattr(ra, "hashes", None) if hasattr(ra, "hashes") else _as_dict(ra).get("hashes"))
    b_hash = _as_dict(getattr(rb, "hashes", None) if hasattr(rb, "hashes") else _as_dict(rb).get("hashes"))

    a_atts_raw = _as_list(getattr(ra, "attachments", None) if hasattr(ra, "attachments") else _as_dict(ra).get("attachments"))
    b_atts_raw = _as_list(getattr(rb, "attachments", None) if hasattr(rb, "attachments") else _as_dict(rb).get("attachments"))
    a_atts = [_as_dict(x) for x in a_atts_raw]
    b_atts = [_as_dict(x) for x in b_atts_raw]

    # Key outcome fields
    a_risk = _safe_str(a_dec.get("risk_level", "UNKNOWN")).upper()
    b_risk = _safe_str(b_dec.get("risk_level", "UNKNOWN")).upper()
    a_block = _safe_str(a_dec.get("block_reason") or "").strip()
    b_block = _safe_str(b_dec.get("block_reason") or "").strip()

    # Feasibility rule deltas (operator-friendly)
    a_rules = _rules_from_feasibility(a_feat)
    b_rules = _rules_from_feasibility(b_feat)
    rules_added = sorted(list(b_rules - a_rules))
    rules_removed = sorted(list(a_rules - b_rules))

    # CAM/gcode changes (hash driven)
    a_toolpaths = _safe_str(a_hash.get("toolpaths_sha256") or "").strip()
    b_toolpaths = _safe_str(b_hash.get("toolpaths_sha256") or "").strip()
    a_opplan = _safe_str(a_hash.get("opplan_sha256") or "").strip()
    b_opplan = _safe_str(b_hash.get("opplan_sha256") or "").strip()
    a_gcode = _safe_str(a_hash.get("gcode_sha256") or "").strip()
    b_gcode = _safe_str(b_hash.get("gcode_sha256") or "").strip()

    # Override detection (presence of override attachment or meta.override)
    def _has_override(run_obj: Any, atts: List[JsonDict]) -> bool:
        for a in atts:
            if _safe_str(a.get("kind")).strip() == "override":
                return True
        meta = None
        if hasattr(run_obj, "meta"):
            meta = getattr(run_obj, "meta", None)
        else:
            meta = _as_dict(run_obj).get("meta")
        meta = _as_dict(meta)
        return "override" in meta

    a_override = _has_override(ra, a_atts)
    b_override = _has_override(rb, b_atts)

    # Attachment changes by identity (kind, sha)
    a_idx = _attachments_index(a_atts)
    b_idx = _attachments_index(b_atts)
    only_in_a = sorted(list(a_idx - b_idx))
    only_in_b = sorted(list(b_idx - a_idx))

    request_diff = _dict_diff(a_req, b_req)
    feasibility_diff = _dict_diff(a_feat, b_feat)
    decision_diff = _dict_diff(a_dec, b_dec)
    hashes_diff = _dict_diff(a_hash, b_hash)

    param_diff = _param_diff_from_request_summary(a_req, b_req)

    summary = CompareSummary(
        risk_changed=(a_risk != b_risk),
        blocking_changed=(a_block != b_block),
        feasibility_changed=bool(rules_added or rules_removed or feasibility_diff),
        cam_changed=(a_toolpaths != b_toolpaths) or (a_opplan != b_opplan),
        gcode_changed=(a_gcode != b_gcode),
        attachments_changed=bool(only_in_a or only_in_b),
        override_changed=(a_override != b_override),
    )

    return {
        "summary": {
            "risk_changed": summary.risk_changed,
            "blocking_changed": summary.blocking_changed,
            "feasibility_changed": summary.feasibility_changed,
            "cam_changed": summary.cam_changed,
            "gcode_changed": summary.gcode_changed,
            "attachments_changed": summary.attachments_changed,
            "override_changed": summary.override_changed,
        },
        "decision_diff": {
            "before": {"risk_level": a_risk, "block_reason": a_block or None},
            "after": {"risk_level": b_risk, "block_reason": b_block or None},
        },
        "feasibility_diff": {
            "rules_added": rules_added,
            "rules_removed": rules_removed,
        },
        "param_diff": param_diff,
        "artifact_diff": {
            "toolpaths_sha256": [a_toolpaths or None, b_toolpaths or None] if a_toolpaths != b_toolpaths else None,
            "opplan_sha256": [a_opplan or None, b_opplan or None] if a_opplan != b_opplan else None,
            "gcode_sha256": [a_gcode or None, b_gcode or None] if a_gcode != b_gcode else None,
        },
        # Optional deep diffs (useful for engineers / debugging)
        "request_diff": request_diff,
        "feasibility_deep_diff": feasibility_diff,
        "decision_deep_diff": decision_diff,
        "hashes_deep_diff": hashes_diff,
        "attachments_diff": {
            "only_in_a": [{"kind": k, "sha256": s} for (k, s) in only_in_a],
            "only_in_b": [{"kind": k, "sha256": s} for (k, s) in only_in_b],
        },
    }
