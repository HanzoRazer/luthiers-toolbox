"""
Test for Manufacturing Candidate Queue API Endpoints.

Tests the following endpoints:
- GET /api/rmos/runs/{run_id}/manufacturing/candidates
- POST /api/rmos/runs/{run_id}/manufacturing/candidates/{candidate_id}/decision
- GET /api/rmos/runs/{run_id}/manufacturing/candidates/{candidate_id}/download-zip

RBAC:
- List: No auth required (public read)
- Decision: Requires admin/operator role
- Download: Requires any authenticated role
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


# Role headers for RBAC testing
OPERATOR_HEADERS = {"x-user-role": "operator", "x-user-id": "test_operator"}
ADMIN_HEADERS = {"x-user-role": "admin", "x-user-id": "test_admin"}
ENGINEER_HEADERS = {"x-user-role": "engineer", "x-user-id": "test_engineer"}
VIEWER_HEADERS = {"x-user-role": "viewer", "x-user-id": "test_viewer"}


@pytest.fixture
def client():
    """TestClient using app directly."""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def run_with_candidate(client: TestClient):
    """Create a run with an advisory and promote it to create a candidate."""
    import hashlib
    import base64

    # Create a run
    run_req = client.post(
        "/api/rmos/runs",
        json={
            "mode": "test_manufacturing",
            "tool_id": "saw:test_manufacturing",
            "status": "OK",
            "event_type": "test_manufacturing_candidate",
            "request_summary": {"test": "manufacturing_candidate"},
            "feasibility": {"score": 0.9},
        },
    )
    assert run_req.status_code == 200, run_req.text
    run_id = run_req.json()["run_id"]

    # Create SVG content and attach it
    svg_content = b'<svg xmlns="http://www.w3.org/2000/svg"><rect width="100" height="100" fill="green"/></svg>'
    sha256 = hashlib.sha256(svg_content).hexdigest()
    b64 = base64.b64encode(svg_content).decode()

    # Create the attachment
    att_req = client.post(
        f"/api/rmos/runs/{run_id}/attachments",
        json={
            "kind": "advisory",
            "filename": "test_candidate.svg",
            "content_type": "image/svg+xml",
            "sha256": sha256,
            "b64": b64,
        },
    )
    assert att_req.status_code == 200, f"Failed to create attachment: {att_req.text}"
    advisory_id = att_req.json().get("sha256", sha256)

    # Link as advisory
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

    # Promote to create a manufacturing candidate
    promote_req = client.post(
        f"/api/rmos/runs/{run_id}/advisory/{advisory_id}/promote",
        headers=OPERATOR_HEADERS,
        json={"label": "test_label", "note": "test promotion"},
    )
    assert promote_req.status_code == 200, f"Failed to promote: {promote_req.text}"

    data = promote_req.json()
    candidate_id = data.get("manufactured_candidate_id")
    assert candidate_id, f"No candidate_id in response: {data}"

    return {
        "run_id": run_id,
        "advisory_id": advisory_id,
        "candidate_id": candidate_id,
    }


def test_list_candidates_returns_list(client: TestClient, run_with_candidate):
    """Test that the candidates endpoint returns a list."""
    run_id = run_with_candidate["run_id"]

    res = client.get(f"/api/rmos/runs/{run_id}/manufacturing/candidates")
    assert res.status_code == 200, res.text

    data = res.json()
    assert "items" in data
    assert "count" in data
    assert "run_id" in data
    assert data["count"] >= 1
    assert len(data["items"]) >= 1


def test_list_candidates_returns_correct_candidate(client: TestClient, run_with_candidate):
    """Test that the listed candidate has correct fields."""
    run_id = run_with_candidate["run_id"]
    candidate_id = run_with_candidate["candidate_id"]

    res = client.get(f"/api/rmos/runs/{run_id}/manufacturing/candidates")
    assert res.status_code == 200, res.text

    data = res.json()
    items = data["items"]
    found = next((c for c in items if c["candidate_id"] == candidate_id), None)

    assert found is not None, f"Candidate {candidate_id} not found in {items}"
    assert found["status"] == "PROPOSED"
    assert found["advisory_id"] == run_with_candidate["advisory_id"]


def test_list_candidates_404_for_missing_run(client: TestClient):
    """Test that candidates endpoint returns 404 for non-existent run."""
    res = client.get("/api/rmos/runs/nonexistent_run_id/manufacturing/candidates")
    assert res.status_code == 404


def test_decision_accept_succeeds(client: TestClient, run_with_candidate):
    """Test that accepting a candidate works."""
    run_id = run_with_candidate["run_id"]
    candidate_id = run_with_candidate["candidate_id"]

    res = client.post(
        f"/api/rmos/runs/{run_id}/manufacturing/candidates/{candidate_id}/decision",
        headers=OPERATOR_HEADERS,
        json={"decision": "ACCEPT", "note": "Approved for production"},
    )
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"

    data = res.json()
    assert data["status"] == "ACCEPTED"
    assert data["candidate_id"] == candidate_id
    assert data["updated_by"] == "test_operator"


def test_decision_reject_succeeds(client: TestClient, run_with_candidate):
    """Test that rejecting a candidate works."""
    run_id = run_with_candidate["run_id"]
    candidate_id = run_with_candidate["candidate_id"]

    res = client.post(
        f"/api/rmos/runs/{run_id}/manufacturing/candidates/{candidate_id}/decision",
        headers=ADMIN_HEADERS,
        json={"decision": "REJECT", "note": "Does not meet quality standards"},
    )
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"

    data = res.json()
    assert data["status"] == "REJECTED"
    assert data["updated_by"] == "test_admin"


def test_decision_401_without_auth(client: TestClient, run_with_candidate):
    """Test that decision endpoint returns 401 without authentication."""
    run_id = run_with_candidate["run_id"]
    candidate_id = run_with_candidate["candidate_id"]

    res = client.post(
        f"/api/rmos/runs/{run_id}/manufacturing/candidates/{candidate_id}/decision",
        json={"decision": "ACCEPT"},
    )
    assert res.status_code == 401, f"Expected 401, got {res.status_code}: {res.text}"


def test_decision_403_for_engineer(client: TestClient, run_with_candidate):
    """Test that engineer role cannot make decisions (requires admin/operator)."""
    run_id = run_with_candidate["run_id"]
    candidate_id = run_with_candidate["candidate_id"]

    res = client.post(
        f"/api/rmos/runs/{run_id}/manufacturing/candidates/{candidate_id}/decision",
        headers=ENGINEER_HEADERS,
        json={"decision": "ACCEPT"},
    )
    assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"


def test_decision_403_for_viewer(client: TestClient, run_with_candidate):
    """Test that viewer role cannot make decisions."""
    run_id = run_with_candidate["run_id"]
    candidate_id = run_with_candidate["candidate_id"]

    res = client.post(
        f"/api/rmos/runs/{run_id}/manufacturing/candidates/{candidate_id}/decision",
        headers=VIEWER_HEADERS,
        json={"decision": "ACCEPT"},
    )
    assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"


def test_decision_404_for_missing_candidate(client: TestClient, run_with_candidate):
    """Test that decision endpoint returns 404 for non-existent candidate."""
    run_id = run_with_candidate["run_id"]

    res = client.post(
        f"/api/rmos/runs/{run_id}/manufacturing/candidates/nonexistent_candidate/decision",
        headers=OPERATOR_HEADERS,
        json={"decision": "ACCEPT"},
    )
    assert res.status_code == 404


def test_download_zip_succeeds(client: TestClient, run_with_candidate):
    """Test that downloading candidate ZIP works."""
    run_id = run_with_candidate["run_id"]
    candidate_id = run_with_candidate["candidate_id"]

    res = client.get(
        f"/api/rmos/runs/{run_id}/manufacturing/candidates/{candidate_id}/download-zip",
        headers=VIEWER_HEADERS,  # Any authenticated role can download
    )
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    assert res.headers.get("content-type") == "application/zip"
    assert "attachment" in res.headers.get("content-disposition", "")


def test_download_zip_401_without_auth(client: TestClient, run_with_candidate):
    """Test that download endpoint returns 401 without authentication."""
    run_id = run_with_candidate["run_id"]
    candidate_id = run_with_candidate["candidate_id"]

    res = client.get(
        f"/api/rmos/runs/{run_id}/manufacturing/candidates/{candidate_id}/download-zip",
    )
    assert res.status_code == 401, f"Expected 401, got {res.status_code}: {res.text}"


def test_download_zip_404_for_missing_candidate(client: TestClient, run_with_candidate):
    """Test that download endpoint returns 404 for non-existent candidate."""
    run_id = run_with_candidate["run_id"]

    res = client.get(
        f"/api/rmos/runs/{run_id}/manufacturing/candidates/nonexistent_candidate/download-zip",
        headers=VIEWER_HEADERS,
    )
    assert res.status_code == 404


def test_decision_persists_status(client: TestClient, run_with_candidate):
    """Test that decision status persists and shows in list."""
    run_id = run_with_candidate["run_id"]
    candidate_id = run_with_candidate["candidate_id"]

    # Accept the candidate
    accept_res = client.post(
        f"/api/rmos/runs/{run_id}/manufacturing/candidates/{candidate_id}/decision",
        headers=OPERATOR_HEADERS,
        json={"decision": "ACCEPT", "note": "Good to go"},
    )
    assert accept_res.status_code == 200

    # Verify status in list
    list_res = client.get(f"/api/rmos/runs/{run_id}/manufacturing/candidates")
    assert list_res.status_code == 200

    items = list_res.json()["items"]
    found = next((c for c in items if c["candidate_id"] == candidate_id), None)
    assert found is not None
    assert found["status"] == "ACCEPTED"
    assert found["note"] == "Good to go"
