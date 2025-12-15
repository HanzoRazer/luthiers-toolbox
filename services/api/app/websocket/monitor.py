"""
Real-time Monitoring WebSocket Manager (N10.0 + MM-6)

Provides WebSocket endpoint for live job/pattern/material updates with fragility awareness.
Clients connect to /ws/monitor and receive real-time events with material and fragility context.

Event Types:
- job:created, job:updated, job:completed, job:failed (now includes fragility context)
- pattern:created, pattern:updated
- material:created, material:updated
- metrics:snapshot (periodic stats push)

MM-6 Integration:
- Job events now include materials[], worst_fragility_score, fragility_band, lane_hint
- Enables real-time visibility into material risk as jobs run
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set, Any
import json
import asyncio
import logging
from datetime import datetime

from app.core.live_monitor_fragility import build_fragility_context_for_job

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.subscription_filters: Dict[WebSocket, List[str]] = {}
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        self.subscription_filters.pop(websocket, None)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
        
    async def send_to(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to specific client."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send to client: {e}")
            self.disconnect(websocket)
            
    async def broadcast(self, event_type: str, data: Dict[str, Any], filters: List[str] = None):
        """Broadcast event to all connected clients (optionally filtered)."""
        message = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        disconnected = []
        for connection in self.active_connections:
            # Check subscription filters if provided
            if filters:
                client_filters = self.subscription_filters.get(connection, [])
                if not any(f in filters for f in client_filters):
                    continue
                    
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Broadcast failed: {e}")
                disconnected.append(connection)
                
        # Clean up dead connections
        for conn in disconnected:
            self.disconnect(conn)
            
    def set_filters(self, websocket: WebSocket, filters: List[str]):
        """Set event filters for a specific client."""
        self.subscription_filters[websocket] = filters


# Global connection manager instance
manager = ConnectionManager()


async def broadcast_job_event(event_type: str, job: Dict[str, Any]):
    """
    Broadcast job-related event to all clients with fragility context (MM-6).
    
    Enriches job data with:
    - materials: List of material types from metadata
    - worst_fragility_score: Float 0.0-1.0 from CAM profile summary
    - fragility_band: "stable", "medium", "fragile", or "unknown"
    - lane_hint: Suggested quality lane
    """
    # MM-6: Extract fragility context from job metadata
    try:
        frag_ctx = build_fragility_context_for_job(job)
        enriched_job = {
            **job,
            "materials": frag_ctx.get("materials", []),
            "worst_fragility_score": frag_ctx.get("worst_fragility_score"),
            "fragility_band": frag_ctx.get("fragility_band", "unknown"),
            "lane_hint": frag_ctx.get("lane_hint"),
        }
    except Exception as e:
        logger.warning(f"Failed to extract fragility context for job {job.get('id')}: {e}")
        enriched_job = job  # Fallback to original job without fragility data
    
    await manager.broadcast(f"job:{event_type}", enriched_job, filters=["job", "all"])


async def broadcast_pattern_event(event_type: str, pattern: Dict[str, Any]):
    """Broadcast pattern-related event to all clients."""
    await manager.broadcast(f"pattern:{event_type}", pattern, filters=["pattern", "all"])


async def broadcast_material_event(event_type: str, material: Dict[str, Any]):
    """Broadcast material-related event to all clients."""
    await manager.broadcast(f"material:{event_type}", material, filters=["material", "all"])


async def broadcast_metrics_snapshot(metrics: Dict[str, Any]):
    """Broadcast periodic metrics snapshot."""
    await manager.broadcast("metrics:snapshot", metrics, filters=["metrics", "all"])


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance."""
    return manager
