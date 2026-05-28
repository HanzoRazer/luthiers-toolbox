#!/usr/bin/env python3
"""
RMOS ↔ CAM domain boundary check — Makefile / FENCE_REGISTRY entry point.

Makefile step [2/7] and FENCE_REGISTRY `rmos_cam_boundary` reference this module.
Delegates to fence_runner for profile enforcement.

Usage:
  cd services/api
  python -m app.ci.domain_boundaries --profile rmos_cam
"""

from __future__ import annotations

import argparse
import sys

from app.ci.fence_runner import FENCE_REGISTRY_PATH, FenceRunner

PROFILE_ALIASES = {
    "rmos_cam": "rmos_cam_boundary",
    "rmos_cam_boundary": "rmos_cam_boundary",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.ci.domain_boundaries",
        description="RMOS ↔ CAM domain boundary enforcement",
    )
    parser.add_argument(
        "--profile",
        default="rmos_cam",
        help="Fence profile alias (default: rmos_cam → rmos_cam_boundary)",
    )
    args = parser.parse_args(argv)

    profile = PROFILE_ALIASES.get(args.profile, args.profile)
    runner = FenceRunner(FENCE_REGISTRY_PATH)
    violations = runner.run_fence(profile)
    runner.print_summary()
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
