# services/api/tests/test_compare_history_smoke.py
from fastapi.testclient import TestClient

try:
    # Adjust import to match your app entrypoint
    from app.main import app
except ImportError:
    # Fallback if your app is under services/api/app/main.py
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from app.main import app  # type: ignore

client = TestClient(app)


def test_compare_history_smoke():
    """
    Simple smoke test: /api/compare/history should respond 200
    and return a JSON list (possibly empty).
    """
    resp = client.get("/api/compare/history")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    # optional: check a few keys if entries exist
    if data:
        first = data[0]
        assert "lane" in first
        assert "baseline_id" in first
        assert "added_paths" in first
        assert "removed_paths" in first
        # preset is optional but should not crash if missing
        _ = first.get("preset", None)


def test_risk_aggregate_endpoint_smoke():
    """
    Phase 28.3: Test new /api/compare/risk_aggregate endpoint
    """
    resp = client.get("/api/compare/risk_aggregate")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    
    # If buckets exist, validate structure
    if data:
        bucket = data[0]
        required_fields = [
            "lane", "preset", "count",
            "avg_added", "avg_removed", "avg_unchanged",
            "risk_score", "risk_label",
            "added_series", "removed_series"
        ]
        
        for field in required_fields:
            assert field in bucket, f"Missing required field: {field}"
        
        # Validate types
        assert isinstance(bucket["count"], int)
        assert isinstance(bucket["avg_added"], (int, float))
        assert isinstance(bucket["risk_score"], (int, float))
        assert isinstance(bucket["risk_label"], str)
        assert isinstance(bucket["added_series"], list)
        assert isinstance(bucket["removed_series"], list)
        
        # Validate risk label
        assert bucket["risk_label"] in ["Low", "Medium", "High", "Extreme"]
