"""
Phase 28.5: Risk Bucket Export Tests

Unit tests for CSV and JSON export functionality.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_export_csv_empty(monkeypatch):
    """Test CSV export with no data."""
    from app.services import compare_risk_log
    monkeypatch.setattr(compare_risk_log, "_load_log", lambda: {"entries": []})
    
    response = client.get("/api/compare/risk_bucket_export?format=csv")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "Content-Disposition" in response.headers
    assert "risk_bucket.csv" in response.headers["Content-Disposition"]
    
    # Should have header row
    content = response.text
    assert "ts,lane,preset,job_id" in content


def test_export_csv_with_data(monkeypatch):
    """Test CSV export with sample data."""
    mock_data = {
        "entries": [
            {"ts": "2025-11-12T10:00:00", "lane": "rosette", "preset": "GRBL", "job_id": "j1", 
             "added_paths": 3, "removed_paths": 1, "unchanged_paths": 45},
            {"ts": "2025-11-12T11:00:00", "lane": "rosette", "preset": "GRBL", "job_id": "j2", 
             "added_paths": 4, "removed_paths": 2, "unchanged_paths": 44},
        ]
    }
    
    from app.services import compare_risk_log
    monkeypatch.setattr(compare_risk_log, "_load_log", lambda: mock_data)
    
    response = client.get("/api/compare/risk_bucket_export?lane=rosette&preset=GRBL&format=csv")
    
    assert response.status_code == 200
    assert "rosette_GRBL.csv" in response.headers["Content-Disposition"]
    
    content = response.text
    lines = content.strip().split("\n")
    assert len(lines) == 3  # header + 2 data rows
    assert "j1" in content
    assert "j2" in content
    assert "3" in content  # added_paths


def test_export_json_with_data(monkeypatch):
    """Test JSON export with sample data."""
    mock_data = {
        "entries": [
            {"ts": "2025-11-12T10:00:00", "lane": "adaptive", "preset": "Mach4", "job_id": "j1", 
             "added_paths": 5, "removed_paths": 2, "unchanged_paths": 40},
        ]
    }
    
    from app.services import compare_risk_log
    monkeypatch.setattr(compare_risk_log, "_load_log", lambda: mock_data)
    
    response = client.get("/api/compare/risk_bucket_export?lane=adaptive&preset=Mach4&format=json")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert "adaptive_Mach4.json" in response.headers["Content-Disposition"]
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["job_id"] == "j1"
    assert data[0]["added_paths"] == 5


def test_export_json_all_entries(monkeypatch):
    """Test JSON export with no filters (all entries)."""
    mock_data = {
        "entries": [
            {"ts": "2025-11-12T10:00:00", "lane": "rosette", "preset": "GRBL", "job_id": "j1", 
             "added_paths": 3, "removed_paths": 1, "unchanged_paths": 45},
            {"ts": "2025-11-12T11:00:00", "lane": "adaptive", "preset": "Mach4", "job_id": "j2", 
             "added_paths": 5, "removed_paths": 2, "unchanged_paths": 40},
        ]
    }
    
    from app.services import compare_risk_log
    monkeypatch.setattr(compare_risk_log, "_load_log", lambda: mock_data)
    
    response = client.get("/api/compare/risk_bucket_export?format=json")
    
    assert response.status_code == 200
    assert "risk_bucket.json" in response.headers["Content-Disposition"]
    
    data = response.json()
    assert len(data) == 2


def test_export_invalid_format():
    """Test with invalid format parameter."""
    response = client.get("/api/compare/risk_bucket_export?format=xml")
    
    assert response.status_code == 422  # Validation error


def test_export_csv_filename_sanitization(monkeypatch):
    """Test that filename is properly constructed from filters."""
    mock_data = {
        "entries": [
            {"ts": "2025-11-12T10:00:00", "lane": "pipeline", "preset": "PathPilot", "job_id": "j1", 
             "added_paths": 8, "removed_paths": 4, "unchanged_paths": 30},
        ]
    }
    
    from app.services import compare_risk_log
    monkeypatch.setattr(compare_risk_log, "_load_log", lambda: mock_data)
    
    response = client.get("/api/compare/risk_bucket_export?lane=pipeline&format=csv")
    
    assert response.status_code == 200
    assert "risk_bucket_pipeline.csv" in response.headers["Content-Disposition"]


def test_export_csv_field_escaping(monkeypatch):
    """Test that CSV fields with commas are properly escaped."""
    mock_data = {
        "entries": [
            {"ts": "2025-11-12T10:00:00", "lane": "test,lane", "preset": "GRBL", "job_id": "j1", 
             "added_paths": 1, "removed_paths": 0, "unchanged_paths": 50},
        ]
    }
    
    from app.services import compare_risk_log
    monkeypatch.setattr(compare_risk_log, "_load_log", lambda: mock_data)
    
    response = client.get("/api/compare/risk_bucket_export?format=csv")
    
    assert response.status_code == 200
    content = response.text
    # Field with comma should be quoted
    assert '"test,lane"' in content
