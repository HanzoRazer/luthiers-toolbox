from __future__ import annotations

from fastapi import APIRouter

from app.cnc_production.feeds_speeds.api.routes import feeds_speeds as feeds_speeds_router

router = APIRouter(prefix="/cnc-production", tags=["cnc-production"])

# Feeds & Speeds service is always available once this module imports.
router.include_router(feeds_speeds_router.router)

# Optional Saw Lab routers load lazily so missing schemas do not break import.
try:  # pragma: no cover - optional dependency
    from app.api.routes import saw_tools
except Exception:  # noqa: BLE001
    saw_tools = None

if saw_tools is not None:
    router.include_router(saw_tools.router)

try:  # pragma: no cover - optional dependency
    from app.api.routes import saw_ops
except Exception:  # noqa: BLE001
    saw_ops = None

if saw_ops is not None:
    router.include_router(saw_ops.router)
