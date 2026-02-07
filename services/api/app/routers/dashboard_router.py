"""
CP-S61/62: Dashboard API for Saw Lab Live Learn system.

Exposes run summaries with risk classifications, metrics, and action recommendations.
Frontend: Operator dashboard for monitoring CNC health and risk trends.
"""
from __future__ import annotations
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

try:
    from .._experimental.cnc_production.learn.saw_live_learn_dashboard import list_run_summaries
except ImportError:
    # Direct testing import
    from _experimental.cnc_production.learn.saw_live_learn_dashboard import list_run_summaries


router = APIRouter(prefix="/dashboard/saw", tags=["dashboard", "saw_lab"])


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class LaneScaleHistoryPoint(BaseModel):
    """Historical lane-scale adjustment point."""
    ts: str = Field(..., description="ISO timestamp of adjustment")
    lane_scale: float = Field(..., description="Scale factor (0.5-1.5)")
    source: Optional[str] = Field(None, description="Source of adjustment (manual/auto)")


class MetricsSummary(BaseModel):
    """Aggregated telemetry metrics."""
    n_samples: int = Field(..., description="Number of cutting samples")
    avg_rpm: Optional[float] = Field(None, description="Average spindle RPM")
    avg_feed_mm_min: Optional[float] = Field(None, description="Average feed rate (mm/min)")
    avg_spindle_load_pct: Optional[float] = Field(None, description="Average spindle load (%)")
    max_spindle_load_pct: Optional[float] = Field(None, description="Peak spindle load (%)")
    avg_vibration_rms: Optional[float] = Field(None, description="Average vibration (mm/s RMS)")
    max_vibration_rms: Optional[float] = Field(None, description="Peak vibration (mm/s RMS)")


class RiskBucketInfo(BaseModel):
    """Risk classification bucket."""
    id: str = Field(..., description="Bucket ID (unknown/green/yellow/orange/red)")
    label: str = Field(..., description="Human-readable label")
    description: str = Field(..., description="Risk level explanation")


class RunSummaryItem(BaseModel):
    """Dashboard item for a single CNC run."""
    run_id: str = Field(..., description="Unique run identifier")
    created_at: str = Field(..., description="Run creation timestamp (ISO)")
    
    # Metadata
    op_type: str = Field(..., description="Operation type (slice/batch/contour)")
    machine_profile: str = Field(..., description="Machine configuration")
    material_family: str = Field(..., description="Material being cut")
    blade_id: Optional[str] = Field(None, description="Blade identifier")
    
    # Status
    status: str = Field(..., description="Run status (pending/running/completed/error)")
    started_at: Optional[str] = Field(None, description="Execution start time (ISO)")
    completed_at: Optional[str] = Field(None, description="Execution end time (ISO)")
    
    # Metrics
    has_telemetry: bool = Field(..., description="Whether telemetry data exists")
    metrics: Optional[MetricsSummary] = Field(None, description="Aggregated metrics")
    
    # Risk
    risk_score: float = Field(..., description="Risk score 0.0-1.0")
    risk_bucket: RiskBucketInfo = Field(..., description="Color-coded risk classification")
    
    # History
    lane_scale_history: List[LaneScaleHistoryPoint] = Field(
        default_factory=list,
        description="Historical scale adjustments for this lane"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "run_id": "20251127T120000Z_a1b2c3",
                "created_at": "2025-11-27T12:00:00Z",
                "op_type": "slice",
                "machine_profile": "SAW_LAB_01",
                "material_family": "hardwood",
                "blade_id": "BLADE_10IN_60T",
                "status": "completed",
                "started_at": "2025-11-27T12:00:05Z",
                "completed_at": "2025-11-27T12:05:30Z",
                "has_telemetry": True,
                "metrics": {
                    "n_samples": 150,
                    "avg_rpm": 3600,
                    "avg_feed_mm_min": 1200,
                    "avg_spindle_load_pct": 65.5,
                    "max_spindle_load_pct": 82.3,
                    "avg_vibration_rms": 5.2,
                    "max_vibration_rms": 8.1
                },
                "risk_score": 0.42,
                "risk_bucket": {
                    "id": "yellow",
                    "label": "Yellow",
                    "description": "Moderate load or occasional vibration spikes."
                },
                "lane_scale_history": []
            }
        }


class DashboardSummary(BaseModel):
    """Dashboard response with run summaries."""
    total_runs: int = Field(..., description="Total runs in system")
    returned_runs: int = Field(..., description="Number of runs in this response")
    runs: List[RunSummaryItem] = Field(..., description="Run summaries with metrics")


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/runs", response_model=DashboardSummary)
def get_dashboard_runs(
    limit: int = Query(
        50,
        ge=1,
        le=500,
        description="Maximum number of runs to return"
    )
) -> DashboardSummary:
    """
    Get recent CNC runs with risk classifications and metrics.
    
    **Process:**
    1. Load runs from JobLog (CP-S59)
    2. Load telemetry data
    3. Compute metrics (avg load, rpm, vibration)
    4. Score risk (0-1) using Live Learn algorithm
    5. Classify into risk buckets (green/yellow/orange/red)
    6. Sort by creation time (newest first)
    
    **Risk Buckets:**
    - **Unknown** (gray): No telemetry or insufficient data
    - **Green**: Risk 0-0.3 (safe operation)
    - **Yellow**: Risk 0.3-0.6 (moderate, monitor recommended)
    - **Orange**: Risk 0.6-0.85 (high, consider slowing)
    - **Red**: Risk 0.85-1.0 (dangerous, slow down immediately)
    
    **Use Cases:**
    - Operator dashboard for real-time monitoring
    - Risk trend analysis across runs
    - Identifying problematic tool/material combinations
    - Triggering automatic slowdown actions
    
    **Example:**
    ```typescript
    const response = await fetch('/api/dashboard/saw/runs?limit=20')
    const { runs } = await response.json()
    
    // Filter by risk level
    const highRisk = runs.filter(r => r.risk_bucket.id === 'orange' || r.risk_bucket.id === 'red')
    
    // Display in dashboard
    highRisk.forEach(run => {
        console.log(`⚠️ ${run.run_id}: ${run.risk_bucket.label} (${run.risk_score.toFixed(2)})`)
        console.log(`   Load: ${run.metrics.avg_spindle_load_pct}%`)
        console.log(`   Vibration: ${run.metrics.avg_vibration_rms} mm/s`)
    })
    ```
    
    Args:
        limit: Maximum number of runs to return (1-500, default: 50)
    
    Returns:
        DashboardSummary with recent runs sorted by creation time
    
    Raises:
        500: Internal error loading runs or computing metrics
    """
    try:
        summaries = list_run_summaries(limit=limit)
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load dashboard summaries: {str(e)}"
        )
    
    # Convert RunSummary objects to API models
    run_items = []
    for summary in summaries:
        # Convert metrics
        metrics_dict = None
        if summary.metrics.n_samples > 0:
            metrics_dict = MetricsSummary(
                n_samples=summary.metrics.n_samples,
                avg_rpm=summary.metrics.avg_rpm,
                avg_feed_mm_min=summary.metrics.avg_feed_mm_min,
                avg_spindle_load_pct=summary.metrics.avg_spindle_load_pct,
                max_spindle_load_pct=summary.metrics.max_spindle_load_pct,
                avg_vibration_rms=summary.metrics.avg_vibration_rms,
                max_vibration_rms=summary.metrics.max_vibration_rms,
            )
        
        # Convert risk bucket
        risk_bucket_info = RiskBucketInfo(
            id=summary.risk_bucket.id,
            label=summary.risk_bucket.label,
            description=summary.risk_bucket.description,
        )
        
        # Convert lane-scale history
        history = [
            LaneScaleHistoryPoint(**point)
            for point in summary.lane_scale_history
        ]
        
        # Convert run timestamps
        created_at = summary.run.created_at.isoformat() if isinstance(summary.run.created_at, object) else str(summary.run.created_at)
        started_at = summary.run.started_at.isoformat() if summary.run.started_at and isinstance(summary.run.started_at, object) else (str(summary.run.started_at) if summary.run.started_at else None)
        completed_at = summary.run.completed_at.isoformat() if summary.run.completed_at and isinstance(summary.run.completed_at, object) else (str(summary.run.completed_at) if summary.run.completed_at else None)
        
        run_items.append(
            RunSummaryItem(
                run_id=summary.run.run_id,
                created_at=created_at,
                op_type=summary.run.meta.op_type,
                machine_profile=summary.run.meta.machine_profile,
                material_family=summary.run.meta.material_family,
                blade_id=summary.run.meta.blade_id,
                status=summary.run.status,
                started_at=started_at,
                completed_at=completed_at,
                has_telemetry=summary.telemetry is not None,
                metrics=metrics_dict,
                risk_score=summary.risk_score,
                risk_bucket=risk_bucket_info,
                lane_scale_history=history,
            )
        )
    
    # Count total runs (approximation - could load full count if needed)
    total_runs = len(run_items)  # Conservative estimate
    
    return DashboardSummary(
        total_runs=total_runs,
        returned_runs=len(run_items),
        runs=run_items,
    )


@router.get("/health")
def health_check():
    """
    Health check for dashboard API.
    
    Returns:
        Status object with module info
    """
    return {
        "status": "healthy",
        "module": "CP-S61/62 Dashboard + Risk Actions",
        "features": [
            "Run summaries with risk classifications",
            "Telemetry metrics aggregation",
            "Risk bucket color coding",
            "Lane-scale history tracking"
        ]
    }
