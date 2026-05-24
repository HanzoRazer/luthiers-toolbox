#!/usr/bin/env python
"""
Execute mock replay from a JSON bundle file.

Sprint: MRP-5O
Usage: python execute_replay_bundle.py <bundle.json>
"""

import argparse
import json
import sys
from pathlib import Path

# Add services/api to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "api"))

from app.cam.runtime_provenance import (
    RuntimeReplayBundle,
    ReplayExecutionHarness,
    ReplayExecutionStatus,
)


def main():
    parser = argparse.ArgumentParser(description="Execute mock replay from JSON bundle")
    parser.add_argument("bundle_file", help="Path to bundle JSON file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    bundle_path = Path(args.bundle_file)
    if not bundle_path.exists():
        print(f"Error: Bundle file not found: {bundle_path}", file=sys.stderr)
        sys.exit(1)

    with open(bundle_path) as f:
        bundle_data = json.load(f)

    bundle = RuntimeReplayBundle.from_dict(bundle_data)

    if args.verbose:
        print(f"Loaded bundle: {bundle.bundle_id}")
        print(f"  Run ID: {bundle.provenance.run_id}")
        print(f"  Replayable: {bundle.replayable}")
        print(f"  Adapter: {bundle.provenance.adapter_id}")

    harness = ReplayExecutionHarness()
    result = harness.execute(bundle)

    print(f"\nReplay Result: {result.status.value}")
    print(f"  Run ID: {result.run_id}")
    print(f"  Message: {result.message}")

    if result.status == ReplayExecutionStatus.REPLAYED:
        print(f"  Reproduced Hash: {result.reproduced_hash}")
        print(f"  Reproduced Size: {result.reproduced_size} bytes")
        print(f"  Execution Time: {result.execution_time_ms:.2f}ms")
    else:
        if result.constraints:
            print("  Constraints:")
            for c in result.constraints:
                print(f"    - {c}")

    if args.verbose:
        print("\nFull result:")
        print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
