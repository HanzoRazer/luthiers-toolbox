from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_list_presets_endpoint():
    resp = client.get("/api/art/presets")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_create_preset_endpoint():
    payload = {
        "lane": "rosette",
        "name": "Safe Default",
        "params": {"feed_xy": 800, "stepdown": 1.0},
    }
    resp = client.post("/api/art/presets", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert "id" in body
    assert body["lane"] == "rosette"
