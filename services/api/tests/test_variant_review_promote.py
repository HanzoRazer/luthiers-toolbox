"""
Test for Variant Review, Rating, and Promotion API Endpoints.

Tests the following endpoints:
- GET /api/rmos/runs/{run_id}/advisory/variants
- POST /api/rmos/runs/{run_id}/advisory/{advisory_id}/review
- POST /api/rmos/runs/{run_id}/advisory/{advisory_id}/promote

RBAC:
- Promotion requires x-user-role header: admin|operator|engineer
- User identity via x-user-id header
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


# Role headers for RBAC testing
OPERATOR_HEADERS = {"x-user-role": "operator", "x-user-id": "test_operator"}
VIEWER_HEADERS = {"x-user-role": "viewer", "x-user-id": "test_viewer"}
NO_ROLE_HEADERS = {"x-user-id": "anonymous"}


@pytest.fixture
def client():
    """TestClient using app directly."""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def run_with_advisory(client: TestClient, tmp_path):
    """Create a run artifact with an advisory attached for testing."""
    import hashlib
    import base64

    # Create a run first
    run_req = client.post(
        "/api/rmos/runs",
        json={
            "mode": "test_review",
            "tool_id": "saw:test_review",
            "status": "OK",
            "event_type": "test_variant_review",
            "request_summary": {"test": "variant_review"},
            "feasibility": {"score": 0.9},
        },
    )
    assert run_req.status_code == 200, run_req.text
    run_id = run_req.json()["run_id"]

    # Create SVG content and attach it as advisory
    svg_content = b'<svg xmlns="http://www.w3.org/2000/svg"><rect width="100" height="100" fill="blue"/></svg>'
    sha256 = hashlib.sha256(svg_content).hexdigest()
    b64 = base64.b64encode(svg_content).decode()

    # Step 1: Create the attachment in CAS
    att_req = client.post(
        f"/api/rmos/runs/{run_id}/attachments",
        json={
            "kind": "advisory",
            "filename": "test_advisory.svg",
            "content_type": "image/svg+xml",
            "sha256": sha256,
            "b64": b64,
        },
    )
    assert att_req.status_code == 200, f"Failed to create attachment: {att_req.text}"
    advisory_id = att_req.json().get("sha256", sha256)

    # Step 2: Link the attachment as an advisory input
    link_req = client.post(
        f"/api/rmos/runs/{run_id}/attach-advisory",
        json={
            "advisory_id": advisory_id,
            "kind": "advisory",
            "engine_id": "test_engine",
            "engine_version": "1.0.0",
        },
    )
    assert link_req.status_code == 200, f"Failed to link advisory: {link_req.text}"

    return {"run_id": run_id, "advisory_id": advisory_id}


def test_list_advisory_variants_returns_list(client: TestClient, run_with_advisory):
    """Test that the variants endpoint returns a structured response with items."""
    run_id = run_with_advisory["run_id"]

    res = client.get(f"/api/rmos/runs/{run_id}/advisory/variants")
    assert res.status_code == 200, res.text

    data = res.json()
    assert "items" in data
    assert "count" in data
    assert "run_id" in data
    assert isinstance(data["items"], list)


def test_list_advisory_variants_404_for_missing_run(client: TestClient):
    """Test that variants endpoint returns 404 for non-existent run."""
    res = client.get("/api/rmos/runs/nonexistent_run_id/advisory/variants")
    assert res.status_code == 404


def test_save_review_requires_valid_rating(client: TestClient, run_with_advisory):
    """Test that review endpoint validates rating range 1-5."""
    run_id = run_with_advisory["run_id"]
    advisory_id = run_with_advisory["advisory_id"]

    # Rating below 1 should fail (400 from service or 422 from Pydantic)
    res = client.post(
        f"/api/rmos/runs/{run_id}/advisory/{advisory_id}/review",
        json={"rating": 0, "notes": "test"},
    )
    assert res.status_code in (400, 422), f"Expected 400/422, got {res.status_code}: {res.text}"

    # Rating above 5 should fail
    res = client.post(
        f"/api/rmos/runs/{run_id}/advisory/{advisory_id}/review",
        json={"rating": 6, "notes": "test"},
    )
    assert res.status_code in (400, 422), f"Expected 400/422, got {res.status_code}: {res.text}"


def test_save_review_succeeds_with_valid_data(client: TestClient, run_with_advisory):
    """Test that review can be saved with valid rating and notes."""
    run_id = run_with_advisory["run_id"]
    advisory_id = run_with_advisory["advisory_id"]

    res = client.post(
        f"/api/rmos/runs/{run_id}/advisory/{advisory_id}/review",
        headers=OPERATOR_HEADERS,
        json={
            "rating": 4,
            "notes": "Good variant, slight edge roughness",
        },
    )
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert data["rating"] == 4
    assert "updated_at_utc" in data
    assert data.get("updated_by") == "test_operator"


def test_save_review_404_for_missing_run(client: TestClient):
    """Test that review endpoint returns 404 for non-existent run."""
    res = client.post(
        "/api/rmos/runs/nonexistent_run_id/advisory/some_advisory/review",
        json={"rating": 3, "notes": "test"},
    )
    assert res.status_code == 404


def test_promote_creates_manufacturing_candidate(client: TestClient, run_with_advisory):
    """Test that promotion creates a new manufacturing candidate on the run."""
    run_id = run_with_advisory["run_id"]
    advisory_id = run_with_advisory["advisory_id"]

    res = client.post(
        f"/api/rmos/runs/{run_id}/advisory/{advisory_id}/promote",
        headers=OPERATOR_HEADERS,
        json={"label": "test_candidate", "note": "promotion test"},
    )
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert data["run_id"] == run_id
    assert data["advisory_id"] == advisory_id
    assert data["decision"] in ("ALLOW", "BLOCK")
    assert data["risk_level"] in ("GREEN", "YELLOW", "RED")
    assert "score" in data
    assert "reason" in data
    # For ALLOW decision, we should have a candidate ID
    if data["decision"] == "ALLOW":
        assert data.get("manufactured_candidate_id") is not None


def test_promote_returns_409_if_already_promoted(client: TestClient, run_with_advisory):
    """Test that promoting the same variant twice returns 409 Conflict."""
    run_id = run_with_advisory["run_id"]
    advisory_id = run_with_advisory["advisory_id"]

    # First promotion
    res1 = client.post(
        f"/api/rmos/runs/{run_id}/advisory/{advisory_id}/promote",
        headers=OPERATOR_HEADERS,
        json={"label": None, "note": None},
    )
    assert res1.status_code == 200, f"First promotion failed: {res1.status_code}: {res1.text}"

    # Second promotion should fail with 409
    res2 = client.post(
        f"/api/rmos/runs/{run_id}/advisory/{advisory_id}/promote",
        headers=OPERATOR_HEADERS,
        json={"label": None, "note": None},
    )
    assert res2.status_code == 409, f"Expected 409, got {res2.status_code}: {res2.text}"


def test_promote_404_for_missing_run(client: TestClient):
    """Test that promote endpoint returns 404 for non-existent run."""
    res = client.post(
        "/api/rmos/runs/nonexistent_run_id/advisory/some_advisory/promote",
        headers=OPERATOR_HEADERS,
        json={"label": None, "note": None},
    )
    assert res.status_code == 404


def test_promote_401_without_auth(client: TestClient, run_with_advisory):
    """Test that promote endpoint returns 401 without authentication."""
    run_id = run_with_advisory["run_id"]
    advisory_id = run_with_advisory["advisory_id"]

    # No auth headers at all - should get 401 Not Authenticated
    res = client.post(
        f"/api/rmos/runs/{run_id}/advisory/{advisory_id}/promote",
        json={"label": None, "note": None},
    )
    assert res.status_code == 401, f"Expected 401, got {res.status_code}: {res.text}"


def test_promote_403_with_viewer_role(client: TestClient, run_with_advisory):
    """Test that viewer role cannot promote variants."""
    run_id = run_with_advisory["run_id"]
    advisory_id = run_with_advisory["advisory_id"]

    res = client.post(
        f"/api/rmos/runs/{run_id}/advisory/{advisory_id}/promote",
        headers=VIEWER_HEADERS,
        json={"label": None, "note": None},
    )
    assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"


def test_review_preserves_promoted_status(client: TestClient, run_with_advisory):
    """Test that updating a review after promotion preserves promoted status."""
    run_id = run_with_advisory["run_id"]
    advisory_id = run_with_advisory["advisory_id"]

    # First, promote
    promote_res = client.post(
        f"/api/rmos/runs/{run_id}/advisory/{advisory_id}/promote",
        headers=OPERATOR_HEADERS,
        json={"label": None, "note": None},
    )
    assert promote_res.status_code == 200, f"Promotion failed: {promote_res.text}"

    # Now update the review
    review_res = client.post(
        f"/api/rmos/runs/{run_id}/advisory/{advisory_id}/review",
        headers={"x-user-role": "viewer", "x-user-id": "tester"},
        json={"rating": 5, "notes": "Updated after promotion"},
    )
    assert review_res.status_code == 200, f"Review update failed: {review_res.text}"

    # Verify promoted status is preserved
    variants_res = client.get(f"/api/rmos/runs/{run_id}/advisory/variants")
    assert variants_res.status_code == 200
    data = variants_res.json()
    variants = data.get("items", [])
    promoted_variant = next(
        (v for v in variants if v.get("advisory_id") == advisory_id),
        None,
    )
    assert promoted_variant is not None, f"Variant not found: {advisory_id}"
    assert promoted_variant.get("promoted") is True


def test_variants_include_review_data(client: TestClient, run_with_advisory):
    """Test that variant list includes review data after saving a review."""
    run_id = run_with_advisory["run_id"]
    advisory_id = run_with_advisory["advisory_id"]

    # Save a review
    review_res = client.post(
        f"/api/rmos/runs/{run_id}/advisory/{advisory_id}/review",
        headers={"x-user-role": "viewer", "x-user-id": "tester"},
        json={"rating": 3, "notes": "Test notes"},
    )
    assert review_res.status_code == 200, f"Review save failed: {review_res.text}"

    # Get variants and check review data is present
    variants_res = client.get(f"/api/rmos/runs/{run_id}/advisory/variants")
    assert variants_res.status_code == 200
    data = variants_res.json()
    variants = data.get("items", [])
    reviewed_variant = next(
        (v for v in variants if v.get("advisory_id") == advisory_id),
        None,
    )
    assert reviewed_variant is not None, f"Variant not found: {advisory_id}"
    assert reviewed_variant.get("rating") == 3
    assert reviewed_variant.get("notes") == "Test notes"


def test_save_review_allows_optional_rating_and_notes(client: TestClient, run_with_advisory):
    """Test that review can be saved with optional fields."""
    run_id = run_with_advisory["run_id"]
    advisory_id = run_with_advisory["advisory_id"]

    # Notes only, no rating
    res = client.post(
        f"/api/rmos/runs/{run_id}/advisory/{advisory_id}/review",
        headers=OPERATOR_HEADERS,
        json={"notes": "Just notes, no rating"},
    )
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert data.get("rating") is None
    assert data.get("notes") == "Just notes, no rating"

    # Rating only, no notes
    res = client.post(
        f"/api/rmos/runs/{run_id}/advisory/{advisory_id}/review",
        headers=OPERATOR_HEADERS,
        json={"rating": 4},
    )
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert data.get("rating") == 4
