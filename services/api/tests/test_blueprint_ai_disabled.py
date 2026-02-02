"""Test blueprint AI routes return 503 when AI dependencies/keys are missing."""
import io
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


def _valid_png_bytes() -> bytes:
    """Create minimal valid PNG (1x1 pixel) to pass file validation."""
    from PIL import Image
    
    img = Image.new("RGB", (1, 1), color="red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


@pytest.fixture
def client_no_ai_keys():
    """Create test client with AI keys cleared."""
    env_patch = {
        "EMERGENT_LLM_KEY": "",
        "ANTHROPIC_API_KEY": "",
    }
    with patch.dict(os.environ, env_patch, clear=False):
        from app.main import app
        yield TestClient(app)


def test_blueprint_analyze_returns_503_when_ai_keys_missing(client_no_ai_keys):
    """Blueprint analyze should return 503 when AI keys are not configured."""
    resp = client_no_ai_keys.post(
        "/api/blueprint/analyze",
        files={"file": ("test.png", _valid_png_bytes(), "image/png")},
    )
    assert resp.status_code == 503
    data = resp.json()
    assert data.get("detail", {}).get("error") == "AI_DISABLED"


def test_blueprint_health_is_200_even_when_ai_disabled(client_no_ai_keys):
    """Blueprint health endpoint should still work even when AI is disabled."""
    resp = client_no_ai_keys.get("/api/blueprint/health")
    assert resp.status_code == 200
