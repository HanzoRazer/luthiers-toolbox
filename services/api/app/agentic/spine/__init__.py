"""
Agentic Spine — Core moment detection, policy, and replay infrastructure.

This module implements the M1 Advisory Mode decision pipeline:
- moments.py: Detect user moments from event streams
- policy.py: Decide what directive to emit based on moment + UWSM
- uwsm_update.py: Update user working style model based on feedback
- replay.py: Replay harness for determinism testing
"""

from .moments import detect_moments
from .policy import decide
from .uwsm_update import update_uwsm
from .replay import load_events, run_shadow_replay, ReplayConfig

__all__ = [
    "detect_moments",
    "decide",
    "update_uwsm",
    "load_events",
    "run_shadow_replay",
    "ReplayConfig",
]
