"""
Test suite for /api/cam/compare/diff endpoint (CompareLab B22)

Covers:
- Successful diff between two known job IDs
- 404 error for missing job IDs
- Structure and type checks for diff response
"""

import pytest
from fastapi.testclient import TestClient

try:
    from app.main import app
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from app.main import app  # type: ignore

client = TestClient(app)

# You may need to adjust these job IDs to match real test data in your environment
KNOWN_BASELINE_ID = "test-job-001"
KNOWN_COMPARE_ID = "test-job-002"
MISSING_ID = "no_such_job_999"

def test_compare_diff_success():
    """Test successful diff between two known jobs."""
    resp = client.get(f"/api/cam/compare/diff?baseline={KNOWN_BASELINE_ID}&compare={KNOWN_COMPARE_ID}")
    assert resp.status_code == 200
    data = resp.json()
    # Check top-level keys
    assert "baseline" in data
    assert "compare" in data
    assert "delta" in data
    # Check stats structure (stats are nested inside baseline/compare)
    for key in ["length", "time", "retracts"]:
        assert key in data["baseline"]["stats"], f"Missing {key} in baseline stats"
        assert key in data["compare"]["stats"], f"Missing {key} in compare stats"
        assert key in data["delta"], f"Missing {key} in delta"
    # Types
    assert isinstance(data["baseline"], dict)
    assert isinstance(data["compare"], dict)
    assert isinstance(data["delta"], dict)

def test_compare_diff_missing_job():
    """Test 404 error when one or both job IDs are missing."""
    resp = client.get(f"/api/cam/compare/diff?baseline={MISSING_ID}&compare={KNOWN_COMPARE_ID}")
    assert resp.status_code == 404
    resp = client.get(f"/api/cam/compare/diff?baseline={KNOWN_BASELINE_ID}&compare={MISSING_ID}")
    assert resp.status_code == 404
    resp = client.get(f"/api/cam/compare/diff?baseline={MISSING_ID}&compare={MISSING_ID}")
    assert resp.status_code == 404
