"""
Vision Attach Flow — Smoke Test (Acceptance Contract)

This test locks the Vision → Attach → Review flow as a "never break again" contract.

Tests the complete flow:
1. GET /api/vision/providers - returns stub configured (CI) or openai (local)
2. POST /api/vision/generate - returns assets with sha256 and url
3. POST /api/rmos/runs - creates a run
4. POST /api/rmos/runs/{run_id}/advisory/attach - attaches advisory by sha256
5. GET /api/rmos/runs/{run_id}/advisory/variants - includes attached advisory

Uses stub provider in CI, openai provider when OPENAI_API_KEY is set.
"""
from __future__ import annotations

import os
import pytest
from fastapi.testclient import TestClient


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def client():
    """TestClient using app directly."""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def use_openai():
    """Check if OpenAI is available (for local testing with real images)."""
    return bool(os.environ.get("OPENAI_API_KEY"))


# =============================================================================
# Test: Vision Providers Available
# =============================================================================

def test_vision_providers_returns_configured_provider(client: TestClient):
    """GET /api/vision/providers returns at least one configured provider."""
    response = client.get("/api/vision/providers")
    assert response.status_code == 200, response.text

    data = response.json()
    assert "providers" in data
    assert len(data["providers"]) > 0

    # At least stub should always be configured
    provider_names = [p["name"] for p in data["providers"]]
    assert "stub" in provider_names or "openai" in provider_names

    # At least one provider should be configured
    configured = [p for p in data["providers"] if p.get("configured")]
    assert len(configured) >= 1, "No providers are configured"


# =============================================================================
# Test: Vision Generate Returns Assets with SHA256
# =============================================================================

def test_vision_generate_returns_assets_with_sha256(client: TestClient):
    """POST /api/vision/generate returns assets with sha256 identity."""
    response = client.post(
        "/api/vision/generate",
        json={
            "prompt": "test image for smoke test",
            "provider": "stub",  # Always use stub for CI
            "num_images": 1,
            "size": "1024x1024",
            "quality": "standard",
        },
    )
    assert response.status_code == 200, response.text

    data = response.json()
    assert "assets" in data
    assert len(data["assets"]) >= 1

    asset = data["assets"][0]
    assert "sha256" in asset, "Asset missing sha256 identity"
    assert len(asset["sha256"]) == 64, "sha256 should be 64 hex chars"
    assert "url" in asset, "Asset missing url for browser display"
    assert asset["url"].startswith("/api/"), "URL should be API path"


# =============================================================================
# Test: Create Run Returns run_id
# =============================================================================

def test_create_run_returns_run_id(client: TestClient):
    """POST /api/rmos/runs creates a run and returns run_id."""
    response = client.post(
        "/api/rmos/runs",
        json={
            "event_type": "vision_image_review",
            "mode": "vision",
            "tool_id": "vision:smoke_test",
            "status": "OK",
        },
    )
    assert response.status_code == 200, response.text

    data = response.json()
    assert "run_id" in data
    assert data["run_id"].startswith("run_")


# =============================================================================
# Test: Full Flow — Generate → Create Run → Attach → Variants
# =============================================================================

def test_full_vision_attach_flow(client: TestClient):
    """
    Complete smoke test of Vision → Attach → Review flow.

    This is the "never break again" acceptance test.
    """
    # Step 1: Generate an image (stub provider)
    gen_response = client.post(
        "/api/vision/generate",
        json={
            "prompt": "acceptance test image",
            "provider": "stub",
            "num_images": 1,
        },
    )
    assert gen_response.status_code == 200, f"Generate failed: {gen_response.text}"

    gen_data = gen_response.json()
    assert len(gen_data["assets"]) >= 1
    asset = gen_data["assets"][0]
    sha256 = asset["sha256"]
    assert sha256, "Asset missing sha256"

    # Step 2: Create a run
    run_response = client.post(
        "/api/rmos/runs",
        json={
            "event_type": "vision_image_review",
            "mode": "vision",
            "tool_id": "vision:acceptance_test",
            "status": "OK",
        },
    )
    assert run_response.status_code == 200, f"Create run failed: {run_response.text}"

    run_data = run_response.json()
    run_id = run_data["run_id"]
    assert run_id, "Run missing run_id"

    # Step 3: Attach the generated asset as advisory
    attach_response = client.post(
        f"/api/rmos/runs/{run_id}/advisory/attach",
        json={
            "advisory_id": sha256,
            "kind": "advisory",
            "mime": asset.get("mime", "image/png"),
            "filename": asset.get("filename", "generated.png"),
        },
    )
    assert attach_response.status_code == 200, f"Attach failed: {attach_response.text}"

    attach_data = attach_response.json()
    assert attach_data.get("attached") is True, "Attach should return attached=true"
    assert attach_data.get("advisory_id") == sha256

    # Step 4: Verify the advisory appears in variants list
    variants_response = client.get(f"/api/rmos/runs/{run_id}/advisory/variants")
    assert variants_response.status_code == 200, f"Variants failed: {variants_response.text}"

    variants_data = variants_response.json()
    assert "items" in variants_data

    # Find our attached advisory
    advisory_ids = [v.get("advisory_id") for v in variants_data["items"]]
    assert sha256 in advisory_ids, f"Attached advisory {sha256[:12]}... not in variants"


# =============================================================================
# Test: Attach Idempotent (Already Attached)
# =============================================================================

def test_attach_advisory_idempotent(client: TestClient):
    """Attaching the same advisory twice returns attached=false (already attached)."""
    # Generate
    gen_response = client.post(
        "/api/vision/generate",
        json={"prompt": "idempotent test", "provider": "stub", "num_images": 1},
    )
    assert gen_response.status_code == 200
    sha256 = gen_response.json()["assets"][0]["sha256"]

    # Create run
    run_response = client.post(
        "/api/rmos/runs",
        json={"event_type": "vision_image_review"},
    )
    assert run_response.status_code == 200
    run_id = run_response.json()["run_id"]

    # First attach
    attach1 = client.post(
        f"/api/rmos/runs/{run_id}/advisory/attach",
        json={"advisory_id": sha256, "kind": "advisory"},
    )
    assert attach1.status_code == 200
    assert attach1.json()["attached"] is True

    # Second attach (should be idempotent)
    attach2 = client.post(
        f"/api/rmos/runs/{run_id}/advisory/attach",
        json={"advisory_id": sha256, "kind": "advisory"},
    )
    assert attach2.status_code == 200
    assert attach2.json()["attached"] is False, "Second attach should return attached=false"


# =============================================================================
# Test: Attach with Invalid Advisory Returns 409
# =============================================================================

def test_attach_invalid_advisory_returns_409(client: TestClient):
    """Attaching an advisory_id that doesn't exist in CAS returns 409."""
    # Create a valid run first
    run_response = client.post(
        "/api/rmos/runs",
        json={"event_type": "vision_image_review"},
    )
    assert run_response.status_code == 200
    run_id = run_response.json()["run_id"]

    # Try to attach a non-existent advisory
    response = client.post(
        f"/api/rmos/runs/{run_id}/advisory/attach",
        json={"advisory_id": "nonexistent_sha256_abc123", "kind": "advisory"},
    )
    # Returns 409 CAS_MISSING_BLOB because advisory doesn't exist in CAS
    assert response.status_code == 409


# =============================================================================
# Optional: Test with OpenAI (Local Only)
# =============================================================================

@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set - skipping real OpenAI test"
)
def test_vision_generate_with_openai(client: TestClient):
    """
    Test with real OpenAI provider (local development only).

    Skipped in CI unless OPENAI_API_KEY is set.
    """
    response = client.post(
        "/api/vision/generate",
        json={
            "prompt": "a simple red square on white background",
            "provider": "openai",
            "num_images": 1,
            "size": "1024x1024",
            "quality": "standard",
        },
        timeout=120,  # OpenAI can be slow
    )
    assert response.status_code == 200, response.text

    data = response.json()
    assert len(data["assets"]) >= 1
    asset = data["assets"][0]
    assert "sha256" in asset
    assert "url" in asset
    assert asset["provider"] == "openai"
