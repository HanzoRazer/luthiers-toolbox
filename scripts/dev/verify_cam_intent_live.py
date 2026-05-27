#!/usr/bin/env python3
"""
Live smoke check for H7 CAM Intent HTTP surface (post PR #46).

Hits both canonical endpoints against a running API and expects HTTP 200.
Use after deploy or local uvicorn start — avoids re-deriving port/process checks.

Usage:
  # API already listening (default http://127.0.0.1:8000)
  python scripts/dev/verify_cam_intent_live.py

  # Custom base URL (no trailing slash)
  python scripts/dev/verify_cam_intent_live.py --base-url http://127.0.0.1:8001

Env:
  CAM_INTENT_SMOKE_BASE_URL  — overrides --base-url default

Exit codes:
  0 — both endpoints returned 200
  1 — failure (connection, non-200, or wrong-path sanity check)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_BASE = os.getenv("CAM_INTENT_SMOKE_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

NORMALIZE_PATH = "/api/rmos/cam/intent/normalize"
ROUGHING_PATH = "/api/cam/roughing/gcode_intent"
LEGACY_WRONG_PATH = "/api/cam/roughing_gcode_intent"

NORMALIZE_BODY = {
    "intent": {
        "mode": "router_3axis",
        "units": "mm",
        "design": {
            "width_mm": 100.0,
            "height_mm": 50.0,
            "depth_mm": 5.0,
            "stepdown_mm": 2.0,
            "stepover_mm": 5.0,
        },
    },
    "strict": False,
}

ROUGHING_BODY = {
    "mode": "router_3axis",
    "units": "mm",
    "design": {
        "geometry": {"type": "rectangle", "width_mm": 100.0, "height_mm": 50.0},
        "width_mm": 100.0,
        "height_mm": 50.0,
        "depth_mm": 5.0,
        "stepdown_mm": 2.0,
        "stepover_mm": 5.0,
    },
    "context": {"feed_rate": 1000.0},
}


def _post(base: str, path: str, body: dict, query: str = "") -> tuple[int, str]:
    url = f"{base}{path}{query}"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, resp.read(200).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        chunk = e.read(200).decode("utf-8", errors="replace")
        return e.code, chunk


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test H7 CAM Intent live endpoints")
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE,
        help=f"API origin (default: {DEFAULT_BASE})",
    )
    parser.add_argument(
        "--skip-legacy-check",
        action="store_true",
        help="Do not assert underscore legacy path returns 404",
    )
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    print(f"CAM Intent live smoke — base URL: {base}")

    status, snippet = _post(base, NORMALIZE_PATH, NORMALIZE_BODY)
    if status != 200:
        print(f"FAIL: {NORMALIZE_PATH} -> HTTP {status}")
        print(f"  body: {snippet[:300]}")
        print("  Hint: confirm uvicorn is THIS repo on the expected port (WinError 10048 = stale process).")
        return 1
    print(f"OK:   {NORMALIZE_PATH} -> 200")

    status, snippet = _post(base, ROUGHING_PATH, ROUGHING_BODY, "?strict=false")
    if status != 200:
        print(f"FAIL: {ROUGHING_PATH} -> HTTP {status}")
        print(f"  body: {snippet[:300]}")
        return 1
    print(f"OK:   {ROUGHING_PATH} -> 200")

    if not args.skip_legacy_check:
        legacy_status, _ = _post(base, LEGACY_WRONG_PATH, ROUGHING_BODY)
        if legacy_status != 404:
            print(f"FAIL: legacy underscore path should 404, got {legacy_status}")
            return 1
        print(f"OK:   {LEGACY_WRONG_PATH} -> 404 (SDK bug path correctly unmounted)")

    print("CAM Intent live smoke passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
