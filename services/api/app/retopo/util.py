"""
Retopo utility helpers: subprocess runner with timeout, sidecar logging.
"""
from __future__ import annotations

import json
import logging
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_log = logging.getLogger(__name__)

# Default timeout for external retopo tools (seconds)
DEFAULT_TIMEOUT_SEC = 300


def run_cmd(
    args: list[str],
    *,
    timeout_sec: int = DEFAULT_TIMEOUT_SEC,
    cwd: str | Path | None = None,
) -> tuple[int, str, str, float]:
    """
    Run an external command with timeout.

    Args:
        args: Command + arguments list.
        timeout_sec: Max execution time in seconds.
        cwd: Working directory (optional).

    Returns:
        Tuple of (return_code, stdout, stderr, elapsed_sec).
        On timeout, return_code = -1 and stderr contains timeout message.
    """
    start = time.perf_counter()
    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            cwd=cwd,
        )
        elapsed = time.perf_counter() - start
        return proc.returncode, proc.stdout, proc.stderr, elapsed
    except subprocess.TimeoutExpired:
        elapsed = time.perf_counter() - start
        _log.warning("Command timed out after %.1fs: %s", elapsed, args[0])
        return -1, "", f"Timeout after {timeout_sec}s", elapsed
    except FileNotFoundError as e:
        elapsed = time.perf_counter() - start
        _log.warning("Command not found: %s", args[0])
        return -2, "", str(e), elapsed


def write_sidecar(
    out_dir: str | Path,
    adapter_name: str,
    *,
    returncode: int,
    stdout: str,
    stderr: str,
    elapsed_sec: float,
    args: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> Path:
    """
    Write a sidecar JSON log for a retopo run.

    Args:
        out_dir: Output directory.
        adapter_name: Name of the adapter (qrm, miq, etc.).
        returncode: Exit code from the subprocess.
        stdout: Captured stdout.
        stderr: Captured stderr.
        elapsed_sec: Execution time in seconds.
        args: Command arguments (optional, for debugging).
        extra: Additional metadata to include.

    Returns:
        Path to the written sidecar file.
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    sidecar = {
        "adapter": adapter_name,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "returncode": returncode,
        "elapsed_sec": round(elapsed_sec, 3),
        "success": returncode == 0,
    }

    if args:
        sidecar["args"] = args
    if stdout:
        sidecar["stdout"] = stdout[:4096]  # Truncate for safety
    if stderr:
        sidecar["stderr"] = stderr[:4096]
    if extra:
        sidecar.update(extra)

    sidecar_path = out_path / f"{adapter_name}_sidecar.json"
    sidecar_path.write_text(json.dumps(sidecar, indent=2), encoding="utf-8")
    _log.debug("Wrote sidecar: %s", sidecar_path)
    return sidecar_path
