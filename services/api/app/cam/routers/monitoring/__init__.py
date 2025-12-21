"""
CAM Monitoring Routers

CAM metrics and logging.

Migrated from:
    - routers/cam_metrics_router.py → metrics_router.py
    - routers/cam_logs_router.py   → logs_router.py

Endpoints (under /api/cam/monitoring):
    POST /metrics/energy              - Calculate cutting energy
    POST /metrics/energy_csv          - Export energy as CSV
    POST /metrics/heat_timeseries     - Calculate heat over time
    POST /metrics/bottleneck_csv      - Export bottlenecks as CSV
    POST /metrics/thermal_report_md   - Generate thermal report
    POST /metrics/thermal_report_bundle - Export report bundle
    POST /logs/write                  - Log a CAM run
    GET  /logs/caps/{machine_id}      - Get bottleneck distribution
"""

from fastapi import APIRouter

from .metrics_router import router as metrics_router
from .logs_router import router as logs_router

# Aggregate all monitoring routers
router = APIRouter()
router.include_router(metrics_router, prefix="/metrics")
router.include_router(logs_router, prefix="/logs")

__all__ = ["router", "metrics_router", "logs_router"]
