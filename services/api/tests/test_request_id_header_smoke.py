from fastapi.testclient import TestClient

from app.main import app
from .conftest import assert_request_id_header


def _first_working_path(client: TestClient) -> str:
    """
    Find a stable "health-ish" endpoint without knowing the repo's exact choice.
    We try a small list of common endpoints and pick the first that isn't 404.
    """
    candidates = [
        "/api/health",
        "/health",
        "/api/rmos/health",
        "/api/vision/health",
        "/api/ai/health",
    ]
    for path in candidates:
        r = client.get(path)
        if r.status_code != 404:
            return path
    # If none exist, this repo needs a canonical health route; fail loudly.
    raise AssertionError(
        "No health endpoint found. Add one of: "
        + ", ".join(candidates)
        + " (recommended: /api/health)."
    )


def test_request_id_header_present_on_health():
    """
    Enterprise-safe smoke: confirms middleware always sets X-Request-Id.
    """
    client = TestClient(app)
    path = _first_working_path(client)
    resp = client.get(path)
    assert resp.status_code < 500
    assert_request_id_header(resp)
