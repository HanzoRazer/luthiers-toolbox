# tests/test_websocket_router.py
"""
WebSocket Router Tests

Tests for WebSocket event streaming endpoints.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient


class TestWebSocketStatus:
    """Test WebSocket status endpoint (HTTP)."""

    def test_websocket_status_returns_connection_info(self, client):
        """Test /ws/status returns expected structure."""
        response = client.get("/ws/status")
        assert response.status_code == 200

        data = response.json()
        assert "active_connections" in data
        assert "available_filters" in data
        assert "event_types" in data
        assert "endpoints" in data

        # Verify expected filters
        assert "all" in data["available_filters"]
        assert "job" in data["available_filters"]
        assert "cam" in data["available_filters"]
        assert "ai" in data["available_filters"]

        # Verify expected endpoints
        assert data["endpoints"]["monitor"] == "/ws/monitor"
        assert data["endpoints"]["live"] == "/ws/live"


class TestConnectionManager:
    """Test WebSocket ConnectionManager."""

    def test_connection_manager_connect(self):
        """Test connecting a WebSocket client."""
        from app.websocket.monitor import ConnectionManager

        manager = ConnectionManager()
        mock_ws = AsyncMock()

        import asyncio
        asyncio.get_event_loop().run_until_complete(manager.connect(mock_ws))

        assert mock_ws in manager.active_connections
        mock_ws.accept.assert_called_once()

    def test_connection_manager_disconnect(self):
        """Test disconnecting a WebSocket client."""
        from app.websocket.monitor import ConnectionManager

        manager = ConnectionManager()
        mock_ws = AsyncMock()
        manager.active_connections.add(mock_ws)
        manager.subscription_filters[mock_ws] = ["all"]

        manager.disconnect(mock_ws)

        assert mock_ws not in manager.active_connections
        assert mock_ws not in manager.subscription_filters

    def test_connection_manager_set_filters(self):
        """Test setting filters for a WebSocket client."""
        from app.websocket.monitor import ConnectionManager

        manager = ConnectionManager()
        mock_ws = AsyncMock()
        manager.active_connections.add(mock_ws)

        manager.set_filters(mock_ws, ["job", "cam"])

        assert manager.subscription_filters[mock_ws] == ["job", "cam"]

    def test_connection_manager_get_filters_default(self):
        """Test getting filters returns empty list for unregistered client."""
        from app.websocket.monitor import ConnectionManager

        manager = ConnectionManager()
        mock_ws = AsyncMock()

        filters = manager.get_filters(mock_ws)
        assert filters == []

    def test_connection_manager_should_receive_with_all_filter(self):
        """Test 'all' filter receives all events."""
        from app.websocket.monitor import ConnectionManager

        manager = ConnectionManager()
        mock_ws = AsyncMock()
        manager.active_connections.add(mock_ws)
        manager.set_filters(mock_ws, ["all"])

        assert manager._should_receive(mock_ws, ["job"])
        assert manager._should_receive(mock_ws, ["cam", "ai"])

    def test_connection_manager_should_receive_with_specific_filter(self):
        """Test specific filter only receives matching events."""
        from app.websocket.monitor import ConnectionManager

        manager = ConnectionManager()
        mock_ws = AsyncMock()
        manager.active_connections.add(mock_ws)
        manager.set_filters(mock_ws, ["job"])

        assert manager._should_receive(mock_ws, ["job"])
        assert not manager._should_receive(mock_ws, ["cam"])


class TestBroadcast:
    """Test WebSocket broadcast functionality."""

    def test_broadcast_sends_to_matching_clients(self):
        """Test broadcast sends to clients with matching filters."""
        from app.websocket.monitor import ConnectionManager

        manager = ConnectionManager()

        # Create mock WebSocket clients
        client_all = AsyncMock()
        client_job = AsyncMock()
        client_cam = AsyncMock()

        manager.active_connections.add(client_all)
        manager.active_connections.add(client_job)
        manager.active_connections.add(client_cam)

        manager.set_filters(client_all, ["all"])
        manager.set_filters(client_job, ["job"])
        manager.set_filters(client_cam, ["cam"])

        import asyncio
        asyncio.get_event_loop().run_until_complete(
            manager.broadcast("job:completed", {"job_id": "123"}, filters=["job", "all"])
        )

        # client_all and client_job should receive
        assert client_all.send_json.called
        assert client_job.send_json.called
        # client_cam should NOT receive (only subscribed to "cam")
        assert not client_cam.send_json.called


class TestLiveMonitorPublish:
    """Test LiveMonitor publish_event integration."""

    def test_publish_event_logs(self, caplog):
        """Test publish_event logs the event."""
        import logging
        from app.infra.live_monitor import publish_event

        with caplog.at_level(logging.INFO):
            publish_event("test:event", {"key": "value"})

        assert "LiveMonitor event: test:event" in caplog.text

    def test_publish_job_event_formats_correctly(self, caplog):
        """Test publish_job_event creates correct event type."""
        import logging
        from app.infra.live_monitor import publish_job_event

        with caplog.at_level(logging.INFO):
            publish_job_event("completed", {"job_id": "JOB-123"})

        assert "job:completed" in caplog.text

    def test_publish_cam_event_formats_correctly(self, caplog):
        """Test publish_cam_event creates correct event type."""
        import logging
        from app.infra.live_monitor import publish_cam_event

        with caplog.at_level(logging.INFO):
            publish_cam_event("gcode_exported", {"file": "output.nc"})

        assert "cam:gcode_exported" in caplog.text

    def test_publish_ai_event_formats_correctly(self, caplog):
        """Test publish_ai_event creates correct event type."""
        import logging
        from app.infra.live_monitor import publish_ai_event

        with caplog.at_level(logging.INFO):
            publish_ai_event("vision_complete", {"image_id": "IMG-123"})

        assert "ai:vision_complete" in caplog.text

    def test_publish_system_event_formats_correctly(self, caplog):
        """Test publish_system_event creates correct event type."""
        import logging
        from app.infra.live_monitor import publish_system_event

        with caplog.at_level(logging.INFO):
            publish_system_event("health", {"status": "ok"})

        assert "system:health" in caplog.text


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def client():
    """Create a test client."""
    from app.main import app
    from fastapi.testclient import TestClient
    return TestClient(app)
