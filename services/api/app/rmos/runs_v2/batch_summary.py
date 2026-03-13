from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .batch_tree import list_batch_tree, resolve_batch_root
from app.rmos.artifact_helpers import (
    as_dict as _as_dict,
    get_kind as _kind,
    extract_created_utc as _created_utc,
    get_artifact_id as _artifact_id,
    pick_latest as _pick_latest,
)

logger = logging.getLogger(__name__)


def _status(art: Dict[str, Any]) -> Optional[str]:
    p = _as_dict(art.get("payload") or art.get("data"))
    for k in ("status", "run_status", "state"):
        v = p.get(k)
        if v:
            return str(v).upper()
    v2 = art.get("status")
    return str(v2).upper() if v2 else None


def _risk_bucket(art: Dict[str, Any]) -> Optional[str]:
    p = _as_dict(art.get("payload") or art.get("data"))
    m = _as_dict(art.get("index_meta"))
    for src in (p, m):
        for k in ("risk_bucket", "risk_level", "risk"):
            v = src.get(k)
            if v:
                return str(v).upper()
    return None


def _type_bucket(kind: str) -> str:
    k = (kind or "").lower()
    if "batch_spec" in k:
        return "spec"
    if "batch_plan" in k:
        return "plan"
    if "decision" in k or "approve" in k:
        return "decision"
    if "toolpaths" in k:
        return "toolpaths"
    if "execution" in k:
        return "execution"
    if "job_log" in k or "joblog" in k:
        return "job_log"
    if "learning" in k:
        return "learning_event"
    return "other"


def _rollup_status(statuses: List[str]) -> str:
    """
    Conservative rollup:
      ERROR > BLOCKED > OK > UNKNOWN
    """
    S = {s.upper() for s in statuses if s}
    if "ERROR" in S:
        return "ERROR"
    if "BLOCKED" in S:
        return "BLOCKED"
    if "OK" in S or "APPROVED" in S:
        return "OK"
    return "UNKNOWN"


def _rollup_risk(risks: List[str]) -> Optional[str]:
    """
    Conservative rollup:
      RED > YELLOW > GREEN
    """
    R = {r.upper() for r in risks if r}
    if "RED" in R:
        return "RED"
    if "YELLOW" in R:
        return "YELLOW"
    if "GREEN" in R:
        return "GREEN"
    return None


@dataclass
class BatchSummaryPorts:
    list_runs_filtered: Any
    get_run: Any


# --- Helper functions extracted for complexity reduction ---


def _load_artifacts(
    ports: BatchSummaryPorts,
    tree: Dict[str, Any],
    session_id: str,
    batch_label: str,
    tool_kind: Optional[str],
    max_nodes: int,
) -> List[Dict[str, Any]]:
    """Load artifacts from tree nodes, with fallback to flat listing."""
    nodes = tree.get("nodes") or []
    ids = [n.get("id") for n in nodes if isinstance(n, dict) and n.get("id")]

    artifacts: List[Dict[str, Any]] = []
    for aid in ids:
        art = ports.get_run(aid)
        if isinstance(art, dict):
            artifacts.append(art)

    if artifacts:
        return artifacts

    # Fallback: tree had no nodes but batch might exist flat
    flat = ports.list_runs_filtered(
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
        limit=max_nodes,
    )
    items = flat.get("items") if isinstance(flat, dict) else flat
    if isinstance(items, list):
        return [a for a in items if isinstance(a, dict)]
    return []


def _compute_type_buckets(
    artifacts: List[Dict[str, Any]],
) -> Tuple[Dict[str, int], Dict[str, Optional[str]]]:
    """Group artifacts by type, compute counts and latest IDs."""
    by_type: Dict[str, List[Dict[str, Any]]] = {}
    for a in artifacts:
        t = _type_bucket(_kind(a))
        by_type.setdefault(t, []).append(a)

    counts = {t: len(v) for t, v in by_type.items()}
    latest = {t: _pick_latest(v) for t, v in by_type.items()}
    latest_ids = {t: _artifact_id(a) if a else None for t, a in latest.items()}

    return counts, latest_ids


def _compute_time_bounds(
    artifacts: List[Dict[str, Any]],
) -> Tuple[Optional[str], Optional[str]]:
    """Compute first_seen and last_seen timestamps."""
    created = [c for c in (_created_utc(a) for a in artifacts) if c]
    if not created:
        return None, None
    created.sort()
    return created[0], created[-1]


def _compute_rollups(
    artifacts: List[Dict[str, Any]],
) -> Tuple[str, Optional[str]]:
    """Compute overall status and risk rollups."""
    statuses = [s for s in (_status(a) for a in artifacts) if s]
    risks = [r for r in (_risk_bucket(a) for a in artifacts) if r]
    return _rollup_status(statuses), _rollup_risk(risks)


def _resolve_root_id(
    ports: BatchSummaryPorts,
    tree: Dict[str, Any],
    session_id: str,
    batch_label: str,
    tool_kind: Optional[str],
) -> Optional[str]:
    """Resolve batch root ID with fallback to resolver."""
    root_id = tree.get("root_artifact_id")
    if root_id:
        return root_id

    try:
        return resolve_batch_root(
            list_runs_filtered=ports.list_runs_filtered,
            session_id=session_id,
            batch_label=batch_label,
            tool_kind=tool_kind,
        )
    except (ValueError, TypeError, KeyError, AttributeError) as e:
        logger.warning(
            "Failed to resolve batch root for session=%s batch=%s: %s",
            session_id, batch_label, e,
        )
        return None


_STAGE_KEYS = ("spec", "plan", "decision", "toolpaths", "execution", "job_log", "learning_event", "other")


def _build_stages_dict(
    counts: Dict[str, int],
    latest_ids: Dict[str, Optional[str]],
) -> Dict[str, Dict[str, Any]]:
    """Build stages dict for UI cards."""
    return {
        key: {"latest_id": latest_ids.get(key), "count": counts.get(key, 0)}
        for key in _STAGE_KEYS
    }


# --- Main function (now orchestrates helpers) ---


def build_batch_summary(
    ports: BatchSummaryPorts,
    *,
    session_id: str,
    batch_label: str,
    tool_kind: Optional[str] = None,
    max_nodes: int = 5000,
) -> Dict[str, Any]:
    """
    Batch Summary Dashboard payload:
      - root id
      - counts by type
      - latest artifact ids for key stages (spec/plan/decision/toolpaths/execution/job_log/learning)
      - rollups: overall_status, overall_risk
      - timestamps: first_seen_utc, last_seen_utc
    """
    tree = list_batch_tree(
        list_runs_filtered=ports.list_runs_filtered,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
        limit=max_nodes,
    )

    artifacts = _load_artifacts(ports, tree, session_id, batch_label, tool_kind, max_nodes)
    counts, latest_ids = _compute_type_buckets(artifacts)
    first_seen, last_seen = _compute_time_bounds(artifacts)
    overall_status, overall_risk = _compute_rollups(artifacts)
    root_id = _resolve_root_id(ports, tree, session_id, batch_label, tool_kind)
    stages = _build_stages_dict(counts, latest_ids)

    return {
        "session_id": session_id,
        "batch_label": batch_label,
        "tool_kind": tool_kind,
        "root_artifact_id": root_id,
        "node_count": tree.get("node_count", len(artifacts)),
        "counts_by_type": counts,
        "stages": stages,
        "overall_status": overall_status,
        "overall_risk": overall_risk,
        "first_seen_utc": first_seen,
        "last_seen_utc": last_seen,
    }
