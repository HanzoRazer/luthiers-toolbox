"""
test_compare_risk_aggregate.py

Unit tests for compare risk aggregation service (Phase 28.3).
Tests the pure function aggregate_compare_history() with mock data.
"""

import pytest
from app.services.compare_risk_aggregate import aggregate_compare_history


def test_aggregate_empty_entries():
    """Test aggregation with empty entries list"""
    result = aggregate_compare_history(entries=[])
    assert result == []


def test_aggregate_single_entry():
    """Test aggregation with single entry"""
    entries = [
        {
            "lane": "rosette",
            "preset": "A1",
            "added_paths": 5,
            "removed_paths": 3,
            "unchanged_paths": 10,
            "timestamp": "2025-01-15T10:00:00Z"
        }
    ]
    
    result = aggregate_compare_history(entries=entries)
    
    assert len(result) == 1
    bucket = result[0]
    assert bucket["lane"] == "rosette"
    assert bucket["preset"] == "A1"
    assert bucket["count"] == 1
    assert bucket["avg_added"] == 5.0
    assert bucket["avg_removed"] == 3.0
    assert bucket["avg_unchanged"] == 10.0
    assert bucket["risk_score"] == pytest.approx(6.5)  # 5*0.7 + 3*1.0
    assert bucket["risk_label"] == "Extreme"
    assert bucket["added_series"] == [5]
    assert bucket["removed_series"] == [3]


def test_aggregate_multiple_entries_same_bucket():
    """Test aggregation with multiple entries for same (lane, preset)"""
    entries = [
        {
            "lane": "rosette",
            "preset": "A1",
            "added_paths": 4,
            "removed_paths": 2,
            "unchanged_paths": 10,
            "timestamp": "2025-01-15T10:00:00Z"
        },
        {
            "lane": "rosette",
            "preset": "A1",
            "added_paths": 6,
            "removed_paths": 4,
            "unchanged_paths": 12,
            "timestamp": "2025-01-15T11:00:00Z"
        },
        {
            "lane": "rosette",
            "preset": "A1",
            "added_paths": 2,
            "removed_paths": 1,
            "unchanged_paths": 8,
            "timestamp": "2025-01-15T12:00:00Z"
        }
    ]
    
    result = aggregate_compare_history(entries=entries)
    
    assert len(result) == 1
    bucket = result[0]
    assert bucket["count"] == 3
    assert bucket["avg_added"] == pytest.approx(4.0)  # (4+6+2)/3
    assert bucket["avg_removed"] == pytest.approx(2.333, rel=1e-2)  # (2+4+1)/3
    assert bucket["avg_unchanged"] == pytest.approx(10.0)  # (10+12+8)/3
    assert bucket["added_series"] == [4, 6, 2]
    assert bucket["removed_series"] == [2, 4, 1]


def test_aggregate_multiple_buckets():
    """Test aggregation with different (lane, preset) combinations"""
    entries = [
        {
            "lane": "rosette",
            "preset": "A1",
            "added_paths": 5,
            "removed_paths": 3,
            "unchanged_paths": 10,
            "timestamp": "2025-01-15T10:00:00Z"
        },
        {
            "lane": "rosette",
            "preset": "B2",
            "added_paths": 2,
            "removed_paths": 1,
            "unchanged_paths": 8,
            "timestamp": "2025-01-15T11:00:00Z"
        },
        {
            "lane": "adaptive",
            "preset": "A1",
            "added_paths": 8,
            "removed_paths": 6,
            "unchanged_paths": 15,
            "timestamp": "2025-01-15T12:00:00Z"
        }
    ]
    
    result = aggregate_compare_history(entries=entries)
    
    assert len(result) == 3
    
    # Find specific buckets (order not guaranteed)
    rosette_a1 = next(b for b in result if b["lane"] == "rosette" and b["preset"] == "A1")
    rosette_b2 = next(b for b in result if b["lane"] == "rosette" and b["preset"] == "B2")
    adaptive_a1 = next(b for b in result if b["lane"] == "adaptive" and b["preset"] == "A1")
    
    assert rosette_a1["count"] == 1
    assert rosette_a1["avg_added"] == 5.0
    
    assert rosette_b2["count"] == 1
    assert rosette_b2["avg_added"] == 2.0
    
    assert adaptive_a1["count"] == 1
    assert adaptive_a1["avg_added"] == 8.0


def test_aggregate_risk_labels():
    """Test risk label assignment based on score thresholds"""
    entries = [
        {
            "lane": "rosette",
            "preset": "Low",
            "added_paths": 0,
            "removed_paths": 0,
            "unchanged_paths": 10,
            "timestamp": "2025-01-15T10:00:00Z"
        },
        {
            "lane": "rosette",
            "preset": "Medium",
            "added_paths": 1,
            "removed_paths": 1,
            "unchanged_paths": 10,
            "timestamp": "2025-01-15T10:00:00Z"
        },
        {
            "lane": "rosette",
            "preset": "High",
            "added_paths": 4,
            "removed_paths": 2,
            "unchanged_paths": 10,
            "timestamp": "2025-01-15T10:00:00Z"
        },
        {
            "lane": "rosette",
            "preset": "Extreme",
            "added_paths": 6,
            "removed_paths": 4,
            "unchanged_paths": 10,
            "timestamp": "2025-01-15T10:00:00Z"
        }
    ]
    
    result = aggregate_compare_history(entries=entries)
    
    low_bucket = next(b for b in result if b["preset"] == "Low")
    assert low_bucket["risk_label"] == "Low"
    assert low_bucket["risk_score"] < 1.0
    
    medium_bucket = next(b for b in result if b["preset"] == "Medium")
    assert medium_bucket["risk_label"] == "Medium"
    assert 1.0 <= medium_bucket["risk_score"] < 3.0
    
    high_bucket = next(b for b in result if b["preset"] == "High")
    assert high_bucket["risk_label"] == "High"
    assert 3.0 <= high_bucket["risk_score"] < 6.0
    
    extreme_bucket = next(b for b in result if b["preset"] == "Extreme")
    assert extreme_bucket["risk_label"] == "Extreme"
    assert extreme_bucket["risk_score"] >= 6.0


def test_aggregate_chronological_order():
    """Test that series arrays preserve chronological order"""
    entries = [
        {
            "lane": "rosette",
            "preset": "A1",
            "added_paths": 8,
            "removed_paths": 4,
            "unchanged_paths": 10,
            "ts": "2025-01-15T12:00:00Z"  # Latest
        },
        {
            "lane": "rosette",
            "preset": "A1",
            "added_paths": 4,
            "removed_paths": 2,
            "unchanged_paths": 10,
            "ts": "2025-01-15T10:00:00Z"  # Earliest
        },
        {
            "lane": "rosette",
            "preset": "A1",
            "added_paths": 6,
            "removed_paths": 3,
            "unchanged_paths": 10,
            "ts": "2025-01-15T11:00:00Z"  # Middle
        }
    ]
    
    result = aggregate_compare_history(entries=entries)
    
    bucket = result[0]
    # Should be sorted: 10:00 -> 11:00 -> 12:00
    assert bucket["added_series"] == [4, 6, 8]
    assert bucket["removed_series"] == [2, 3, 4]


def test_aggregate_handles_null_preset():
    """Test graceful handling of null/empty preset"""
    entries = [
        {
            "lane": "rosette",
            "preset": None,
            "added_paths": 5,
            "removed_paths": 3,
            "unchanged_paths": 10,
            "timestamp": "2025-01-15T10:00:00Z"
        },
        {
            "lane": "rosette",
            "preset": "",
            "added_paths": 2,
            "removed_paths": 1,
            "unchanged_paths": 8,
            "timestamp": "2025-01-15T11:00:00Z"
        }
    ]
    
    result = aggregate_compare_history(entries=entries)
    
    # Both should be treated as "(none)" bucket
    assert len(result) == 1
    bucket = result[0]
    assert bucket["preset"] == "(none)"
    assert bucket["count"] == 2


def test_aggregate_zero_averages():
    """Test handling of all-zero metrics"""
    entries = [
        {
            "lane": "rosette",
            "preset": "A1",
            "added_paths": 0,
            "removed_paths": 0,
            "unchanged_paths": 0,
            "timestamp": "2025-01-15T10:00:00Z"
        }
    ]
    
    result = aggregate_compare_history(entries=entries)
    
    bucket = result[0]
    assert bucket["avg_added"] == 0.0
    assert bucket["avg_removed"] == 0.0
    assert bucket["avg_unchanged"] == 0.0
    assert bucket["risk_score"] == 0.0
    assert bucket["risk_label"] == "Low"


def test_aggregate_sorting_by_lane_preset():
    """Test that buckets are sorted by (lane, preset)"""
    entries = [
        {"lane": "relief", "preset": "A", "added_paths": 1, "removed_paths": 1, "unchanged_paths": 1, "timestamp": "2025-01-15T10:00:00Z"},
        {"lane": "adaptive", "preset": "B", "added_paths": 1, "removed_paths": 1, "unchanged_paths": 1, "timestamp": "2025-01-15T10:00:00Z"},
        {"lane": "rosette", "preset": "C", "added_paths": 1, "removed_paths": 1, "unchanged_paths": 1, "timestamp": "2025-01-15T10:00:00Z"},
        {"lane": "adaptive", "preset": "A", "added_paths": 1, "removed_paths": 1, "unchanged_paths": 1, "timestamp": "2025-01-15T10:00:00Z"}
    ]
    
    result = aggregate_compare_history(entries=entries)
    
    # Check sorting: should be sorted by (lane, preset)
    lanes_presets = [(b["lane"], b["preset"]) for b in result]
    sorted_lanes_presets = sorted(lanes_presets)
    assert lanes_presets == sorted_lanes_presets
