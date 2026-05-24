#!/usr/bin/env python
"""
Compare recorded vs replayed artifact from a bundle.

Sprint: MRP-5O
Usage: python compare_replay_artifact.py <bundle.json>
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
    ArtifactRegressionComparator,
    ReplayExecutionStatus,
    RegressionStatus,
    DivergenceSeverity,
)


def main():
    parser = argparse.ArgumentParser(description="Compare recorded vs replayed artifact")
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
        print(f"  Baseline Hash: {bundle.provenance.artifact_lineage.content_hash}")
        print(f"  Baseline Size: {bundle.provenance.artifact_lineage.content_size_bytes}")

    harness = ReplayExecutionHarness()
    exec_result = harness.execute(bundle)

    if exec_result.status != ReplayExecutionStatus.REPLAYED:
        print(f"\nReplay failed: {exec_result.status.value}")
        print(f"  Message: {exec_result.message}")
        sys.exit(1)

    comparator = ArtifactRegressionComparator()
    report = comparator.compare(bundle, exec_result)

    print(f"\nRegression Report: {report.status.value}")
    print(f"  Hash Match: {report.hash_match}")
    print(f"  Baseline Hash: {report.baseline_hash}")
    print(f"  Reproduced Hash: {report.reproduced_hash}")
    print(f"  Overall Severity: {report.overall_severity.value}")

    if report.divergences:
        print("\nDivergences:")
        for d in report.divergences:
            print(f"  - {d.field}: {d.message}")
            print(f"      Expected: {d.expected}")
            print(f"      Actual: {d.actual}")
            print(f"      Severity: {d.severity.value}")

    if args.verbose:
        print("\nFull report:")
        print(json.dumps(report.to_dict(), indent=2))

    if report.status == RegressionStatus.MATCH:
        print("\n✓ Regression check PASSED")
        sys.exit(0)
    else:
        print("\n✗ Regression check FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
