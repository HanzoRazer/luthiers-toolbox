"""Smoke tests for AI routers (Session E).

Tests:
- assistant_router.py (POST /chat, GET /history, DELETE /history, GET /status)
- defect_detection_router.py (POST /analyze, GET /status)
- recommendations_router.py (POST /generate, GET /status)
- wood_grading_router.py (POST /analyze, GET /health)

All tests mock LLM/Vision clients to avoid external API calls.
"""

from __future__ import annotations

import base64
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient



# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def client():
    """Function-scoped TestClient to prevent shared state pollution."""
    from app.main import app
    
    # Clear any stale dependency overrides from previous tests
    app.dependency_overrides.clear()
    
    with TestClient(app) as c:
        yield c
    
    # Clean up after tests
    app.dependency_overrides.clear()


@pytest.fixture
def mock_llm_response():
    """Mock LLM client response."""
    response = MagicMock()
    response.content = "This is a mock AI response about lutherie."
    response.total_tokens = 100
    response.model = "mock-model"
    return response


@pytest.fixture
def mock_llm_client(mock_llm_response):
    """Mock LLM client that returns a successful response."""
    client_mock = MagicMock()
    client_mock.is_configured = True
    client_mock.request_text.return_value = mock_llm_response
    return client_mock


@pytest.fixture
def mock_vision_response():
    """Mock Vision client response."""
    response = MagicMock()
    response.content = {
        "observations": "Mock wood surface observations",
        "grain_spacing_estimate": "medium",
        "runout_visible": False,
        "anomalies_detected": False,
        "confidence": "high",
    }
    response.as_json = response.content
    return response


@pytest.fixture
def mock_vision_client(mock_vision_response):
    """Mock Vision client that returns a successful response."""
    client_mock = MagicMock()
    client_mock.is_configured = True
    client_mock.analyze.return_value = mock_vision_response
    return client_mock


@pytest.fixture
def sample_image_base64():
    """Valid base64 image that passes size validation (>100 bytes)."""
    # Create a 50x50 red PNG using PIL - well over 100 bytes
    import io
    try:
        from PIL import Image
        img = Image.new('RGB', (50, 50), color='red')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode()
    except ImportError:
        # Fallback: create padded data that exceeds 100 bytes
        # Valid PNG header + padding
        png_header = b'\x89PNG\r\n\x1a\n'
        padding = b'\x00' * 200
        return base64.b64encode(png_header + padding).decode()


# =============================================================================
# ASSISTANT ROUTER TESTS
# =============================================================================


class TestAssistantRouter:
    """Tests for /api/ai/assistant/* endpoints."""

    def test_status_endpoint_exists(self, client):
        """GET /api/ai/assistant/status returns valid response."""
        response = client.get("/api/ai/assistant/status")
        assert response.status_code == 200
        data = response.json()
        assert "ok" in data
        assert "providers" in data
        assert "anthropic" in data["providers"]
        assert "openai" in data["providers"]

    def test_history_endpoint_empty_session(self, client):
        """GET /api/ai/assistant/history returns empty for new session."""
        response = client.get(
            "/api/ai/assistant/history",
            params={"session_id": "test-smoke-session-001"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-smoke-session-001"
        assert data["messages"] == []
        assert data["count"] == 0

    def test_history_requires_session_id(self, client):
        """GET /api/ai/assistant/history requires session_id param."""
        response = client.get("/api/ai/assistant/history")
        assert response.status_code == 422  # Validation error

    def test_clear_history_endpoint(self, client):
        """DELETE /api/ai/assistant/history clears session."""
        response = client.delete(
            "/api/ai/assistant/history",
            params={"session_id": "test-smoke-session-002"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["session_id"] == "test-smoke-session-002"
        assert "messages_cleared" in data

    def test_chat_requires_message(self, client):
        """POST /api/ai/assistant/chat validates empty message."""
        response = client.post(
            "/api/ai/assistant/chat",
            json={"message": "", "session_id": "test-session"}
        )
        assert response.status_code == 422  # Validation error (min_length=1)

    def test_chat_requires_session_id(self, client):
        """POST /api/ai/assistant/chat requires session_id."""
        response = client.post(
            "/api/ai/assistant/chat",
            json={"message": "Hello"}
        )
        assert response.status_code == 422  # Missing required field

    @patch("app.routers.ai.assistant_router.get_llm_client")
    def test_chat_success_with_mock(self, mock_get_client, mock_llm_client, mock_llm_response, client):
        """POST /api/ai/assistant/chat returns AI response."""
        mock_get_client.return_value = mock_llm_client

        response = client.post(
            "/api/ai/assistant/chat",
            json={
                "message": "What is the ideal scale length for a classical guitar?",
                "session_id": "test-smoke-session-003"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["session_id"] == "test-smoke-session-003"

    @patch("app.routers.ai.assistant_router.get_llm_client")
    def test_chat_no_api_key_returns_503(self, mock_get_client, client):
        """POST /api/ai/assistant/chat returns 503 when no API configured."""
        unconfigured_client = MagicMock()
        unconfigured_client.is_configured = False
        mock_get_client.return_value = unconfigured_client

        response = client.post(
            "/api/ai/assistant/chat",
            json={
                "message": "Test message",
                "session_id": "test-session-no-key"
            }
        )
        assert response.status_code == 503
        assert "not configured" in response.json()["detail"].lower()


# =============================================================================
# DEFECT DETECTION ROUTER TESTS
# =============================================================================


class TestDefectDetectionRouter:
    """Tests for /api/ai/defects/* endpoints."""

    def test_status_endpoint_exists(self, client):
        """GET /api/ai/defects/status returns valid response."""
        response = client.get("/api/ai/defects/status")
        assert response.status_code == 200
        data = response.json()
        assert "ok" in data
        assert "provider" in data
        assert "configured" in data

    def test_analyze_requires_image(self, client):
        """POST /api/ai/defects/analyze requires image_base64."""
        response = client.post(
            "/api/ai/defects/analyze",
            json={}
        )
        assert response.status_code == 422  # Validation error

    def test_analyze_rejects_invalid_base64(self, client):
        """POST /api/ai/defects/analyze rejects invalid base64."""
        response = client.post(
            "/api/ai/defects/analyze",
            json={"image_base64": "not-valid-base64!!!"}
        )
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    def test_analyze_rejects_tiny_image(self, client):
        """POST /api/ai/defects/analyze rejects images < 100 bytes."""
        tiny_data = base64.b64encode(b"tiny").decode()
        response = client.post(
            "/api/ai/defects/analyze",
            json={"image_base64": tiny_data}
        )
        assert response.status_code == 400
        assert "small" in response.json()["detail"].lower()

    @patch("app.routers.ai.defect_detection_router.get_vision_client")
    def test_analyze_success_with_mock(
        self, mock_get_client, mock_vision_client, sample_image_base64, client
    ):
        """POST /api/ai/defects/analyze returns observations."""
        mock_get_client.return_value = mock_vision_client

        response = client.post(
            "/api/ai/defects/analyze",
            json={
                "image_base64": sample_image_base64,
                "wood_species": "sitka spruce"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "observations" in data
        assert "grain_spacing_estimate" in data
        assert "runout_visible" in data
        assert "anomalies_detected" in data
        assert "confidence" in data

    @patch("app.routers.ai.defect_detection_router.get_vision_client")
    def test_analyze_without_species(
        self, mock_get_client, mock_vision_client, sample_image_base64, client
    ):
        """POST /api/ai/defects/analyze works without wood_species."""
        mock_get_client.return_value = mock_vision_client

        response = client.post(
            "/api/ai/defects/analyze",
            json={"image_base64": sample_image_base64}
        )
        assert response.status_code == 200

    @patch("app.routers.ai.defect_detection_router.get_vision_client")
    def test_analyze_unconfigured_returns_503(self, mock_get_client, sample_image_base64, client):
        """POST /api/ai/defects/analyze returns 503 when vision not configured."""
        unconfigured = MagicMock()
        unconfigured.is_configured = False
        mock_get_client.return_value = unconfigured

        response = client.post(
            "/api/ai/defects/analyze",
            json={"image_base64": sample_image_base64}
        )
        assert response.status_code == 503


# =============================================================================
# RECOMMENDATIONS ROUTER TESTS
# =============================================================================


class TestRecommendationsRouter:
    """Tests for /api/ai/recommendations/* endpoints."""

    def test_status_endpoint_exists(self, client):
        """GET /api/ai/recommendations/status returns valid response."""
        response = client.get("/api/ai/recommendations/status")
        assert response.status_code == 200
        data = response.json()
        assert "ok" in data
        assert "providers" in data

    def test_generate_requires_all_fields(self, client):
        """POST /api/ai/recommendations/generate validates required fields."""
        # Missing all fields
        response = client.post("/api/ai/recommendations/generate", json={})
        assert response.status_code == 422

        # Missing some fields
        response = client.post(
            "/api/ai/recommendations/generate",
            json={"build_type": "acoustic"}
        )
        assert response.status_code == 422

    @patch("app.routers.ai.recommendations_router.get_llm_client")
    def test_generate_success_with_mock(self, mock_get_client, mock_llm_client, client):
        """POST /api/ai/recommendations/generate returns recommendations."""
        # Mock response with valid JSON
        mock_response = MagicMock()
        mock_response.content = '''
        {
            "tonewoods": [
                {"name": "Sitka Spruce Top", "reason": "Excellent projection", "score": 92}
            ],
            "design": [
                {"feature": "Body Shape", "suggestion": "Dreadnought for volume"}
            ],
            "hardware": [
                {"item": "Tuners", "recommendation": "Gotoh 510 for stability"}
            ],
            "reasoning": "Based on fingerstyle playing preference..."
        }
        '''
        mock_llm_client.request_text.return_value = mock_response
        mock_get_client.return_value = mock_llm_client

        response = client.post(
            "/api/ai/recommendations/generate",
            json={
                "build_type": "acoustic",
                "target_tone": "warm",
                "playing_style": "fingerstyle",
                "budget": "mid"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "tonewoods" in data
        assert "design" in data
        assert "hardware" in data
        assert "reasoning" in data

    @patch("app.routers.ai.recommendations_router.get_llm_client")
    def test_generate_unconfigured_returns_503(self, mock_get_client, client):
        """POST /api/ai/recommendations/generate returns 503 when not configured."""
        unconfigured = MagicMock()
        unconfigured.is_configured = False
        mock_get_client.return_value = unconfigured

        response = client.post(
            "/api/ai/recommendations/generate",
            json={
                "build_type": "acoustic",
                "target_tone": "warm",
                "playing_style": "fingerstyle",
                "budget": "mid"
            }
        )
        assert response.status_code == 503


# =============================================================================
# WOOD GRADING ROUTER TESTS
# =============================================================================


class TestWoodGradingRouter:
    """Tests for /api/ai/wood-grading/* endpoints."""

    def test_health_endpoint_exists(self, client):
        """GET /api/ai/wood-grading/health returns valid response."""
        response = client.get("/api/ai/wood-grading/health")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "service" in data
        assert "vision_configured" in data
        assert "note" in data  # Reminder about acoustic grading

    def test_analyze_requires_image(self, client):
        """POST /api/ai/wood-grading/analyze requires image_base64."""
        response = client.post(
            "/api/ai/wood-grading/analyze",
            json={}
        )
        assert response.status_code == 422

    def test_analyze_rejects_invalid_base64(self, client):
        """POST /api/ai/wood-grading/analyze rejects invalid base64."""
        response = client.post(
            "/api/ai/wood-grading/analyze",
            json={"image_base64": "###invalid###"}
        )
        assert response.status_code == 400

    @patch("app.routers.ai.wood_grading_router.get_vision_client")
    def test_analyze_returns_stub_when_unconfigured(self, mock_get_client, sample_image_base64, client):
        """POST /api/ai/wood-grading/analyze returns stub when vision not configured."""
        unconfigured = MagicMock()
        unconfigured.is_configured = False
        mock_get_client.return_value = unconfigured

        response = client.post(
            "/api/ai/wood-grading/analyze",
            json={"image_base64": sample_image_base64}
        )
        # Wood grading returns stub response instead of 503
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "placeholder" in data["observations"].lower() or "not configured" in data["observations"].lower()
        assert data["confidence"] == "low"

    @patch("app.routers.ai.wood_grading_router.get_vision_client")
    def test_analyze_success_with_mock(self, mock_get_client, sample_image_base64, client):
        """POST /api/ai/wood-grading/analyze returns visual observations."""
        mock_client = MagicMock()
        mock_client.is_configured = True
        mock_response = MagicMock()
        mock_response.as_json = {
            "observations": "Tight grain pattern with consistent spacing",
            "grain_spacing_estimate": "tight",
            "grain_straightness": "straight",
            "figure_type": "plain",
            "color_uniformity": "uniform",
            "surface_anomalies": [],
            "confidence": "high"
        }
        mock_client.analyze.return_value = mock_response
        mock_get_client.return_value = mock_client

        response = client.post(
            "/api/ai/wood-grading/analyze",
            json={
                "image_base64": sample_image_base64,
                "wood_species": "sitka spruce"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "observations" in data
        assert "grain_spacing_estimate" in data
        assert "grain_straightness" in data
        assert "figure_type" in data
        assert "color_uniformity" in data
        assert "surface_anomalies" in data
        assert "confidence" in data
        assert "note" in data  # Tap Tone reminder

    @patch("app.routers.ai.wood_grading_router.get_vision_client")
    def test_analyze_without_species(self, mock_get_client, sample_image_base64, client):
        """POST /api/ai/wood-grading/analyze works without wood_species."""
        mock_client = MagicMock()
        mock_client.is_configured = True
        mock_response = MagicMock()
        mock_response.as_json = {
            "observations": "General wood surface",
            "grain_spacing_estimate": "medium",
            "grain_straightness": "straight",
            "figure_type": "plain",
            "color_uniformity": "uniform",
            "surface_anomalies": [],
            "confidence": "medium"
        }
        mock_client.analyze.return_value = mock_response
        mock_get_client.return_value = mock_client

        response = client.post(
            "/api/ai/wood-grading/analyze",
            json={"image_base64": sample_image_base64}
        )
        assert response.status_code == 200


# =============================================================================
# ROUTER REGISTRATION TESTS
# =============================================================================


class TestAIRouterRegistration:
    """Verify all AI routers are properly mounted."""

    def test_assistant_router_mounted(self, client):
        """Assistant router is mounted at /api/ai/assistant."""
        response = client.get("/api/ai/assistant/status")
        assert response.status_code == 200

    def test_defects_router_mounted(self, client):
        """Defect detection router is mounted at /api/ai/defects."""
        response = client.get("/api/ai/defects/status")
        assert response.status_code == 200

    def test_recommendations_router_mounted(self, client):
        """Recommendations router is mounted at /api/ai/recommendations."""
        response = client.get("/api/ai/recommendations/status")
        assert response.status_code == 200

    def test_wood_grading_router_mounted(self, client):
        """Wood grading router is mounted at /api/ai/wood-grading."""
        response = client.get("/api/ai/wood-grading/health")
        assert response.status_code == 200
