"""
RMOS N10.1: Event Builder for Subjob Drill-Down

Constructs deep subjob events from joblog metadata with CAM event heuristics.
"""

from __future__ import annotations
from datetime import datetime
from typing import Dict, Any, List

from ..models.rmos_subjob_event import SubjobEvent, CAMEvent
from .live_monitor_heuristics import evaluate_feed_state, evaluate_heuristic


def clamp(value, lo, hi):
    """Clamp value to range [lo, hi]."""
    return max(lo, min(hi, value))


class SubjobEventBuilder:
    """
    Constructs deep subjob events from joblog metadata for LiveMonitor drill-down.
    
    Usage:
        builder = SubjobEventBuilder()
        subjobs = builder.build_subjobs_from_metadata(job_entry)
    """

    def build_subjobs_from_metadata(self, entry: Dict[str, Any]) -> List[SubjobEvent]:
        """
        Extract subjobs and CAM events from job metadata.
        
        Expected metadata structure:
        {
            "metadata": {
                "subjobs": [
                    {
                        "subjob_type": "roughing",
                        "started_at": "2025-11-30T12:00:00",
                        "ended_at": "2025-11-30T12:05:00",
                        "cam_events": [
                            {
                                "timestamp": "2025-11-30T12:01:00",
                                "feedrate": 800,
                                "target_feed": 1000,
                                "spindle_speed": 18000,
                                "doc": 0.3,
                                "doc_limit": 0.5,
                                "message": "Optional warning"
                            }
                        ]
                    }
                ]
            }
        }
        
        Args:
            entry: Job dict from joblog store
        
        Returns:
            List of SubjobEvent objects with evaluated heuristics
        """
        meta = entry.get("metadata") or {}
        subjobs = meta.get("subjobs") or []

        results = []

        for sj in subjobs:
            cam_evts = []
            cam_raw = sj.get("cam_events") or []

            for e in cam_raw:
                feed = e.get("feedrate", 0)
                target = e.get("target_feed", feed)
                spindle = e.get("spindle_speed", 0)
                doc = e.get("doc", 0)
                doc_limit = e.get("doc_limit", 1)

                # Evaluate feed state and heuristic risk
                feed_state = evaluate_feed_state(feed, target)
                heuristic = evaluate_heuristic(feed_state, doc, doc_limit)

                cam_evts.append(
                    CAMEvent(
                        timestamp=e.get("timestamp", datetime.utcnow().isoformat()),
                        feedrate=feed,
                        spindle_speed=spindle,
                        doc=doc,
                        feed_state=feed_state,
                        heuristic=heuristic,
                        message=e.get("message"),
                    )
                )

            results.append(
                SubjobEvent(
                    subjob_type=sj.get("subjob_type", "roughing"),
                    started_at=sj.get("started_at", datetime.utcnow().isoformat()),
                    ended_at=sj.get("ended_at"),
                    cam_events=cam_evts,
                )
            )

        return results
