from __future__ import annotations

from typing import Any, Dict, Optional


def _as_dict(x: Any) -> Dict[str, Any]:
    if isinstance(x, dict):
        return x
    if hasattr(x, "model_dump"):
        return x.model_dump()
    if hasattr(x, "dict"):
        return x.dict()
    return getattr(x, "__dict__", {}) or {}


def _payload(it: Dict[str, Any]) -> Dict[str, Any]:
    p = it.get("payload")
    return p if isinstance(p, dict) else {}


def _sub(d: Dict[str, Any], key: str) -> Dict[str, Any]:
    x = d.get(key)
    return x if isinstance(x, dict) else {}


def _num(x: Any) -> float:
    try:
        if x is None:
            return 0.0
        return float(x)
    except Exception:
        return 0.0


def diff_rollups(
    *,
    left_rollup_artifact_id: str,
    right_rollup_artifact_id: str,
) -> Dict[str, Any]:
    """
    Lightweight diff intended for rollup artifacts (execution/decision).

    Focus:
      - metrics.* numeric deltas
      - signals.* numeric deltas
      - counts.* numeric deltas
      - ignore other nested fields (UI can still show raw payloads)
    """
    from app.rmos.run_artifacts.store import read_run_artifact

    l = _as_dict(read_run_artifact(left_rollup_artifact_id))
    r = _as_dict(read_run_artifact(right_rollup_artifact_id))

    lp = _payload(l)
    rp = _payload(r)

    l_metrics = _sub(lp, "metrics")
    r_metrics = _sub(rp, "metrics")
    l_signals = _sub(lp, "signals")
    r_signals = _sub(rp, "signals")
    l_counts = _sub(lp, "counts")
    r_counts = _sub(rp, "counts")

    def _delta_map(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        keys = sorted(set(a.keys()) | set(b.keys()))
        out: Dict[str, Dict[str, float]] = {}
        for k in keys:
            av = _num(a.get(k))
            bv = _num(b.get(k))
            out[k] = {"left": av, "right": bv, "delta": bv - av}
        return out

    return {
        "left_artifact_id": left_rollup_artifact_id,
        "right_artifact_id": right_rollup_artifact_id,
        "left_kind": l.get("kind"),
        "right_kind": r.get("kind"),
        "metrics": _delta_map(l_metrics, r_metrics),
        "signals": _delta_map(l_signals, r_signals),
        "counts": _delta_map(l_counts, r_counts),
        "raw": {
            "left_created_utc": l.get("created_utc"),
            "right_created_utc": r.get("created_utc"),
            "left_payload": lp,
            "right_payload": rp,
        },
    }
