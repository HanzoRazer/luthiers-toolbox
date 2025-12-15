"""
Phase 27.0 + 27.1: Rosette Compare Mode MVP
Geometry diff service with color annotations for path-level overlay visualization
"""
from __future__ import annotations

import hashlib
from math import hypot
from typing import Any, Dict, Iterable, List, Set, Tuple

from ..models.compare_baseline import CompareDiffStats
from ..models.compare_diff import DiffResult, DiffSegment, DiffSummary


def _path_key(path: Dict[str, Any]) -> str:
    """Compute a stable key for a path.

    Prefer 'id' if provided, otherwise hash the coordinates.
    """
    if "id" in path and isinstance(path["id"], str):
        return path["id"]

    pts = path.get("points") or path.get("pts") or []
    flat: List[str] = []
    for p in pts:
        if isinstance(p, (list, tuple)) and len(p) >= 2:
            flat.append(f"{p[0]:.6f},{p[1]:.6f}")
    digest = hashlib.sha1("|".join(flat).encode("utf-8")).hexdigest()
    return digest


def _extract_path_keys(geometry: Dict[str, Any]) -> List[str]:
    """Extract path keys from geometry object."""
    paths = geometry.get("paths") or geometry.get("loops") or []
    keys: List[str] = []
    for p in paths:
        if isinstance(p, dict):
            keys.append(_path_key(p))
    return keys


def diff_geometries(
    baseline_geometry: Dict[str, Any], current_geometry: Dict[str, Any]
) -> CompareDiffStats:
    """Compute simple path-count diff stats between two geometries."""
    base_keys = _extract_path_keys(baseline_geometry)
    curr_keys = _extract_path_keys(current_geometry)

    base_set = set(base_keys)
    curr_set = set(curr_keys)

    added = curr_set - base_set
    removed = base_set - curr_set
    unchanged = base_set & curr_set

    return CompareDiffStats(
        baseline_path_count=len(base_keys),
        current_path_count=len(curr_keys),
        added_paths=len(added),
        removed_paths=len(removed),
        unchanged_paths=len(unchanged),
    )


def annotate_geometries_with_colors(
    baseline_geometry: Dict[str, Any], current_geometry: Dict[str, Any]
) -> tuple[CompareDiffStats, Dict[str, Any], Dict[str, Any]]:
    """Return stats plus color-annotated baseline/current geometries.

    Phase 27.1: Color-coded overlay visualization
    Coloring convention:
      - Baseline:
          removed   -> red
          unchanged -> gray
      - Current:
          added     -> green
          unchanged -> gray
    """
    base_keys = _extract_path_keys(baseline_geometry)
    curr_keys = _extract_path_keys(current_geometry)

    base_set: Set[str] = set(base_keys)
    curr_set: Set[str] = set(curr_keys)

    added = curr_set - base_set
    removed = base_set - curr_set
    unchanged = base_set & curr_set

    stats = CompareDiffStats(
        baseline_path_count=len(base_keys),
        current_path_count=len(curr_keys),
        added_paths=len(added),
        removed_paths=len(removed),
        unchanged_paths=len(unchanged),
    )

    # prepare copies so we don't mutate original dicts
    base_copy = dict(baseline_geometry)
    curr_copy = dict(current_geometry)

    base_paths = list(base_copy.get("paths") or base_copy.get("loops") or [])
    curr_paths = list(curr_copy.get("paths") or curr_copy.get("loops") or [])

    def _set_color(path: Dict[str, Any], color: str) -> None:
        """Inject meta.color field for frontend rendering."""
        meta = path.get("meta") or {}
        meta["color"] = color
        path["meta"] = meta

    # annotate baseline
    for p in base_paths:
        if not isinstance(p, dict):
            continue
        k = _path_key(p)
        if k in removed:
            _set_color(p, "red")
        elif k in unchanged:
            _set_color(p, "gray")
        else:
            # fallback, heuristically treat as unchanged
            _set_color(p, "gray")

    # annotate current
    for p in curr_paths:
        if not isinstance(p, dict):
            continue
        k = _path_key(p)
        if k in added:
            _set_color(p, "green")
        elif k in unchanged:
            _set_color(p, "gray")
        else:
            _set_color(p, "gray")

    # put paths back
    if "paths" in base_copy:
        base_copy["paths"] = base_paths
    elif "loops" in base_copy:
        base_copy["loops"] = base_paths

    if "paths" in curr_copy:
        curr_copy["paths"] = curr_paths
    elif "loops" in curr_copy:
        curr_copy["loops"] = curr_paths

    return stats, base_copy, curr_copy


# ---------------------------------------------------------------------------
# B22 geometry diff helpers (segment level)
# ---------------------------------------------------------------------------


def _segment_key(segment: Dict[str, Any]) -> Tuple:
    if segment.get("type") == "line":
        return (
            "line",
            round(float(segment.get("x1", 0.0)), 4),
            round(float(segment.get("y1", 0.0)), 4),
            round(float(segment.get("x2", 0.0)), 4),
            round(float(segment.get("y2", 0.0)), 4),
        )
    return (
        "arc",
        round(float(segment.get("cx", 0.0)), 4),
        round(float(segment.get("cy", 0.0)), 4),
        round(float(segment.get("r", 0.0)), 4),
        round(float(segment.get("start", 0.0)), 4),
        round(float(segment.get("end", 0.0)), 4),
    )


def _segment_length(segment: Dict[str, Any]) -> float:
    if segment.get("type") == "line":
        return hypot(
            float(segment.get("x2", 0.0)) - float(segment.get("x1", 0.0)),
            float(segment.get("y2", 0.0)) - float(segment.get("y1", 0.0)),
        )
    radius = float(segment.get("r", 0.0))
    sweep = abs(float(segment.get("end", 0.0)) - float(segment.get("start", 0.0)))
    return radius * sweep


def _flatten_paths(paths: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    flattened: List[Dict[str, Any]] = []
    for path_index, path in enumerate(paths):
        segments = path.get("segments") or []
        for segment in segments:
            seg_copy = dict(segment)
            seg_copy["path_index"] = path_index
            flattened.append(seg_copy)
    return flattened


def diff_geometry_segments(
    baseline_geometry: Dict[str, Any],
    current_geometry: Dict[str, Any],
    baseline_id: str,
    baseline_name: str,
) -> DiffResult:
    baseline_segments = _flatten_paths(baseline_geometry.get("paths", []))
    current_segments = _flatten_paths(current_geometry.get("paths", []))

    base_lookup = {_segment_key(seg): seg for seg in baseline_segments}
    curr_lookup = {_segment_key(seg): seg for seg in current_segments}

    summary = DiffSummary(
        segments_baseline=len(baseline_segments),
        segments_current=len(current_segments),
    )

    segments: List[DiffSegment] = []

    for key, seg in curr_lookup.items():
        if key in base_lookup:
            summary.unchanged += 1
            status = "match"
        else:
            summary.added += 1
            status = "added"
        segments.append(
            DiffSegment(
                id=f"curr-{len(segments)}",
                type=str(seg.get("type", "line")),
                status=status,
                length=_segment_length(seg),
                path_index=int(seg.get("path_index", 0)),
            )
        )

    for key, seg in base_lookup.items():
        if key in curr_lookup:
            continue
        summary.removed += 1
        segments.append(
            DiffSegment(
                id=f"base-{len(segments)}",
                type=str(seg.get("type", "line")),
                status="removed",
                length=_segment_length(seg),
                path_index=int(seg.get("path_index", 0)),
            )
        )

    total = max(summary.segments_current, 1)
    summary.overlap_ratio = summary.unchanged / total

    return DiffResult(
        baseline_id=baseline_id,
        baseline_name=baseline_name,
        summary=summary,
        segments=segments,
        baseline_geometry=baseline_geometry,
        current_geometry=current_geometry,
    )
