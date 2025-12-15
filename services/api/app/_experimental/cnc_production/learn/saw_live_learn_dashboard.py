"""
CP-S61/62: Dashboard aggregation for Saw Lab Live Learn system.

Provides run summaries with telemetry metrics, risk scores, and bucket classifications.
Integrates with CP-S59 (JobLog), CP-S60 (Live Learn), and risk bucket system.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from ..joblog.models import SawRunRecord, SawTelemetryRecord
    from ..joblog.storage import RUNS_PATH, TELEMETRY_PATH
    from .models import LaneMetrics
    from .live_learn_ingestor import compute_lane_metrics, score_risk
    from .risk_buckets import classify_risk, RiskBucket
except ImportError:
    # Direct testing import
    from cnc_production.joblog.models import SawRunRecord, SawTelemetryRecord
    from cnc_production.joblog.storage import RUNS_PATH, TELEMETRY_PATH
    from cnc_production.learn.models import LaneMetrics
    from cnc_production.learn.live_learn_ingestor import compute_lane_metrics, score_risk
    from cnc_production.learn.risk_buckets import classify_risk, RiskBucket

import json
from pathlib import Path


# Optional hook into lane-scale history system (for future integration)
try:
    from cnc_production.feeds_speeds.core.lane_scale_store import get_lane_scale_history
except ImportError:
    def get_lane_scale_history(
        tool_id: str,
        material: str,
        mode: str,
        machine_profile: str
    ) -> List[Dict[str, Any]]:
        """Stub for lane-scale history when not available."""
        return []


class RunSummary:
    """
    Dashboard summary for a single CNC run.
    
    Aggregates:
    - Run metadata (CP-S59 JobLog)
    - Telemetry metrics (CP-S60 Live Learn)
    - Risk score and bucket classification (CP-S61)
    - Lane-scale history (optional, future)
    
    Attributes:
        run: SawRunRecord with job metadata
        telemetry: Optional telemetry samples
        metrics: Aggregated metrics (load, rpm, vibration, etc.)
        risk_score: 0-1 risk assessment
        risk_bucket: Color-coded risk classification
        lane_scale_history: Historical scale adjustments (optional)
    """
    def __init__(
        self,
        run: SawRunRecord,
        telemetry: Optional[SawTelemetryRecord],
        metrics: LaneMetrics,
        risk_score: float,
        risk_bucket: RiskBucket,
        lane_scale_history: List[Dict[str, Any]],
    ):
        self.run = run
        self.telemetry = telemetry
        self.metrics = metrics
        self.risk_score = risk_score
        self.risk_bucket = risk_bucket
        self.lane_scale_history = lane_scale_history


def _load_all_runs() -> Dict[str, SawRunRecord]:
    """Load all runs from saw_runs.json."""
    if not RUNS_PATH.exists():
        return {}
    
    with open(RUNS_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    runs_raw: Dict[str, dict] = data.get("runs", {})
    out: Dict[str, SawRunRecord] = {}
    
    for run_id, run_dict in runs_raw.items():
        try:
            out[run_id] = SawRunRecord.model_validate(run_dict)
        except Exception:
            # Skip invalid runs
            continue
    
    return out


def _load_all_telemetry() -> Dict[str, SawTelemetryRecord]:
    """Load all telemetry from saw_telemetry.json."""
    if not TELEMETRY_PATH.exists():
        return {}
    
    with open(TELEMETRY_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    telem_raw: Dict[str, dict] = data.get("telemetry", {})
    out: Dict[str, SawTelemetryRecord] = {}
    
    for run_id, telem_dict in telem_raw.items():
        try:
            out[run_id] = SawTelemetryRecord.model_validate(telem_dict)
        except Exception:
            # Skip invalid telemetry
            continue
    
    return out


def list_run_summaries(limit: int = 50) -> List[RunSummary]:
    """
    List recent runs with telemetry metrics and risk classifications.
    
    Process:
    1. Load all runs from JobLog (CP-S59)
    2. Load all telemetry records
    3. For each run:
       - Compute metrics from telemetry (CP-S60)
       - Score risk (0-1)
       - Classify into risk bucket (CP-S61)
       - Optionally fetch lane-scale history
    4. Sort by created_at (newest first)
    5. Return top N summaries
    
    Args:
        limit: Maximum number of runs to return (default: 50)
    
    Returns:
        List of RunSummary objects with metrics and risk assessments
    
    Example:
        >>> summaries = list_run_summaries(limit=10)
        >>> for s in summaries:
        ...     print(f"{s.run.run_id}: {s.risk_bucket.label} ({s.risk_score:.2f})")
        20251127_T120000_a1b2: Green (0.15)
        20251127_T110000_c3d4: Orange (0.72)
    """
    runs = _load_all_runs()
    telem = _load_all_telemetry()
    
    # Sort runs by created_at desc (newest first)
    sorted_runs = sorted(
        runs.values(),
        key=lambda r: r.created_at if isinstance(r.created_at, datetime) else datetime.min,
        reverse=True,
    )
    
    summaries: List[RunSummary] = []
    
    for run in sorted_runs[:limit]:
        telemetry_record = telem.get(run.run_id)
        
        if telemetry_record and telemetry_record.samples:
            # Compute metrics from telemetry
            metrics = compute_lane_metrics(telemetry_record)
            
            # Score risk using Live Learn algorithm
            from .models import TelemetryIngestConfig
            cfg = TelemetryIngestConfig()
            risk = score_risk(metrics, cfg)
            
            has_data = metrics.n_samples > 0
        else:
            # No telemetry - create empty metrics
            metrics = LaneMetrics(n_samples=0)
            risk = 0.0
            has_data = False
        
        # Classify into risk bucket
        bucket = classify_risk(risk, has_data=has_data)
        
        # Optionally fetch lane-scale history for context
        # (requires tool_id, which may not be in current SawRunMeta)
        tool_id = None  # TODO: extract from run.meta if available
        material = run.meta.material_family
        mode = run.meta.op_type
        machine_profile = run.meta.machine_profile
        
        lane_scale_history = []
        if tool_id:
            try:
                lane_scale_history = get_lane_scale_history(
                    tool_id=tool_id,
                    material=material,
                    mode=mode,
                    machine_profile=machine_profile,
                )
            except Exception:
                lane_scale_history = []
        
        summaries.append(
            RunSummary(
                run=run,
                telemetry=telemetry_record,
                metrics=metrics,
                risk_score=risk,
                risk_bucket=bucket,
                lane_scale_history=lane_scale_history,
            )
        )
    
    return summaries
