from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_risk_reports_index_endpoint():
    resp = client.get(
        "/api/cam/risk/reports_index",
        params=[("job_ids", "fake_job_1")],
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), dict)
