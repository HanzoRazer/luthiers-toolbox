from __future__ import annotations

from fastapi import APIRouter

from .router_import import router as import_router
from .router_query import router as query_router
from .router_zip_export import router as zip_export_router

# NOTE (Issue A fix, 2025-12-31):
# router_attachments.py and router_run_attachments.py are EXCLUDED here.
# Their functionality is superseded by runs_v2/acoustics_router.py (Wave 22)
# which provides H7.2.2.1 features: signed URLs, attachment meta index,
# no-path disclosure, and advisory endpoints.

router = APIRouter()
router.include_router(import_router)
router.include_router(query_router)
router.include_router(zip_export_router)
