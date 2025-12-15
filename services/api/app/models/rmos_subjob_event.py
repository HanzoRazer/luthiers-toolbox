"""
RMOS N10.1: Subjob Event Models

Pydantic models for LiveMonitor drill-down with subjobs, CAM events, and heuristics.
"""

from __future__ import annotations
from typing import Optional, Literal, List
from pydantic import BaseModel


SubjobType = Literal[
    "roughing",
    "profiling",
    "finishing",
    "cleanup",
    "infeed",
    "outfeed"
]

FeedState = Literal[
    "stable",
    "increasing",
    "decreasing",
    "danger_low",
    "danger_high"
]

HeuristicLevel = Literal[
    "info",
    "warning",
    "danger"
]


class CAMEvent(BaseModel):
    """
    Individual CAM event within a subjob.
    
    Captures feed/spindle/DOC state with heuristic risk evaluation.
    """
    timestamp: str
    feedrate: float
    spindle_speed: float
    doc: float
    feed_state: FeedState
    heuristic: HeuristicLevel
    message: Optional[str] = None


class SubjobEvent(BaseModel):
    """
    A subjob phase within a larger job (e.g., roughing → profiling → finishing).
    
    Contains timeline and associated CAM events with heuristics.
    """
    subjob_type: SubjobType
    started_at: str
    ended_at: Optional[str] = None
    cam_events: List[CAMEvent] = []
