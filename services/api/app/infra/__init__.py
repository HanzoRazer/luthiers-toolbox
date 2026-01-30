"""Infrastructure module - production facade.

Re-exports from experimental infra for cross-cutting concerns:
monitoring, logging, and runtime observability.
"""
from app._experimental.infra.live_monitor import publish_event

__all__ = [
    "publish_event",
]
