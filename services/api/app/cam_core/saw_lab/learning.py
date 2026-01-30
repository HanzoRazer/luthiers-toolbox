"""Saw Lab learning lanes - telemetry-based feed/speed optimization.

Integrates with the live_learn_ingestor to compute lane-scale adjustments
based on real-world telemetry data (spindle load, vibration, temps).
"""
from __future__ import annotations

from typing import Dict, Any, List, Optional

from .models import (
    TelemetryIngestConfig,
    LaneMetrics,
    LaneAdjustment,
    TelemetryIngestRequest,
    TelemetryIngestResponse,
)

# Import learning functions from experimental
from app._experimental.cnc_production.learn.live_learn_ingestor import (
    compute_lane_metrics,
    score_risk,
    decide_scale_delta,
    clamp_scale,
    ingest_run_telemetry,
    ingest_run_telemetry_by_id,
)

from app._experimental.cnc_production.learn.risk_buckets import (
    classify_risk,
    RiskBucket,
)

from app._experimental.cnc_production.joblog.storage import get_telemetry


def compute_learning_lanes(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute learning insights from telemetry events.

    This is the legacy facade that accepts raw event dicts and returns
    aggregated insights. For new code, use ingest_run_telemetry_by_id().

    Args:
        events: List of telemetry event dictionaries with keys like:
            - run_id: Run identifier
            - rpm_actual: Actual spindle speed
            - spindle_load_pct: Spindle load percentage
            - vibration_rms: Vibration level

    Returns:
        Learning insights with risk assessment and recommendations
    """
    if not events:
        return {
            "events": [],
            "insights": [],
            "status": "no_events",
        }

    # Group events by run_id
    runs: Dict[str, List[Dict[str, Any]]] = {}
    for event in events:
        run_id = event.get("run_id", "unknown")
        if run_id not in runs:
            runs[run_id] = []
        runs[run_id].append(event)

    # Compute metrics for each run
    insights = []
    config = TelemetryIngestConfig()

    for run_id, run_events in runs.items():
        # Aggregate metrics
        n_samples = len(run_events)
        avg_load = sum(e.get("spindle_load_pct", 0) for e in run_events) / n_samples
        max_load = max(e.get("spindle_load_pct", 0) for e in run_events)
        avg_vib = sum(e.get("vibration_rms", 0) for e in run_events) / n_samples

        # Create metrics object
        metrics = LaneMetrics(
            n_samples=n_samples,
            avg_spindle_load_pct=avg_load,
            max_spindle_load_pct=max_load,
            avg_vibration_rms=avg_vib,
        )

        # Compute risk score
        risk = score_risk(metrics, config)
        risk_bucket = classify_risk(risk)

        # Compute scale recommendation
        scale_delta = decide_scale_delta(metrics, config)

        insights.append({
            "run_id": run_id,
            "n_samples": n_samples,
            "avg_spindle_load_pct": round(avg_load, 1),
            "max_spindle_load_pct": round(max_load, 1),
            "avg_vibration_rms": round(avg_vib, 3),
            "risk_score": round(risk, 3),
            "risk_grade": risk_bucket.id.upper(),  # e.g., "GREEN", "YELLOW", "RED"
            "risk_label": risk_bucket.label,
            "recommended_scale_delta": round(scale_delta, 3),
            "recommendation": _get_recommendation(scale_delta, risk_bucket),
        })

    return {
        "events": events,
        "insights": insights,
        "status": "computed",
        "total_runs": len(runs),
        "total_events": len(events),
    }


def _get_recommendation(scale_delta: float, risk: RiskBucket) -> str:
    """Generate human-readable recommendation."""
    risk_id = risk.id.lower()
    if risk_id == "red":
        return "STOP: High risk detected. Check tooling and parameters."
    elif risk_id in ("yellow", "orange"):
        if scale_delta < 0:
            return f"SLOW DOWN: Reduce feed/speed by {abs(scale_delta)*100:.0f}%"
        else:
            return "MONITOR: Parameters at upper limit of safe range."
    else:  # green or unknown
        if scale_delta > 0:
            return f"OPTIMIZE: Can increase feed/speed by {scale_delta*100:.0f}%"
        else:
            return "GOOD: Parameters are optimal."


def analyze_run_telemetry(
    run_id: str,
    tool_id: str,
    material: str,
    machine_profile: str = "default",
    current_scale: float = 1.0,
    apply_adjustment: bool = False,
) -> Dict[str, Any]:
    """
    Analyze telemetry for a specific run and compute adjustments.

    Args:
        run_id: Run identifier
        tool_id: Tool/blade identifier
        material: Material family
        machine_profile: Machine profile identifier
        current_scale: Current lane scale multiplier
        apply_adjustment: Whether to apply the recommended adjustment

    Returns:
        Analysis results with metrics and recommendations
    """
    request = TelemetryIngestRequest(
        run_id=run_id,
        tool_id=tool_id,
        material=material,
        machine_profile=machine_profile,
        current_lane_scale=current_scale,
        apply=apply_adjustment,
    )

    response = ingest_run_telemetry_by_id(request)
    return response.model_dump()


def get_run_metrics(run_id: str) -> Optional[Dict[str, Any]]:
    """
    Get computed metrics for a run's telemetry.

    Args:
        run_id: Run identifier

    Returns:
        Metrics dict or None if no telemetry found
    """
    telemetry = get_telemetry(run_id)
    if telemetry is None or not telemetry.samples:
        return None

    metrics = compute_lane_metrics(telemetry)
    config = TelemetryIngestConfig()
    risk = score_risk(metrics, config)
    risk_bucket = classify_risk(risk)

    return {
        "run_id": run_id,
        "metrics": metrics.model_dump(),
        "risk_score": risk,
        "risk_grade": risk_bucket.id.upper(),
        "risk_label": risk_bucket.label,
    }


# Re-export key functions for convenience
__all__ = [
    "compute_learning_lanes",
    "analyze_run_telemetry",
    "get_run_metrics",
    "ingest_run_telemetry_by_id",
    "compute_lane_metrics",
    "score_risk",
    "classify_risk",
]
