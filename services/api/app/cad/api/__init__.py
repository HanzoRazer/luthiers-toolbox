# services/api/app/cad/api/__init__.py
"""
CAD API Routes package.

Exports the DXF router for registration in main.py.
"""

from .dxf_routes import router as dxf_router

__all__ = ["dxf_router"]
