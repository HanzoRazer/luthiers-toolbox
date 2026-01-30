"""Quick-and-safe heat heuristics."""
from __future__ import annotations


def estimate_heat_rating(rpm: int, feed_mm_min: float, doc_mm: float) -> str:
    """Return COOL/WARM/HOT based on aggressive rpm vs feed vs depth."""
    if feed_mm_min <= 0 or rpm <= 0:
        return "UNKNOWN"

    # Too slow feed relative to spindle speed burns material fast.
    if feed_mm_min < rpm * 0.005:
        return "HOT"

    # Deep cuts stock removal -> warm.
    if doc_mm > 2.0:
        return "WARM"

    return "COOL"
