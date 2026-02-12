"""Luthier's ToolBox API - Main Application

Simplified entry point using router_registry for centralized router loading.
Phase 9 god-object decomposition reduced this from 915+ lines to <200 lines.
"""

# Load environment variables from .env file FIRST (before any imports that need them)
from dotenv import load_dotenv

load_dotenv()

import logging
import os
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .util.request_context import set_request_id
from .util.logging_request_id import RequestIdFilter

# Deprecation guardrails
from .middleware.deprecation import DeprecationHeadersMiddleware

# AI availability (for health endpoint)
from .ai.availability import get_ai_status

# Endpoint governance (H4 - canonical endpoint registry + safety rails)
from .governance.endpoint_middleware import EndpointGovernanceMiddleware
from .governance.metrics_router import router as metrics_router

# Centralized router loading (Phase 9)
from .router_registry import load_all_routers, get_router_health


# =============================================================================
# LOGGING
# =============================================================================

_log = logging.getLogger(__name__)

LOG_FORMAT = "%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s"

_log_handler = logging.StreamHandler()
_log_handler.setFormatter(logging.Formatter(LOG_FORMAT))
_log_handler.addFilter(RequestIdFilter())

_root_logger = logging.getLogger()
# Avoid duplicating handlers on reload
if not any(isinstance(h, logging.StreamHandler) for h in _root_logger.handlers):
    _root_logger.addHandler(_log_handler)
_root_logger.setLevel(logging.INFO)


# =============================================================================
# REQUEST ID MIDDLEWARE
# =============================================================================


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Global request correlation middleware."""

    async def dispatch(self, request: Request, call_next):
        # Prefer client-supplied ID, otherwise generate one
        req_id = request.headers.get("x-request-id")
        if not req_id:
            req_id = f"req_{uuid.uuid4().hex[:12]}"

        # Attach to request context
        request.state.request_id = req_id

        # Set ContextVar for deep logging
        set_request_id(req_id)

        # Continue request
        response: Response = await call_next(request)

        # Echo back for client-side correlation
        response.headers["x-request-id"] = req_id

        # Clear ContextVar after request
        set_request_id(None)

        return response


# =============================================================================
# APPLICATION SETUP
# =============================================================================

app = FastAPI(
    title="Luthier's ToolBox API",
    description="CAM system for guitar builders - DXF templates, G-code generation, manufacturing orchestration",
    version="2.0.0-clean",
    docs_url="/docs",
    redoc_url="/redoc",
)


def create_app() -> FastAPI:
    """Factory function for creating the FastAPI application."""
    return app


# Request ID middleware - MUST be registered FIRST (before CORS)
# Provides request correlation for logging, auditing, and debugging
app.add_middleware(RequestIdMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Deprecation headers middleware - emits warnings for legacy lanes
app.add_middleware(DeprecationHeadersMiddleware)

# Endpoint governance middleware (H4) - logs warnings for legacy/shadow endpoints
app.add_middleware(EndpointGovernanceMiddleware)


# =============================================================================
# STARTUP EVENTS
# =============================================================================

from .db.startup import run_migrations_on_startup
from .core.observability import set_version, register_loaded_feature
from .health.startup import validate_startup


@app.on_event("startup")
def _startup_safety_validation() -> None:
    """Validate safety-critical modules are loaded. FAIL FAST if not."""
    strict_mode = os.getenv("RMOS_STRICT_STARTUP", "1") != "0"
    validate_startup(strict=strict_mode)


@app.on_event("startup")
def _startup_db_migrations() -> None:
    """Run database migrations on startup (if enabled)."""
    run_migrations_on_startup()


@app.on_event("startup")
def _startup_observability() -> None:
    """Initialize observability with version info."""
    set_version("2.0.0-clean")
    register_loaded_feature("core_cam")
    register_loaded_feature("rmos")
    register_loaded_feature("health")


# =============================================================================
# ROUTER REGISTRATION (via router_registry)
# =============================================================================

# Load all routers from the centralized manifest
for router, prefix, tags in load_all_routers():
    if prefix:
        app.include_router(router, prefix=prefix, tags=tags)
    else:
        app.include_router(router, tags=tags)

# Prometheus metrics endpoint - no prefix, accessible at /metrics
app.include_router(metrics_router)

# Curated API v1 - stable, documented endpoints for golden path workflows
from .api_v1 import router as api_v1_router
app.include_router(api_v1_router)


# =============================================================================
# HEALTH ENDPOINTS (fallback for basic CI compatibility)
# =============================================================================


@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint (CI compatibility)."""
    from datetime import datetime, timezone

    return {
        "status": "ok",
        "version": "2.0.0-clean",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "paths": {},  # Empty paths dict for CI compatibility
    }


@app.get("/api/health", tags=["Health"])
async def api_health_check():
    """API health check with router summary and AI status."""
    ai_status = get_ai_status()
    router_health = get_router_health()

    return {
        "status": "healthy" if ai_status["status"] == "available" else "degraded",
        "version": "2.0.0-clean",
        "ai": ai_status,
        "routers": {
            "total": router_health["total"],
            "loaded": router_health["loaded"],
            "failed": router_health["failed"],
            "by_category": router_health["by_category"],
        },
    }
