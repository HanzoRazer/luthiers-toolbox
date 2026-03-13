"""
CAM Monitoring Routers (Consolidated)

CAM metrics and logging.

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

from .monitoring_consolidated_router import (
    router,
    metrics_router,
    logs_router,
    ThermalBudget,
    ThermalReportIn,
)

__all__ = ["router", "metrics_router", "logs_router", "ThermalBudget", "ThermalReportIn"]
