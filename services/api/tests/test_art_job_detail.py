from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_job_detail_endpoint_exists():
    resp = client.get("/api/art/jobs/nonexistent_123")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict)
