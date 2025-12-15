# services/api/app/services/compare_risk_aggregate.py
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Tuple

from . import compare_risk_log


def _load_entries() -> List[Dict[str, Any]]:
    """
    Load raw compare entries from the same log used elsewhere.
    The compare_risk_log module is expected to expose a _load_log() helper
    that returns a dict with an 'entries' list.
    """
    data = compare_risk_log._load_log()  # type: ignore[attr-defined]
    entries = data.get("entries") or []
    # Ensure it's a list of dicts
    return [e for e in entries if isinstance(e, dict)]


def _bucket_key(entry: Dict[str, Any]) -> Tuple[str, str]:
    lane = str(entry.get("lane") or "(none)")
    preset = str(entry.get("preset") or "").strip() or "(none)"
    return lane, preset


def aggregate_compare_history(
    entries: List[Dict[str, Any]] | None = None,
    since: str | None = None,
    until: str | None = None,
) -> List[Dict[str, Any]]:
    """
    Aggregate raw compare history entries into lane+preset buckets.
    
    Phase 28.7: Added time-window filtering via `since` and `until` parameters.

    Args:
        entries: Optional pre-loaded entries (for testing)
        since: ISO timestamp - only include entries >= this time
        until: ISO timestamp - only include entries < this time

    Returns a list of dicts with:
      - lane
      - preset
      - count
      - avg_added
      - avg_removed
      - avg_unchanged
      - risk_score
      - risk_label
      - added_series: list of added_paths in chronological order
      - removed_series: list of removed_paths in chronological order
    """
    if entries is None:
        entries = _load_entries()

    # Phase 28.7: Filter by time window
    if since or until:
        filtered_entries = []
        for e in entries:
            ts = e.get("ts", "")
            if since and ts < since:
                continue
            if until and ts >= until:
                continue
            filtered_entries.append(e)
        entries = filtered_entries

    # Sort by timestamp if present so series are time-ordered
    sorted_entries = sorted(
        entries,
        key=lambda e: e.get("ts") or "",
    )

    buckets: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    for e in sorted_entries:
        key = _bucket_key(e)
        buckets[key].append(e)

    results: List[Dict[str, Any]] = []
    for (lane, preset), bucket_entries in buckets.items():
        count = len(bucket_entries)
        if count == 0:
            continue

        added_vals: List[float] = []
        removed_vals: List[float] = []
        unchanged_vals: List[float] = []

        for e in bucket_entries:
            added_vals.append(float(e.get("added_paths") or 0))
            removed_vals.append(float(e.get("removed_paths") or 0))
            unchanged_vals.append(float(e.get("unchanged_paths") or 0))

        def avg(vals: List[float]) -> float:
            return sum(vals) / len(vals) if vals else 0.0

        avg_added = avg(added_vals)
        avg_removed = avg(removed_vals)
        avg_unchanged = avg(unchanged_vals)

        # Simple heuristic: more added + more removed = more "spice"
        risk_score = avg_added * 0.7 + avg_removed * 1.0
        if risk_score < 1:
            risk_label = "Low"
        elif risk_score < 3:
            risk_label = "Medium"
        elif risk_score < 6:
            risk_label = "High"
        else:
            risk_label = "Extreme"

        results.append(
            {
                "lane": lane,
                "preset": preset,
                "count": count,
                "avg_added": avg_added,
                "avg_removed": avg_removed,
                "avg_unchanged": avg_unchanged,
                "risk_score": risk_score,
                "risk_label": risk_label,
                # store the series for sparkline generation on the client
                "added_series": added_vals,
                "removed_series": removed_vals,
            }
        )

    # Sort output by lane, then preset
    results.sort(key=lambda r: (r["lane"], r["preset"]))
    return results
