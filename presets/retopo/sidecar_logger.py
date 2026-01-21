"""
Sidecar logger: record adapter, preset, commit, and basic metrics to a JSONL.

Scaffold only; integrate after real adapters are wired.

Usage:
    from presets.retopo.sidecar_logger import log_run
    log_run(model_id="...", adapter="qrm", preset="qrm-default", metrics={...})
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


SIDECAR_LOG_PATH = Path("logs/retopo_sidecar.jsonl")


def log_run(
    model_id: str,
    adapter: str,
    preset: str,
    metrics: Dict[str, Any],
    commit: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None
) -> None:
    """Append a run record to the sidecar log.
    
    Args:
        model_id: The model identifier
        adapter: "miq" or "qrm"
        preset: Preset name used
        metrics: Metrics dict from adapter
        commit: Git commit hash (optional)
        extra: Additional metadata (optional)
    """
    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "model_id": model_id,
        "adapter": adapter,
        "preset": preset,
        "metrics": metrics,
        "commit": commit,
        **(extra or {})
    }
    
    SIDECAR_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SIDECAR_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
