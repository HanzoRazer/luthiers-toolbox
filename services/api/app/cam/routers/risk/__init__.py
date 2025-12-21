"""
CAM Risk Routers

Risk reports and aggregation.

Migrated from:
    - routers/cam_risk_router.py          → reports_router (proxy)
    - routers/cam_risk_aggregate_router.py → aggregate_router (proxy)

Note: Proxies to existing routers until full migration.
"""

from fastapi import APIRouter

# Proxy imports from existing routers (transitional)
try:
    from ....routers.cam_risk_router import router as reports_router
except ImportError:
    reports_router = None

try:
    from ....routers.cam_risk_aggregate_router import router as aggregate_router
except ImportError:
    aggregate_router = None

# Aggregate all risk routers
router = APIRouter()

if reports_router:
    router.include_router(reports_router)
if aggregate_router:
    router.include_router(aggregate_router)

__all__ = ["router"]
