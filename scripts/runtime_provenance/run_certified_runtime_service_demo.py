#!/usr/bin/env python
"""
Certified Runtime Service Demo Harness.

Sprint: MRP-5Q/R
Usage: python run_certified_runtime_service_demo.py [--output FILE] [--verbose]

Demonstrates the CertifiedRuntimeService:
- Builds or loads deterministic certified topology fixture
- Creates runtime context
- Runs CertifiedRuntimeService
- Prints execution results

Does NOT persist canonical state by default.
"""

import argparse
import json
import sys
from pathlib import Path

# Add services/api to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "api"))

from app.cam.topology_validation import certify_topology, ValidationTier
from app.cam.runtime_service import (
    ArtifactIntent,
    CertifiedRuntimeRequest,
    CertifiedRuntimeService,
    ServiceExecutionStatus,
)


def build_demo_topology(request_id: str = "demo-001") -> dict:
    """Build a deterministic demo topology."""
    return {
        "request_id": request_id,
        "tier": "PROTOTYPE",
        "shells": [
            {
                "shell_id": "body_demo",
                "shell_type": "flat_extrusion",
                "component_name": "guitar_body",
                "is_closed": True,
                "is_manifold": True,
                "surface_count": 6,
                "edge_count": 12,
                "vertex_count": 8,
                "continuity": [],
            }
        ],
    }


def run_demo(
    request_id: str = "demo-001",
    adapter_id: str = "mock",
    verbose: bool = False,
) -> dict:
    """Run the certified runtime service demo."""
    print("=" * 60)
    print("Certified Runtime Service Demo")
    print("Sprint: MRP-5Q/R")
    print("=" * 60)

    # Step 1: Build topology
    print("\n[1] Building demo topology...")
    topology = build_demo_topology(request_id=request_id)
    print(f"    Request ID: {topology['request_id']}")
    print(f"    Shells: {len(topology['shells'])}")

    # Step 2: Certify topology
    print("\n[2] Certifying topology...")
    try:
        certified = certify_topology(topology)
        print(f"    Certification: PASSED")
        print(f"    Signature: {certified.signature.input_hash[:16]}...")
    except Exception as e:
        print(f"    Certification: FAILED - {e}")
        return {"success": False, "error": str(e)}

    # Step 3: Create request
    print("\n[3] Creating service request...")
    request = CertifiedRuntimeRequest(
        certified_topology=certified,
        adapter_id=adapter_id,
        artifact_intent=ArtifactIntent.MOCK_DETERMINISTIC,
    )
    print(f"    Request ID: {request.request_id}")
    print(f"    Trace ID: {request.trace_id}")
    print(f"    Adapter: {request.adapter_id}")

    # Step 4: Execute service
    print("\n[4] Executing CertifiedRuntimeService...")
    service = CertifiedRuntimeService()
    result = service.execute(request)

    # Step 5: Print results
    print("\n[5] Execution Result:")
    print(f"    Status: {result.status.value}")
    print(f"    Success: {result.success}")

    if result.success:
        print(f"    Admission: {result.admission_decision.value}")
        print(f"    Artifact ID: {result.artifact_id}")
        print(f"    Artifact Hash: {result.artifact_hash}")
        print(f"    Artifact Size: {result.artifact_size_bytes} bytes")
        print(f"    Replay Bundle ID: {result.replay_bundle_id}")
        print(f"    Execution Time: {result.execution_time_ms:.2f}ms")

        if verbose:
            print("\n[Verbose] Provenance Details:")
            provenance = result.replay_bundle.provenance
            print(f"    Run ID: {provenance.run_id}")
            print(f"    Source Topology Hash: {provenance.source_topology_hash}")
            print(f"    Trace Events: {len(provenance.trace_events)}")

            print("\n[Verbose] Bundle Integrity:")
            from app.cam.runtime_provenance import verify_replay_bundle_integrity
            integrity = verify_replay_bundle_integrity(result.replay_bundle)
            print(f"    Integrity Check: {'PASSED' if integrity.passed else 'FAILED'}")

            print("\n[Verbose] Replay Test:")
            from app.cam.runtime_provenance import ReplayExecutionHarness
            harness = ReplayExecutionHarness()
            replay = harness.execute(result.replay_bundle)
            print(f"    Replay Status: {replay.status.value}")
            print(f"    Reproduced Hash: {replay.reproduced_hash}")
    else:
        print(f"    Error: {result.error_message}")
        if result.error_details:
            print(f"    Details: {json.dumps(result.error_details, indent=2)}")

    print("\n" + "=" * 60)

    return result.to_dict()


def main():
    parser = argparse.ArgumentParser(
        description="Certified Runtime Service Demo Harness"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file for replay bundle JSON (optional)"
    )
    parser.add_argument(
        "--request-id",
        default="demo-001",
        help="Request ID for the demo topology"
    )
    parser.add_argument(
        "--adapter",
        default="mock",
        help="Adapter ID (default: mock)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output including replay test"
    )
    args = parser.parse_args()

    result = run_demo(
        request_id=args.request_id,
        adapter_id=args.adapter,
        verbose=args.verbose,
    )

    if args.output and result.get("replay_bundle_id"):
        # Re-run to get the bundle for output
        topology = build_demo_topology(request_id=args.request_id)
        certified = certify_topology(topology)
        request = CertifiedRuntimeRequest(
            certified_topology=certified,
            adapter_id=args.adapter,
        )
        service = CertifiedRuntimeService()
        full_result = service.execute(request)

        if full_result.success:
            output_path = Path(args.output)
            bundle_json = full_result.replay_bundle.to_json(indent=2)
            with open(output_path, "w") as f:
                f.write(bundle_json)
            print(f"\nWrote replay bundle to: {output_path}")

    return 0 if result.get("status") == "SUCCESS" else 1


if __name__ == "__main__":
    sys.exit(main())
