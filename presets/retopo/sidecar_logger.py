"""
Sidecar logger: record adapter, preset, commit, and basic metrics to JSONL.

Integrates with adapters to provide run audit trail.

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
) -> Path:
    """Append a run record to the global sidecar log.
    
    Args:
        model_id: The model identifier
        adapter: "miq" or "qrm"
        preset: Preset name used
        metrics: Metrics dict from adapter
        commit: Git commit hash (optional)
        extra: Additional metadata (optional)
    
    Returns:
        Path to the log file
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
    
    return SIDECAR_LOG_PATH


def read_recent(n: int = 10) -> list[Dict[str, Any]]:
    """Read the N most recent log entries.
    
    Args:
        n: Number of entries to return
    
    Returns:
        List of log records (most recent first)
    """
    if not SIDECAR_LOG_PATH.exists():
        return []
    
    lines = SIDECAR_LOG_PATH.read_text(encoding="utf-8").strip().split("\n")
    entries = []
    for line in reversed(lines[-n:]):
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries
