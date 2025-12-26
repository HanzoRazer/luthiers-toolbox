from __future__ import annotations

from fastapi import APIRouter

from .router_import import router as import_router
from .router_query import router as query_router
from .router_attachments import router as attachments_router
from .router_run_attachments import router as run_attachments_router

router = APIRouter()
router.include_router(import_router)
router.include_router(query_router)
router.include_router(attachments_router)
router.include_router(run_attachments_router)
