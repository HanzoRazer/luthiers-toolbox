"""
CP-S60 — Live Learn Telemetry API Router

REST API for telemetry ingestion and lane-scale learning.
Analyzes real-world CNC performance data and suggests feed/speed optimizations.

Endpoints:
- POST /learn/ingest - Ingest telemetry and compute lane adjustments

Usage:
```python
# In main.py
from routers import learn_router

app.include_router(learn_router.router)
```

Example Request:
```bash
curl -X POST http://localhost:8000/api/learn/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "run_id": "20251127T120000Z_a1b2c3d4",
    "tool_id": "TENRYU_GM-305100AB",
    "material": "hardwood",
    "mode": "roughing",
    "machine_profile": "bcam_router_2030",
    "current_lane_scale": 1.0,
    "apply": false
  }'
```

Response:
```json
{
  "run_id": "20251127T120000Z_a1b2c3d4",
  "metrics": {
    "n_samples": 47,
    "avg_spindle_load_pct": 85.3,
    "max_spindle_load_pct": 92.1,
    "avg_vibration_rms": 1.2
  },
  "adjustment": {
    "tool_id": "TENRYU_GM-305100AB",
    "material": "hardwood",
    "mode": "roughing",
    "machine_profile": "bcam_router_2030",
    "risk_score": 0.72,
    "recommended_scale_delta": -0.05,
    "new_lane_scale": 0.95,
    "applied": false,
    "reason": "Average load 85.3% above high threshold 80.0%, suggesting we should slow down slightly."
  }
}
```
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

try:
    # FastAPI application import (normal deployment)
    from .._experimental.cnc_production.learn.models import (
        TelemetryIngestRequest,
        TelemetryIngestResponse,
    )
    from .._experimental.cnc_production.learn.live_learn_ingestor import ingest_run_telemetry_by_id
except ImportError:
    # Direct testing import
    from _experimental.cnc_production.learn.models import (
        TelemetryIngestRequest,
        TelemetryIngestResponse,
    )
    from _experimental.cnc_production.learn.live_learn_ingestor import ingest_run_telemetry_by_id


router = APIRouter(prefix="/learn", tags=["learn", "telemetry"])


@router.post("/ingest", response_model=TelemetryIngestResponse)
def ingest_telemetry(req: TelemetryIngestRequest) -> TelemetryIngestResponse:
    """
    Ingest telemetry from a saw operation run and compute lane-scale adjustments.
    
    This endpoint analyzes real-world CNC performance data (spindle loads, vibration,
    temperatures) and recommends feed/speed scaling adjustments for future operations
    with the same tool/material/machine combination.
    
    **Process:**
    1. Load run and telemetry data from JobLog (CP-S59)
    2. Aggregate samples into lane metrics (averages, maxima, totals)
    3. Compute risk score based on spindle load and vibration thresholds
    4. Recommend scale delta: high load → slow down, low load → speed up
    5. Optionally apply adjustment to learned overrides system
    
    **Use Cases:**
    - **Dry-run analysis** (apply=false): Preview recommended adjustments
    - **Automatic tuning** (apply=true): Apply adjustments immediately
    - **Batch optimization**: Process multiple runs to find optimal settings
    - **Risk monitoring**: Track risk scores across jobs for quality control
    
    **Safety Features:**
    - Minimum samples threshold prevents premature learning
    - Scale clamping (0.5x - 1.5x) prevents extreme adjustments
    - Neutral load band (40%-80%) avoids unnecessary changes
    - Human-readable explanations for all decisions
    
    Args:
        req: Ingest request with run_id, tool/material/machine context, and config
    
    Returns:
        TelemetryIngestResponse with aggregated metrics and recommended adjustment
    
    Raises:
        404: Run or telemetry not found in JobLog
        500: Ingestion processing error
    
    Example:
        ```json
        {
          "run_id": "20251127T120000Z_a1b2c3d4",
          "tool_id": "TENRYU_GM-305100AB",
          "material": "hardwood",
          "mode": "roughing",
          "machine_profile": "bcam_router_2030",
          "current_lane_scale": 1.0,
          "config": {
            "low_load_threshold_pct": 40,
            "high_load_threshold_pct": 80,
            "min_samples": 5
          },
          "apply": false
        }
        ```
    
    Response includes:
    - **metrics**: Aggregated telemetry statistics
      - n_samples: Number of cutting samples
      - avg_spindle_load_pct: Average spindle load during cutting
      - max_spindle_load_pct: Peak spindle load
      - avg_vibration_rms: Average vibration (mm/s RMS)
      - total_cut_time_s: Total time in cut
    
    - **adjustment**: Recommended lane-scale adjustment
      - risk_score: 0-1 risk assessment (0=safe, 1=dangerous)
      - recommended_scale_delta: Suggested change (-0.05 = slow 5%, +0.05 = speed 5%)
      - new_lane_scale: New scale if applied
      - applied: Whether adjustment was written to overrides
      - reason: Human-readable explanation
    
    **Integration with Saw Lab:**
    ```typescript
    // After completing a saw operation
    const response = await axios.post('/api/learn/ingest', {
      run_id: jobLog.run_id,
      tool_id: selectedBlade.id,
      material: operation.material,
      machine_profile: machineProfile,
      current_lane_scale: 1.0,
      apply: false  // Preview first
    })
    
    if (response.data.adjustment.risk_score > 0.5) {
      console.warn('High risk detected:', response.data.adjustment.reason)
    }
    
    if (response.data.adjustment.recommended_scale_delta !== 0) {
      console.log('Suggested adjustment:', response.data.adjustment.reason)
      // Optionally apply with another request (apply=true)
    }
    ```
    """
    try:
        return ingest_run_telemetry_by_id(req)
    except ValueError as e:
        # Run or telemetry not found
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        # Other processing errors
        raise HTTPException(
            status_code=500,
            detail=f"Telemetry ingestion failed: {str(e)}"
        )


@router.get("/health")
def health_check():
    """
    Health check endpoint for Live Learn system.
    
    Returns:
        Status and version information
    """
    return {
        "status": "healthy",
        "module": "CP-S60 Live Learn Ingestor",
        "version": "1.0.0",
        "features": [
            "Telemetry ingestion",
            "Lane-scale learning",
            "Risk scoring",
            "Automatic feed/speed optimization"
        ]
    }
