"""Central /health endpoint for FastAPI application."""
from __future__ import annotations

import os
import socket
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse

from fastapi import APIRouter
from importlib import metadata
from importlib.metadata import PackageNotFoundError

from ..core.observability import get_health_summary
from ..core.features import get_feature_summary, get_feature_catalog
from ..health.startup import get_startup_summary
from ..router_registry.health import get_router_health

router = APIRouter(tags=["System"])


def _find_repo_root() -> Path:
    """Find repo root, handling different deployment environments."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return parent
    if Path("/app").exists():
        return Path("/app")
    try:
        return current.parents[4]
    except IndexError:
        return current.parent


REPO_ROOT = _find_repo_root()

CRITICAL_PATHS = {
    "services_api": REPO_ROOT / "services" / "api" if (REPO_ROOT / "services").exists() else REPO_ROOT,
    "packages_client": REPO_ROOT / "packages" / "client" if (REPO_ROOT / "packages").exists() else REPO_ROOT,
    "projects": REPO_ROOT / "projects" if (REPO_ROOT / "projects").exists() else REPO_ROOT,
    "scripts": REPO_ROOT / "scripts" if (REPO_ROOT / "scripts").exists() else REPO_ROOT,
    "docs": REPO_ROOT / "docs" if (REPO_ROOT / "docs").exists() else REPO_ROOT,
}

DIAGNOSTIC_DEPENDENCIES = ("fastapi", "uvicorn", "pydantic", "numpy", "pyclipper")

SCHEME_DEFAULT_PORT = {"redis": 6379, "rediss": 6380, "amqp": 5672, "amqps": 5671}


def _collect_path_state() -> Dict[str, bool]:
    return {name: path.exists() for name, path in CRITICAL_PATHS.items()}


def _status_from(checks: Dict[str, bool]) -> str:
    return "ok" if all(checks.values()) else "degraded"


def _dependency_versions() -> Dict[str, str]:
    versions: Dict[str, str] = {}
    for name in DIAGNOSTIC_DEPENDENCIES:
        try:
            versions[name] = metadata.version(name)
        except PackageNotFoundError:
            versions[name] = "missing"
    return versions


def _probe_socket(target: str) -> Dict[str, Any]:
    parsed = urlparse(target)
    host = parsed.hostname
    port = parsed.port or SCHEME_DEFAULT_PORT.get(parsed.scheme)
    if not host or not port:
        return {"status": "error", "endpoint": target, "details": "Unable to determine host/port"}
    try:
        with closing(socket.create_connection((host, port), timeout=1.0)):
            return {"status": "ok", "endpoint": target, "details": "TCP handshake succeeded"}
    except OSError as exc:
        return {"status": "error", "endpoint": target, "details": str(exc)}


def _queue_status() -> Dict[str, Any]:
    queue_url = os.getenv("QUEUE_URL")
    if not queue_url:
        return {"status": "not_configured", "endpoint": None, "details": "QUEUE_URL not set"}
    return _probe_socket(queue_url)


def _cache_status() -> Dict[str, Any]:
    cache_url = os.getenv("CACHE_URL")
    if not cache_url:
        return {"status": "not_configured", "endpoint": None, "details": "CACHE_URL not set"}
    return _probe_socket(cache_url)


@router.get("/health", summary="System health check")
def health_check(include_diagnostics: bool = False) -> Dict[str, Any]:
    """Return repository/instance health metadata with router status."""
    path_checks = _collect_path_state()
    router_health = get_router_health()
    has_router_errors = len(router_health.get("errors", {})) > 0
    status = "degraded" if (not all(path_checks.values()) or has_router_errors) else "ok"
    payload: Dict[str, Any] = {
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "paths": path_checks,
        "router_count": router_health.get("loaded", 0),
        "router_errors": router_health.get("errors", {}),
        "message": "Service ready." if status == "ok" else "One or more critical paths missing or routers failed.",
    }
    if include_diagnostics:
        payload["diagnostics"] = {
            "dependencies": _dependency_versions(),
            "queue": _queue_status(),
            "cache": _cache_status(),
        }
    return payload


@router.get("/health/detailed", summary="Detailed system health with feature tracking")
def detailed_health() -> Dict[str, Any]:
    """Return comprehensive health summary."""
    return get_health_summary()


@router.get("/features", summary="List loaded API features")
def list_features() -> Dict[str, Any]:
    """Return summary of all API features/routers."""
    return get_feature_summary()


@router.get("/features/catalog", summary="Feature catalog with use cases")
def feature_catalog() -> Dict[str, Any]:
    """Return user-friendly feature catalog with versions and use cases."""
    return get_feature_catalog()


@router.get("/health/modules", summary="Safety-critical module status")
def module_status() -> Dict[str, Any]:
    """Return status of safety-critical modules validated at startup."""
    return get_startup_summary()


@router.get("/health/routers", summary="Router loading status")
def router_health_status() -> Dict[str, Any]:
    """
    Return status of all routers loaded from the router registry.
    
    Response includes:
    - total: Total number of routers in manifest
    - loaded: Number of successfully loaded routers
    - failed: Number of failed routers
    - by_category: Breakdown by router category
    - errors: Dict of module -> error message for failures
    """
    return get_router_health()


# =============================================================================
# Kubernetes-style probes
# =============================================================================


@router.get("/health/live", summary="Liveness probe (K8s)")
def liveness_probe() -> Dict[str, Any]:
    """Kubernetes liveness probe."""
    return {"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/health/ready", summary="Readiness probe (K8s)")
def readiness_probe() -> Dict[str, Any]:
    """Kubernetes readiness probe."""
    checks = {"paths": all(_collect_path_state().values())}
    try:
        from ..core.reliability import CircuitBreaker
        breaker_status = CircuitBreaker.all_status()
        open_circuits = [name for name, status in breaker_status.items() if status.get("state") == "open"]
        checks["circuits"] = len(open_circuits) == 0
        if open_circuits:
            checks["open_circuits"] = open_circuits
    except ImportError:
        checks["circuits"] = True
    ready = all(v for k, v in checks.items() if k != "open_circuits")
    return {"status": "ready" if ready else "not_ready", "timestamp": datetime.now(timezone.utc).isoformat(), "checks": checks}


@router.get("/health/circuits", summary="Circuit breaker status")
def circuit_status() -> Dict[str, Any]:
    """Return status of all circuit breakers."""
    try:
        from ..core.reliability import CircuitBreaker
        return {"circuits": CircuitBreaker.all_status(), "timestamp": datetime.now(timezone.utc).isoformat()}
    except ImportError:
        return {"circuits": {}, "message": "Circuit breaker module not loaded", "timestamp": datetime.now(timezone.utc).isoformat()}
