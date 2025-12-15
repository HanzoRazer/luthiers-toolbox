"""
RMOS N10.1: LiveMonitor Drill-Down Tests

Tests for subjob event builder and heuristic engine.
"""

from app.core.live_monitor_event_builder import SubjobEventBuilder
from app.core.live_monitor_heuristics import evaluate_feed_state, evaluate_heuristic


def test_subjob_builder_basic():
    """Test basic subjob extraction from metadata."""
    entry = {
        "metadata": {
            "subjobs": [
                {
                    "subjob_type": "roughing",
                    "started_at": "2025-11-30T00:00:00",
                    "cam_events": [
                        {
                            "timestamp": "2025-11-30T00:01:00",
                            "feedrate": 800,
                            "target_feed": 1000,
                            "spindle_speed": 18000,
                            "doc": 0.3,
                            "doc_limit": 0.5
                        }
                    ]
                }
            ]
        }
    }

    builder = SubjobEventBuilder()
    res = builder.build_subjobs_from_metadata(entry)
    
    assert len(res) == 1
    assert res[0].subjob_type == "roughing"
    assert len(res[0].cam_events) == 1
    
    evt = res[0].cam_events[0]
    assert evt.feedrate == 800
    assert evt.feed_state in ("decreasing", "stable", "danger_low")
    assert evt.heuristic in ("info", "warning", "danger")


def test_subjob_builder_empty_metadata():
    """Test builder handles missing metadata gracefully."""
    entry = {}
    
    builder = SubjobEventBuilder()
    res = builder.build_subjobs_from_metadata(entry)
    
    assert res == []


def test_subjob_builder_multiple_subjobs():
    """Test builder handles multiple subjobs and events."""
    entry = {
        "metadata": {
            "subjobs": [
                {
                    "subjob_type": "roughing",
                    "started_at": "2025-11-30T00:00:00",
                    "ended_at": "2025-11-30T00:05:00",
                    "cam_events": [
                        {"feedrate": 1000, "target_feed": 1000, "doc": 0.2, "doc_limit": 0.5}
                    ]
                },
                {
                    "subjob_type": "finishing",
                    "started_at": "2025-11-30T00:05:00",
                    "cam_events": [
                        {"feedrate": 600, "target_feed": 500, "doc": 0.1, "doc_limit": 0.5}
                    ]
                }
            ]
        }
    }
    
    builder = SubjobEventBuilder()
    res = builder.build_subjobs_from_metadata(entry)
    
    assert len(res) == 2
    assert res[0].subjob_type == "roughing"
    assert res[1].subjob_type == "finishing"


def test_feed_state_stable():
    """Test feed state evaluation: stable zone."""
    assert evaluate_feed_state(1000, 1000) == "stable"
    assert evaluate_feed_state(1050, 1000) == "stable"  # +5%
    assert evaluate_feed_state(950, 1000) == "stable"   # -5%


def test_feed_state_deviation():
    """Test feed state evaluation: moderate deviation."""
    assert evaluate_feed_state(1150, 1000) == "increasing"  # +15%
    assert evaluate_feed_state(850, 1000) == "decreasing"   # -15%


def test_feed_state_danger():
    """Test feed state evaluation: danger zone."""
    assert evaluate_feed_state(1300, 1000) == "danger_high"  # +30%
    assert evaluate_feed_state(700, 1000) == "danger_low"    # -30%


def test_feed_state_zero_target():
    """Test feed state handles zero target gracefully."""
    assert evaluate_feed_state(100, 0) == "stable"


def test_heuristic_info():
    """Test heuristic evaluation: info level."""
    assert evaluate_heuristic("stable", 0.2, 0.5) == "info"


def test_heuristic_warning_doc():
    """Test heuristic evaluation: warning from high DOC."""
    assert evaluate_heuristic("stable", 0.46, 0.5) == "warning"  # 92% of limit


def test_heuristic_danger_feed():
    """Test heuristic evaluation: danger from feed state."""
    assert evaluate_heuristic("danger_low", 0.2, 0.5) == "danger"
    assert evaluate_heuristic("danger_high", 0.2, 0.5) == "danger"
