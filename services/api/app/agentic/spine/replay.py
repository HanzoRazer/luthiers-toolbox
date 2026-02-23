"""
Agentic replay module stub.

This is a placeholder module - the full implementation is planned
but not yet available. Functions raise NotImplementedError to
indicate they are not yet implemented.
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, List, Dict


@dataclass
class ReplayConfig:
    """Configuration for replay sessions."""
    shadow_mode: bool = True
    strict_order: bool = True


def load_events(path: Path) -> List[Dict[str, Any]]:
    """Load events from a JSONL file.
    
    Not implemented - this is a placeholder.
    """
    raise NotImplementedError("agentic.spine.replay.load_events is not yet implemented")


def run_shadow_replay(events: List[Dict[str, Any]], config: ReplayConfig = None) -> Iterator[Any]:
    """Run shadow replay on a sequence of events.
    
    Not implemented - this is a placeholder.
    """
    raise NotImplementedError("agentic.spine.replay.run_shadow_replay is not yet implemented")


def group_by_session(events: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group events by session ID.
    
    Not implemented - this is a placeholder.
    """
    raise NotImplementedError("agentic.spine.replay.group_by_session is not yet implemented")


def select_moment_with_grace(moments: List[Any], grace_period_ms: int = 1000) -> Any:
    """Select the appropriate moment given a grace period.
    
    Not implemented - this is a placeholder.
    """
    raise NotImplementedError("agentic.spine.replay.select_moment_with_grace is not yet implemented")
