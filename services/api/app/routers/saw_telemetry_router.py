"""
CP-S60: Saw Telemetry Router
Live telemetry ingestion with automatic learning updates.

Features:
- Ingest telemetry data (RPM, load, vibration, sound)
- Compute risk scores (0-1 scale, higher = riskier)
- Calculate lane scale deltas based on risk
- Automatic override updates for learned_overrides system
- Run record management (create, update, list, stats)

Risk Scoring:
- Overload: spindle_load_pct / 100 (>80% = high risk)
- Vibration: vibration_rms scaled (>0.5g = high risk)
- Sound: (sound_db - 70) / 30 clamped to [0,1] (>100dB = high risk)
- Overall: weighted average (40% overload, 30% vibration, 30% sound)

Lane Scale Updates:
- Low risk (0-0.3): Increase lane_scale by +0.05 (speed up)
- Medium risk (0.3-0.7): No change (maintain)
- High risk (0.7-1.0): Decrease lane_scale by -0.10 (slow down)

Integration:
- CP-S50: blade_id from saw_blade_registry
- CP-S52: Updates learned_overrides via set_override() and update_lane_scale()
- CP-S59: Stores run records in saw_joblog
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional

from .._experimental.cnc_production.joblog.saw_joblog_models import (
    SawRunRecord,
    SawRunRecordCreate,
    SawRunRecordUpdate,
    TelemetryData,
    RunStatus,
    SawOperationType,
    get_saw_joblog_store
)
from .._experimental.cnc_production.feeds_speeds.core.learned_overrides import (
    LaneKey,
    OverrideSource,
    get_learned_overrides_store
)


router = APIRouter()


# ============================================================================
# Risk Scoring Functions
# ============================================================================

def compute_overload_risk(spindle_load_pct: Optional[float]) -> float:
    """
    Compute spindle overload risk (0-1).
    
    Logic:
    - <50%: Low risk (0.0-0.5)
    - 50-80%: Medium risk (0.5-0.8)
    - >80%: High risk (0.8-1.0)
    """
    if spindle_load_pct is None:
        return 0.5  # Unknown = assume medium risk
    
    # Linear scale: 0% = 0.0, 100% = 1.0
    risk = spindle_load_pct / 100.0
    return max(0.0, min(1.0, risk))


def compute_vibration_risk(vibration_rms: Optional[float]) -> float:
    """
    Compute vibration risk (0-1).
    
    Logic:
    - <0.2g: Low risk (0.0-0.4)
    - 0.2-0.5g: Medium risk (0.4-0.7)
    - >0.5g: High risk (0.7-1.0)
    
    Typical wood CNC: <0.3g nominal, >0.5g concerning
    """
    if vibration_rms is None:
        return 0.5  # Unknown = assume medium risk
    
    # Scale: 0g = 0.0, 0.7g+ = 1.0
    risk = vibration_rms / 0.7
    return max(0.0, min(1.0, risk))


def compute_sound_risk(sound_db: Optional[float]) -> float:
    """
    Compute sound risk (0-1).
    
    Logic:
    - <70dB: Low risk (0.0-0.3)
    - 70-90dB: Medium risk (0.3-0.7)
    - >100dB: High risk (0.7-1.0)
    
    Typical wood CNC: 70-90dB nominal, >100dB problematic
    """
    if sound_db is None:
        return 0.5  # Unknown = assume medium risk
    
    # Scale: 70dB = 0.0, 100dB+ = 1.0
    if sound_db < 70:
        risk = 0.0
    elif sound_db > 100:
        risk = 1.0
    else:
        risk = (sound_db - 70) / 30.0
    
    return max(0.0, min(1.0, risk))


def compute_overall_risk(telemetry: TelemetryData) -> TelemetryData:
    """
    Compute all risk scores and overall risk.
    
    Weights:
    - Overload: 40% (most critical)
    - Vibration: 30% (tool wear indicator)
    - Sound: 30% (quality indicator)
    """
    telemetry.overload_risk = compute_overload_risk(telemetry.spindle_load_pct)
    telemetry.vibration_risk = compute_vibration_risk(telemetry.vibration_rms)
    telemetry.sound_risk = compute_sound_risk(telemetry.sound_db)
    
    # Weighted average
    telemetry.overall_risk = (
        0.40 * telemetry.overload_risk +
        0.30 * telemetry.vibration_risk +
        0.30 * telemetry.sound_risk
    )
    
    return telemetry


# ============================================================================
# Learning Functions
# ============================================================================

def calculate_lane_scale_delta(overall_risk: float, current_scale: float) -> float:
    """
    Calculate lane scale adjustment based on risk.
    
    Logic:
    - Low risk (0-0.3): Speed up (+0.05, max 1.3)
    - Medium risk (0.3-0.7): Maintain (0.0)
    - High risk (0.7-1.0): Slow down (-0.10, min 0.7)
    
    Conservative approach: Slow down faster than speed up.
    """
    if overall_risk < 0.3:
        # Low risk: Speed up gradually
        delta = 0.05
        new_scale = min(1.3, current_scale + delta)  # Cap at 130%
    elif overall_risk < 0.7:
        # Medium risk: No change
        delta = 0.0
        new_scale = current_scale
    else:
        # High risk: Slow down aggressively
        delta = -0.10
        new_scale = max(0.7, current_scale + delta)  # Floor at 70%
    
    return new_scale - current_scale


def apply_auto_learning(
    run: SawRunRecord,
    telemetry: TelemetryData
) -> bool:
    """
    Apply automatic learning based on telemetry.
    
    Steps:
    1. Get lane from learned_overrides (or create if new)
    2. Calculate risk-based lane scale delta
    3. Update lane scale if delta significant (|delta| > 0.02)
    4. Record successful run in learned_overrides
    
    Returns:
        True if learning applied, False if no action taken
    """
    try:
        store = get_learned_overrides_store()
        
        # Build lane key
        lane_key = LaneKey(
            tool_id=run.blade_id,
            material=run.material_family,
            mode=run.op_type.value,
            machine_profile=run.machine_profile
        )
        
        # Get or create lane
        lane = store.get_or_create_lane(lane_key)
        current_scale = lane.lane_scale
        
        # Calculate delta
        delta = calculate_lane_scale_delta(telemetry.overall_risk, current_scale)
        
        # Apply if significant
        if abs(delta) > 0.02:
            new_scale = current_scale + delta
            
            # Update lane scale
            store.update_lane_scale(
                lane_key=lane_key,
                lane_scale=new_scale,
                source=OverrideSource.AUTO_LEARN,
                operator="system",
                reason=f"Risk-based adjustment: overall_risk={telemetry.overall_risk:.2f}, delta={delta:+.2f}"
            )
            
            # Record in run
            run.lane_scale_before = current_scale
            run.lane_scale_after = new_scale
            run.auto_learned = True
            
            return True
        
        # Record run even if no scale update
        success = run.status == RunStatus.SUCCESS
        store.record_run(lane_key, success=success)
        
        return False
    
    except Exception as e:
        # Don't fail run if learning fails
        print(f"Warning: Auto-learning failed: {e}")
        return False


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/saw/telemetry/ingest", response_model=SawRunRecord)
def ingest_telemetry(
    run_id: str,
    telemetry: TelemetryData,
    apply_learning: bool = True
):
    """
    Ingest telemetry data for a run and optionally apply auto-learning.
    
    Steps:
    1. Get run record
    2. Compute risk scores
    3. Update run with telemetry
    4. Apply auto-learning if enabled
    
    Returns updated run record.
    """
    store = get_saw_joblog_store()
    
    # Get run
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    # Compute risk scores
    telemetry = compute_overall_risk(telemetry)
    
    # Update run
    update = SawRunRecordUpdate(telemetry=telemetry)
    run = store.update_run(run_id, update)
    
    if not run:
        raise HTTPException(status_code=500, detail="Failed to update run")
    
    # Apply learning
    if apply_learning and run.status == RunStatus.SUCCESS:
        apply_auto_learning(run, telemetry)
        
        # Re-fetch to get updated learning fields
        run = store.get_run(run_id)
    
    return run


@router.post("/saw/joblog/run", response_model=SawRunRecord)
def create_run(create_req: SawRunRecordCreate):
    """
    Create new saw run record.
    
    Called when starting a new operation.
    """
    store = get_saw_joblog_store()
    run = store.create_run(create_req)
    return run


@router.patch("/saw/joblog/run/{run_id}", response_model=SawRunRecord)
def update_run(run_id: str, update_req: SawRunRecordUpdate):
    """
    Update existing run record.
    
    Used to mark completion, add notes, etc.
    """
    store = get_saw_joblog_store()
    
    run = store.update_run(run_id, update_req)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    return run


@router.get("/saw/joblog/run/{run_id}", response_model=SawRunRecord)
def get_run(run_id: str):
    """Get run record by ID"""
    store = get_saw_joblog_store()
    
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    return run


@router.get("/saw/joblog/runs", response_model=List[SawRunRecord])
def list_runs(
    limit: Optional[int] = None,
    machine_profile: Optional[str] = None,
    material_family: Optional[str] = None,
    blade_id: Optional[str] = None,
    status: Optional[RunStatus] = None
):
    """
    List run records with optional filters.
    
    Query parameters:
    - limit: Max number of runs to return (default: all)
    - machine_profile: Filter by machine
    - material_family: Filter by material
    - blade_id: Filter by blade
    - status: Filter by status (success/failed/aborted/pending)
    """
    store = get_saw_joblog_store()
    runs = store.list_runs(
        limit=limit,
        machine_profile=machine_profile,
        material_family=material_family,
        blade_id=blade_id,
        status=status
    )
    return runs


@router.delete("/saw/joblog/run/{run_id}")
def delete_run(run_id: str):
    """Delete run record"""
    store = get_saw_joblog_store()
    
    if not store.delete_run(run_id):
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    return {"message": f"Run {run_id} deleted"}


@router.get("/saw/joblog/stats")
def get_stats():
    """
    Get aggregate statistics.
    
    Returns:
    - total_runs: Total number of runs
    - success_rate: Fraction of successful runs
    - avg_time_s: Average run time
    - total_length_mm: Total material cut
    - runs_by_status: Count per status
    - runs_by_machine: Count per machine
    - runs_by_material: Count per material
    """
    store = get_saw_joblog_store()
    return store.get_statistics()


# ============================================================================
# Learning Analysis Endpoints
# ============================================================================

@router.get("/saw/telemetry/risk_summary")
def get_risk_summary(
    machine_profile: Optional[str] = None,
    material_family: Optional[str] = None,
    limit: int = 50
):
    """
    Get risk summary across recent runs.
    
    Analyzes telemetry data to identify:
    - High risk runs (overall_risk > 0.7)
    - Average risk by machine/material
    - Trends over time
    """
    store = get_saw_joblog_store()
    
    # Get runs with telemetry
    runs = store.list_runs(
        limit=limit,
        machine_profile=machine_profile,
        material_family=material_family
    )
    
    # Filter runs with telemetry
    runs_with_telemetry = [r for r in runs if r.telemetry and r.telemetry.overall_risk is not None]
    
    if not runs_with_telemetry:
        return {
            "total_runs": 0,
            "avg_risk": 0.0,
            "high_risk_count": 0,
            "risk_distribution": {"low": 0, "medium": 0, "high": 0}
        }
    
    # Calculate statistics
    risks = [r.telemetry.overall_risk for r in runs_with_telemetry]
    avg_risk = sum(risks) / len(risks)
    
    high_risk_count = sum(1 for r in risks if r > 0.7)
    
    risk_dist = {
        "low": sum(1 for r in risks if r < 0.3),
        "medium": sum(1 for r in risks if 0.3 <= r < 0.7),
        "high": sum(1 for r in risks if r >= 0.7)
    }
    
    return {
        "total_runs": len(runs_with_telemetry),
        "avg_risk": avg_risk,
        "high_risk_count": high_risk_count,
        "risk_distribution": risk_dist,
        "recent_runs": [
            {
                "run_id": r.run_id,
                "timestamp": r.timestamp,
                "overall_risk": r.telemetry.overall_risk,
                "overload_risk": r.telemetry.overload_risk,
                "vibration_risk": r.telemetry.vibration_risk,
                "sound_risk": r.telemetry.sound_risk,
                "auto_learned": r.auto_learned,
                "lane_scale_delta": (r.lane_scale_after - r.lane_scale_before) if (r.lane_scale_after and r.lane_scale_before) else None
            }
            for r in runs_with_telemetry[:10]  # Last 10 runs
        ]
    }


@router.post("/saw/telemetry/simulate_learning")
def simulate_learning(
    telemetry: TelemetryData,
    current_lane_scale: float = 1.0
):
    """
    Simulate learning without applying changes.
    
    Useful for:
    - Testing risk scoring
    - Previewing learning behavior
    - Operator training
    
    Returns:
    - Risk scores
    - Recommended lane scale delta
    - Explanation
    """
    # Compute risk scores
    telemetry = compute_overall_risk(telemetry)
    
    # Calculate delta
    delta = calculate_lane_scale_delta(telemetry.overall_risk, current_lane_scale)
    new_scale = current_lane_scale + delta
    
    # Determine action
    if abs(delta) <= 0.02:
        action = "No change (risk in acceptable range)"
    elif delta > 0:
        action = f"Speed up (+{delta:.2f}) - Low risk detected"
    else:
        action = f"Slow down ({delta:.2f}) - High risk detected"
    
    return {
        "telemetry": telemetry.dict(),
        "current_lane_scale": current_lane_scale,
        "recommended_lane_scale": new_scale,
        "delta": delta,
        "action": action,
        "explanation": {
            "overload": f"Spindle load {telemetry.spindle_load_pct or 0:.1f}% → risk {telemetry.overload_risk:.2f}",
            "vibration": f"Vibration {telemetry.vibration_rms or 0:.2f}g → risk {telemetry.vibration_risk:.2f}",
            "sound": f"Sound {telemetry.sound_db or 0:.1f}dB → risk {telemetry.sound_risk:.2f}",
            "overall": f"Overall risk {telemetry.overall_risk:.2f}"
        }
    }
