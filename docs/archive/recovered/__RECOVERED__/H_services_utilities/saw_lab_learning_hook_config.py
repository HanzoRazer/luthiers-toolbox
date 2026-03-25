from __future__ import annotations

import os


def is_saw_lab_learning_hook_enabled() -> bool:
    """
    Feature flag for emitting learning events from operator job logs.

    Default: OFF
      - conservative for production rollout
      - safe to enable in sandbox/dev and in targeted CI tests

    Env var:
      SAW_LAB_LEARNING_HOOK_ENABLED=true/false
    """
    v = os.getenv("SAW_LAB_LEARNING_HOOK_ENABLED", "false").strip().lower()
    return v in ("1", "true", "yes", "y", "on")
