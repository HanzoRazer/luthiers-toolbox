"""
Stage Timer Utility
===================

Shared timing infrastructure for measuring pipeline stages.
Used across photo vectorizer, blueprint vectorizer, and cleaner.

Usage:
    timer = StageTimer()

    with timer.stage("image_load"):
        img = load_image(path)

    with timer.stage("edge_detect"):
        edges = detect_edges(img)

    # Get results
    timings = timer.get_timings()  # {"image_load_ms": 420.5, "edge_detect_ms": 1823.1}
    total = timer.total_ms         # 2243.6

Author: Production Shop
"""

from __future__ import annotations

import logging
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Dict, Generator, Optional

logger = logging.getLogger(__name__)


def is_debug_enabled() -> bool:
    """Check if vectorizer debug mode is enabled via environment."""
    return os.environ.get("VECTORIZER_DEBUG", "").lower() in ("1", "true", "yes")


@dataclass
class StageTimer:
    """
    Collects timing measurements for pipeline stages.

    Thread-safe for sequential stage execution within a single request.
    """

    _stages: Dict[str, float] = field(default_factory=dict)
    _start_time: float = field(default_factory=time.perf_counter)
    _current_stage: Optional[str] = None
    _current_start: float = 0.0

    @contextmanager
    def stage(self, name: str) -> Generator[None, None, None]:
        """
        Context manager to time a named stage.

        Args:
            name: Stage identifier (e.g., "image_load", "edge_detect")

        Yields:
            None - execute stage code in the with block
        """
        start = time.perf_counter()
        self._current_stage = name
        self._current_start = start

        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self._stages[f"{name}_ms"] = round(elapsed_ms, 1)
            self._current_stage = None
            logger.debug(f"STAGE_TIMER | {name} | {elapsed_ms:.1f}ms")

    def mark(self, name: str, elapsed_ms: float) -> None:
        """
        Manually record a stage timing (for stages measured elsewhere).

        Args:
            name: Stage identifier
            elapsed_ms: Duration in milliseconds
        """
        self._stages[f"{name}_ms"] = round(elapsed_ms, 1)

    def get_timings(self) -> Dict[str, float]:
        """Return all recorded stage timings."""
        return dict(self._stages)

    @property
    def total_ms(self) -> float:
        """Total elapsed time since timer creation."""
        return round((time.perf_counter() - self._start_time) * 1000, 1)

    def log_summary(self, prefix: str = "TIMER") -> None:
        """Log a summary of all stages."""
        stages_str = " | ".join(f"{k}={v}" for k, v in self._stages.items())
        logger.info(f"{prefix} | total={self.total_ms}ms | {stages_str}")


@dataclass
class DebugInfo:
    """
    Debug information container for vectorizer responses.

    Only populated when debug mode is enabled.
    """

    stage_timings: Dict[str, float] = field(default_factory=dict)
    candidates: list = field(default_factory=list)
    best_ownership_score: float = 0.0
    ownership_threshold: float = 0.0
    candidate_count: int = 0
    rejection_reasons: list = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON response."""
        return {
            "stage_timings": self.stage_timings,
            "candidates": self.candidates,
            "best_ownership_score": self.best_ownership_score,
            "ownership_threshold": self.ownership_threshold,
            "candidate_count": self.candidate_count,
            "rejection_reasons": self.rejection_reasons,
        }

    @classmethod
    def empty(cls) -> "DebugInfo":
        """Return empty debug info (for non-debug responses)."""
        return cls()
