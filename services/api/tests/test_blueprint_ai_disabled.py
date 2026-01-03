"""Test blueprint AI routes return 503 when AI dependencies/keys are missing."""
import os

from fastapi.testclient import TestClient


def _dummy_pdf_bytes() -> bytes:
    # Minimal-ish PDF header to satisfy content checks.
    return b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"


def test_blueprint_analyze_returns_503_when_ai_keys_missing(monkeypatch):
    """Blueprint analyze should return 503 when AI keys are not configured."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("EMERGENT_LLM_KEY", raising=False)

    from app.main import app

    client = TestClient(app)
    resp = client.post(
        "/api/blueprint/analyze",
        files={"file": ("test.pdf", _dummy_pdf_bytes(), "application/pdf")},
    )
    assert resp.status_code == 503
    data = resp.json()
    assert data.get("detail", {}).get("error") == "AI_DISABLED"


def test_blueprint_health_is_200_even_when_ai_disabled(monkeypatch):
    """Blueprint health endpoint should still work even when AI is disabled."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("EMERGENT_LLM_KEY", raising=False)

    from app.main import app

    client = TestClient(app)
    resp = client.get("/api/blueprint/health")
    assert resp.status_code == 200
