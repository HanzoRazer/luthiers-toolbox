#!/usr/bin/env python3
"""
Runtime Capability Audit Utility.

Sprint: MRP-5V
Status: PROTOTYPE

Audits the runtime capability federation layer for:
  - Registry completeness
  - Policy determinism
  - Manifest stability
  - Integration status

Usage:
    python scripts/runtime_provenance/audit_runtime_capabilities.py
    python scripts/runtime_provenance/audit_runtime_capabilities.py --json
    python scripts/runtime_provenance/audit_runtime_capabilities.py --output audit_report.json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

# Add services/api to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "api"))

from app.cam.runtime_capabilities import (
    CapabilityRegistry,
    CapabilityResolver,
    ExecutionPolicyFederation,
    ResolutionContext,
    ResolutionStatus,
    build_capability_manifest,
    register_default_sources,
)


@dataclass
class AuditFinding:
    """Single audit finding."""

    category: str
    severity: str
    message: str
    details: dict = field(default_factory=dict)


@dataclass
class AuditReport:
    """Complete audit report."""

    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    sprint: str = "MRP-5V"

    # Counts
    registered_capabilities: int = 0
    enabled_capabilities: int = 0
    disabled_capabilities: int = 0
    replay_safe_capabilities: int = 0
    deterministic_capabilities: int = 0

    # By namespace
    capabilities_by_namespace: dict = field(default_factory=dict)

    # Checks
    deterministic_manifest: bool = True
    policy_determinism: bool = True
    registry_completeness: bool = True

    # Findings
    findings: List[AuditFinding] = field(default_factory=list)

    @property
    def blocking_findings(self) -> List[AuditFinding]:
        return [f for f in self.findings if f.severity == "BLOCKING"]

    @property
    def blocking_count(self) -> int:
        return len(self.blocking_findings)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "sprint": self.sprint,
            "statistics": {
                "registered_capabilities": self.registered_capabilities,
                "enabled_capabilities": self.enabled_capabilities,
                "disabled_capabilities": self.disabled_capabilities,
                "replay_safe_capabilities": self.replay_safe_capabilities,
                "deterministic_capabilities": self.deterministic_capabilities,
                "by_namespace": self.capabilities_by_namespace,
            },
            "checks": {
                "deterministic_manifest": self.deterministic_manifest,
                "policy_determinism": self.policy_determinism,
                "registry_completeness": self.registry_completeness,
            },
            "findings": [
                {
                    "category": f.category,
                    "severity": f.severity,
                    "message": f.message,
                    "details": f.details,
                }
                for f in self.findings
            ],
            "blocking_count": self.blocking_count,
        }


def run_audit() -> AuditReport:
    """Run the full capability audit."""
    report = AuditReport()

    # 1. Create and populate registry
    registry = CapabilityRegistry()
    try:
        register_default_sources(registry)
    except Exception as e:
        report.findings.append(
            AuditFinding(
                category="registry",
                severity="BLOCKING",
                message=f"Failed to register default sources: {e}",
            )
        )
        report.registry_completeness = False
        return report

    # 2. Collect statistics
    capabilities = registry.list_capabilities()
    report.registered_capabilities = len(capabilities)
    report.enabled_capabilities = sum(1 for c in capabilities if c.enabled)
    report.disabled_capabilities = report.registered_capabilities - report.enabled_capabilities
    report.replay_safe_capabilities = sum(1 for c in capabilities if c.replay_safe)
    report.deterministic_capabilities = sum(1 for c in capabilities if c.deterministic)

    # By namespace
    for cap in capabilities:
        ns = cap.namespace.value
        report.capabilities_by_namespace[ns] = report.capabilities_by_namespace.get(ns, 0) + 1

    # 3. Check manifest determinism
    manifest1 = build_capability_manifest(registry)
    manifest2 = build_capability_manifest(registry)

    if manifest1.content_hash != manifest2.content_hash:
        report.deterministic_manifest = False
        report.findings.append(
            AuditFinding(
                category="manifest",
                severity="BLOCKING",
                message="Manifest generation is not deterministic",
                details={
                    "hash1": manifest1.content_hash,
                    "hash2": manifest2.content_hash,
                },
            )
        )

    # 4. Check policy determinism
    policy = ExecutionPolicyFederation()
    for cap in capabilities[:5]:  # Sample first 5
        ctx = ResolutionContext()
        result1 = policy.evaluate(cap, ctx)
        result2 = policy.evaluate(cap, ctx)
        if result1.overall_decision != result2.overall_decision:
            report.policy_determinism = False
            report.findings.append(
                AuditFinding(
                    category="policy",
                    severity="BLOCKING",
                    message=f"Policy evaluation not deterministic for {cap.capability_id}",
                )
            )
            break

    # 5. Check resolver integration
    resolver = CapabilityResolver(registry=registry, policy_federation=policy)

    # Test known capabilities
    test_ids = ["operation:nut_slot", "translator:dxf_r12"]
    for cap_id in test_ids:
        result = resolver.resolve(cap_id)
        if result.status == ResolutionStatus.NOT_FOUND:
            report.findings.append(
                AuditFinding(
                    category="resolver",
                    severity="WARNING",
                    message=f"Expected capability not found: {cap_id}",
                )
            )

    # Test unknown capability rejection
    result = resolver.resolve("operation:nonexistent_test_capability")
    if result.status != ResolutionStatus.NOT_FOUND:
        report.findings.append(
            AuditFinding(
                category="resolver",
                severity="BLOCKING",
                message="Unknown capability was not rejected",
            )
        )

    # 6. Check for duplicate IDs (should have been caught at registration)
    seen_ids = set()
    for cap in capabilities:
        if cap.capability_id in seen_ids:
            report.findings.append(
                AuditFinding(
                    category="registry",
                    severity="BLOCKING",
                    message=f"Duplicate capability ID detected: {cap.capability_id}",
                )
            )
        seen_ids.add(cap.capability_id)

    return report


def print_report(report: AuditReport) -> None:
    """Print human-readable report."""
    print("=" * 60)
    print("RUNTIME CAPABILITY AUDIT")
    print(f"Sprint: {report.sprint}")
    print("=" * 60)
    print()

    print("[Statistics]")
    print(f"    Registered capabilities: {report.registered_capabilities}")
    print(f"    Enabled capabilities:    {report.enabled_capabilities}")
    print(f"    Disabled capabilities:   {report.disabled_capabilities}")
    print(f"    Replay-safe capabilities:{report.replay_safe_capabilities}")
    print(f"    Deterministic:           {report.deterministic_capabilities}")
    print()

    print("[By Namespace]")
    for ns, count in sorted(report.capabilities_by_namespace.items()):
        print(f"    {ns}: {count}")
    print()

    print("[Checks]")
    def status(ok: bool) -> str:
        return "PASS" if ok else "FAIL"

    print(f"    Deterministic manifest: {status(report.deterministic_manifest)}")
    print(f"    Policy determinism:     {status(report.policy_determinism)}")
    print(f"    Registry completeness:  {status(report.registry_completeness)}")
    print()

    if report.findings:
        print("[Findings]")
        for f in report.findings:
            print(f"    [{f.severity}] {f.category}: {f.message}")
        print()

    print(f"[Summary]")
    print(f"    Blocking findings: {report.blocking_count}")
    if report.blocking_count == 0:
        print("    Status: PASS")
    else:
        print("    Status: FAIL")


def main():
    parser = argparse.ArgumentParser(
        description="Audit runtime capability federation layer"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output file path",
    )
    args = parser.parse_args()

    report = run_audit()

    if args.json:
        output = json.dumps(report.to_dict(), indent=2)
        if args.output:
            Path(args.output).write_text(output)
            print(f"Report written to {args.output}")
        else:
            print(output)
    else:
        print_report(report)
        if args.output:
            Path(args.output).write_text(json.dumps(report.to_dict(), indent=2))
            print(f"\nJSON report written to {args.output}")

    # Exit with error if blocking findings
    sys.exit(1 if report.blocking_count > 0 else 0)


if __name__ == "__main__":
    main()
