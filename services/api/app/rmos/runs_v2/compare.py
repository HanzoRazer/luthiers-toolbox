from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple, Union

logger = logging.getLogger(__name__)

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
        except (ValueError, TypeError, AttributeError) as e:  # WP-1: narrowed from except Exception
            logger.debug("Failed to convert object to dict via model_dump: %s", e)
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
    except (ValueError, TypeError) as e:  # WP-1: narrowed from except Exception
        logger.debug("Failed to convert object to list: %s", e)
        return []


def _safe_str(x: Any) -> str:
    try:
        return str(x)
    except (ValueError, TypeError) as e:  # WP-1: narrowed from except Exception
        logger.debug("Failed to convert object to string: %s", e)
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


def _get_field_dict(run_obj: Any, name: str) -> JsonDict:
    """Extract a named field from a run object (attr or dict) and normalize to dict."""
    if hasattr(run_obj, name):
        return _as_dict(getattr(run_obj, name, None))
    return _as_dict(_as_dict(run_obj).get(name))


def _get_field_list(run_obj: Any, name: str) -> List[Any]:
    """Extract a named field from a run object (attr or dict) and normalize to list."""
    if hasattr(run_obj, name):
        return _as_list(getattr(run_obj, name, None))
    return _as_list(_as_dict(run_obj).get(name))


def _has_override(run_obj: Any, atts: List[JsonDict]) -> bool:
    """Check if a run has an override attachment or meta.override."""
    for a in atts:
        if _safe_str(a.get("kind")).strip() == "override":
            return True
    meta = _as_dict(getattr(run_obj, "meta", None) if hasattr(run_obj, "meta") else _as_dict(run_obj).get("meta"))
    return "override" in meta


def _compute_hash_changes(a_hash: JsonDict, b_hash: JsonDict) -> JsonDict:
    """Compare hash fields and return diff dict with [before, after] for changed hashes."""
    result: JsonDict = {}
    for key in ("toolpaths_sha256", "opplan_sha256", "gcode_sha256"):
        va = _safe_str(a_hash.get(key) or "").strip()
        vb = _safe_str(b_hash.get(key) or "").strip()
        result[key] = [va or None, vb or None] if va != vb else None
    return result


def compare_run_artifacts(run_a: Any, run_b: Any) -> JsonDict:
    """
    Produce a structured, deterministic comparison between two RunArtifacts.
    No timestamps, no prose, just facts.
    """
    # Extract fields
    a_req = _get_field_dict(run_a, "request_summary")
    b_req = _get_field_dict(run_b, "request_summary")
    a_feat = _get_field_dict(run_a, "feasibility")
    b_feat = _get_field_dict(run_b, "feasibility")
    a_dec = _get_field_dict(run_a, "decision")
    b_dec = _get_field_dict(run_b, "decision")
    a_hash = _get_field_dict(run_a, "hashes")
    b_hash = _get_field_dict(run_b, "hashes")
    a_atts = [_as_dict(x) for x in _get_field_list(run_a, "attachments")]
    b_atts = [_as_dict(x) for x in _get_field_list(run_b, "attachments")]

    # Key outcome fields
    a_risk = _safe_str(a_dec.get("risk_level", "UNKNOWN")).upper()
    b_risk = _safe_str(b_dec.get("risk_level", "UNKNOWN")).upper()
    a_block = _safe_str(a_dec.get("block_reason") or "").strip()
    b_block = _safe_str(b_dec.get("block_reason") or "").strip()

    # Feasibility rule deltas
    a_rules = _rules_from_feasibility(a_feat)
    b_rules = _rules_from_feasibility(b_feat)
    rules_added = sorted(list(b_rules - a_rules))
    rules_removed = sorted(list(a_rules - b_rules))

    # Hash-driven artifact changes
    hash_changes = _compute_hash_changes(a_hash, b_hash)
    a_toolpaths = _safe_str(a_hash.get("toolpaths_sha256") or "").strip()
    b_toolpaths = _safe_str(b_hash.get("toolpaths_sha256") or "").strip()
    a_opplan = _safe_str(a_hash.get("opplan_sha256") or "").strip()
    b_opplan = _safe_str(b_hash.get("opplan_sha256") or "").strip()
    a_gcode = _safe_str(a_hash.get("gcode_sha256") or "").strip()
    b_gcode = _safe_str(b_hash.get("gcode_sha256") or "").strip()

    # Override + attachment changes
    a_override = _has_override(run_a, a_atts)
    b_override = _has_override(run_b, b_atts)
    a_idx = _attachments_index(a_atts)
    b_idx = _attachments_index(b_atts)
    only_in_a = sorted(list(a_idx - b_idx))
    only_in_b = sorted(list(b_idx - a_idx))

    # Diffs
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
        "artifact_diff": hash_changes,
        "request_diff": request_diff,
        "feasibility_deep_diff": feasibility_diff,
        "decision_deep_diff": decision_diff,
        "hashes_deep_diff": hashes_diff,
        "attachments_diff": {
            "only_in_a": [{"kind": k, "sha256": s} for (k, s) in only_in_a],
            "only_in_b": [{"kind": k, "sha256": s} for (k, s) in only_in_b],
        },
    }
