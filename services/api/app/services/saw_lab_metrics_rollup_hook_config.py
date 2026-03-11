from __future__ import annotations

import os


def is_saw_lab_metrics_rollup_hook_enabled() -> bool:
    """
    Feature flag:
      SAW_LAB_METRICS_ROLLUP_HOOK_ENABLED=true/false

    Default: false (safe until you review the persisted rollups).
    """
    v = os.getenv("SAW_LAB_METRICS_ROLLUP_HOOK_ENABLED", "false").strip().lower()
    return v in ("1", "true", "yes", "y", "on")
