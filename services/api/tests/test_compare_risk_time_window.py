"""
Phase 28.7: Time-Windowed Risk View Tests

Unit tests for time-window filtering on aggregation, detail, and export endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_aggregate_with_since_filter(monkeypatch):
    """Test aggregation with since timestamp filter."""
    from app.services import compare_risk_log
    mock_data = {
        "entries": [
            {"ts": "2025-11-10T10:00:00", "lane": "rosette", "preset": "GRBL", "job_id": "j1", 
             "added_paths": 3, "removed_paths": 1, "unchanged_paths": 45},
            {"ts": "2025-11-12T10:00:00", "lane": "rosette", "preset": "GRBL", "job_id": "j2", 
             "added_paths": 5, "removed_paths": 2, "unchanged_paths": 43},
            {"ts": "2025-11-14T10:00:00", "lane": "rosette", "preset": "GRBL", "job_id": "j3", 
             "added_paths": 7, "removed_paths": 3, "unchanged_paths": 41},
        ]
    }
    monkeypatch.setattr(compare_risk_log, "_load_log", lambda: mock_data)
    
    response = client.get("/api/compare/risk_aggregate?since=2025-11-12T00:00:00")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    bucket = data[0]
    assert bucket["lane"] == "rosette"
    assert bucket["preset"] == "GRBL"
    assert bucket["count"] == 2  # Only j2 and j3


def test_aggregate_with_until_filter(monkeypatch):
    """Test aggregation with until timestamp filter."""
    from app.services import compare_risk_log
    mock_data = {
        "entries": [
            {"ts": "2025-11-10T10:00:00", "lane": "rosette", "preset": "GRBL", "job_id": "j1", 
             "added_paths": 3, "removed_paths": 1, "unchanged_paths": 45},
            {"ts": "2025-11-12T10:00:00", "lane": "rosette", "preset": "GRBL", "job_id": "j2", 
             "added_paths": 5, "removed_paths": 2, "unchanged_paths": 43},
            {"ts": "2025-11-14T10:00:00", "lane": "rosette", "preset": "GRBL", "job_id": "j3", 
             "added_paths": 7, "removed_paths": 3, "unchanged_paths": 41},
        ]
    }
    monkeypatch.setattr(compare_risk_log, "_load_log", lambda: mock_data)
    
    response = client.get("/api/compare/risk_aggregate?until=2025-11-13T00:00:00")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    bucket = data[0]
    assert bucket["count"] == 2  # Only j1 and j2 (j3 excluded)


def test_aggregate_with_time_window(monkeypatch):
    """Test aggregation with both since and until filters."""
    from app.services import compare_risk_log
    mock_data = {
        "entries": [
            {"ts": "2025-11-10T10:00:00", "lane": "rosette", "preset": "GRBL", "job_id": "j1", 
             "added_paths": 3, "removed_paths": 1, "unchanged_paths": 45},
            {"ts": "2025-11-12T10:00:00", "lane": "rosette", "preset": "GRBL", "job_id": "j2", 
             "added_paths": 5, "removed_paths": 2, "unchanged_paths": 43},
            {"ts": "2025-11-14T10:00:00", "lane": "rosette", "preset": "GRBL", "job_id": "j3", 
             "added_paths": 7, "removed_paths": 3, "unchanged_paths": 41},
        ]
    }
    monkeypatch.setattr(compare_risk_log, "_load_log", lambda: mock_data)
    
    response = client.get("/api/compare/risk_aggregate?since=2025-11-11T00:00:00&until=2025-11-13T00:00:00")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    bucket = data[0]
    assert bucket["count"] == 1  # Only j2


def test_bucket_detail_with_since_filter(monkeypatch):
    """Test bucket detail with since timestamp filter."""
    from app.services import compare_risk_log
    mock_data = {
        "entries": [
            {"ts": "2025-11-10T10:00:00", "lane": "rosette", "preset": "GRBL", "job_id": "j1", 
             "added_paths": 3, "removed_paths": 1, "unchanged_paths": 45},
            {"ts": "2025-11-12T10:00:00", "lane": "rosette", "preset": "GRBL", "job_id": "j2", 
             "added_paths": 5, "removed_paths": 2, "unchanged_paths": 43},
        ]
    }
    monkeypatch.setattr(compare_risk_log, "_load_log", lambda: mock_data)
    
    response = client.get("/api/compare/risk_bucket_detail?lane=rosette&preset=GRBL&since=2025-11-12T00:00:00")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["job_id"] == "j2"


def test_bucket_detail_with_time_window(monkeypatch):
    """Test bucket detail with both since and until filters."""
    from app.services import compare_risk_log
    mock_data = {
        "entries": [
            {"ts": "2025-11-10T10:00:00", "lane": "adaptive", "preset": "Mach4", "job_id": "j1", 
             "added_paths": 5, "removed_paths": 2, "unchanged_paths": 40},
            {"ts": "2025-11-12T10:00:00", "lane": "adaptive", "preset": "Mach4", "job_id": "j2", 
             "added_paths": 7, "removed_paths": 3, "unchanged_paths": 38},
            {"ts": "2025-11-14T10:00:00", "lane": "adaptive", "preset": "Mach4", "job_id": "j3", 
             "added_paths": 9, "removed_paths": 4, "unchanged_paths": 36},
        ]
    }
    monkeypatch.setattr(compare_risk_log, "_load_log", lambda: mock_data)
    
    response = client.get("/api/compare/risk_bucket_detail?lane=adaptive&since=2025-11-11T00:00:00&until=2025-11-13T00:00:00")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["job_id"] == "j2"


def test_export_csv_with_time_window(monkeypatch):
    """Test CSV export with time-window filtering."""
    from app.services import compare_risk_log
    mock_data = {
        "entries": [
            {"ts": "2025-11-10T10:00:00", "lane": "pipeline", "preset": "PathPilot", "job_id": "j1", 
             "added_paths": 8, "removed_paths": 4, "unchanged_paths": 30},
            {"ts": "2025-11-12T10:00:00", "lane": "pipeline", "preset": "PathPilot", "job_id": "j2", 
             "added_paths": 11, "removed_paths": 6, "unchanged_paths": 28},
        ]
    }
    monkeypatch.setattr(compare_risk_log, "_load_log", lambda: mock_data)
    
    response = client.get("/api/compare/risk_bucket_export?lane=pipeline&since=2025-11-12T00:00:00&format=csv")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    content = response.text
    lines = content.strip().split("\n")
    assert len(lines) == 2  # header + 1 data row (j2 only)
    assert "j2" in content


def test_export_json_with_time_window(monkeypatch):
    """Test JSON export with time-window filtering."""
    from app.services import compare_risk_log
    mock_data = {
        "entries": [
            {"ts": "2025-11-10T10:00:00", "lane": "relief", "preset": "LinuxCNC", "job_id": "j1", 
             "added_paths": 1, "removed_paths": 0, "unchanged_paths": 52},
            {"ts": "2025-11-14T10:00:00", "lane": "relief", "preset": "LinuxCNC", "job_id": "j2", 
             "added_paths": 1, "removed_paths": 0, "unchanged_paths": 52},
        ]
    }
    monkeypatch.setattr(compare_risk_log, "_load_log", lambda: mock_data)
    
    response = client.get("/api/compare/risk_bucket_export?preset=LinuxCNC&until=2025-11-13T00:00:00&format=json")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    data = response.json()
    assert len(data) == 1
    assert data[0]["job_id"] == "j1"


def test_empty_window_returns_empty_results(monkeypatch):
    """Test that a window with no matching entries returns empty results."""
    from app.services import compare_risk_log
    mock_data = {
        "entries": [
            {"ts": "2025-11-10T10:00:00", "lane": "rosette", "preset": "GRBL", "job_id": "j1", 
             "added_paths": 3, "removed_paths": 1, "unchanged_paths": 45},
        ]
    }
    monkeypatch.setattr(compare_risk_log, "_load_log", lambda: mock_data)
    
    # Query for future dates
    response = client.get("/api/compare/risk_aggregate?since=2025-12-01T00:00:00")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0
