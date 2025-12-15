"""
Real-time Monitoring WebSocket Router (N10.0)

Provides /ws/monitor endpoint for real-time updates.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Optional
import logging
import json

from ..websocket.monitor import get_connection_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/monitor")
async def websocket_monitor(websocket: WebSocket):
    """
    WebSocket endpoint for real-time monitoring.
    
    Client sends filter commands:
    {"action": "subscribe", "filters": ["job", "pattern", "metrics"]}
    
    Server broadcasts events:
    {
        "type": "job:created|job:updated|job:completed|job:failed|pattern:created|material:created|metrics:snapshot",
        "data": {...},
        "timestamp": "2025-01-01T12:00:00.000Z"
    }
    """
    manager = get_connection_manager()
    await manager.connect(websocket)
    
    try:
        # Send welcome message
        await manager.send_to(websocket, {
            "type": "system:connected",
            "data": {"message": "Real-time monitoring active"},
            "timestamp": ""
        })
        
        while True:
            # Wait for client messages (commands)
            data = await websocket.receive_text()
            
            try:
                command = json.loads(data)
                
                if command.get("action") == "subscribe":
                    filters = command.get("filters", ["all"])
                    manager.set_filters(websocket, filters)
                    await manager.send_to(websocket, {
                        "type": "system:subscribed",
                        "data": {"filters": filters},
                        "timestamp": ""
                    })
                    logger.info(f"Client subscribed to filters: {filters}")
                    
                elif command.get("action") == "ping":
                    await manager.send_to(websocket, {
                        "type": "system:pong",
                        "data": {},
                        "timestamp": ""
                    })
                    
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from client: {data}")
                await manager.send_to(websocket, {
                    "type": "system:error",
                    "data": {"message": "Invalid JSON command"},
                    "timestamp": ""
                })
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected")
