# services/api/app/ai_context_adapter/providers/run_summary.py
"""Run summary provider for AI context envelope."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict


def utc_now_iso() -> str:
    """Get current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def get_run_summary(run: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract schema-compatible run_summary from a ToolBox run dict.

    Input: a ToolBox run dict (already fetched by caller).
    Output: schema-compatible run_summary object.

    Note: This intentionally excludes toolpaths, G-code, and other
    manufacturing-sensitive data.
    """
    return {
        "run_id": str(run.get("run_id") or run.get("id") or "unknown"),
        "status": str(run.get("status") or "unknown"),
        "event_type": str(run.get("event_type") or "unknown"),
        "created_at_utc": str(run.get("created_at_utc") or utc_now_iso()),
        "notes": str(run.get("notes") or "")[:4000],
    }
