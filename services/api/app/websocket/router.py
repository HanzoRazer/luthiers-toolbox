# services/api/app/websocket/router.py
"""
WebSocket Router - Live Event Streaming Endpoints

Provides WebSocket endpoints for real-time event monitoring:
- /ws/monitor - Live job, pattern, material, and system events
- /ws/live - Simplified live event stream (alias)

Event Protocol:
1. Client connects to WebSocket endpoint
2. Client optionally sends filter message: {"filters": ["job", "cam", "ai"]}
3. Server broadcasts events matching filters (or all if no filters)
4. Events are JSON: {"type": "event_type", "data": {...}, "timestamp": "ISO8601"}

Supported Event Types:
- job:created, job:updated, job:completed, job:failed
- cam:gcode_exported, cam:toolpath_generated
- ai:vision_request, ai:vision_complete
- pattern:created, pattern:updated
- material:created, material:updated
- metrics:snapshot
- system:health, system:error

Usage:
    # JavaScript client
    const ws = new WebSocket('ws://localhost:8000/ws/monitor');
    ws.onopen = () => ws.send(JSON.stringify({filters: ['job', 'cam']}));
    ws.onmessage = (e) => console.log(JSON.parse(e.data));
"""

from __future__ import annotations

import json
import logging
from typing import List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .monitor import get_connection_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/monitor")
async def websocket_monitor(websocket: WebSocket):
    """
    Real-time event monitoring WebSocket endpoint.

    Connect to receive live events from the Production Shop API.
    Send a JSON message with {"filters": [...]} to filter events.

    Example filters:
    - "job" - Job lifecycle events
    - "cam" - CAM/CNC events (gcode export, toolpath generation)
    - "ai" - AI/vision events
    - "pattern" - Pattern updates
    - "material" - Material updates
    - "metrics" - Periodic metrics snapshots
    - "all" - All events (default)
    """
    manager = get_connection_manager()
    await manager.connect(websocket)

    # Default to all events
    manager.set_filters(websocket, ["all"])

    try:
        while True:
            # Wait for client messages (filter updates, pings)
            data = await websocket.receive_text()

            try:
                message = json.loads(data)

                # Handle filter subscription
                if "filters" in message:
                    filters = message["filters"]
                    if isinstance(filters, list):
                        manager.set_filters(websocket, filters)
                        await websocket.send_json({
                            "type": "subscription:updated",
                            "filters": filters,
                        })
                        logger.info(f"WebSocket filters updated: {filters}")

                # Handle ping/pong for keepalive
                elif message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

            except json.JSONDecodeError:
                # Non-JSON messages are ignored (could be heartbeats)
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected normally")
    except Exception as e:
        manager.disconnect(websocket)
        logger.error(f"WebSocket error: {e}")


@router.websocket("/ws/live")
async def websocket_live(websocket: WebSocket):
    """
    Simplified live event stream (alias for /ws/monitor).

    Receives all events without filtering.
    """
    manager = get_connection_manager()
    await manager.connect(websocket)
    manager.set_filters(websocket, ["all"])

    try:
        while True:
            # Just keep connection alive, no client messages expected
            data = await websocket.receive_text()

            # Handle ping for keepalive
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)
        logger.error(f"WebSocket live error: {e}")


@router.get("/ws/status", tags=["WebSocket"])
async def websocket_status():
    """
    Get WebSocket connection status.

    Returns current connection count and available event types.
    """
    manager = get_connection_manager()

    return {
        "active_connections": len(manager.active_connections),
        "available_filters": [
            "all",
            "job",
            "cam",
            "ai",
            "pattern",
            "material",
            "metrics",
            "system",
        ],
        "event_types": [
            "job:created",
            "job:updated",
            "job:completed",
            "job:failed",
            "cam:gcode_exported",
            "cam:toolpath_generated",
            "ai:vision_request",
            "ai:vision_complete",
            "pattern:created",
            "pattern:updated",
            "material:created",
            "material:updated",
            "metrics:snapshot",
            "system:health",
            "system:error",
        ],
        "endpoints": {
            "monitor": "/ws/monitor",
            "live": "/ws/live",
        },
    }
