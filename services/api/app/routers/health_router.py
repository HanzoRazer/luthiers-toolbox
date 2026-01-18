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

router = APIRouter(tags=["System"])

# Determine repository root relative to this file
# In local dev: /repo/services/api/app/routers/health_router.py -> parents[4]
# In Railway container: /app/app/routers/health_router.py -> different structure
def _find_repo_root() -> Path:
    """Find repo root, handling different deployment environments."""
    current = Path(__file__).resolve()
    # Try to find repo root by looking for marker files
    for parent in current.parents:
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return parent
    # Fallback: in containerized deployment, /app is the working directory
    if Path("/app").exists():
        return Path("/app")
    # Last resort: go up 4 levels (local dev structure)
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

DIAGNOSTIC_DEPENDENCIES = (
    "fastapi",
    "uvicorn",
    "pydantic",
    "numpy",
    "pyclipper",
)

SCHEME_DEFAULT_PORT = {
    "redis": 6379,
    "rediss": 6380,
    "amqp": 5672,
    "amqps": 5671,
}


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
        return {
            "status": "error",
            "endpoint": target,
            "details": "Unable to determine host/port",
        }

    try:
        with closing(socket.create_connection((host, port), timeout=1.0)):
            return {
                "status": "ok",
                "endpoint": target,
                "details": "TCP handshake succeeded",
            }
    except OSError as exc:
        return {
            "status": "error",
            "endpoint": target,
            "details": str(exc),
        }


def _queue_status() -> Dict[str, Any]:
    queue_url = os.getenv("QUEUE_URL")
    if not queue_url:
        return {
            "status": "not_configured",
            "endpoint": None,
            "details": "QUEUE_URL not set",
        }
    return _probe_socket(queue_url)


def _cache_status() -> Dict[str, Any]:
    cache_url = os.getenv("CACHE_URL")
    if not cache_url:
        return {
            "status": "not_configured",
            "endpoint": None,
            "details": "CACHE_URL not set",
        }
    return _probe_socket(cache_url)


@router.get("/health", summary="System health check")
def health_check(include_diagnostics: bool = False) -> Dict[str, Any]:
    """Return repository/instance health metadata."""
    path_checks = _collect_path_state()
    status = _status_from(path_checks)
    payload: Dict[str, Any] = {
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "paths": path_checks,
        "message": "Service ready." if status == "ok" else "One or more critical paths missing.",
    }

    if include_diagnostics:
        payload["diagnostics"] = {
            "dependencies": _dependency_versions(),
            "queue": _queue_status(),
            "cache": _cache_status(),
        }

    return payload
