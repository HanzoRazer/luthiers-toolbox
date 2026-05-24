#!/usr/bin/env python
"""
Audit the runtime spine integration.

Sprint: MRP-5P
Usage: python audit_runtime_spine.py [--verbose]

Verifies that the runtime spine modules compose correctly:
  topology_validation -> runtime_admission -> runtime_provenance
"""

import argparse
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

# Add services/api to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "api"))


class FindingSeverity(str, Enum):
    """Audit finding severity."""
    BLOCKING = "BLOCKING"
    REQUIRED_FIX = "REQUIRED_FIX"
    FOLLOW_UP = "FOLLOW_UP"
    OBSERVATION = "OBSERVATION"


@dataclass
class AuditFinding:
    """Single audit finding."""
    severity: FindingSeverity
    module: str
    message: str
    resolved: bool = False
    resolution: Optional[str] = None


def check_module_imports() -> List[AuditFinding]:
    """Check that all runtime modules can be imported."""
    findings = []

    # topology_validation
    try:
        from app.cam.topology_validation import (
            CertifiedTopology,
            TopologyValidator,
            ValidationResult,
            ValidationTier,
            certify_topology,
            validate_topology,
        )
        print("  [OK] topology_validation imports OK")
    except ImportError as e:
        findings.append(AuditFinding(
            severity=FindingSeverity.BLOCKING,
            module="topology_validation",
            message=f"Import failed: {e}",
        ))
        print(f"  [FAIL] topology_validation import FAILED: {e}")

    # runtime_admission
    try:
        from app.cam.runtime_admission import (
            AdmissionDecision,
            ExecutionAdmissionController,
            ExecutionAdmissionRequest,
            ExecutionAdmissionResult,
            ExecutionMode,
            RuntimeExecutionContext,
            RuntimeTier,
            get_admission_controller,
        )
        print("  [OK] runtime_admission imports OK")
    except ImportError as e:
        findings.append(AuditFinding(
            severity=FindingSeverity.BLOCKING,
            module="runtime_admission",
            message=f"Import failed: {e}",
        ))
        print(f"  [FAIL] runtime_admission import FAILED: {e}")

    # runtime_provenance (MRP-5N + MRP-5O)
    try:
        from app.cam.runtime_provenance import (
            # MRP-5N
            RuntimeReplayBundle,
            RuntimeArtifactProvenance,
            verify_replay_bundle_integrity,
            # MRP-5O
            ReplayExecutionHarness,
            ReplayExecutionStatus,
            ArtifactRegressionComparator,
            RegressionStatus,
            DivergenceSeverity,
            build_minimal_replay_bundle,
        )
        print("  [OK] runtime_provenance imports OK (MRP-5N + MRP-5O)")
    except ImportError as e:
        findings.append(AuditFinding(
            severity=FindingSeverity.BLOCKING,
            module="runtime_provenance",
            message=f"Import failed: {e}",
        ))
        print(f"  [FAIL] runtime_provenance import FAILED: {e}")

    return findings


def check_step_translator() -> List[AuditFinding]:
    """Check STEP translator status."""
    findings = []

    try:
        from app.cam.translators.step import (
            BodyOutlineStepTranslator,
            STEP_AP203_TRANSLATOR_ID,
        )
        print("  [OK] STEP translator available")
    except ImportError as e:
        findings.append(AuditFinding(
            severity=FindingSeverity.FOLLOW_UP,
            module="translators/step",
            message=f"STEP translator not importable: {e}. Source .py files missing (only .pyc remain).",
        ))
        print(f"  [INFO] STEP translator UNAVAILABLE (not blocking): {e}")

    return findings


def check_kernel_adapters() -> List[AuditFinding]:
    """Check kernel adapter status."""
    findings = []

    try:
        from app.cam.topology_builder.kernel_adapters import MockKernelAdapter

        adapter = MockKernelAdapter()
        print("  [OK] MockKernelAdapter available")
    except ImportError as e:
        findings.append(AuditFinding(
            severity=FindingSeverity.BLOCKING,
            module="kernel_adapters",
            message=f"MockKernelAdapter import failed: {e}",
        ))
        print(f"  [FAIL] MockKernelAdapter FAILED: {e}")

    return findings


def check_spine_integration() -> List[AuditFinding]:
    """Check that spine modules integrate correctly."""
    findings = []

    try:
        from app.cam.topology_validation import TopologyValidator, ValidationTier
        from app.cam.runtime_admission import (
            ExecutionAdmissionController,
            ExecutionAdmissionRequest,
            RuntimeExecutionContext,
            RuntimeTier,
            ExecutionMode,
            AdmissionDecision,
        )
        from app.cam.runtime_provenance import (
            build_minimal_replay_bundle,
            ReplayExecutionHarness,
            ReplayExecutionStatus,
        )

        # Test topology validation
        topology = {
            "request_id": "audit-test-001",
            "tier": "PROTOTYPE",
            "shells": [{
                "shell_id": "shell_001",
                "shell_type": "flat_extrusion",
                "component_name": "body",
                "is_closed": True,
                "is_manifold": True,
            }],
        }

        validator = TopologyValidator(tier=ValidationTier.PROTOTYPE)
        certified = validator.certify(topology)
        print("  [OK] Topology validation -> certification OK")

        # Test admission
        controller = ExecutionAdmissionController()
        context = RuntimeExecutionContext(
            requested_adapter_id="mock",
            available_adapter_ids=["mock"],
            execution_mode=ExecutionMode.DETERMINISTIC,
            runtime_tier=RuntimeTier.PROTOTYPE,
        )
        request = ExecutionAdmissionRequest(
            certified_topology=certified,
            runtime_context=context,
        )
        admission = controller.evaluate(request)

        if admission.decision == AdmissionDecision.ADMITTED:
            print("  [OK] Admission evaluation -> ADMITTED OK")
        else:
            findings.append(AuditFinding(
                severity=FindingSeverity.REQUIRED_FIX,
                module="runtime_admission",
                message=f"Admission rejected valid certified topology: {admission.decision}",
            ))
            print(f"  [FAIL] Admission REJECTED: {admission.decision}")

        # Test provenance bundle creation
        bundle = build_minimal_replay_bundle(
            request_id="audit-test-001",
            adapter_id="mock",
            decision="ADMITTED",
        )
        print("  [OK] Provenance bundle creation OK")

        # Test replay execution
        harness = ReplayExecutionHarness()
        result = harness.execute(bundle)

        if result.status == ReplayExecutionStatus.REPLAYED:
            print("  [OK] Replay execution -> REPLAYED OK")
        else:
            findings.append(AuditFinding(
                severity=FindingSeverity.REQUIRED_FIX,
                module="runtime_provenance",
                message=f"Replay failed: {result.status}",
            ))
            print(f"  [FAIL] Replay FAILED: {result.status}")

    except Exception as e:
        findings.append(AuditFinding(
            severity=FindingSeverity.BLOCKING,
            module="spine_integration",
            message=f"Integration test failed: {e}",
        ))
        print(f"  [FAIL] Integration test FAILED: {e}")

    return findings


def main():
    parser = argparse.ArgumentParser(description="Audit runtime spine integration")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    print("=" * 60)
    print("MRP-5P Runtime Spine Integration Audit")
    print("=" * 60)

    all_findings = []

    print("\n[1] Module Import Check")
    all_findings.extend(check_module_imports())

    print("\n[2] STEP Translator Check")
    all_findings.extend(check_step_translator())

    print("\n[3] Kernel Adapters Check")
    all_findings.extend(check_kernel_adapters())

    print("\n[4] Spine Integration Check")
    all_findings.extend(check_spine_integration())

    print("\n" + "=" * 60)
    print("AUDIT SUMMARY")
    print("=" * 60)

    blocking = [f for f in all_findings if f.severity == FindingSeverity.BLOCKING]
    required_fix = [f for f in all_findings if f.severity == FindingSeverity.REQUIRED_FIX]
    follow_up = [f for f in all_findings if f.severity == FindingSeverity.FOLLOW_UP]
    observations = [f for f in all_findings if f.severity == FindingSeverity.OBSERVATION]

    print(f"\nBLOCKING: {len(blocking)}")
    for f in blocking:
        print(f"  - [{f.module}] {f.message}")

    print(f"\nREQUIRED_FIX: {len(required_fix)}")
    for f in required_fix:
        print(f"  - [{f.module}] {f.message}")

    print(f"\nFOLLOW_UP: {len(follow_up)}")
    for f in follow_up:
        print(f"  - [{f.module}] {f.message}")

    print(f"\nOBSERVATIONS: {len(observations)}")
    for f in observations:
        print(f"  - [{f.module}] {f.message}")

    print("\n" + "-" * 60)
    if blocking:
        print("AUDIT STATUS: BLOCKED - resolve blocking issues before proceeding")
        return 1
    elif required_fix:
        print("AUDIT STATUS: NEEDS FIXES - spine functional but requires attention")
        return 1
    else:
        print("AUDIT STATUS: PASSED - runtime spine composes correctly")
        return 0


if __name__ == "__main__":
    sys.exit(main())
