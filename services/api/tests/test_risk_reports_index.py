"""
Test for /api/cam/risk/reports_index endpoint.

NOTE (January 2026 - Legacy Router Cleanup):
This endpoint was in cam_risk_router.py which was deleted in Phase 2+3.
The risk router proxy (app/cam/routers/risk/__init__.py) now returns None
for the reports_router import, so the endpoint is no longer registered.

Related endpoints that still exist:
- /api/cam/jobs/risk_report
- /api/cam/jobs/{job_id}/risk_timeline
- /api/compare/risk_aggregate

Frontend reference: ArtJobTimeline.vue uses this endpoint.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

_SKIP_REASON = (
    "Endpoint /api/cam/risk/reports_index was in deleted cam_risk_router.py. "
    "See January 2026 Phase 2+3 legacy cleanup. "
    "Frontend (ArtJobTimeline.vue) may need update to use /api/cam/jobs/risk_report."
)


@pytest.mark.skip(reason=_SKIP_REASON)
def test_risk_reports_index_endpoint():
    resp = client.get(
        "/api/cam/risk/reports_index",
        params=[("job_ids", "fake_job_1")],
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), dict)
