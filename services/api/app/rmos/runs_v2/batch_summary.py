from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .batch_tree import list_batch_tree, resolve_batch_root


def _as_dict(x: Any) -> Dict[str, Any]:
    return x if isinstance(x, dict) else {}


def _kind(art: Dict[str, Any]) -> str:
    return str(art.get("kind") or _as_dict(art.get("index_meta")).get("kind") or "")


def _created_utc(art: Dict[str, Any]) -> str:
    p = _as_dict(art.get("payload") or art.get("data"))
    if isinstance(p.get("created_utc"), str):
        return p["created_utc"]
    if isinstance(art.get("created_utc"), str):
        return art["created_utc"]
    return ""


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


def _artifact_id(art: Dict[str, Any]) -> Optional[str]:
    v = art.get("id") or art.get("artifact_id")
    return str(v) if v else None


def _pick_latest(arts: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not arts:
        return None
    arts = [a for a in arts if isinstance(a, dict)]
    arts.sort(
        key=lambda a: (_created_utc(a) or "9999", str(_artifact_id(a) or "")),
        reverse=True,
    )
    return arts[0]


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
    nodes = tree.get("nodes") or []
    ids = [n.get("id") for n in nodes if isinstance(n, dict) and n.get("id")]

    artifacts: List[Dict[str, Any]] = []
    for aid in ids:
        art = ports.get_run(aid)
        if isinstance(art, dict):
            artifacts.append(art)

    # fallback if tree had no nodes but batch exists flat
    if not artifacts:
        flat = ports.list_runs_filtered(session_id=session_id, batch_label=batch_label, tool_kind=tool_kind, limit=max_nodes)
        items = flat.get("items") if isinstance(flat, dict) else flat
        if isinstance(items, list):
            artifacts = [a for a in items if isinstance(a, dict)]

    # counts + buckets
    by_type: Dict[str, List[Dict[str, Any]]] = {}
    for a in artifacts:
        t = _type_bucket(_kind(a))
        by_type.setdefault(t, []).append(a)

    counts = {t: len(v) for t, v in by_type.items()}

    latest = {t: _pick_latest(v) for t, v in by_type.items()}
    latest_ids = {t: _artifact_id(a) if a else None for t, a in latest.items()}

    # time bounds
    created = [c for c in (_created_utc(a) for a in artifacts) if c]
    created.sort()
    first_seen = created[0] if created else None
    last_seen = created[-1] if created else None

    # rollups across all artifacts (or key types if you want to be stricter later)
    statuses = [s for s in (_status(a) for a in artifacts) if s]
    risks = [r for r in (_risk_bucket(a) for a in artifacts) if r]

    overall_status = _rollup_status(statuses)
    overall_risk = _rollup_risk(risks)

    # root resolution (prefer resolver, but keep tree root if present)
    root_id = tree.get("root_artifact_id")
    if not root_id:
        try:
            root_id = resolve_batch_root(
                list_runs_filtered=ports.list_runs_filtered,
                session_id=session_id,
                batch_label=batch_label,
                tool_kind=tool_kind,
            )
        except Exception:
            root_id = None

    # small "stage" surface for UI cards
    stages = {
        "spec": {"latest_id": latest_ids.get("spec"), "count": counts.get("spec", 0)},
        "plan": {"latest_id": latest_ids.get("plan"), "count": counts.get("plan", 0)},
        "decision": {"latest_id": latest_ids.get("decision"), "count": counts.get("decision", 0)},
        "toolpaths": {"latest_id": latest_ids.get("toolpaths"), "count": counts.get("toolpaths", 0)},
        "execution": {"latest_id": latest_ids.get("execution"), "count": counts.get("execution", 0)},
        "job_log": {"latest_id": latest_ids.get("job_log"), "count": counts.get("job_log", 0)},
        "learning_event": {"latest_id": latest_ids.get("learning_event"), "count": counts.get("learning_event", 0)},
        "other": {"latest_id": latest_ids.get("other"), "count": counts.get("other", 0)},
    }

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
