"""
Phase 28.4: Risk Bucket Detail Service Tests

Unit tests for get_bucket_detail() function.
"""

import pytest
from app.services.compare_risk_bucket_detail import get_bucket_detail


def test_get_bucket_detail_empty(monkeypatch):
    """Test with no entries."""
    from app.services import compare_risk_log
    monkeypatch.setattr(compare_risk_log, "_load_log", lambda: {"entries": []})
    
    result = get_bucket_detail(lane="nonexistent", preset="fake")
    assert isinstance(result, list)
    assert len(result) == 0


def test_get_bucket_detail_filter_by_lane(monkeypatch):
    """Test filtering by lane only."""
    mock_entries = [
        {"ts": "2025-11-12T10:00:00", "lane": "rosette", "preset": "GRBL", "job_id": "j1", "added_paths": 3, "removed_paths": 1, "unchanged_paths": 45},
        {"ts": "2025-11-12T11:00:00", "lane": "rosette", "preset": "Mach4", "job_id": "j2", "added_paths": 2, "removed_paths": 0, "unchanged_paths": 48},
        {"ts": "2025-11-12T12:00:00", "lane": "adaptive", "preset": "GRBL", "job_id": "j3", "added_paths": 5, "removed_paths": 2, "unchanged_paths": 40},
    ]
    
    from app.services import compare_risk_log
    monkeypatch.setattr(compare_risk_log, "_load_log", lambda: {"entries": mock_entries})
    
    result = get_bucket_detail(lane="rosette")
    
    assert len(result) == 2
    assert all(e["lane"] == "rosette" for e in result)
    assert result[0]["job_id"] == "j1"
    assert result[1]["job_id"] == "j2"


def test_get_bucket_detail_filter_by_preset(monkeypatch):
    """Test filtering by preset only."""
    mock_entries = [
        {"ts": "2025-11-12T10:00:00", "lane": "rosette", "preset": "GRBL", "job_id": "j1", "added_paths": 3, "removed_paths": 1, "unchanged_paths": 45},
        {"ts": "2025-11-12T11:00:00", "lane": "adaptive", "preset": "GRBL", "job_id": "j2", "added_paths": 5, "removed_paths": 2, "unchanged_paths": 40},
        {"ts": "2025-11-12T12:00:00", "lane": "rosette", "preset": "Mach4", "job_id": "j3", "added_paths": 2, "removed_paths": 0, "unchanged_paths": 48},
    ]
    
    from app.services import compare_risk_log
    monkeypatch.setattr(compare_risk_log, "_load_log", lambda: {"entries": mock_entries})
    
    result = get_bucket_detail(preset="GRBL")
    
    assert len(result) == 2
    assert all(e["preset"] == "GRBL" for e in result)
    assert result[0]["job_id"] == "j1"
    assert result[1]["job_id"] == "j2"


def test_get_bucket_detail_filter_by_both(monkeypatch):
    """Test filtering by both lane and preset."""
    mock_entries = [
        {"ts": "2025-11-12T10:00:00", "lane": "rosette", "preset": "GRBL", "job_id": "j1", "added_paths": 3, "removed_paths": 1, "unchanged_paths": 45},
        {"ts": "2025-11-12T11:00:00", "lane": "rosette", "preset": "GRBL", "job_id": "j2", "added_paths": 4, "removed_paths": 2, "unchanged_paths": 44},
        {"ts": "2025-11-12T12:00:00", "lane": "rosette", "preset": "Mach4", "job_id": "j3", "added_paths": 2, "removed_paths": 0, "unchanged_paths": 48},
        {"ts": "2025-11-12T13:00:00", "lane": "adaptive", "preset": "GRBL", "job_id": "j4", "added_paths": 5, "removed_paths": 2, "unchanged_paths": 40},
    ]
    
    from app.services import compare_risk_log
    monkeypatch.setattr(compare_risk_log, "_load_log", lambda: {"entries": mock_entries})
    
    result = get_bucket_detail(lane="rosette", preset="GRBL")
    
    assert len(result) == 2
    assert all(e["lane"] == "rosette" and e["preset"] == "GRBL" for e in result)
    assert result[0]["job_id"] == "j1"
    assert result[1]["job_id"] == "j2"


def test_get_bucket_detail_no_filters(monkeypatch):
    """Test with no filters (returns all entries)."""
    mock_entries = [
        {"ts": "2025-11-12T10:00:00", "lane": "rosette", "preset": "GRBL", "job_id": "j1", "added_paths": 3, "removed_paths": 1, "unchanged_paths": 45},
        {"ts": "2025-11-12T11:00:00", "lane": "adaptive", "preset": "Mach4", "job_id": "j2", "added_paths": 5, "removed_paths": 2, "unchanged_paths": 40},
    ]
    
    from app.services import compare_risk_log
    monkeypatch.setattr(compare_risk_log, "_load_log", lambda: {"entries": mock_entries})
    
    result = get_bucket_detail()
    
    assert len(result) == 2


def test_get_bucket_detail_chronological_sort(monkeypatch):
    """Test that entries are sorted chronologically."""
    mock_entries = [
        {"ts": "2025-11-12T12:00:00", "lane": "rosette", "preset": "GRBL", "job_id": "j3", "added_paths": 5, "removed_paths": 3, "unchanged_paths": 43},
        {"ts": "2025-11-12T10:00:00", "lane": "rosette", "preset": "GRBL", "job_id": "j1", "added_paths": 3, "removed_paths": 1, "unchanged_paths": 45},
        {"ts": "2025-11-12T11:00:00", "lane": "rosette", "preset": "GRBL", "job_id": "j2", "added_paths": 4, "removed_paths": 2, "unchanged_paths": 44},
    ]
    
    from app.services import compare_risk_log
    monkeypatch.setattr(compare_risk_log, "_load_log", lambda: {"entries": mock_entries})
    
    result = get_bucket_detail(lane="rosette", preset="GRBL")
    
    assert len(result) == 3
    assert result[0]["job_id"] == "j1"  # 10:00
    assert result[1]["job_id"] == "j2"  # 11:00
    assert result[2]["job_id"] == "j3"  # 12:00


def test_get_bucket_detail_empty_preset(monkeypatch):
    """Test filtering with empty preset string."""
    mock_entries = [
        {"ts": "2025-11-12T10:00:00", "lane": "rosette", "preset": "", "job_id": "j1", "added_paths": 1, "removed_paths": 0, "unchanged_paths": 50},
        {"ts": "2025-11-12T11:00:00", "lane": "rosette", "preset": "GRBL", "job_id": "j2", "added_paths": 3, "removed_paths": 1, "unchanged_paths": 45},
    ]
    
    from app.services import compare_risk_log
    monkeypatch.setattr(compare_risk_log, "_load_log", lambda: {"entries": mock_entries})
    
    # Filter by empty preset
    result = get_bucket_detail(lane="rosette", preset="")
    
    assert len(result) == 1
    assert result[0]["job_id"] == "j1"
    assert result[0]["preset"] == ""


def test_get_bucket_detail_null_preset(monkeypatch):
    """Test filtering with None preset (should match empty presets)."""
    mock_entries = [
        {"ts": "2025-11-12T10:00:00", "lane": "rosette", "preset": "", "job_id": "j1", "added_paths": 1, "removed_paths": 0, "unchanged_paths": 50},
        {"ts": "2025-11-12T11:00:00", "lane": "rosette", "preset": "GRBL", "job_id": "j2", "added_paths": 3, "removed_paths": 1, "unchanged_paths": 45},
    ]
    
    from app.services import compare_risk_log
    monkeypatch.setattr(compare_risk_log, "_load_log", lambda: {"entries": mock_entries})
    
    # Filter by None preset (should match empty preset entries)
    result = get_bucket_detail(lane="rosette", preset=None)
    
    # When preset=None, should return all rosette entries (no preset filtering)
    assert len(result) == 2
