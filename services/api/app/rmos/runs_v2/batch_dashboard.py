from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def _as_dict(x: Any) -> Dict[str, Any]:
    return x if isinstance(x, dict) else {}


def _as_list(x: Any) -> List[Any]:
    return x if isinstance(x, list) else []


def _kind(n: Dict[str, Any]) -> str:
    return str(n.get("kind") or _as_dict(n.get("index_meta")).get("kind") or "")


def _created_utc(n: Dict[str, Any]) -> str:
    if isinstance(n.get("created_utc"), str):
        return n["created_utc"]
    p = _as_dict(n.get("payload") or n.get("data"))
    if isinstance(p.get("created_utc"), str):
        return p["created_utc"]
    return ""


def _id(n: Dict[str, Any]) -> str:
    v = n.get("id") or n.get("artifact_id")
    return str(v) if v else ""


def _group_key_from_kind(kind: str) -> str:
    k = (kind or "").lower()
    # major batch lifecycle
    if "batch_spec" in k:
        return "spec"
    if "batch_plan" in k and "choose" not in k:
        return "plan"
    if "plan_choose" in k or ("choose" in k and "plan" in k):
        return "plan_choose"
    if "batch_decision" in k:
        return "decision"
    if "batch_execution" in k or (("execution" in k) and ("batch" in k)):
        return "execution"
    # supporting
    if "toolpath" in k or "gcode" in k:
        return "toolpaths"
    if "job_log" in k or "joblog" in k:
        return "job_logs"
    if "learning" in k:
        return "learning"
    if "diff" in k:
        return "diffs"
    if (
        "batch_execution_metrics" in k
        or "execution_metrics" in k
        or ("metrics" in k and "execution" in k)
    ):
        return "execution_metrics"
    return "other"


def _latest_by_group(nodes: List[Dict[str, Any]]) -> Dict[str, Optional[str]]:
    latest: Dict[str, Tuple[str, str]] = {}  # group -> (created_utc, id)
    for n in nodes:
        if not isinstance(n, dict):
            continue
        gid = _group_key_from_kind(_kind(n))
        ts = _created_utc(n) or ""
        nid = _id(n)
        if not nid:
            continue
        cur = latest.get(gid)
        if cur is None or (ts, nid) > cur:
            latest[gid] = (ts, nid)
    return {k: v[1] for k, v in latest.items()}


def _counts_by_group(nodes: List[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for n in nodes:
        if not isinstance(n, dict):
            continue
        gid = _group_key_from_kind(_kind(n))
        counts[gid] = counts.get(gid, 0) + 1
    return counts


def _try_extract_execution_kpis_from_metrics_artifact(
    nodes: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    # Find latest "execution_metrics" artifact and return its kpis block (if present)
    best: Optional[Dict[str, Any]] = None
    best_key: Tuple[str, str] = ("", "")
    for n in nodes:
        if not isinstance(n, dict):
            continue
        if _group_key_from_kind(_kind(n)) != "execution_metrics":
            continue
        ts = _created_utc(n) or ""
        nid = _id(n)
        if (ts, nid) >= best_key:
            best_key = (ts, nid)
            best = n
    if not best:
        return None
    p = _as_dict(best.get("payload") or best.get("data"))
    kpis = p.get("kpis")
    if isinstance(kpis, dict):
        return {
            "source": "execution_metrics_artifact",
            "artifact_id": _id(best) or None,
            "kpis": kpis,
        }
    return None


def _heuristic_rollup_from_job_logs(nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Minimal KPI rollup when you haven't persisted a dedicated metrics artifact yet.
    Looks for common fields in job log payloads, sums what it can, and reports counts.
    """
    total_job_logs = 0
    total_length_mm = 0.0
    total_cut_count = 0
    total_move_count = 0
    notes_hits = {"burn": 0, "tearout": 0, "kickback": 0, "chatter": 0, "bog": 0}

    for n in nodes:
        if not isinstance(n, dict):
            continue
        if _group_key_from_kind(_kind(n)) != "job_logs":
            continue
        total_job_logs += 1
        p = _as_dict(n.get("payload") or n.get("data"))
        stats = _as_dict(p.get("statistics") or p.get("metrics") or {})
        if isinstance(stats.get("total_length_mm"), (int, float)):
            total_length_mm += float(stats["total_length_mm"])
        if isinstance(stats.get("cut_count"), (int, float)):
            total_cut_count += int(stats["cut_count"])
        if isinstance(stats.get("move_count"), (int, float)):
            total_move_count += int(stats["move_count"])

        note = ""
        for k in ("notes", "note", "operator_notes", "comments", "comment"):
            v = p.get(k)
            if isinstance(v, str):
                note = v.lower()
                break
        for k in list(notes_hits.keys()):
            if k in note:
                notes_hits[k] += 1

    return {
        "source": "job_log_heuristic",
        "job_log_count": total_job_logs,
        "kpis": {
            "total_length_mm": round(total_length_mm, 3),
            "total_cut_count": total_cut_count,
            "total_move_count": total_move_count,
        },
        "signal_mentions": notes_hits,
    }


def build_batch_summary_dashboard_card(
    *,
    session_id: str,
    batch_label: str,
    tool_kind: str = "saw",
    include_links: bool = True,
    include_kpis: bool = True,
) -> Dict[str, Any]:
    """
    Single compact "card" payload for UI dashboards.
    Includes:
      - counts by artifact group
      - latest IDs by group
      - KPI rollups (best available)
      - links to existing endpoints (tree/timeline/export)
    """
    from app.rmos.runs_v2.batch_tree import list_batch_tree

    tree = list_batch_tree(
        list_runs_filtered=None,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
    )
    nodes = _as_list(tree.get("nodes"))

    counts = _counts_by_group(nodes)
    latest = _latest_by_group(nodes)

    kpi_block: Optional[Dict[str, Any]] = None
    if include_kpis:
        kpi_block = _try_extract_execution_kpis_from_metrics_artifact(nodes)
        if not kpi_block:
            kpi_block = _heuristic_rollup_from_job_logs(nodes)

    links: Optional[Dict[str, str]] = None
    if include_links:
        # Keep them relative (frontend already knows base URL)
        links = {
            "batch_tree": f"/api/rmos/runs/batch-tree?session_id={session_id}&batch_label={batch_label}&tool_kind={tool_kind}",
            "batch_root": f"/api/rmos/runs/batch-root?session_id={session_id}&batch_label={batch_label}&tool_kind={tool_kind}",
            "batch_timeline_grouped": f"/api/rmos/runs/batch-timeline-grouped?session_id={session_id}&batch_label={batch_label}&tool_kind={tool_kind}",
            "batch_audit_export_zip": f"/api/rmos/runs/batch-audit-export?session_id={session_id}&batch_label={batch_label}&tool_kind={tool_kind}&include_attachments=true",
        }

    # A small, stable "latest ids" surface for UI cards
    latest_ids = {
        "spec": latest.get("spec"),
        "plan": latest.get("plan"),
        "plan_choose": latest.get("plan_choose"),
        "decision": latest.get("decision"),
        "execution": latest.get("execution"),
        "toolpaths": latest.get("toolpaths"),
        "job_log": latest.get("job_logs"),
        "learning_event": latest.get("learning"),
        "execution_metrics": latest.get("execution_metrics"),
        "diff": latest.get("diffs"),
        "other": latest.get("other"),
    }

    return {
        "session_id": session_id,
        "batch_label": batch_label,
        "tool_kind": tool_kind,
        "root_artifact_id": tree.get("root_artifact_id"),
        "node_count": tree.get("node_count") or len(nodes),
        "counts": counts,
        "latest_ids": latest_ids,
        "kpi_rollup": kpi_block,
        "links": links,
    }
