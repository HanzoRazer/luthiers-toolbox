"""
CAM Drilling Routers

Modal drilling (G81, G83) and pattern drilling operations.

Migrated from:
    - routers/cam_drill_router.py
    - routers/cam_drill_pattern_router.py
"""

from fastapi import APIRouter

router = APIRouter()

# Router will be populated during Phase 3.4 migration
# For now, exports empty router to allow aggregator to function

__all__ = ["router"]
