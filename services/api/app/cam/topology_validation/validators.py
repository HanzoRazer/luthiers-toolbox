"""
Topology Validators.

Sprint: MRP-5I, MRP-5J
Status: PROTOTYPE

Main validation orchestrator for topology validation.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .contracts import (
    CertifiedTopology,
    ShellIntegrityReport,
    ValidationCategory,
    ValidationFinding,
    ValidationResult,
    ValidationSeverity,
    ValidationSignature,
    ValidationTier,
)
from .exceptions import ValidationError


class TopologyValidator:
    """
    Main topology validation orchestrator.

    Provides validate() and certify() methods.
    """

    def __init__(self, tier: ValidationTier = ValidationTier.PROTOTYPE):
        self._tier = tier

    @property
    def tier(self) -> ValidationTier:
        return self._tier

    def validate(
        self,
        topology_dict: Dict[str, Any],
        continuity_targets: Optional[Dict[str, str]] = None,
    ) -> ValidationResult:
        """Validate a topology dictionary."""
        return self.validate_topology_object(topology_dict, continuity_targets)

    def validate_topology_object(
        self,
        topology_dict: Dict[str, Any],
        continuity_targets: Optional[Dict[str, str]] = None,
    ) -> ValidationResult:
        """
        Validate a topology dictionary.

        Returns ValidationResult with pass/fail status and findings.
        """
        request_id = topology_dict.get("request_id", "unknown")
        findings: List[ValidationFinding] = []
        shell_reports: List[ShellIntegrityReport] = []

        shells = topology_dict.get("shells", [])
        if not shells:
            findings.append(ValidationFinding(
                category=ValidationCategory.TOPOLOGY_STRUCTURE,
                severity=ValidationSeverity.BLOCKING,
                message="Topology has no shells",
            ))

        for shell in shells:
            report = self._validate_shell(shell)
            shell_reports.append(report)
            findings.extend(report.findings)

        has_blocking = any(f.severity == ValidationSeverity.BLOCKING for f in findings)
        passed = not has_blocking

        result = ValidationResult(
            request_id=request_id,
            passed=passed,
            tier=self._tier,
            shell_reports=shell_reports,
            findings=findings,
        )

        timestamp = datetime.now(timezone.utc).isoformat()
        result.signature = ValidationSignature.compute(
            topology_dict=topology_dict,
            result_dict=result.to_dict(),
            tier=self._tier,
            timestamp_iso=timestamp,
        )

        return result

    def _validate_shell(self, shell: Dict[str, Any]) -> ShellIntegrityReport:
        """Validate a single shell descriptor."""
        shell_id = shell.get("shell_id", "unknown")
        component_name = shell.get("component_name", "unknown")
        is_closed = shell.get("is_closed", False)
        is_manifold = shell.get("is_manifold", False)

        findings: List[ValidationFinding] = []

        if not is_closed:
            findings.append(ValidationFinding(
                category=ValidationCategory.SHELL_CLOSURE,
                severity=ValidationSeverity.BLOCKING,
                message=f"Shell {shell_id} is not closed",
                location=shell_id,
            ))

        if not is_manifold:
            findings.append(ValidationFinding(
                category=ValidationCategory.SHELL_MANIFOLD,
                severity=ValidationSeverity.BLOCKING,
                message=f"Shell {shell_id} is not manifold",
                location=shell_id,
            ))

        return ShellIntegrityReport(
            shell_id=shell_id,
            component_name=component_name,
            is_closed=is_closed,
            is_manifold=is_manifold,
            surface_count=shell.get("surface_count", 0),
            edge_count=shell.get("edge_count", 0),
            vertex_count=shell.get("vertex_count", 0),
            findings=findings,
        )

    def certify(
        self,
        topology_dict: Dict[str, Any],
        continuity_targets: Optional[Dict[str, str]] = None,
    ) -> CertifiedTopology:
        """
        Certify a topology dictionary.

        Returns CertifiedTopology if validation passes.
        Raises ValidationError if validation fails.
        """
        result = self.validate_topology_object(topology_dict, continuity_targets)

        if not result.passed:
            raise ValidationError(
                message=f"Cannot certify topology: validation failed with {result.blocking_count} blocking issues",
                classification="CERTIFICATION_DENIED",
                blocking_count=result.blocking_count,
                findings=[f.to_dict() for f in result.findings],
            )

        return CertifiedTopology._create(
            topology_dict=topology_dict,
            validation=result,
            signature=result.signature,
        )


def validate_topology(
    topology_dict: Dict[str, Any],
    tier: ValidationTier = ValidationTier.PROTOTYPE,
) -> ValidationResult:
    """Convenience function to validate topology."""
    validator = TopologyValidator(tier=tier)
    return validator.validate(topology_dict)


def certify_topology(
    topology_dict: Dict[str, Any],
    tier: ValidationTier = ValidationTier.PROTOTYPE,
) -> CertifiedTopology:
    """Convenience function to certify topology."""
    validator = TopologyValidator(tier=tier)
    return validator.certify(topology_dict)
