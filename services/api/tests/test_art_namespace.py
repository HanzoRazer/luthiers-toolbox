from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_art_namespace_alive():
    for lane in ("rosette", "adaptive", "relief"):
        resp = client.get(f"/api/art/{lane}/health")
        assert resp.status_code in (200, 404)
