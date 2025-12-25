from __future__ import annotations

import os
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from .endpoint_stats import snapshot_prometheus_text

router = APIRouter(tags=["Governance", "Metrics"])


def _enabled() -> bool:
    v = (os.getenv("ENDPOINT_METRICS_ENABLED") or "true").strip().lower()
    return v not in {"0", "false", "no", "off"}


@router.get("/metrics", response_class=PlainTextResponse)
def metrics():
    """
    Prometheus exposition endpoint.

    Env:
      ENDPOINT_METRICS_ENABLED=true|false
    """
    if not _enabled():
        return PlainTextResponse("# metrics disabled\n", status_code=404)
    return PlainTextResponse(snapshot_prometheus_text(), media_type="text/plain; version=0.0.4")
