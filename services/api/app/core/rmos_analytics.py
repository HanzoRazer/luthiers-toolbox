"""
RMOS Analytics Core (MM-4)

Material-aware risk analytics engine.
Extracts fragility and material data from job metadata (MM-2) and aggregates
into global and per-lane statistics.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Tuple

from app.api.deps.rmos_stores import get_pattern_store, get_joblog_store
from app.schemas.rmos_analytics import (
    LaneAnalyticsResponse,
    GlobalRiskSummary,
    LaneRiskSummary,
    RecentRunItem,
    LaneTransition,
    RiskTimelineResponse,
    RiskTimelinePoint,
    MaterialRiskSummary,
    Lane,
    RiskGrade,
)


def _normalize_grade(value: Any) -> RiskGrade:
    """Normalize risk grade to valid enum value."""
    if not value:
        return "unknown"  # type: ignore[return-value]
    v = str(value).upper()
    if v not in ("GREEN", "YELLOW", "RED"):
        return "unknown"  # type: ignore[return-value]
    return v  # type: ignore[return-value]


def _risk_score(grade: RiskGrade) -> float:
    """Convert risk grade to numeric score."""
    if grade == "GREEN":
        return 0.0
    if grade == "YELLOW":
        return 0.5
    if grade == "RED":
        return 1.0
    return 0.75  # unknown -> pessimistic


def _normalize_lane(value: Any) -> Lane:
    """Normalize lane to valid enum value."""
    v = (value or "unknown").lower()
    mapping = {
        "safe": "safe",
        "tuned_v1": "tuned_v1",
        "tuned_v2": "tuned_v2",
        "experimental": "experimental",
        "archived": "archived",
    }
    return mapping.get(v, "unknown")  # type: ignore[return-value]


def compute_lane_analytics(limit_recent: int = 200) -> LaneAnalyticsResponse:
    """
    Compute material-aware lane analytics.
    
    Aggregates:
    - Risk grades per lane
    - Fragility scores from MM-2 CAM profiles
    - Material type distribution
    - Lane transitions (promotions/rollbacks)
    """
    pattern_store = get_pattern_store()
    joblog_store = get_joblog_store()

    patterns = pattern_store.list(limit=10000)
    patterns_by_id: Dict[str, Dict[str, Any]] = {p["id"]: p for p in patterns if p.get("id")}

    entries = joblog_store.list(limit=50000)
    total_jobs = len(entries)
    total_presets = len({e.get("preset_id") for e in entries if e.get("preset_id")})

    global_grade_counts = defaultdict(int)
    global_score_sum = 0.0

    # MM-4: global fragility & material counters
    material_stats: Dict[str, Dict[str, Any]] = {}
    global_fragility_sum = 0.0
    global_fragility_count = 0

    lane_stats: Dict[Lane, Dict[str, Any]] = {}
    transitions: Dict[Tuple[Lane, Lane], int] = {}
    recent_runs: List[RecentRunItem] = []

    for entry in entries:
        lane: Lane = _normalize_lane(
            entry.get("lane") or entry.get("promotion_lane") or _lane_from_pattern(entry, patterns_by_id)
        )
        risk_grade: RiskGrade = _normalize_grade(entry.get("risk_grade"))
        doc_grade: RiskGrade = _normalize_grade(entry.get("doc_grade"))
        gantry_grade: RiskGrade = _normalize_grade(entry.get("gantry_grade"))

        global_grade_counts[risk_grade] += 1
        score = _risk_score(risk_grade)
        global_score_sum += score

        # Initialize lane bucket if needed
        ls = lane_stats.setdefault(
            lane,
            {
                "job_count": 0,
                "score_sum": 0.0,
                "grade_counts": defaultdict(int),
                "fragility_sum": 0.0,
                "fragility_count": 0,
                "material_counts": defaultdict(int),
            },
        )
        ls["job_count"] += 1
        ls["score_sum"] += score
        ls["grade_counts"][risk_grade] += 1

        # MM-4: extract fragility + materials from metadata
        meta = entry.get("metadata") or {}
        cam_summary = meta.get("cam_profile_summary") or {}
        worst_fragility = cam_summary.get("worst_fragility_score")
        materials = meta.get("materials") or []

        # Global material stats
        mat_types_seen = set()
        for m in materials:
            m_type = (m.get("type") or "unknown").lower()
            if not m_type:
                m_type = "unknown"
            mat_types_seen.add(m_type)
        
        # Mark job_count per type
        for t in mat_types_seen:
            material_stats.setdefault(
                t,
                {
                    "job_count": 0,
                    "fragility_sum": 0.0,
                    "fragility_count": 0,
                    "worst_fragility": 0.0,
                },
            )["job_count"] += 1

        # Fragility contribution
        if isinstance(worst_fragility, (int, float)):
            global_fragility_sum += worst_fragility
            global_fragility_count += 1
            ls["fragility_sum"] += worst_fragility
            ls["fragility_count"] += 1
            for t in mat_types_seen:
                ms = material_stats[t]
                ms["fragility_sum"] += worst_fragility
                ms["fragility_count"] += 1
                if worst_fragility > ms["worst_fragility"]:
                    ms["worst_fragility"] = worst_fragility

        # Lane material counts
        for t in mat_types_seen:
            ls["material_counts"][t] += 1

        # Lane transitions (promotion / rollback jobs)
        if entry.get("job_type") in ("preset_promote_winner", "preset_rollback"):
            from_lane = _normalize_lane(entry.get("from_lane") or entry.get("parent_lane") or lane)
            to_lane = _normalize_lane(entry.get("to_lane") or entry.get("promotion_lane") or lane)
            key = (from_lane, to_lane)
            transitions[key] = transitions.get(key, 0) + 1

        # Recent runs (truncate later)
        recent_runs.append(
            RecentRunItem(
                job_id=entry.get("id", ""),
                preset_id=entry.get("preset_id"),
                created_at=_as_iso(entry.get("created_at")),
                lane=lane,
                job_type=entry.get("job_type") or "",
                risk_grade=risk_grade,
                doc_grade=doc_grade,
                gantry_grade=gantry_grade,
                worst_fragility_score=worst_fragility if isinstance(worst_fragility, (int, float)) else None,
            )
        )

    # Sort recent runs by created_at descending and slice
    recent_runs.sort(key=lambda r: r.created_at, reverse=True)
    if limit_recent and len(recent_runs) > limit_recent:
        recent_runs = recent_runs[:limit_recent]

    # Build lane summaries
    lane_summaries: List[LaneRiskSummary] = []
    for lane, data in lane_stats.items():
        job_count = data["job_count"]
        score_sum = data["score_sum"]
        grade_counts = dict(data["grade_counts"])
        frag_sum = data["fragility_sum"]
        frag_count = data["fragility_count"]
        mat_counts = data["material_counts"]

        avg_score = score_sum / job_count if job_count > 0 else None
        avg_frag = frag_sum / frag_count if frag_count > 0 else None
        dominant_materials = _top_keys(mat_counts, max_items=3)

        lane_summaries.append(
            LaneRiskSummary(
                lane=lane,
                job_count=job_count,
                avg_risk_score=avg_score,
                grade_counts=grade_counts,
                avg_fragility_score=avg_frag,
                dominant_material_types=dominant_materials,
            )
        )

    # Build global material summary list
    material_risk_global: List[MaterialRiskSummary] = []
    for m_type, stats in material_stats.items():
        jc = stats["job_count"]
        frag_count = stats["fragility_count"]
        avg_frag = stats["fragility_sum"] / frag_count if frag_count > 0 else None
        material_risk_global.append(
            MaterialRiskSummary(
                material_type=m_type,
                job_count=jc,
                avg_fragility=avg_frag,
                worst_fragility=stats["worst_fragility"] if frag_count > 0 else None,
            )
        )

    # Sort material summary by job_count desc
    material_risk_global.sort(key=lambda m: m.job_count, reverse=True)

    # Global averages
    avg_risk_global = global_score_sum / total_jobs if total_jobs > 0 else None
    overall_fragility = (
        global_fragility_sum / global_fragility_count if global_fragility_count > 0 else None
    )

    global_summary = GlobalRiskSummary(
        total_jobs=total_jobs,
        total_presets=total_presets,
        avg_risk_score=avg_risk_global,
        grade_counts=dict(global_grade_counts),
        overall_fragility_score=overall_fragility,
        material_risk_by_type=material_risk_global,
    )

    lane_transitions = [
        LaneTransition(from_lane=k[0], to_lane=k[1], count=v)
        for k, v in transitions.items()
    ]

    return LaneAnalyticsResponse(
        global_summary=global_summary,
        lane_summaries=lane_summaries,
        recent_runs=recent_runs,
        lane_transitions=lane_transitions,
        material_risk_global=material_risk_global,
    )


def compute_risk_timeline_for_preset(preset_id: str, limit: int = 200) -> RiskTimelineResponse:
    """
    Compute risk timeline for a specific preset.
    
    Returns chronological sequence of job runs with risk and fragility data.
    """
    joblog_store = get_joblog_store()
    entries = [e for e in joblog_store.list(limit=50000) if e.get("preset_id") == preset_id]
    entries.sort(key=lambda e: e.get("created_at") or "", reverse=False)

    points: List[RiskTimelinePoint] = []
    for e in entries[:limit]:
        lane: Lane = _normalize_lane(
            e.get("lane") or e.get("promotion_lane") or "unknown"
        )
        risk_grade: RiskGrade = _normalize_grade(e.get("risk_grade"))
        score = _risk_score(risk_grade)

        meta = e.get("metadata") or {}
        cam_summary = meta.get("cam_profile_summary") or {}
        worst_fragility = cam_summary.get("worst_fragility_score")

        points.append(
            RiskTimelinePoint(
                job_id=e.get("id", ""),
                created_at=_as_iso(e.get("created_at")),
                lane=lane,
                risk_grade=risk_grade,
                risk_score=score,
                worst_fragility_score=worst_fragility if isinstance(worst_fragility, (int, float)) else None,
            )
        )

    return RiskTimelineResponse(
        preset_id=preset_id,
        points=points,
    )


def _lane_from_pattern(entry: Dict[str, Any], patterns_by_id: Dict[str, Dict[str, Any]]) -> Lane:
    """Extract lane from pattern metadata."""
    pid = entry.get("preset_id")
    if not pid:
        return "unknown"  # type: ignore[return-value]
    pat = patterns_by_id.get(pid)
    if not pat:
        return "unknown"  # type: ignore[return-value]
    lane = pat.get("promotion_lane") or pat.get("lane") or "unknown"
    return _normalize_lane(lane)


def _as_iso(v: Any) -> str:
    """Convert timestamp to ISO string."""
    if not v:
        return ""
    if isinstance(v, str):
        return v
    if isinstance(v, datetime):
        return v.isoformat()
    return str(v)


def _top_keys(counter: Dict[str, int], max_items: int = 3) -> List[str]:
    """Get top N keys from counter."""
    return [k for k, _ in sorted(counter.items(), key=lambda kv: kv[1], reverse=True)[:max_items]]
