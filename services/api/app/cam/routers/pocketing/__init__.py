"""
CAM Pocketing Routers Package
=============================

Pocketing operations using L.1 adaptive core.

Sub-modules:
- intent_router.py (1 route: /intent-gcode) [CamIntentV1 - 8J]

Total: 1 route under /api/cam/pocketing
"""
from .intent_router import router as intent_router

# Aggregate router (just the intent router for now)
router = intent_router

__all__ = [
    "router",
    "intent_router",
]
