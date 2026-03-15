# services/api/app/infra/live_monitor.py
"""
LiveMonitor Event Publisher

Centralized hook for emitting runtime events to:
1. Logging (always)
2. WebSocket clients (if connected)
3. Future: message queues, external services

Event Types:
- job:created, job:updated, job:completed, job:failed
- cam:gcode_exported, cam:toolpath_generated
- ai:vision_request, ai:vision_complete
- pattern:created, pattern:updated
- material:created, material:updated
- metrics:snapshot
- system:health, system:error

Usage:
    from app.infra.live_monitor import publish_event, publish_cam_event

    # Generic event
    publish_event("job:completed", {"job_id": "JOB-123", "status": "success"})

    # Typed helper
    publish_cam_event("gcode_exported", {"job_id": "JOB-123", "file": "output.nc"})
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..websocket.monitor import ConnectionManager

logger = logging.getLogger(__name__)

# Cached reference to avoid circular imports
_connection_manager: Optional["ConnectionManager"] = None


def _get_connection_manager() -> Optional["ConnectionManager"]:
    """
    Lazily get the WebSocket connection manager.

    Returns None if WebSocket module not available (e.g., during tests).
    """
    global _connection_manager
    if _connection_manager is None:
        try:
            from ..websocket.monitor import get_connection_manager
            _connection_manager = get_connection_manager()
        except ImportError:
            logger.debug("WebSocket monitor not available")
            return None
    return _connection_manager


def _get_event_loop() -> Optional[asyncio.AbstractEventLoop]:
    """Get the current event loop if one is running."""
    try:
        loop = asyncio.get_running_loop()
        return loop
    except RuntimeError:
        # No running loop
        return None


async def _broadcast_event(event_type: str, payload: Dict[str, Any]) -> None:
    """
    Internal async broadcast to WebSocket clients.

    Extracts category from event_type (e.g., "job" from "job:completed")
    and broadcasts to clients subscribed to that category or "all".
    """
    manager = _get_connection_manager()
    if manager is None:
        return

    # Extract category from event type (e.g., "job" from "job:completed")
    category = event_type.split(":")[0] if ":" in event_type else event_type
    filters = [category, "all"]

    try:
        await manager.broadcast(event_type, payload, filters=filters)
    except Exception as e:
        logger.warning(f"Failed to broadcast event {event_type}: {e}")


def publish_event(event_type: str, payload: Dict[str, Any]) -> None:
    """
    Publish a LiveMonitor event.

    1. Always logs the event at INFO level
    2. Broadcasts to WebSocket clients if event loop is running

    Args:
        event_type: Type of event (e.g., 'job:completed', 'cam:gcode_exported')
        payload: Event data dictionary

    Example:
        publish_event(
            "cam:gcode_exported",
            {
                "job_id": "JOB-ROSETTE-20251201-123456-abc123",
                "ring_id": 1,
                "material": "hardwood",
                "runtime_sec": 45.3
            }
        )
    """
    # Always log
    logger.info("LiveMonitor event: %s - %s", event_type, payload)

    # Broadcast to WebSocket clients if we have an event loop
    loop = _get_event_loop()
    if loop is not None and loop.is_running():
        # Schedule broadcast as a task (non-blocking)
        asyncio.create_task(_broadcast_event(event_type, payload))


# =============================================================================
# TYPED EVENT HELPERS
# =============================================================================

def publish_job_event(action: str, data: Dict[str, Any]) -> None:
    """
    Publish a job lifecycle event.

    Actions: created, updated, completed, failed
    """
    publish_event(f"job:{action}", data)


def publish_cam_event(action: str, data: Dict[str, Any]) -> None:
    """
    Publish a CAM/CNC event.

    Actions: gcode_exported, toolpath_generated, simulation_complete
    """
    publish_event(f"cam:{action}", data)


def publish_ai_event(action: str, data: Dict[str, Any]) -> None:
    """
    Publish an AI/vision event.

    Actions: vision_request, vision_complete, explain_generated
    """
    publish_event(f"ai:{action}", data)


def publish_pattern_event(action: str, data: Dict[str, Any]) -> None:
    """
    Publish a pattern event.

    Actions: created, updated, deleted
    """
    publish_event(f"pattern:{action}", data)


def publish_material_event(action: str, data: Dict[str, Any]) -> None:
    """
    Publish a material event.

    Actions: created, updated, deleted
    """
    publish_event(f"material:{action}", data)


def publish_system_event(action: str, data: Dict[str, Any]) -> None:
    """
    Publish a system event.

    Actions: health, error, warning
    """
    publish_event(f"system:{action}", data)


def publish_metrics_snapshot(data: Dict[str, Any]) -> None:
    """
    Publish a metrics snapshot event.

    Used for periodic metrics broadcasting.
    """
    publish_event("metrics:snapshot", data)
