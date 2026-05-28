#!/usr/bin/env python3
"""
Operation lane compliance — Makefile / FENCE_REGISTRY entry point.

Makefile step [3/7] and FENCE_REGISTRY `operation_lane_boundary` reference this module.
Delegates to fence_runner for profile enforcement.

Usage:
  cd services/api
  python -m app.ci.operation_lane_compliance
"""

from __future__ import annotations

import argparse
import sys

from app.ci.fence_runner import FENCE_REGISTRY_PATH, FenceRunner

PROFILE = "operation_lane_boundary"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.ci.operation_lane_compliance",
        description="Operation lane boundary enforcement",
    )
    parser.parse_args(argv)

    runner = FenceRunner(FENCE_REGISTRY_PATH)
    violations = runner.run_fence(PROFILE)
    runner.print_summary()
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
