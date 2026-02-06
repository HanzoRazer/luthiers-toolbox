"""Tiny run-ID helper: creates a timestamped run directory.

Creates directories like out/2026-01-20T17-22-31Z_abcdef/ and returns the Path.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timezone
from pathlib import Path


def _ts() -> str:
    """ISO timestamp without colons (cross-platform friendly)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def new_run_dir(root: str = "out") -> str:
    """Create and return a new timestamped run directory.

    Args:
        root: Parent directory for run folders (default: "out")

    Returns:
        Absolute path to the newly created run directory

    Raises:
        FileExistsError: If directory already exists (extremely unlikely)
    """
    rid = f"{_ts()}_{secrets.token_hex(3)}"
    p = Path(root) / rid
    p.mkdir(parents=True, exist_ok=False)
    return str(p)
