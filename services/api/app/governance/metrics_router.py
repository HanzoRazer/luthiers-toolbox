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
      ENDPOINT_METRICS_MAX_SERIES=2000            # cap series
      ENDPOINT_METRICS_OTHER_LABEL=__other__      # overflow bucket
      ENDPOINT_OTEL_ENABLED=true|false            # optional OTEL emission elsewhere
    """
    if not _enabled():
        return PlainTextResponse("# metrics disabled\n", status_code=404)
    return PlainTextResponse(snapshot_prometheus_text(), media_type="text/plain; version=0.0.4")
