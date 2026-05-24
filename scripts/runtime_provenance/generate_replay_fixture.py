#!/usr/bin/env python
"""
Generate a deterministic replay fixture bundle.

Sprint: MRP-5O
Usage: python generate_replay_fixture.py [--output FILE] [--request-id ID]
"""

import argparse
import json
import sys
from pathlib import Path

# Add services/api to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "api"))

from app.cam.runtime_provenance import (
    build_minimal_replay_bundle,
)


def main():
    parser = argparse.ArgumentParser(description="Generate deterministic replay fixture")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument("--request-id", help="Request ID for topology")
    parser.add_argument("--adapter", default="mock", help="Adapter ID (default: mock)")
    parser.add_argument("--decision", default="ADMITTED",
                       choices=["ADMITTED", "REJECTED", "CONDITIONALLY_ADMITTED"],
                       help="Admission decision (default: ADMITTED)")
    args = parser.parse_args()

    bundle = build_minimal_replay_bundle(
        request_id=args.request_id,
        adapter_id=args.adapter,
        decision=args.decision,
    )

    bundle_json = bundle.to_json(indent=2)

    if args.output:
        output_path = Path(args.output)
        with open(output_path, "w") as f:
            f.write(bundle_json)
        print(f"Wrote bundle to: {output_path}", file=sys.stderr)
        print(f"  Bundle ID: {bundle.bundle_id}", file=sys.stderr)
        print(f"  Run ID: {bundle.provenance.run_id}", file=sys.stderr)
        print(f"  Replayable: {bundle.replayable}", file=sys.stderr)
    else:
        print(bundle_json)


if __name__ == "__main__":
    main()
