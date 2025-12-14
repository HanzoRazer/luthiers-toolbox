# CAM Risk Aggregate Router (Phase 26.0)
# Backend aggregation endpoints for risk timeline

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/cam/jobs", tags=["cam-risk-aggregate"])

# Adjust this path to match wherever you're persisting risk reports now.
RISK_JOB_STORE_PATH = Path("data/cam_risk_jobs.jsonl")


class PresetAggregate(BaseModel):
    preset_name: str = Field(..., description="Name of the preset (Safe, Standard, Aggressive, Custom, etc.)")
    preset_source: Optional[str] = Field(
        None, description="Where this preset came from (e.g. ArtStudio, Lab)"
    )
    jobs_count: int = Field(..., description="Number of jobs matching this preset")
    avg_risk: float = Field(..., description="Average risk_score across jobs")
    avg_total_issues: float = Field(..., description="Average total_issues across jobs")
    total_critical: int = Field(..., description="Total critical incidents across jobs")
    avg_avg_floor_thickness: Optional[float] = Field(
        None, description="Average of avg_floor_thickness from sim bridge stats"
    )
    avg_min_floor_thickness: Optional[float] = Field(
        None, description="Average of min_floor_thickness from sim bridge stats"
    )
    avg_max_load_index: Optional[float] = Field(
        None, description="Average of max_load_index from sim bridge stats"
    )
    avg_time_s: Optional[float] = Field(
        None, description="Average estimated time (if included in analytics/meta)"
    )


class RiskAggregateResponse(BaseModel):
    from_ts: Optional[datetime]
    to_ts: Optional[datetime]
    pipeline_ids: List[str]
    preset_names: List[str]
    total_jobs: int
    presets: List[PresetAggregate]


def _parse_iso(dt_str: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        return None


def load_risk_reports() -> List[Dict[str, Any]]:
    """
    Load risk reports from a JSONL file.
    This should be kept in sync with whatever your /risk_report POST handler uses.
    """
    if not RISK_JOB_STORE_PATH.exists():
        return []
    out: List[Dict[str, Any]] = []
    with RISK_JOB_STORE_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _classify_preset_name(name: Optional[str]) -> str:
    if not name:
        return "Custom"
    n = name.lower()
    if "safe" in n:
        return "Safe"
    if "standard" in n or "std" in n:
        return "Standard"
    if "agg" in n or "aggressive" in n:
        return "Aggressive"
    return "Custom"


@router.get("/risk_aggregate", response_model=RiskAggregateResponse)
def get_risk_aggregate(
    from_ts: Optional[datetime] = Query(
        None, description="Start datetime (inclusive) in ISO8601"
    ),
    to_ts: Optional[datetime] = Query(
        None, description="End datetime (exclusive) in ISO8601"
    ),
    pipeline_id: Optional[str] = Query(
        None, description="Filter by a single pipeline_id (e.g. artstudio_relief_v16)"
    ),
    preset_name: Optional[str] = Query(
        None,
        description=(
            "Filter by preset name category: Safe, Standard, Aggressive, Custom. "
            "If omitted, all presets are included."
        ),
    ),
) -> RiskAggregateResponse:
    """
    Aggregate risk reports by preset name (Safe/Standard/Aggressive/Custom)
    across an optional time range and pipeline filter.

    This endpoint is designed to be the server-side twin of the interactive
    Relief Risk Timeline view.
    """
    reports = load_risk_reports()
    if not reports:
        return RiskAggregateResponse(
            from_ts=from_ts,
            to_ts=to_ts,
            pipeline_ids=[],
            preset_names=[],
            total_jobs=0,
            presets=[],
        )

    def within_date_range(rep: Dict[str, Any]) -> bool:
        if not from_ts and not to_ts:
            return True

        ts_str = rep.get("created_at") or rep.get("timestamp")
        if not ts_str:
            return False
        ts = _parse_iso(ts_str)
        if not ts:
            return False
        if from_ts and ts < from_ts:
            return False
        if to_ts and ts >= to_ts:
            return False
        return True

    filtered: List[Dict[str, Any]] = []
    for rep in reports:
        if pipeline_id:
            pid = rep.get("pipeline_id") or rep.get("pipelineId") or ""
            if pid != pipeline_id:
                continue
        if not within_date_range(rep):
            continue

        meta = rep.get("meta") or {}
        preset_meta = meta.get("preset") or {}
        raw_name = preset_meta.get("name")
        category = _classify_preset_name(raw_name)
        if preset_name and category != preset_name:
            continue

        filtered.append(rep)

    if not filtered:
        return RiskAggregateResponse(
            from_ts=from_ts,
            to_ts=to_ts,
            pipeline_ids=[],
            preset_names=[],
            total_jobs=0,
            presets=[],
        )

    # group by normalized preset category + source
    buckets: Dict[tuple, Dict[str, Any]] = {}
    used_pipelines: set[str] = set()
    used_presets: set[str] = set()

    for rep in filtered:
        pid = rep.get("pipeline_id") or rep.get("pipelineId") or ""
        used_pipelines.add(pid)

        meta = rep.get("meta") or {}
        preset_meta = meta.get("preset") or {}
        raw_name = preset_meta.get("name")
        category = _classify_preset_name(raw_name)
        source = preset_meta.get("source") or None

        used_presets.add(category)

        key = (category, source)
        bucket = buckets.setdefault(
            key,
            dict(
                count=0,
                risk_sum=0.0,
                total_issues_sum=0.0,
                critical_sum=0,
                avg_floor_sum=0.0,
                min_floor_sum=0.0,
                max_load_sum=0.0,
                time_sum=0.0,
                stats_count=0,
            ),
        )

        bucket["count"] += 1

        analytics = rep.get("analytics") or {}
        risk_score = float(analytics.get("risk_score") or 0.0)
        total_issues = float(analytics.get("total_issues") or 0.0)
        sc = (analytics.get("severity_counts") or {}) or {}
        critical = int(sc.get("critical") or 0)

        bucket["risk_sum"] += risk_score
        bucket["total_issues_sum"] += total_issues
        bucket["critical_sum"] += critical

        stats = meta.get("relief_sim_bridge") or meta.get("sim_stats") or None
        if stats:
            avg_floor = stats.get("avg_floor_thickness")
            min_floor = stats.get("min_floor_thickness")
            max_load = stats.get("max_load_index")
            est_time = stats.get("est_time_s")  # if you store it in stats/meta

            if isinstance(avg_floor, (int, float)):
                bucket["avg_floor_sum"] += float(avg_floor)
            if isinstance(min_floor, (int, float)):
                bucket["min_floor_sum"] += float(min_floor)
            if isinstance(max_load, (int, float)):
                bucket["max_load_sum"] += float(max_load)
            if isinstance(est_time, (int, float)):
                bucket["time_sum"] += float(est_time)

            bucket["stats_count"] += 1

    presets_out: List[PresetAggregate] = []
    for (category, source), agg in buckets.items():
        count = agg["count"]
        stats_count = max(agg["stats_count"], 1)
        presets_out.append(
            PresetAggregate(
                preset_name=category,
                preset_source=source,
                jobs_count=count,
                avg_risk=agg["risk_sum"] / max(count, 1),
                avg_total_issues=agg["total_issues_sum"] / max(count, 1),
                total_critical=agg["critical_sum"],
                avg_avg_floor_thickness=(
                    agg["avg_floor_sum"] / stats_count if agg["stats_count"] > 0 else None
                ),
                avg_min_floor_thickness=(
                    agg["min_floor_sum"] / stats_count if agg["stats_count"] > 0 else None
                ),
                avg_max_load_index=(
                    agg["max_load_sum"] / stats_count if agg["stats_count"] > 0 else None
                ),
                avg_time_s=(
                    agg["time_sum"] / stats_count if agg["stats_count"] > 0 else None
                ),
            )
        )

    return RiskAggregateResponse(
        from_ts=from_ts,
        to_ts=to_ts,
        pipeline_ids=sorted(used_pipelines),
        preset_names=sorted(used_presets),
        total_jobs=len(filtered),
        presets=presets_out,
    )


# Phase 26.6: Preset Evolution Trendline - Server-side series endpoint
@router.get("/risk_aggregate_pair_series")
def risk_aggregate_pair_series(
    preset_a: str = Query(..., description="Safe/Standard/Aggressive/Custom"),
    preset_b: str = Query(..., description="Safe/Standard/Aggressive/Custom"),
    pipeline_id: Optional[str] = Query(None, description="Filter by pipeline ID"),
    from_ts: Optional[str] = Query(None, description="ISO timestamp from (inclusive)"),
    to_ts: Optional[str] = Query(None, description="ISO timestamp to (exclusive)"),
):
    """
    Return weekly average risk for presets A and B, plus delta (B-A) per bucket.
    
    Response format:
    {
      "series": [
        {"bucket": "2025-W45", "avg_risk_A": 4.2, "avg_risk_B": 6.8, "delta": 2.6},
        ...
      ]
    }
    """
    reports = load_risk_reports()
    if not reports:
        return {"series": []}

    # Parse time filters
    f_from = from_ts if from_ts else None
    f_to = to_ts if to_ts else None

    def in_range(rep: Dict[str, Any]) -> bool:
        if not f_from and not f_to:
            return True
        ts_raw = rep.get("created_at") or rep.get("timestamp")
        if not ts_raw:
            return False
        dt = _parse_iso(ts_raw)
        if not dt:
            return False
        if f_from and dt < f_from:
            return False
        if f_to and dt >= f_to:
            return False
        return True

    # Filter and split by preset category
    A, B = [], []
    for rep in reports:
        if pipeline_id:
            pid = rep.get("pipeline_id") or rep.get("pipelineId") or ""
            if pid != pipeline_id:
                continue
        if not in_range(rep):
            continue
        name = ((rep.get("meta") or {}).get("preset") or {}).get("name")
        cat = _classify_preset_name(name)
        if cat == preset_a:
            A.append(rep)
        elif cat == preset_b:
            B.append(rep)

    # Bucket by ISO week
    from collections import defaultdict

    buckets: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: {"A": [], "B": []})

    def add_to_bucket(lst: List[Dict[str, Any]], which: str):
        for rep in lst:
            ts_raw = rep.get("created_at") or rep.get("timestamp")
            dt = _parse_iso(ts_raw)
            if not dt:
                continue
            key = _iso_week_label(dt)
            risk = float((rep.get("analytics") or {}).get("risk_score") or 0.0)
            buckets[key][which].append(risk)

    add_to_bucket(A, "A")
    add_to_bucket(B, "B")

    # Build series
    keys = sorted(buckets.keys())
    series = []
    for k in keys:
        a_vals = buckets[k]["A"]
        b_vals = buckets[k]["B"]
        a_avg = sum(a_vals) / len(a_vals) if a_vals else 0.0
        b_avg = sum(b_vals) / len(b_vals) if b_vals else 0.0
        series.append(
            {
                "bucket": k,
                "avg_risk_A": round(a_avg, 2),
                "avg_risk_B": round(b_avg, 2),
                "delta": round(b_avg - a_avg, 2),
            }
        )

    return {"series": series}


def _iso_week_label(dt: datetime) -> str:
    """Generate ISO year-week label (YYYY-Www) from datetime."""
    iso_year, iso_week, _ = dt.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"
