"""
CAM Intent Schema Hash Guard

CI utility to ensure CamIntentV1 schema stays frozen unless intentionally updated.

Usage:
  cd services/api

  # Print the current hash (for initial pinning)
  python -m app.ci.check_cam_intent_schema_hash --print

  # Check that hash matches pinned value (CI mode)
  python -m app.ci.check_cam_intent_schema_hash
"""
from __future__ import annotations

import argparse
import sys

from app.rmos.cam.schemas_intent import (
    CAM_INTENT_SCHEMA_HASH_V1,
    cam_intent_schema_hash_v1,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="check_cam_intent_schema_hash",
        description="CI guard: ensure CamIntentV1 schema stays frozen unless intentionally updated.",
    )
    parser.add_argument(
        "--print",
        action="store_true",
        help="Print the computed schema hash and exit 0 (useful for initial pinning).",
    )
    args = parser.parse_args(argv)

    actual = cam_intent_schema_hash_v1()

    if args.print:
        print(actual)
        return 0

    expected = CAM_INTENT_SCHEMA_HASH_V1
    if expected == "REPLACE_ME_AFTER_FIRST_RUN":
        print(
            "ERROR: CAM_INTENT_SCHEMA_HASH_V1 is not pinned.\n"
            "Run:\n"
            "  cd services/api\n"
            "  python -m app.ci.check_cam_intent_schema_hash --print\n"
            "Then paste the output into CAM_INTENT_SCHEMA_HASH_V1 in:\n"
            "  app/rmos/cam/schemas_intent.py\n",
            file=sys.stderr,
        )
        return 2

    if actual != expected:
        print(
            "ERROR: CamIntentV1 schema hash mismatch (contract drift).\n"
            f"expected={expected}\n"
            f"actual={actual}\n"
            "\nIf intentional, update docs + pin the new hash.",
            file=sys.stderr,
        )
        return 3

    print(f"[check_cam_intent_schema_hash] OK: hash={actual[:16]}...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
