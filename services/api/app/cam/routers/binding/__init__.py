"""
CAM Binding/Purfling Router

Binding channel and purfling ledge toolpath generation.

Endpoints (under /api/cam/binding):
    POST /channel/gcode    - Generate binding channel G-code
    POST /purfling/gcode   - Generate purfling ledge G-code
    POST /preview          - Preview binding/purfling offsets
    GET  /info             - Get binding operation info
"""

from fastapi import APIRouter

from .binding_router import router as binding_router

# Aggregate binding routers
router = APIRouter()
router.include_router(binding_router)

__all__ = ["router"]
