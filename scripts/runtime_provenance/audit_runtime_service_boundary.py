#!/usr/bin/env python
"""
Runtime Service Boundary Audit.

Sprint: MRP-5S
Usage: python audit_runtime_service_boundary.py [--verbose]

Verifies:
- Required packages import
- Service exists and is functional
- Required contracts exported
- Replay path reachable
- Governance boundaries intact
"""

import argparse
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

# Add services/api to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "api"))


class AuditStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"


@dataclass
class AuditCheck:
    name: str
    status: AuditStatus
    message: str


def check_package_imports() -> List[AuditCheck]:
    """Check that all required packages import."""
    checks = []

    # topology_validation
    try:
        from app.cam.topology_validation import (
            CertifiedTopology,
            TopologyValidator,
            certify_topology,
        )
        checks.append(AuditCheck(
            "topology_validation imports",
            AuditStatus.PASS,
            "All required exports available",
        ))
    except ImportError as e:
        checks.append(AuditCheck(
            "topology_validation imports",
            AuditStatus.FAIL,
            str(e),
        ))

    # runtime_admission
    try:
        from app.cam.runtime_admission import (
            ExecutionAdmissionController,
            ExecutionAdmissionRequest,
            AdmissionDecision,
        )
        checks.append(AuditCheck(
            "runtime_admission imports",
            AuditStatus.PASS,
            "All required exports available",
        ))
    except ImportError as e:
        checks.append(AuditCheck(
            "runtime_admission imports",
            AuditStatus.FAIL,
            str(e),
        ))

    # runtime_provenance
    try:
        from app.cam.runtime_provenance import (
            RuntimeReplayBundle,
            ReplayExecutionHarness,
            ArtifactRegressionComparator,
            verify_replay_bundle_integrity,
        )
        checks.append(AuditCheck(
            "runtime_provenance imports",
            AuditStatus.PASS,
            "All required exports available",
        ))
    except ImportError as e:
        checks.append(AuditCheck(
            "runtime_provenance imports",
            AuditStatus.FAIL,
            str(e),
        ))

    # runtime_service
    try:
        from app.cam.runtime_service import (
            CertifiedRuntimeService,
            CertifiedRuntimeRequest,
            CertifiedRuntimeResult,
            ServiceExecutionStatus,
            execute_certified_runtime,
        )
        checks.append(AuditCheck(
            "runtime_service imports",
            AuditStatus.PASS,
            "All required exports available",
        ))
    except ImportError as e:
        checks.append(AuditCheck(
            "runtime_service imports",
            AuditStatus.FAIL,
            str(e),
        ))

    return checks


def check_certification_gate() -> List[AuditCheck]:
    """Check that certification gate works."""
    checks = []

    try:
        from app.cam.runtime_service import CertifiedRuntimeRequest

        # Should reject raw dict
        try:
            CertifiedRuntimeRequest(certified_topology={"raw": "dict"})
            checks.append(AuditCheck(
                "Certification Gate",
                AuditStatus.FAIL,
                "Raw topology was accepted (should reject)",
            ))
        except TypeError:
            checks.append(AuditCheck(
                "Certification Gate",
                AuditStatus.PASS,
                "Raw topology correctly rejected",
            ))
    except Exception as e:
        checks.append(AuditCheck(
            "Certification Gate",
            AuditStatus.FAIL,
            str(e),
        ))

    return checks


def check_admission_gate() -> List[AuditCheck]:
    """Check that admission gate works."""
    checks = []

    try:
        from app.cam.topology_validation import certify_topology
        from app.cam.runtime_service import (
            CertifiedRuntimeService,
            CertifiedRuntimeRequest,
            ServiceExecutionStatus,
        )

        topology = {
            "request_id": "audit-test",
            "tier": "PROTOTYPE",
            "shells": [{"shell_id": "s1", "is_closed": True, "is_manifold": True}],
        }
        certified = certify_topology(topology)
        service = CertifiedRuntimeService()

        # Valid adapter should pass
        request = CertifiedRuntimeRequest(
            certified_topology=certified,
            adapter_id="mock",
        )
        result = service.execute(request)

        if result.success and result.admission_decision is not None:
            checks.append(AuditCheck(
                "Admission Gate",
                AuditStatus.PASS,
                "Admission invoked and passed",
            ))
        else:
            checks.append(AuditCheck(
                "Admission Gate",
                AuditStatus.FAIL,
                f"Unexpected result: {result.status}",
            ))

    except Exception as e:
        checks.append(AuditCheck(
            "Admission Gate",
            AuditStatus.FAIL,
            str(e),
        ))

    return checks


def check_replay_boundary() -> List[AuditCheck]:
    """Check that replay boundary works."""
    checks = []

    try:
        from app.cam.topology_validation import certify_topology
        from app.cam.runtime_service import (
            CertifiedRuntimeService,
            CertifiedRuntimeRequest,
        )
        from app.cam.runtime_provenance import (
            ReplayExecutionHarness,
            ReplayExecutionStatus,
            verify_replay_bundle_integrity,
        )

        topology = {
            "request_id": "replay-audit",
            "tier": "PROTOTYPE",
            "shells": [{"shell_id": "s1", "is_closed": True, "is_manifold": True}],
        }
        certified = certify_topology(topology)
        service = CertifiedRuntimeService()

        request = CertifiedRuntimeRequest(
            certified_topology=certified,
            adapter_id="mock",
        )
        result = service.execute(request)

        if not result.success:
            checks.append(AuditCheck(
                "Replay Boundary",
                AuditStatus.FAIL,
                "Service execution failed",
            ))
            return checks

        # Check bundle integrity
        integrity = verify_replay_bundle_integrity(result.replay_bundle)
        if not integrity.passed:
            checks.append(AuditCheck(
                "Replay Boundary",
                AuditStatus.FAIL,
                "Bundle integrity check failed",
            ))
            return checks

        # Execute replay
        harness = ReplayExecutionHarness()
        replay = harness.execute(result.replay_bundle)

        if replay.status == ReplayExecutionStatus.REPLAYED:
            checks.append(AuditCheck(
                "Replay Boundary",
                AuditStatus.PASS,
                "Replay executed successfully",
            ))
        else:
            checks.append(AuditCheck(
                "Replay Boundary",
                AuditStatus.FAIL,
                f"Replay failed: {replay.status}",
            ))

    except Exception as e:
        checks.append(AuditCheck(
            "Replay Boundary",
            AuditStatus.FAIL,
            str(e),
        ))

    return checks


def check_determinism() -> List[AuditCheck]:
    """Check deterministic execution."""
    checks = []

    try:
        from app.cam.topology_validation import certify_topology
        from app.cam.runtime_service import (
            CertifiedRuntimeService,
            CertifiedRuntimeRequest,
        )

        topology = {
            "request_id": "determinism-audit",
            "tier": "PROTOTYPE",
            "shells": [{"shell_id": "s1", "is_closed": True, "is_manifold": True}],
        }

        cert1 = certify_topology(topology)
        cert2 = certify_topology(topology)

        service = CertifiedRuntimeService()

        result1 = service.execute(CertifiedRuntimeRequest(certified_topology=cert1))
        result2 = service.execute(CertifiedRuntimeRequest(certified_topology=cert2))

        if result1.artifact_hash == result2.artifact_hash:
            checks.append(AuditCheck(
                "Determinism Check",
                AuditStatus.PASS,
                f"Repeated execution produces identical hash: {result1.artifact_hash}",
            ))
        else:
            checks.append(AuditCheck(
                "Determinism Check",
                AuditStatus.FAIL,
                f"Hash mismatch: {result1.artifact_hash} != {result2.artifact_hash}",
            ))

    except Exception as e:
        checks.append(AuditCheck(
            "Determinism Check",
            AuditStatus.FAIL,
            str(e),
        ))

    return checks


def check_export_surface() -> List[AuditCheck]:
    """Check export surface stability."""
    checks = []

    required_exports = [
        "CertifiedRuntimeService",
        "CertifiedRuntimeRequest",
        "CertifiedRuntimeResult",
        "ServiceExecutionStatus",
        "execute_certified_runtime",
        "get_certified_runtime_service",
        "MockRuntimeAdapter",
        "is_adapter_available",
    ]

    try:
        from app.cam import runtime_service

        missing = []
        for name in required_exports:
            if not hasattr(runtime_service, name):
                missing.append(name)

        if not missing:
            checks.append(AuditCheck(
                "Export Surface",
                AuditStatus.PASS,
                f"All {len(required_exports)} required exports present",
            ))
        else:
            checks.append(AuditCheck(
                "Export Surface",
                AuditStatus.FAIL,
                f"Missing exports: {missing}",
            ))

    except Exception as e:
        checks.append(AuditCheck(
            "Export Surface",
            AuditStatus.FAIL,
            str(e),
        ))

    return checks


def main():
    parser = argparse.ArgumentParser(
        description="Runtime Service Boundary Audit"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("RUNTIME SERVICE BOUNDARY AUDIT")
    print("Sprint: MRP-5S")
    print("=" * 60)

    all_checks = []

    print("\n[1] Package Imports")
    checks = check_package_imports()
    all_checks.extend(checks)
    for c in checks:
        print(f"    {c.name}: {c.status.value}")
        if args.verbose:
            print(f"        {c.message}")

    print("\n[2] Certification Gate")
    checks = check_certification_gate()
    all_checks.extend(checks)
    for c in checks:
        print(f"    {c.name}: {c.status.value}")
        if args.verbose:
            print(f"        {c.message}")

    print("\n[3] Admission Gate")
    checks = check_admission_gate()
    all_checks.extend(checks)
    for c in checks:
        print(f"    {c.name}: {c.status.value}")
        if args.verbose:
            print(f"        {c.message}")

    print("\n[4] Replay Boundary")
    checks = check_replay_boundary()
    all_checks.extend(checks)
    for c in checks:
        print(f"    {c.name}: {c.status.value}")
        if args.verbose:
            print(f"        {c.message}")

    print("\n[5] Determinism Check")
    checks = check_determinism()
    all_checks.extend(checks)
    for c in checks:
        print(f"    {c.name}: {c.status.value}")
        if args.verbose:
            print(f"        {c.message}")

    print("\n[6] Export Surface")
    checks = check_export_surface()
    all_checks.extend(checks)
    for c in checks:
        print(f"    {c.name}: {c.status.value}")
        if args.verbose:
            print(f"        {c.message}")

    # Summary
    passed = sum(1 for c in all_checks if c.status == AuditStatus.PASS)
    failed = sum(1 for c in all_checks if c.status == AuditStatus.FAIL)
    warned = sum(1 for c in all_checks if c.status == AuditStatus.WARN)

    print("\n" + "=" * 60)
    print("AUDIT SUMMARY")
    print("=" * 60)
    print(f"    CertifiedTopology Gate: {'PASS' if any(c.name == 'Certification Gate' and c.status == AuditStatus.PASS for c in all_checks) else 'FAIL'}")
    print(f"    Admission Gate: {'PASS' if any(c.name == 'Admission Gate' and c.status == AuditStatus.PASS for c in all_checks) else 'FAIL'}")
    print(f"    Replay Boundary: {'PASS' if any(c.name == 'Replay Boundary' and c.status == AuditStatus.PASS for c in all_checks) else 'FAIL'}")
    print(f"    Determinism Check: {'PASS' if any(c.name == 'Determinism Check' and c.status == AuditStatus.PASS for c in all_checks) else 'FAIL'}")
    print(f"    Blocking Findings: {failed}")

    print("\n" + "-" * 60)
    if failed > 0:
        print("AUDIT STATUS: FAILED")
        return 1
    else:
        print("AUDIT STATUS: PASSED")
        return 0


if __name__ == "__main__":
    sys.exit(main())
