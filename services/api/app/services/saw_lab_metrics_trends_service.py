from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def _payload(it: Dict[str, Any]) -> Dict[str, Any]:
    p = it.get("payload")
    return p if isinstance(p, dict) else {}


def _num(x: Any) -> float:
    try:
        if x is None:
            return 0.0
        return float(x)
    except Exception:
        return 0.0


def _int(x: Any) -> int:
    try:
        if x is None:
            return 0
        return int(x)
    except Exception:
        return 0


def compute_decision_trends(
    *,
    batch_decision_artifact_id: str,
    window: int = 20,
    limit_rollups: int = 500,
) -> Dict[str, Any]:
    """
    Compute simple trend deltas over time from execution rollup artifacts.

    We use:
      kind='saw_batch_execution_metrics_rollup'
      parent_batch_decision_artifact_id = ...

    Output:
      - time-series points (bounded)
      - last vs previous window deltas
    """
    from app.rmos.run_artifacts.store import query_run_artifacts

    window = max(2, min(int(window), 200))
    limit_rollups = max(window, min(int(limit_rollups), 5000))

    rollups = query_run_artifacts(
        kind="saw_batch_execution_metrics_rollup",
        parent_batch_decision_artifact_id=batch_decision_artifact_id,
        limit=limit_rollups,
        offset=0,
    )
    rollups.sort(key=lambda x: str(x.get("created_utc") or ""), reverse=False)

    points: List[Dict[str, Any]] = []
    for it in rollups:
        pl = _payload(it)
        m = (pl.get("metrics") or {}) if isinstance(pl.get("metrics"), dict) else {}
        c = (pl.get("counts") or {}) if isinstance(pl.get("counts"), dict) else {}
        s = (pl.get("signals") or {}) if isinstance(pl.get("signals"), dict) else {}
        points.append(
            {
                "created_utc": it.get("created_utc"),
                "batch_execution_artifact_id": pl.get("batch_execution_artifact_id") or it.get("index_meta", {}).get("parent_batch_execution_artifact_id"),
                "parts_ok": _int(m.get("parts_ok")),
                "parts_scrap": _int(m.get("parts_scrap")),
                "cut_time_s": _num(m.get("cut_time_s")),
                "setup_time_s": _num(m.get("setup_time_s")),
                "job_log_count": _int(c.get("job_log_count")),
                "burn_events": _int(s.get("burn_events")),
                "tearout_events": _int(s.get("tearout_events")),
                "kickback_events": _int(s.get("kickback_events")),
            }
        )

    # If not enough points, still return a valid shape
    if len(points) < 2:
        return {
            "batch_decision_artifact_id": batch_decision_artifact_id,
            "point_count": len(points),
            "window": window,
            "points": points[-200:],
            "deltas": {"available": False},
        }

    # Split into last window and previous window
    tail = points[-window:]
    prev = points[-2 * window : -window] if len(points) >= 2 * window else points[:-window]

    def _agg(xs: List[Dict[str, Any]]) -> Dict[str, float]:
        parts_ok = sum(_int(p.get("parts_ok")) for p in xs)
        parts_scrap = sum(_int(p.get("parts_scrap")) for p in xs)
        cut = sum(_num(p.get("cut_time_s")) for p in xs)
        setup = sum(_num(p.get("setup_time_s")) for p in xs)
        burn = sum(_int(p.get("burn_events")) for p in xs)
        tear = sum(_int(p.get("tearout_events")) for p in xs)
        kick = sum(_int(p.get("kickback_events")) for p in xs)
        denom = max(1, (parts_ok + parts_scrap))
        return {
            "parts_ok": float(parts_ok),
            "parts_scrap": float(parts_scrap),
            "scrap_rate": float(parts_scrap) / float(denom),
            "cut_time_s": float(cut),
            "setup_time_s": float(setup),
            "total_time_s": float(cut + setup),
            "burn_events": float(burn),
            "tearout_events": float(tear),
            "kickback_events": float(kick),
        }

    a_tail = _agg(tail)
    a_prev = _agg(prev) if prev else {k: 0.0 for k in a_tail.keys()}

    deltas = {k: (a_tail[k] - a_prev.get(k, 0.0)) for k in a_tail.keys()}

    return {
        "batch_decision_artifact_id": batch_decision_artifact_id,
        "point_count": len(points),
        "window": window,
        "points": points[-200:],  # bounded
        "aggregate": {"last_window": a_tail, "prev_window": a_prev},
        "deltas": {"available": True, "delta": deltas},
    }
