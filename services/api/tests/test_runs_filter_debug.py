import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def api_client():
    from app.main import app
    with TestClient(app) as c:
        yield c


def test_runs_filter_batch_label_finds_parent_batch_artifact(api_client):
    """Test that we can filter runs list by batch_label to find the parent batch artifact."""
    from app.saw_lab.schemas_compare import SawCompareRequest, SawCompareItem

    client = api_client
    # 1) Create 2 candidates → parent batch artifact is returned
    req = SawCompareRequest(
        batch_label="pytest-batchlabel",
        session_id="sess_pytest_batchlabel",
        candidates=[
            SawCompareItem(candidate_id="c1", candidate_metadata={"rpm": 5000}),
            SawCompareItem(candidate_id="c2", candidate_metadata={"rpm": 6000}),
        ]
    )
    r = client.post("/api/saw/compare", json=req.dict())
    assert r.status_code == 200, r.text
    parent_id = r.json()["parent_artifact_id"]

    # 2) Retrieve parent by batch label (no ID knowledge)
    q = client.get("/api/rmos/runs", params={"batch_label": "pytest-batchlabel", "limit": 10})
    assert q.status_code == 200, q.text
    response_data = q.json()
    print(f"DEBUG: Response data: {response_data}")

    # Handle both list and paginated response formats
    if isinstance(response_data, dict) and "items" in response_data:
        runs = response_data["items"]
    else:
        runs = response_data

    print(f"DEBUG: Runs list: {runs}")
    print(f"DEBUG: Looking for parent_id: {parent_id}")
    print(f"DEBUG: Run IDs in list: {[it.get('run_id') for it in runs]}")

    assert isinstance(runs, list)
    assert any((it.get("run_id") == parent_id) for it in runs), f"Parent {parent_id} not found in runs list"
