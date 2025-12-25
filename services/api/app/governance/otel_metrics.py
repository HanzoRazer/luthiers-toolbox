from __future__ import annotations

import os
from typing import Optional


def _enabled() -> bool:
    v = (os.getenv("ENDPOINT_OTEL_ENABLED") or "false").strip().lower()
    return v in {"1", "true", "yes", "on"}


# Lazy, optional OTEL integration. No hard dependency.
_meter = None
_counter = None


def _init_otel():
    global _meter, _counter
    if _counter is not None:
        return

    if not _enabled():
        _counter = False  # sentinel: disabled
        return

    try:
        # OpenTelemetry metrics API (only works if opentelemetry SDK is installed & configured)
        from opentelemetry import metrics  # type: ignore
        _meter = metrics.get_meter("luthiers_toolbox.governance")
        _counter = _meter.create_counter(
            name="ltb_endpoint_hits_total",
            description="Endpoint hits by status/method/path_pattern (OTEL)",
        )
    except Exception:
        # Not installed or not configured
        _counter = False  # sentinel: unavailable


def otel_increment_endpoint_hit(*, status: str, method: str, path_pattern: str) -> None:
    """
    Emit OTEL metric if available.
    No-op unless ENDPOINT_OTEL_ENABLED=true and OTEL SDK is installed/configured.
    """
    _init_otel()
    if _counter is False or _counter is None:
        return

    # Basic attribute set; keep cardinality bounded (same guardrails should exist upstream)
    attrs = {
        "status": status,
        "method": method,
        "path_pattern": path_pattern,
    }
    try:
        _counter.add(1, attributes=attrs)
    except Exception:
        # Never raise to caller
        return
