from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_delete_preset_endpoint():
    payload = {
        "lane": "rosette",
        "name": "Temp Delete Preset",
        "params": {"feed_xy": 900},
    }
    resp = client.post("/api/art/presets", json=payload)
    assert resp.status_code == 200
    preset_id = resp.json()["id"]

    delete_resp = client.delete(f"/api/art/presets/{preset_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["ok"] is True

    delete_again = client.delete(f"/api/art/presets/{preset_id}")
    assert delete_again.status_code == 200
    assert delete_again.json()["ok"] is False
