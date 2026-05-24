"""
Replay and Regression Classifications.

Sprint: MRP-5O
Status: PROTOTYPE

Defines status and severity enums for replay execution
and artifact regression comparison.
"""

from enum import Enum


class ReplayExecutionStatus(str, Enum):
    """Status of a replay execution attempt (MRP-5O)."""

    REPLAYED = "REPLAYED"
    NON_REPLAYABLE = "NON_REPLAYABLE"
    INVALID_BUNDLE = "INVALID_BUNDLE"
    REJECTED_ADMISSION = "REJECTED_ADMISSION"


class RegressionStatus(str, Enum):
    """Status of artifact regression comparison."""

    MATCH = "MATCH"
    DIVERGED = "DIVERGED"
    BASELINE_MISSING = "BASELINE_MISSING"
    INVALID = "INVALID"


class DivergenceSeverity(str, Enum):
    """Severity of detected divergence."""

    NONE = "NONE"
    WARNING = "WARNING"
    BLOCKING = "BLOCKING"
