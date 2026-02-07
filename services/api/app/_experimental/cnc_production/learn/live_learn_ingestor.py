"""
CP-S60 — Live Learn Telemetry Ingestor

Core logic for ingesting telemetry data and computing lane-scale adjustments.
Takes real-world performance data (spindle load, vibration, temps) and suggests
feed/speed/DOC scaling adjustments per tool/material/machine combination.

Algorithm:
1. Aggregate telemetry samples into lane metrics (averages, maximums, totals)
2. Compute risk score based on spindle load and vibration thresholds
3. Decide scale delta: high load → slow down, low load → speed up
4. Optionally apply adjustment to learned overrides system

Usage:
```python
from cnc_production.learn.live_learn_ingestor import ingest_run_telemetry_by_id
from cnc_production.learn.models import TelemetryIngestRequest

request = TelemetryIngestRequest(
    run_id="20251127T120000Z_a1b2",
    tool_id="TENRYU_GM-305100AB",
    material="hardwood",
    machine_profile="bcam_router_2030",
    current_lane_scale=1.0,
    apply=False  # dry-run
)

result = ingest_run_telemetry_by_id(request)
print(f"Risk: {result.adjustment.risk_score:.2f}")
print(f"Recommended: {result.adjustment.recommended_scale_delta:+.2f}")
```
"""

from __future__ import annotations

from typing import Optional
from datetime import datetime

from .models import (
    TelemetryIngestConfig,
    LaneMetrics,
    LaneAdjustment,
    TelemetryIngestRequest,
    TelemetryIngestResponse,
)

from ..joblog.models import SawRunRecord, SawTelemetryRecord
from ..joblog.storage import get_run, get_telemetry
from ..feeds_speeds.core.learned_overrides import (
    get_learned_overrides_store,
    LaneKey,
    OverrideSource,
)


def apply_lane_scale(
    tool_id: str,
    material: str,
    mode: str,
    machine_profile: str,
    lane_scale: float,
    source: str,
    meta: dict
) -> None:
    """
    Apply lane scale to learned overrides system.

    Updates the lane scale for the (tool_id, material, mode, machine_profile) tuple
    and writes an audit log entry.

    Args:
        tool_id: Tool/blade identifier
        material: Material family
        mode: Operation mode (roughing, finishing)
        machine_profile: Machine identifier
        lane_scale: New scale multiplier (0.5-1.5)
        source: Source of adjustment ("telemetry", "manual", etc.)
        meta: Additional metadata (run_id, risk_score, etc.)
    """
    store = get_learned_overrides_store()

    lane_key = LaneKey(
        tool_id=tool_id,
        material=material,
        mode=mode,
        machine_profile=machine_profile,
    )

    # Map source string to OverrideSource enum
    source_map = {
        "telemetry": OverrideSource.AUTO_LEARN,
        "manual": OverrideSource.MANUAL,
        "operator": OverrideSource.OPERATOR_OVERRIDE,
    }
    override_source = source_map.get(source, OverrideSource.AUTO_LEARN)

    # Build reason string from metadata
    reason_parts = []
    if meta.get("run_id"):
        reason_parts.append(f"run_id={meta['run_id']}")
    if meta.get("risk_score") is not None:
        reason_parts.append(f"risk={meta['risk_score']:.2f}")
    if meta.get("delta") is not None:
        reason_parts.append(f"delta={meta['delta']:+.3f}")
    if meta.get("prev_scale") is not None:
        reason_parts.append(f"prev={meta['prev_scale']:.3f}")
    reason = "; ".join(reason_parts) if reason_parts else "Telemetry-based adjustment"

    store.update_lane_scale(
        lane_key=lane_key,
        lane_scale=lane_scale,
        source=override_source,
        reason=reason,
    )


def compute_lane_metrics(telem: SawTelemetryRecord) -> LaneMetrics:
    """
    Aggregate telemetry samples into lane metrics.
    
    Computes averages and maximums for:
    - RPM and feed rates
    - Spindle load percentages
    - Motor currents
    - Temperatures
    - Vibration RMS
    - Total cutting time
    
    Args:
        telem: Telemetry record with samples list
    
    Returns:
        LaneMetrics with aggregated statistics
    """
    samples = telem.samples
    n = len(samples)
    
    if n == 0:
        return LaneMetrics(n_samples=0)
    
    # Filter to cutting samples only (in_cut=True)
    cut_samples = [s for s in samples if s.in_cut]
    n_cut = len(cut_samples)
    
    if n_cut == 0:
        # No cutting samples, return basic metrics
        return LaneMetrics(n_samples=n)
    
    # Compute averages and maxima
    rpms = [s.rpm_actual for s in cut_samples if s.rpm_actual is not None]
    feeds = [s.feed_actual_mm_min for s in cut_samples if s.feed_actual_mm_min is not None]
    loads = [s.spindle_load_percent for s in cut_samples if s.spindle_load_percent is not None]
    currents = [s.motor_current_amps for s in cut_samples if s.motor_current_amps is not None]
    temps = [s.temp_c for s in cut_samples if s.temp_c is not None]
    vibs = [s.vibration_mg for s in cut_samples if s.vibration_mg is not None]
    
    # Convert vibration from milli-G to mm/s RMS (approximate)
    vib_rms = [v / 1000.0 * 9.81 for v in vibs]  # Convert mG to m/s², then to mm/s
    
    # Compute time span
    total_cut_time_s = None
    if len(cut_samples) >= 2:
        try:
            first_ts = cut_samples[0].timestamp
            last_ts = cut_samples[-1].timestamp
            if isinstance(first_ts, datetime) and isinstance(last_ts, datetime):
                total_cut_time_s = (last_ts - first_ts).total_seconds()
        except (TypeError, ValueError, AttributeError):  # WP-1: narrowed from except Exception
            pass
    
    return LaneMetrics(
        n_samples=n_cut,
        avg_rpm=sum(rpms) / len(rpms) if rpms else None,
        avg_feed_mm_min=sum(feeds) / len(feeds) if feeds else None,
        avg_spindle_load_pct=sum(loads) / len(loads) if loads else None,
        max_spindle_load_pct=max(loads) if loads else None,
        avg_motor_current_amps=sum(currents) / len(currents) if currents else None,
        max_motor_current_amps=max(currents) if currents else None,
        avg_temp_c=sum(temps) / len(temps) if temps else None,
        max_temp_c=max(temps) if temps else None,
        avg_vibration_rms=sum(vib_rms) / len(vib_rms) if vib_rms else None,
        max_vibration_rms=max(vib_rms) if vib_rms else None,
        total_cut_time_s=total_cut_time_s,
    )


def score_risk(metrics: LaneMetrics, cfg: TelemetryIngestConfig) -> float:
    """
    Compute risk score (0-1) based on spindle load and vibration.
    
    Risk factors:
    - Spindle load > high_load_threshold: increases risk
    - Vibration > vibration_warn_threshold: increases risk
    
    Returns:
        0.0 = Safe operation
        1.0 = Dangerous operation (risk of tool breakage, poor finish, etc.)
    
    Args:
        metrics: Aggregated lane metrics
        cfg: Ingest configuration with thresholds
    
    Returns:
        Risk score 0.0-1.0
    """
    load_risk = 0.0
    if metrics.avg_spindle_load_pct is not None and cfg.high_load_threshold_pct > 0:
        load = metrics.avg_spindle_load_pct
        threshold = cfg.high_load_threshold_pct
        if load > threshold:
            # Risk increases linearly above threshold
            load_risk = (load - threshold) / threshold
            load_risk = min(load_risk, 1.0)
    
    vib_risk = 0.0
    if metrics.max_vibration_rms is not None and cfg.vibration_warn_threshold > 0:
        vib = metrics.max_vibration_rms
        threshold = cfg.vibration_warn_threshold
        if vib > threshold:
            # Risk increases linearly above threshold
            vib_risk = (vib - threshold) / threshold
            vib_risk = min(vib_risk, 1.0)
    
    # Weighted blend: load is slightly more important than vibration
    risk = 0.6 * load_risk + 0.4 * vib_risk
    return max(0.0, min(risk, 1.0))


def decide_scale_delta(metrics: LaneMetrics, cfg: TelemetryIngestConfig) -> float:
    """
    Decide lane scale adjustment based on average spindle load.
    
    Decision rules:
    - Load > high_threshold: Slow down (negative delta)
    - Load < low_threshold: Speed up (positive delta)
    - Load in neutral zone: No change (zero delta)
    
    Args:
        metrics: Aggregated lane metrics
        cfg: Ingest configuration with thresholds and step sizes
    
    Returns:
        Scale delta (-down_scale_step to +up_scale_step)
    """
    if metrics.avg_spindle_load_pct is None:
        return 0.0
    
    avg_load = metrics.avg_spindle_load_pct
    
    if avg_load > cfg.high_load_threshold_pct:
        # Too high: slow down
        return -cfg.down_scale_step
    elif avg_load < cfg.low_load_threshold_pct:
        # Too low: speed up
        return cfg.up_scale_step
    else:
        # Neutral zone: no change
        return 0.0


def clamp_scale(current: float, delta: float, cfg: TelemetryIngestConfig) -> float:
    """
    Apply scale delta with clamping to safe bounds.
    
    Args:
        current: Current lane scale
        delta: Proposed change
        cfg: Config with min_scale and max_scale bounds
    
    Returns:
        New scale clamped to [min_scale, max_scale]
    """
    new_val = current + delta
    return max(cfg.min_scale, min(new_val, cfg.max_scale))


def ingest_run_telemetry(
    run: SawRunRecord,
    telem: SawTelemetryRecord,
    tool_id: str,
    material: str,
    mode: str,
    machine_profile: str,
    current_lane_scale: float,
    cfg: TelemetryIngestConfig,
    apply: bool = False,
) -> LaneAdjustment:
    """
    Core ingest function: analyze telemetry and generate lane adjustment.
    
    Process:
    1. Compute lane metrics from telemetry samples
    2. Score risk based on load and vibration
    3. Decide scale delta based on average load
    4. Optionally apply to learned overrides
    
    Args:
        run: Job run record
        telem: Telemetry samples
        tool_id: Tool/blade identifier
        material: Material family
        mode: Operation mode
        machine_profile: Machine identifier
        current_lane_scale: Current scale multiplier
        cfg: Ingest configuration
        apply: Whether to apply adjustment immediately
    
    Returns:
        LaneAdjustment with metrics, risk, and recommended delta
    """
    # Compute metrics
    metrics = compute_lane_metrics(telem)
    
    # Check minimum samples threshold
    if metrics.n_samples < cfg.min_samples:
        return LaneAdjustment(
            tool_id=tool_id,
            material=material,
            mode=mode,
            machine_profile=machine_profile,
            metrics=metrics,
            risk_score=0.0,
            recommended_scale_delta=0.0,
            new_lane_scale=None,
            applied=False,
            reason=f"Not enough telemetry samples (have {metrics.n_samples}, need {cfg.min_samples})",
        )
    
    # Score risk and decide delta
    risk = score_risk(metrics, cfg)
    delta = decide_scale_delta(metrics, cfg)
    
    # Compute new scale with clamping
    new_scale = clamp_scale(current_lane_scale, delta, cfg) if delta != 0 else current_lane_scale
    
    # Generate explanation
    applied_flag = False
    if delta == 0:
        reason = f"Average spindle load {metrics.avg_spindle_load_pct:.1f}% within neutral band [{cfg.low_load_threshold_pct:.1f}%, {cfg.high_load_threshold_pct:.1f}%]; no scale change recommended."
    elif delta > 0:
        reason = f"Average load {metrics.avg_spindle_load_pct:.1f}% below low threshold {cfg.low_load_threshold_pct:.1f}%, suggesting we can speed up slightly."
    else:
        reason = f"Average load {metrics.avg_spindle_load_pct:.1f}% above high threshold {cfg.high_load_threshold_pct:.1f}%, suggesting we should slow down slightly."
    
    # Apply if requested
    if apply and delta != 0:
        apply_lane_scale(
            tool_id=tool_id,
            material=material,
            mode=mode,
            machine_profile=machine_profile,
            lane_scale=new_scale,
            source="telemetry",
            meta={
                "run_id": run.run_id,
                "risk_score": risk,
                "delta": delta,
                "prev_scale": current_lane_scale,
            },
        )
        applied_flag = True
        reason += f" Adjustment applied: {current_lane_scale:.3f} → {new_scale:.3f}."
    
    return LaneAdjustment(
        tool_id=tool_id,
        material=material,
        mode=mode,
        machine_profile=machine_profile,
        metrics=metrics,
        risk_score=risk,
        recommended_scale_delta=delta,
        new_lane_scale=new_scale if delta != 0 else None,
        applied=applied_flag,
        reason=reason,
    )


def ingest_run_telemetry_by_id(req: TelemetryIngestRequest) -> TelemetryIngestResponse:
    """
    Ingest telemetry for a specific run ID (convenience wrapper).
    
    Loads run and telemetry from JobLog storage, then delegates to core ingest function.
    
    Args:
        req: Ingest request with run_id and parameters
    
    Returns:
        TelemetryIngestResponse with metrics and adjustment
    
    Raises:
        ValueError: If run or telemetry not found
    """
    # Load run and telemetry from JobLog
    run = get_run(req.run_id)
    if not run:
        raise ValueError(f"Run {req.run_id} not found in JobLog")
    
    telem = get_telemetry(req.run_id)
    if not telem:
        raise ValueError(f"No telemetry found for run {req.run_id}")
    
    # Ingest and analyze
    adjustment = ingest_run_telemetry(
        run=run,
        telem=telem,
        tool_id=req.tool_id,
        material=req.material,
        mode=req.mode,
        machine_profile=req.machine_profile,
        current_lane_scale=req.current_lane_scale,
        cfg=req.config,
        apply=req.apply,
    )
    
    return TelemetryIngestResponse(
        run_id=req.run_id,
        metrics=adjustment.metrics,
        adjustment=adjustment,
    )
