from __future__ import annotations

import csv
import io
from typing import Any, Dict, List, Optional, Tuple


def _payload(it: Dict[str, Any]) -> Dict[str, Any]:
    p = it.get("payload")
    return p if isinstance(p, dict) else {}


def _meta(it: Dict[str, Any]) -> Dict[str, Any]:
    m = it.get("index_meta")
    return m if isinstance(m, dict) else {}


def _get(it: Dict[str, Any], *path: str, default=None):
    cur: Any = it
    for k in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
    return cur if cur is not None else default


def export_job_logs_csv(
    *,
    batch_execution_artifact_id: str,
    limit: int = 2000,
) -> str:
    """
    CSV export of job logs for a single execution.
    """
    from app.rmos.run_artifacts.store import query_run_artifacts

    limit = max(1, min(int(limit), 20000))

    logs = query_run_artifacts(
        kind="saw_batch_job_log",
        parent_batch_execution_artifact_id=batch_execution_artifact_id,
        limit=limit,
        offset=0,
    )
    logs.sort(key=lambda x: str(x.get("created_utc") or ""), reverse=False)

    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(
        [
            "created_utc",
            "job_log_artifact_id",
            "batch_execution_artifact_id",
            "operator",
            "status",
            "notes",
            "parts_ok",
            "parts_scrap",
            "cut_time_s",
            "setup_time_s",
            "burn",
            "tearout",
            "kickback",
        ]
    )

    for it in logs:
        pl = _payload(it)
        metrics = pl.get("metrics") if isinstance(pl.get("metrics"), dict) else {}
        w.writerow(
            [
                it.get("created_utc"),
                it.get("artifact_id") or it.get("id"),
                batch_execution_artifact_id,
                pl.get("operator") or _meta(it).get("operator"),
                (pl.get("status") or it.get("status") or "").upper(),
                pl.get("notes") or "",
                metrics.get("parts_ok") or "",
                metrics.get("parts_scrap") or metrics.get("scrap_count") or "",
                metrics.get("cut_time_s") or metrics.get("cut_time_sec") or "",
                metrics.get("setup_time_s") or metrics.get("setup_time_sec") or "",
                bool(metrics.get("burn")) if "burn" in metrics else "",
                bool(metrics.get("tearout")) if "tearout" in metrics else "",
                bool(metrics.get("kickback")) if "kickback" in metrics else "",
            ]
        )

    return out.getvalue()


def export_execution_rollups_csv(
    *,
    batch_decision_artifact_id: str,
    limit: int = 5000,
) -> str:
    """
    CSV export of execution metrics rollups under a decision.
    Useful for quick spreadsheet analysis.
    """
    from app.rmos.run_artifacts.store import query_run_artifacts

    limit = max(1, min(int(limit), 50000))

    rollups = query_run_artifacts(
        kind="saw_batch_execution_metrics_rollup",
        parent_batch_decision_artifact_id=batch_decision_artifact_id,
        limit=limit,
        offset=0,
    )
    rollups.sort(key=lambda x: str(x.get("created_utc") or ""), reverse=False)

    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(
        [
            "created_utc",
            "rollup_artifact_id",
            "batch_decision_artifact_id",
            "batch_execution_artifact_id",
            "batch_label",
            "session_id",
            "job_log_count",
            "learning_event_count",
            "parts_ok",
            "parts_scrap",
            "scrap_rate",
            "cut_time_s",
            "setup_time_s",
            "total_time_s",
            "burn_events",
            "tearout_events",
            "kickback_events",
        ]
    )

    for it in rollups:
        pl = _payload(it)
        m = pl.get("metrics") if isinstance(pl.get("metrics"), dict) else {}
        c = pl.get("counts") if isinstance(pl.get("counts"), dict) else {}
        s = pl.get("signals") if isinstance(pl.get("signals"), dict) else {}

        parts_ok = float(m.get("parts_ok") or 0)
        parts_scrap = float(m.get("parts_scrap") or 0)
        denom = max(1.0, (parts_ok + parts_scrap))
        scrap_rate = parts_scrap / denom

        w.writerow(
            [
                it.get("created_utc"),
                it.get("artifact_id") or it.get("id"),
                batch_decision_artifact_id,
                pl.get("batch_execution_artifact_id") or _meta(it).get("parent_batch_execution_artifact_id") or "",
                pl.get("batch_label") or _meta(it).get("batch_label") or "",
                pl.get("session_id") or _meta(it).get("session_id") or "",
                c.get("job_log_count") or "",
                c.get("learning_event_count") or "",
                m.get("parts_ok") or 0,
                m.get("parts_scrap") or 0,
                round(scrap_rate, 6),
                m.get("cut_time_s") or 0.0,
                m.get("setup_time_s") or 0.0,
                m.get("total_time_s") or (float(m.get("cut_time_s") or 0.0) + float(m.get("setup_time_s") or 0.0)),
                s.get("burn_events") or 0,
                s.get("tearout_events") or 0,
                s.get("kickback_events") or 0,
            ]
        )

    return out.getvalue()
