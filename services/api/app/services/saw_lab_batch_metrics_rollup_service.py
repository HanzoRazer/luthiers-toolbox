from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def _id(it: Dict[str, Any]) -> Optional[str]:
    return it.get("artifact_id") or it.get("id")


def _meta(it: Dict[str, Any]) -> Dict[str, Any]:
    m = it.get("index_meta")
    return m if isinstance(m, dict) else {}


def _num(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def _truthy(x: Any) -> bool:
    if isinstance(x, bool):
        return x
    if isinstance(x, (int, float)):
        return x != 0
    if isinstance(x, str):
        return x.strip().lower() in ("1", "true", "yes", "y", "ok", "pass")
    return False


def _collect_metrics_from_log_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a single job log payload into a small canonical metrics dict.
    We accept arbitrary keys but roll up known ones.
    """
    metrics = payload.get("metrics") or {}
    if not isinstance(metrics, dict):
        metrics = {}

    # Common keys (optional)
    # Times
    cut_time_s = _num(metrics.get("cut_time_s") or metrics.get("cut_time_sec") or metrics.get("cut_time_seconds"))
    setup_time_s = _num(metrics.get("setup_time_s") or metrics.get("setup_time_sec") or metrics.get("setup_time_seconds"))
    total_time_s = _num(metrics.get("total_time_s") or metrics.get("total_time_sec") or metrics.get("total_time_seconds"))

    # Yield/quality
    parts_ok = _num(metrics.get("parts_ok"))
    parts_scrap = _num(metrics.get("parts_scrap") or metrics.get("scrap_count"))
    burn = metrics.get("burn")
    tearout = metrics.get("tearout")
    kickback_event = metrics.get("kickback_event") or metrics.get("kickback")

    # Notes for quick triage flags (optional)
    notes = payload.get("notes") or ""
    if isinstance(notes, str):
        ln = notes.lower()
        if burn is None and ("burn" in ln or "scorch" in ln):
            burn = True
        if tearout is None and ("tearout" in ln or "tear out" in ln):
            tearout = True
        if kickback_event is None and ("kickback" in ln):
            kickback_event = True

    return {
        "cut_time_s": cut_time_s,
        "setup_time_s": setup_time_s,
        "total_time_s": total_time_s,
        "parts_ok": parts_ok,
        "parts_scrap": parts_scrap,
        "burn": burn,
        "tearout": tearout,
        "kickback_event": kickback_event,
        # preserve raw metrics (bounded keys count later)
        "_raw_metrics": metrics,
    }


def compute_execution_rollup(
    *,
    batch_execution_artifact_id: str,
    limit_logs: int = 200,
) -> Dict[str, Any]:
    """
    Roll up metrics from saw_batch_job_log artifacts for a given execution.

    Returns a summary dict suitable for:
      - UI display
      - persisting as an artifact (saw_batch_execution_rollup)
      - alerting thresholds later
    """
    from app.rmos.run_artifacts.store import query_run_artifacts, read_run_artifact

    # Validate execution artifact exists
    exec_art = read_run_artifact(batch_execution_artifact_id)
    exec_d: Dict[str, Any] = exec_art if isinstance(exec_art, dict) else {
        "artifact_id": getattr(exec_art, "artifact_id", None) or getattr(exec_art, "id", None),
        "kind": getattr(exec_art, "kind", None),
        "status": getattr(exec_art, "status", None),
        "index_meta": getattr(exec_art, "index_meta", None),
        "payload": getattr(exec_art, "payload", None),
        "created_utc": getattr(exec_art, "created_utc", None),
    }
    if str(exec_d.get("kind") or "") != "saw_batch_execution":
        raise ValueError("batch_execution_artifact_id must reference kind='saw_batch_execution'")

    exec_meta = _meta(exec_d)
    batch_label = exec_meta.get("batch_label")
    session_id = exec_meta.get("session_id")
    decision_id = exec_meta.get("parent_batch_decision_artifact_id")
    plan_id = exec_meta.get("parent_batch_plan_artifact_id")
    spec_id = exec_meta.get("parent_batch_spec_artifact_id")

    logs = query_run_artifacts(
        kind="saw_batch_job_log",
        parent_batch_execution_artifact_id=batch_execution_artifact_id,
        limit=min(max(int(limit_logs), 1), 2000),
        offset=0,
    )
    # Best-effort newest-first if created_utc exists
    logs.sort(key=lambda x: str(x.get("created_utc") or ""), reverse=True)

    # Aggregate
    n = 0
    sum_cut = 0.0
    sum_setup = 0.0
    sum_total = 0.0
    cnt_cut = cnt_setup = cnt_total = 0
    sum_ok = 0.0
    sum_scrap = 0.0
    cnt_ok = cnt_scrap = 0

    burn_events = 0
    tearout_events = 0
    kickback_events = 0

    operators: Dict[str, int] = {}
    statuses: Dict[str, int] = {}

    sample_metrics_keys: Dict[str, int] = {}

    log_ids: List[str] = []

    for it in logs:
        pid = _id(it)
        if pid:
            log_ids.append(pid)
        payload = it.get("payload") or {}
        if not isinstance(payload, dict):
            payload = {}

        operator = payload.get("operator") or _meta(it).get("operator") or "unknown"
        operator = str(operator)
        operators[operator] = operators.get(operator, 0) + 1

        st = payload.get("status") or it.get("status") or "UNKNOWN"
        st = str(st).upper()
        statuses[st] = statuses.get(st, 0) + 1

        m = _collect_metrics_from_log_payload(payload)

        cut = m.get("cut_time_s")
        if cut is not None:
            sum_cut += float(cut)
            cnt_cut += 1
        setup = m.get("setup_time_s")
        if setup is not None:
            sum_setup += float(setup)
            cnt_setup += 1
        total = m.get("total_time_s")
        if total is not None:
            sum_total += float(total)
            cnt_total += 1

        ok = m.get("parts_ok")
        if ok is not None:
            sum_ok += float(ok)
            cnt_ok += 1
        scrap = m.get("parts_scrap")
        if scrap is not None:
            sum_scrap += float(scrap)
            cnt_scrap += 1

        if _truthy(m.get("burn")):
            burn_events += 1
        if _truthy(m.get("tearout")):
            tearout_events += 1
        if _truthy(m.get("kickback_event")):
            kickback_events += 1

        raw = m.get("_raw_metrics") or {}
        if isinstance(raw, dict):
            for k in list(raw.keys())[:200]:
                sample_metrics_keys[k] = sample_metrics_keys.get(k, 0) + 1

        n += 1

    def _avg(sumv: float, cnt: int) -> Optional[float]:
        return (sumv / cnt) if cnt > 0 else None

    # Yield (parts)
    parts_ok_total = sum_ok if cnt_ok > 0 else None
    parts_scrap_total = sum_scrap if cnt_scrap > 0 else None
    parts_total = None
    yield_rate = None
    if parts_ok_total is not None or parts_scrap_total is not None:
        po = float(parts_ok_total or 0.0)
        ps = float(parts_scrap_total or 0.0)
        parts_total = po + ps
        yield_rate = (po / parts_total) if parts_total > 0 else None

    return {
        "batch_execution_artifact_id": batch_execution_artifact_id,
        "batch_label": batch_label,
        "session_id": session_id,
        "batch_decision_artifact_id": decision_id,
        "batch_plan_artifact_id": plan_id,
        "batch_spec_artifact_id": spec_id,
        "log_count": n,
        "log_artifact_ids": log_ids[:500],
        "operators": operators,
        "statuses": statuses,
        "time": {
            "cut_time_s_total": sum_cut if cnt_cut > 0 else None,
            "cut_time_s_avg": _avg(sum_cut, cnt_cut),
            "setup_time_s_total": sum_setup if cnt_setup > 0 else None,
            "setup_time_s_avg": _avg(sum_setup, cnt_setup),
            "total_time_s_total": sum_total if cnt_total > 0 else None,
            "total_time_s_avg": _avg(sum_total, cnt_total),
        },
        "yield": {
            "parts_ok_total": parts_ok_total,
            "parts_scrap_total": parts_scrap_total,
            "parts_total": parts_total,
            "yield_rate": yield_rate,
        },
        "events": {
            "burn_events": burn_events,
            "tearout_events": tearout_events,
            "kickback_events": kickback_events,
        },
        "metrics_keys": {
            "sampled_key_counts": dict(sorted(sample_metrics_keys.items(), key=lambda kv: (-kv[1], kv[0]))[:100]),
        },
    }


def persist_execution_rollup(
    *,
    batch_execution_artifact_id: str,
    limit_logs: int = 200,
) -> Dict[str, Any]:
    """
    Compute + persist an execution rollup artifact (immutable).
    kind='saw_batch_execution_rollup'
    """
    from app.rmos.run_artifacts.store import write_run_artifact, read_run_artifact

    exec_art = read_run_artifact(batch_execution_artifact_id)
    exec_d: Dict[str, Any] = exec_art if isinstance(exec_art, dict) else {
        "artifact_id": getattr(exec_art, "artifact_id", None) or getattr(exec_art, "id", None),
        "kind": getattr(exec_art, "kind", None),
        "status": getattr(exec_art, "status", None),
        "index_meta": getattr(exec_art, "index_meta", None),
        "payload": getattr(exec_art, "payload", None),
        "created_utc": getattr(exec_art, "created_utc", None),
    }
    meta = _meta(exec_d)

    rollup = compute_execution_rollup(batch_execution_artifact_id=batch_execution_artifact_id, limit_logs=limit_logs)

    art = write_run_artifact(
        kind="saw_batch_execution_rollup",
        status="OK",
        session_id=meta.get("session_id"),
        index_meta={
            "tool_kind": "saw_lab",
            "kind_group": "batch",
            "batch_label": meta.get("batch_label"),
            "session_id": meta.get("session_id"),
            "parent_batch_execution_artifact_id": batch_execution_artifact_id,
            "parent_batch_decision_artifact_id": meta.get("parent_batch_decision_artifact_id"),
            "parent_batch_plan_artifact_id": meta.get("parent_batch_plan_artifact_id"),
            "parent_batch_spec_artifact_id": meta.get("parent_batch_spec_artifact_id"),
            "log_count": rollup.get("log_count"),
        },
        payload=rollup,
    )

    return art if isinstance(art, dict) else art.__dict__
