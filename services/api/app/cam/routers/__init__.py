"""
CAM Routers - Consolidated API Layer

This package organizes all CAM-related FastAPI routers into a clean
hierarchical structure with standardized prefixes.

Architecture:
    main.py imports cam_router (single aggregator)
    cam_router includes all category routers with /api/cam/<category> prefix

Categories:
    - drilling/     Modal drilling (G81, G83) and patterns
    - fret_slots/   Fret slot CAM preview and export
    - relief/       Relief carving (heightmap, roughing, finishing)
    - risk/         CAM risk reports and aggregation
    - rosette/      Rosette toolpath and G-code generation
    - simulation/   G-code parsing and simulation
    - toolpath/     Generic toolpath operations (roughing, biarc, helical, vcarve)
    - export/       SVG, post-processor, DXF export
    - monitoring/   CAM metrics and logs
    - pipeline/     Pipeline execution and presets
    - utility/      Settings, backup, compare, optimization

Usage:
    from app.cam.routers import cam_router
    app.include_router(cam_router, prefix="/api/cam", tags=["CAM"])
"""

from .aggregator import cam_router

__all__ = ["cam_router"]
