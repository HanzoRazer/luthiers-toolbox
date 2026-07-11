"""Deprecated compatibility facade for probe routers.

The probe package no longer routes through this aggregate module. Import the package
router from ``app.routers.probe`` or the focused sub-routers directly instead.
This module remains import-compatible for downstream callers during the retirement
window; it must not be reintroduced into package wiring.
"""
from __future__ import annotations

import warnings

from fastapi import APIRouter

from .boss_router import router as boss_router
from .corner_router import router as corner_router
from .pocket_router import router as pocket_router
from .setup_router import router as setup_router
from .surface_z_router import router as surface_z_router
from .vise_square_router import router as vise_square_router

warnings.warn(
    "app.routers.probe.probe_consolidated_router is deprecated; import "
    "app.routers.probe.router or a focused probe sub-router instead.",
    DeprecationWarning,
    stacklevel=2,
)

router = APIRouter(tags=["probe"])

router.include_router(boss_router)
router.include_router(corner_router)
router.include_router(pocket_router)
router.include_router(surface_z_router)
router.include_router(vise_square_router)
router.include_router(setup_router)

__all__ = [
    "router",
    "boss_router",
    "corner_router",
    "pocket_router",
    "surface_z_router",
    "vise_square_router",
    "setup_router",
]
