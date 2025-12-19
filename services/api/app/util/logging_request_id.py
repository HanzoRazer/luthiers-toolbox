"""
Logging Request ID Filter.

Injects `record.request_id` into all log records so formatters can
safely reference %(request_id)s. Works even when logs are emitted
outside route handlers (background tasks, deep helpers, etc.).
"""

from __future__ import annotations

import logging

from .request_context import get_request_id


class RequestIdFilter(logging.Filter):
    """
    Logging filter that injects request_id into log records.

    Usage:
        handler.addFilter(RequestIdFilter())

    Then in your formatter:
        LOG_FORMAT = "%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s"
    """

    def filter(self, record: logging.LogRecord) -> bool:
        # Prefer explicit extra={"request_id": ...}, fallback to ContextVar
        rid = getattr(record, "request_id", None) or get_request_id() or "-"
        record.request_id = rid
        return True
