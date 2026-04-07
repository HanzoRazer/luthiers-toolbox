"""The Production Shop API - Main Application

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
# -----------------------------------------------------------------------------
# AI CONTEXT ADAPTER (v1)
#
# Hard Boundaries:
# - AI modules provide status/availability checking ONLY in main.py
# - No AI code paths execute business logic or modify state here
# - AI-driven features are isolated in .ai/ and ._experimental.ai_* modules
# - RMOS authority controls what AI suggestions can affect manufacturing
# -----------------------------------------------------------------------------
from .ai.availability import get_ai_status

# Endpoint governance (H4 - canonical endpoint registry + safety rails)
from .governance.endpoint_middleware import EndpointGovernanceMiddleware
# NOTE: governance_router now loaded via system_manifest.py (not directly here)

# Route analytics middleware (for router consolidation analysis)
from .middleware.route_analytics_middleware import RouteAnalyticsMiddleware, analytics_router

# API Rate Limiting
from .middleware.rate_limit import limiter, rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

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
    title="The Production Shop API",
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
# Allow all origins for public API access (claude.ai, external tools, etc.)
# NOTE: allow_credentials=False is required when using wildcard origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Deprecation headers middleware - emits warnings for legacy lanes
app.add_middleware(DeprecationHeadersMiddleware)

# Endpoint governance middleware (H4) - logs warnings for legacy/shadow endpoints
app.add_middleware(EndpointGovernanceMiddleware)

# Route analytics middleware - captures usage metrics for router consolidation
# Access via /api/_analytics/summary, /api/_analytics/export
# DISABLED by default in production. Set ENABLE_ROUTE_ANALYTICS=1 to enable.
_ANALYTICS_ENABLED = os.getenv("ENABLE_ROUTE_ANALYTICS", "").lower() in ("1", "true", "yes")
if _ANALYTICS_ENABLED:
    app.add_middleware(RouteAnalyticsMiddleware)
    _log.info("Route analytics middleware ENABLED (ENABLE_ROUTE_ANALYTICS=1)")

# API Rate Limiting - protects against abuse and ensures fair usage
# Disable with RATE_LIMIT_ENABLED=0 in development
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
_log.info("API rate limiting initialized")


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

# NOTE: governance_router removed from here - now loaded via system_manifest.py
# (was causing duplicate /api/_meta/* routes)

# Route analytics endpoints - for router consolidation analysis (only if enabled)
# Access: /api/_analytics/summary, /api/_analytics/export, /api/_analytics/reset
if _ANALYTICS_ENABLED:
    app.include_router(analytics_router, prefix="/api/_analytics", tags=["internal"])

# Curated API v1 - stable, documented endpoints for golden path workflows
from .api_v1 import router as api_v1_router
app.include_router(api_v1_router)

# WebSocket endpoints - real-time event streaming
# Access: /ws/monitor, /ws/live, /ws/status
from .websocket.router import router as websocket_router
app.include_router(websocket_router, tags=["WebSocket"])


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
