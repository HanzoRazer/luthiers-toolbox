# Patch N10/N14 - LiveMonitor event publisher scaffold
#
# This is a minimal, centralized hook for emitting runtime events
# (e.g., rosette CNC exports) to whatever monitoring mechanism you
# want: logs, WebSockets, message queues, etc.
#
# N10/N14: default behavior is to just log to stdout / logging.

from __future__ import annotations

from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


def publish_event(event_type: str, payload: Dict[str, Any]) -> None:
    """
    Publish a LiveMonitor event.

    Current implementation:
      - logs the event_type + payload at INFO level.

    Future implementation:
      - send to WebSocket channel, message bus, etc.

    Args:
        event_type: Type of event (e.g., 'rosette_cnc_export', 'safety_override')
        payload: Event data dictionary

    Example:
        publish_event(
            "rosette_cnc_export",
            {
                "job_id": "JOB-ROSETTE-20251201-123456-abc123",
                "ring_id": 1,
                "material": "hardwood",
                "safety_decision": "allow",
                "runtime_sec": 45.3
            }
        )
    """
    logger.info("LiveMonitor event: %s - %s", event_type, payload)
