"""
RMOS N10.1: Heuristic Engine for LiveMonitor

Evaluates feed state and DOC against targets to generate safe/warning/danger indicators.
"""

from __future__ import annotations


def evaluate_feed_state(feed: float, target: float) -> str:
    """
    Classify feed state based on deviation from target.
    
    Rules:
    - ±10% = stable
    - 10-20% deviation = increasing/decreasing
    - >20% deviation = danger_high/danger_low
    
    Args:
        feed: Actual feedrate (mm/min)
        target: Target feedrate (mm/min)
    
    Returns:
        Feed state: "stable", "increasing", "decreasing", "danger_low", "danger_high"
    """
    if target == 0:
        return "stable"  # Avoid division by zero
    
    ratio = (feed - target) / target

    if abs(ratio) <= 0.10:
        return "stable"

    if abs(ratio) <= 0.20:
        return "increasing" if ratio > 0 else "decreasing"

    return "danger_high" if ratio > 0 else "danger_low"


def evaluate_heuristic(feed_state: str, doc: float, doc_limit: float) -> str:
    """
    Generate heuristic risk level from feed state and DOC.
    
    Rules:
    - Any "danger" feed state → danger
    - DOC > 90% of limit → warning
    - Otherwise → info
    
    Args:
        feed_state: Result from evaluate_feed_state()
        doc: Depth of cut (mm)
        doc_limit: Maximum safe DOC (mm)
    
    Returns:
        Heuristic level: "info", "warning", "danger"
    """
    if "danger" in feed_state:
        return "danger"

    if doc_limit > 0 and doc > doc_limit * 0.9:
        return "warning"

    return "info"
