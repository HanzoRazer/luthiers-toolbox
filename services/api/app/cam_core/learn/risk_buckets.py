"""
CP-S61/62: Risk bucket classification system for CNC operations.

Categorizes risk scores (0-1) into color-coded buckets:
- Unknown (gray): No telemetry or insufficient data
- Green: Safe operation (0-0.3)
- Yellow: Moderate risk (0.3-0.6)
- Orange: High risk (0.6-0.85)
- Red: Dangerous operation (0.85-1.0)

Used by dashboard aggregation and risk actions system.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal


RiskBucketId = Literal["unknown", "green", "yellow", "orange", "red"]


@dataclass
class RiskBucket:
    """
    Risk classification bucket for CNC operations.
    
    Attributes:
        id: Unique bucket identifier (color name)
        label: Human-readable label
        description: Explanation of risk level
        min_score: Minimum risk score (inclusive)
        max_score: Maximum risk score (exclusive, except red=1.0)
    """
    id: RiskBucketId
    label: str
    description: str
    min_score: float
    max_score: float


# Standard risk bucket definitions
BUCKETS = [
    RiskBucket(
        id="unknown",
        label="Unknown",
        description="No telemetry or insufficient data to assign risk.",
        min_score=0.0,
        max_score=0.0,
    ),
    RiskBucket(
        id="green",
        label="Green",
        description="Loads and vibration well within limits. Safe operation.",
        min_score=0.0,
        max_score=0.3,
    ),
    RiskBucket(
        id="yellow",
        label="Yellow",
        description="Moderate load or occasional vibration spikes. Monitor recommended.",
        min_score=0.3,
        max_score=0.6,
    ),
    RiskBucket(
        id="orange",
        label="Orange",
        description="High load or frequent vibration. Monitor closely, consider slowing.",
        min_score=0.6,
        max_score=0.85,
    ),
    RiskBucket(
        id="red",
        label="Red",
        description="Dangerous operation. Tool breakage or poor finish likely. Slow down immediately.",
        min_score=0.85,
        max_score=1.0,
    ),
]


def classify_risk(score: float | None, has_data: bool = True) -> RiskBucket:
    """
    Classify risk score into color-coded bucket.
    
    Args:
        score: Risk score 0.0-1.0 (None = unknown)
        has_data: Whether sufficient telemetry exists
    
    Returns:
        RiskBucket (one of: unknown, green, yellow, orange, red)
    
    Examples:
        >>> classify_risk(0.15, True)
        RiskBucket(id='green', ...)
        
        >>> classify_risk(0.90, True)
        RiskBucket(id='red', ...)
        
        >>> classify_risk(None, False)
        RiskBucket(id='unknown', ...)
    """
    if not has_data or score is None:
        return BUCKETS[0]  # unknown
    
    # Clamp score to [0, 1]
    s = max(0.0, min(1.0, score))
    
    # Find matching bucket
    for bucket in BUCKETS[1:]:  # Skip unknown
        # Red bucket includes 1.0 exactly
        if bucket.id == "red":
            if s >= bucket.min_score:
                return bucket
        else:
            if bucket.min_score <= s < bucket.max_score:
                return bucket
    
    # Fallback (should never reach)
    return BUCKETS[0]
