"""
Compare Routers Module

Consolidated compare endpoints organized by category.

Categories:
    - baselines: Baseline CRUD and geometry diff
    - risk: Risk aggregation, bucket detail, export
    - lab: Compare Lab UI endpoints
    - automation: SVG compare automation

Usage:
    from app.compare.routers import compare_router
    app.include_router(compare_router, prefix="/api/compare", tags=["Compare"])
"""

from .aggregator import compare_router

__all__ = ["compare_router"]
