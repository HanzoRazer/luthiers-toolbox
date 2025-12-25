from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Tuple


class EndpointStatus(str, Enum):
    CANONICAL = "canonical"
    LEGACY = "legacy"
    SHADOW = "shadow"   # duplicate surface retained for backward compatibility
    INTERNAL = "internal"


@dataclass(frozen=True)
class EndpointInfo:
    status: EndpointStatus
    replacement: Optional[str] = None
    notes: Optional[str] = None


# Keyed by (METHOD, PATH) where PATH is the FastAPI route path pattern.
# Example patterns:
# - "/api/rmos/runs"
# - "/api/rmos/runs/{run_id}"
RegistryKey = Tuple[str, str]


ENDPOINT_REGISTRY: Dict[RegistryKey, EndpointInfo] = {
    # ---------------------------------------------------------------------
    # RMOS Runs (canonical)
    # ---------------------------------------------------------------------
    ("GET", "/api/rmos/runs"): EndpointInfo(status=EndpointStatus.CANONICAL),
    ("POST", "/api/rmos/runs"): EndpointInfo(status=EndpointStatus.CANONICAL),
    ("GET", "/api/rmos/runs/{run_id}"): EndpointInfo(status=EndpointStatus.CANONICAL),
    ("GET", "/api/rmos/runs/diff"): EndpointInfo(status=EndpointStatus.CANONICAL),
    ("PATCH", "/api/rmos/runs/{run_id}/meta"): EndpointInfo(status=EndpointStatus.CANONICAL),
    ("GET", "/api/rmos/runs/{run_id}/attachments"): EndpointInfo(status=EndpointStatus.CANONICAL),
    ("GET", "/api/rmos/runs/{run_id}/attachments/{sha256}"): EndpointInfo(status=EndpointStatus.CANONICAL),
    ("GET", "/api/rmos/runs/{run_id}/attachments/verify"): EndpointInfo(status=EndpointStatus.CANONICAL),

    # ---------------------------------------------------------------------
    # RMOS Workflow Sessions (canonical)
    # (If your actual mounted paths differ, update these to match FastAPI.)
    # ---------------------------------------------------------------------
    ("GET", "/api/rmos/workflow-sessions"): EndpointInfo(status=EndpointStatus.CANONICAL),
    ("POST", "/api/rmos/workflow-sessions"): EndpointInfo(status=EndpointStatus.CANONICAL),
    ("GET", "/api/rmos/workflow-sessions/{workflow_session_id}"): EndpointInfo(status=EndpointStatus.CANONICAL),
    ("PATCH", "/api/rmos/workflow-sessions/{workflow_session_id}"): EndpointInfo(status=EndpointStatus.CANONICAL),
    ("DELETE", "/api/rmos/workflow-sessions/{workflow_session_id}"): EndpointInfo(status=EndpointStatus.CANONICAL),
    ("GET", "/api/rmos/workflow-sessions/{workflow_session_id}/runs"): EndpointInfo(status=EndpointStatus.CANONICAL),

    # ---------------------------------------------------------------------
    # Examples of legacy/shadow surfaces (keep placeholders minimal).
    # Update based on ENDPOINT_TRUTH_MAP.md if you want strong coverage.
    # ---------------------------------------------------------------------
    ("POST", "/feasibility"): EndpointInfo(
        status=EndpointStatus.LEGACY,
        replacement="/api/rmos/feasibility (canonical route, if/when added)",
        notes="Root-mounted legacy path retained for backwards compatibility."
    ),
    ("POST", "/toolpaths"): EndpointInfo(
        status=EndpointStatus.LEGACY,
        replacement="/api/rmos/toolpaths (canonical route, if/when added)",
        notes="Root-mounted legacy path retained for backwards compatibility."
    ),
}


def lookup_endpoint(method: str, path_pattern: str) -> Optional[EndpointInfo]:
    """Lookup endpoint status by FastAPI route path pattern."""
    key = (method.upper(), path_pattern)
    return ENDPOINT_REGISTRY.get(key)
