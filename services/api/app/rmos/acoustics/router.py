from __future__ import annotations

from fastapi import APIRouter

from .router_import import router as import_router

router = APIRouter()
router.include_router(import_router)
