"""
CP-S59 — Saw JobLog Storage

File-based persistence for saw operation job logs and telemetry.
Stores runs and telemetry samples in JSON format for audit and learning.

Key Functions:
- save_run() - Persist job log entry
- get_run() - Retrieve job log by run_id
- list_runs() - Query recent runs
- append_telemetry() - Add telemetry sample
- get_telemetry() - Retrieve telemetry for run

Storage:
- data/cnc_production/saw_runs.json - Job log entries
- data/cnc_production/saw_telemetry.json - Telemetry samples

Usage:
```python
from cnc_production.joblog.storage import save_run, append_telemetry

# Save job
run = SawRunRecord(run_id="...", meta=..., gcode="...")
save_run(run)

# Add telemetry
sample = TelemetrySample(x_mm=10.0, y_mm=20.0, rpm_actual=3600)
append_telemetry(run.run_id, sample)
```
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from .models import SawRunRecord, SawTelemetryRecord, TelemetrySample


# ============================================================================
# FILE PATHS
# ============================================================================

# Storage directory (created on first write, not at import time)
DATA_DIR = Path("app/data/cnc_production")

RUNS_PATH = DATA_DIR / "saw_runs.json"
TELEMETRY_PATH = DATA_DIR / "saw_telemetry.json"


def _ensure_data_dir() -> None:
    """Create data directory if it doesn't exist. Called on write operations."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# UTILITIES
# ============================================================================

def _load_json(path: Path) -> Dict[str, Any]:
    """Load JSON file or return empty structure."""
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):  # WP-1: narrowed from except Exception
        return {}


def _save_json(path: Path, data: Dict[str, Any]) -> None:
    """Save data to JSON file with formatting."""
    _ensure_data_dir()  # Create directory on first write
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


# ============================================================================
# JOB LOG PERSISTENCE
# ============================================================================

def save_run(run: SawRunRecord) -> SawRunRecord:
    """
    Save job run to persistent storage.
    
    Creates or updates run entry in saw_runs.json.
    Overwrites existing run with same run_id.
    
    Args:
        run: Complete job run record
    
    Returns:
        Same run record (for chaining)
    
    Example:
        >>> meta = SawRunMeta(op_type="slice", ...)
        >>> run = SawRunRecord(run_id="...", meta=meta, gcode="...")
        >>> save_run(run)
    """
    data = _load_json(RUNS_PATH)
    runs: Dict[str, dict] = data.get("runs", {})
    
    # Convert to dict (handling datetime serialization)
    run_dict = run.model_dump(mode="json")
    runs[run.run_id] = run_dict
    
    data["runs"] = runs
    _save_json(RUNS_PATH, data)
    
    return run


def get_run(run_id: str) -> Optional[SawRunRecord]:
    """
    Retrieve job run by ID.
    
    Args:
        run_id: Unique run identifier
    
    Returns:
        SawRunRecord if found, None otherwise
    
    Example:
        >>> run = get_run("20251127T120000Z_a1b2c3d4")
        >>> print(run.meta.op_type)
        'slice'
    """
    data = _load_json(RUNS_PATH)
    runs: Dict[str, dict] = data.get("runs", {})
    
    if run_id not in runs:
        return None
    
    return SawRunRecord.model_validate(runs[run_id])


def list_runs(
    limit: int = 100,
    op_type: Optional[str] = None,
    machine_profile: Optional[str] = None
) -> List[SawRunRecord]:
    """
    Query recent job runs with optional filtering.
    
    Returns runs in reverse chronological order (newest first).
    
    Args:
        limit: Maximum number of runs to return
        op_type: Filter by operation type (slice, batch, contour)
        machine_profile: Filter by machine identifier
    
    Returns:
        List of SawRunRecord objects
    
    Example:
        >>> recent_slices = list_runs(limit=10, op_type="slice")
        >>> for run in recent_slices:
        ...     print(f"{run.run_id}: {run.meta.total_length_mm}mm")
    """
    data = _load_json(RUNS_PATH)
    runs: Dict[str, dict] = data.get("runs", {})
    
    # Convert to models
    run_list = []
    for run_dict in runs.values():
        try:
            run = SawRunRecord.model_validate(run_dict)
            
            # Apply filters
            if op_type and run.meta.op_type != op_type:
                continue
            if machine_profile and run.meta.machine_profile != machine_profile:
                continue
            
            run_list.append(run)
        except (ValueError, TypeError, KeyError):  # WP-1: narrowed from except Exception
            continue  # Skip malformed entries
    
    # Sort by creation time (newest first)
    run_list.sort(key=lambda r: r.created_at, reverse=True)
    
    return run_list[:limit]


def update_run_status(
    run_id: str,
    status: str,
    started_at: Optional[datetime] = None,
    completed_at: Optional[datetime] = None,
    error_message: Optional[str] = None
) -> Optional[SawRunRecord]:
    """
    Update run execution status and timestamps.
    
    Args:
        run_id: Run identifier
        status: New status (created, running, completed, failed)
        started_at: Execution start time (optional)
        completed_at: Execution completion time (optional)
        error_message: Error details if failed (optional)
    
    Returns:
        Updated SawRunRecord if found, None otherwise
    
    Example:
        >>> update_run_status(
        ...     "20251127T120000Z_a1b2c3d4",
        ...     status="running",
        ...     started_at=datetime.utcnow()
        ... )
    """
    run = get_run(run_id)
    if not run:
        return None
    
    run.status = status
    if started_at:
        run.started_at = started_at
    if completed_at:
        run.completed_at = completed_at
    if error_message:
        run.error_message = error_message
    
    return save_run(run)


# ============================================================================
# TELEMETRY PERSISTENCE
# ============================================================================

def append_telemetry(run_id: str, sample: TelemetrySample) -> SawTelemetryRecord:
    """
    Add telemetry sample to run's telemetry record.
    
    Creates telemetry record if it doesn't exist.
    Appends sample to existing record's sample list.
    
    Args:
        run_id: Associated job run identifier
        sample: Telemetry sample to append
    
    Returns:
        Updated SawTelemetryRecord
    
    Example:
        >>> sample = TelemetrySample(
        ...     x_mm=10.0, y_mm=20.0, z_mm=-1.5,
        ...     rpm_actual=3600, feed_actual_mm_min=1524,
        ...     spindle_load_percent=45.0, in_cut=True
        ... )
        >>> append_telemetry("20251127T120000Z_a1b2c3d4", sample)
    """
    data = _load_json(TELEMETRY_PATH)
    telem: Dict[str, dict] = data.get("telemetry", {})
    
    if run_id in telem:
        # Append to existing record
        rec = SawTelemetryRecord.model_validate(telem[run_id])
        rec.samples.append(sample)
    else:
        # Create new record
        rec = SawTelemetryRecord(run_id=run_id, samples=[sample])
    
    telem[run_id] = rec.model_dump(mode="json")
    data["telemetry"] = telem
    _save_json(TELEMETRY_PATH, data)
    
    return rec


def get_telemetry(run_id: str) -> Optional[SawTelemetryRecord]:
    """
    Retrieve telemetry record for a job run.
    
    Args:
        run_id: Job run identifier
    
    Returns:
        SawTelemetryRecord with all samples if found, None otherwise
    
    Example:
        >>> telem = get_telemetry("20251127T120000Z_a1b2c3d4")
        >>> print(f"Collected {len(telem.samples)} samples")
        >>> avg_load = sum(s.spindle_load_percent for s in telem.samples) / len(telem.samples)
    """
    data = _load_json(TELEMETRY_PATH)
    telem: Dict[str, dict] = data.get("telemetry", {})
    
    if run_id not in telem:
        return None
    
    return SawTelemetryRecord.model_validate(telem[run_id])


def compute_telemetry_stats(run_id: str) -> Optional[SawTelemetryRecord]:
    """
    Compute summary statistics for telemetry record.
    
    Updates avg_feed_mm_min, avg_spindle_load_percent, etc.
    Modifies telemetry record in place.
    
    Args:
        run_id: Job run identifier
    
    Returns:
        Updated SawTelemetryRecord with computed stats, or None if not found
    
    Example:
        >>> compute_telemetry_stats("20251127T120000Z_a1b2c3d4")
        >>> telem = get_telemetry("20251127T120000Z_a1b2c3d4")
        >>> print(f"Avg load: {telem.avg_spindle_load_percent:.1f}%")
    """
    rec = get_telemetry(run_id)
    if not rec or not rec.samples:
        return None
    
    # Filter to cutting samples only
    cut_samples = [s for s in rec.samples if s.in_cut]
    
    if cut_samples:
        # Average feed rate
        feeds = [s.feed_actual_mm_min for s in cut_samples if s.feed_actual_mm_min]
        if feeds:
            rec.avg_feed_mm_min = sum(feeds) / len(feeds)
        
        # Spindle load statistics
        loads = [s.spindle_load_percent for s in cut_samples if s.spindle_load_percent]
        if loads:
            rec.avg_spindle_load_percent = sum(loads) / len(loads)
            rec.max_spindle_load_percent = max(loads)
        
        # Total cut time (approximate)
        if len(cut_samples) > 1:
            first = cut_samples[0].timestamp
            last = cut_samples[-1].timestamp
            rec.total_cut_time_s = (last - first).total_seconds()
        
        # Anomaly detection (simple thresholds)
        anomalies = []
        if rec.max_spindle_load_percent and rec.max_spindle_load_percent > 85:
            anomalies.append(f"High spindle load: {rec.max_spindle_load_percent:.1f}%")
        
        # Check for temperature spikes
        temps = [s.temp_c for s in cut_samples if s.temp_c]
        if temps and max(temps) > 70:
            anomalies.append(f"Temperature spike: {max(temps):.1f}°C")
        
        rec.anomalies = anomalies
    
    # Save updated record
    data = _load_json(TELEMETRY_PATH)
    telem: Dict[str, dict] = data.get("telemetry", {})
    telem[run_id] = rec.model_dump(mode="json")
    data["telemetry"] = telem
    _save_json(TELEMETRY_PATH, data)
    
    return rec
