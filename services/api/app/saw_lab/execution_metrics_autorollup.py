from __future__ import annotations

import os
from typing import Optional


def is_execution_metrics_autorollup_enabled() -> bool:
    """
    Feature flag to auto-write saw_batch_execution_metrics whenever a job log is written.

    Default: false (safe-by-default in prod until reviewed).
    """
    v = os.getenv("SAW_LAB_EXECUTION_METRICS_AUTOROLLUP_ENABLED", "false")
    return str(v).strip().lower() in {"1", "true", "yes", "y", "on"}


def maybe_autorollup_execution_metrics(
    *,
    batch_execution_artifact_id: Optional[str],
    session_id: Optional[str],
    batch_label: Optional[str],
    tool_kind: str = "saw",
) -> Optional[str]:
    """
    Best-effort writer. Never raises.
    Returns metrics artifact id if written, else None.
    """
    if not is_execution_metrics_autorollup_enabled():
        return None
    if not batch_execution_artifact_id:
        return None
    try:
        from .execution_metrics_rollup_service import write_execution_metrics_rollup_artifact

        return write_execution_metrics_rollup_artifact(
            batch_execution_artifact_id=batch_execution_artifact_id,
            session_id=session_id,
            batch_label=batch_label,
            tool_kind=tool_kind,
        )
    except (ImportError, RuntimeError, ValueError, TypeError, OSError):  # WP-1: narrowed from except Exception
        return None
