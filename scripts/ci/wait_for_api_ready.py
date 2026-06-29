#!/usr/bin/env python3
"""Wait for an API server to become ready, with a diagnostic witness.

CI-RED-020-A. Stdlib-only readiness probe shared across CI smoke workflows.

Why this exists: the previous boot loops ended in a bare "connection refused" /
"server not up", which masked the real startup cause and made failures look like
flakes. This utility:
  - polls one or more health paths until one returns HTTP 200,
  - fails *immediately* if a supplied uvicorn PID exits before readiness
    (instead of waiting out the full timeout),
  - on failure prints the attempted URLs, the last status/exception per path,
    and the tail of the uvicorn log,
  - reports which path became ready.

No third-party deps (no requests/httpx/FastAPI/uvicorn) so it can run in any
CI step and be unit-tested without the API stack.

Usage:
    python scripts/ci/wait_for_api_ready.py \
        --base-url http://127.0.0.1:8000 \
        --paths /api/health,/health \
        --timeout-seconds 40 \
        --interval-seconds 0.5 \
        --pid-file /tmp/uvicorn_pid \
        --log-file /tmp/uvicorn.log

Exit codes:
    0 = a path returned HTTP 200 (ready)
    1 = timed out, or the uvicorn PID exited before readiness
    2 = bad invocation
"""
from __future__ import annotations

import argparse
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Callable, Dict, List, Optional, Tuple

# (status_code, error_repr) — exactly one is non-None per probe.
ProbeResult = Tuple[Optional[int], Optional[str]]


class ReadinessError(Exception):
    """Raised when readiness cannot be established (timeout or dead process)."""

    def __init__(self, reason: str, last: Dict[str, ProbeResult]):
        super().__init__(reason)
        self.reason = reason
        self.last = last


def probe(url: str, timeout: float) -> ProbeResult:
    """Return (status_code, None) on any HTTP response, or (None, error) on a
    transport failure (e.g. connection refused). A non-200 status is returned as
    a code, not an error, so the caller can keep trying other paths."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310 (local CI URL)
            return getattr(resp, "status", resp.getcode()), None
    except urllib.error.HTTPError as exc:
        return exc.code, None
    except Exception as exc:  # URLError, socket.timeout, etc.
        return None, repr(exc)


def read_pid(pid_file: Optional[str]) -> Optional[int]:
    if not pid_file:
        return None
    try:
        with open(pid_file, "r", encoding="utf-8") as handle:
            text = handle.read().strip()
        return int(text) if text else None
    except (OSError, ValueError):
        return None


def process_alive(pid: int) -> bool:
    """Best-effort liveness check. POSIX uses signal 0; Windows uses OpenProcess
    (never os.kill, which on Windows would terminate the target)."""
    if pid <= 0:
        return False
    if sys.platform == "win32":
        try:
            import ctypes

            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = ctypes.windll.kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION, False, pid
            )
            if not handle:
                return False
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        except Exception:
            return True  # can't tell — assume alive rather than false-fail
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists, owned by another user
    except OSError:
        return True
    return True


def tail_file(path: Optional[str], lines: int = 40) -> str:
    if not path:
        return "(no log file supplied)"
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            content = handle.read().splitlines()
    except OSError as exc:
        return f"(could not read log {path}: {exc})"
    if not content:
        return f"(log {path} is empty)"
    tail = content[-lines:]
    return "\n".join(tail)


def wait_for_ready(
    base_url: str,
    paths: List[str],
    timeout_seconds: float,
    interval_seconds: float,
    pid_file: Optional[str] = None,
    *,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> str:
    """Poll paths until one returns 200; return that path. Raise ReadinessError
    on dead-process or timeout. clock/sleep are injectable for tests."""
    base = base_url.rstrip("/")
    pid = read_pid(pid_file)
    max_probe_timeout = max(1.0, min(5.0, interval_seconds * 4))
    last: Dict[str, ProbeResult] = {p: (None, "not attempted") for p in paths}
    deadline = clock() + timeout_seconds

    while True:
        for path in paths:
            now = clock()
            # Honor the overall deadline between paths, and never let a single
            # probe block past it — otherwise a hung server with N paths could
            # overshoot the timeout by N * max_probe_timeout.
            if now >= deadline:
                raise ReadinessError(
                    f"timed out after {timeout_seconds}s waiting for readiness", last
                )
            probe_timeout = max(0.1, min(max_probe_timeout, deadline - now))
            status, err = probe(base + path, timeout=probe_timeout)
            last[path] = (status, err)
            if status == 200:
                return path

            # Fail fast if the server process is already gone.
            if pid is not None and not process_alive(pid):
                raise ReadinessError(
                    f"uvicorn process (pid {pid}) exited before readiness", last
                )
        sleep(interval_seconds)


def _format_failure(base_url: str, err: ReadinessError, log_file: Optional[str]) -> str:
    base = base_url.rstrip("/")
    lines = [f"API READINESS FAILED: {err.reason}", "Attempted paths:"]
    for path, (status, error) in err.last.items():
        detail = f"HTTP {status}" if status is not None else f"error {error}"
        lines.append(f"  {base + path} -> {detail}")
    lines.append("--- uvicorn log tail ---")
    lines.append(tail_file(log_file))
    lines.append("--- end log tail ---")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Wait for API readiness (CI-RED-020-A)")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--paths",
        default="/api/health,/health",
        help="Comma-separated health paths, tried in order each round.",
    )
    parser.add_argument("--timeout-seconds", type=float, default=40.0)
    parser.add_argument("--interval-seconds", type=float, default=0.5)
    parser.add_argument("--pid-file", default=None)
    parser.add_argument("--log-file", default=None)
    args = parser.parse_args(argv)

    paths = [p.strip() for p in args.paths.split(",") if p.strip()]
    if not paths:
        print("ERROR: --paths produced no usable paths", file=sys.stderr)
        return 2

    try:
        ready_path = wait_for_ready(
            args.base_url,
            paths,
            args.timeout_seconds,
            args.interval_seconds,
            pid_file=args.pid_file,
        )
    except ReadinessError as err:
        print(_format_failure(args.base_url, err, args.log_file), file=sys.stderr)
        return 1

    print(f"API ready: {args.base_url.rstrip('/') + ready_path} returned HTTP 200")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
