"""
Shell Integrity Validator.

Sprint: MRP-5I
Status: PROTOTYPE

Validates shell integrity: closure, manifold status, and structure.
This is the core geometric integrity check for topology.

Key Principle: Validation does NOT mutate topology.
"""

from typing import Any, Dict, List, Optional

from .contracts import (
    ShellIntegrityReport,
    ValidationCategory,
    ValidationFinding,
    ValidationSeverity,
    ValidationTier,
)
from .exceptions import ShellIntegrityError


# Tolerance constants
CLOSURE_GAP_TOLERANCE_MM = 0.001  # 1 micron
EDGE_LENGTH_MIN_MM = 0.01  # 10 micron minimum edge


class ShellIntegrityValidator:
    """
    Validates shell integrity without modifying the input.

    Checks:
    - Shell closure (no open edges)
    - Manifold status (proper edge sharing)
    - Structural validity (reasonable face/edge/vertex counts)
    """

    def __init__(self, tier: ValidationTier = ValidationTier.PROTOTYPE):
        """
        Initialize the validator.

        Args:
            tier: Validation tier affecting strictness
        """
        self.tier = tier

    def validate_shell(
        self,
        shell_descriptor: Dict[str, Any],
    ) -> ShellIntegrityReport:
        """
        Validate a single shell descriptor.

        Args:
            shell_descriptor: Shell data from topology_builder

        Returns:
            ShellIntegrityReport with validation results
        """
        shell_id = shell_descriptor.get("shell_id", "unknown")
        component_name = shell_descriptor.get("component_name", "unknown")

        report = ShellIntegrityReport(
            shell_id=shell_id,
            component_name=component_name,
            is_closed=shell_descriptor.get("is_closed", False),
            is_manifold=shell_descriptor.get("is_manifold", False),
            surface_count=shell_descriptor.get("surface_count", 0),
            edge_count=shell_descriptor.get("edge_count", 0),
            vertex_count=shell_descriptor.get("vertex_count", 0),
        )

        # Check closure
        self._check_closure(shell_descriptor, report)

        # Check manifold status
        self._check_manifold(shell_descriptor, report)

        # Check structural validity
        self._check_structure(shell_descriptor, report)

        return report

    def validate_shells(
        self,
        shell_descriptors: List[Dict[str, Any]],
    ) -> List[ShellIntegrityReport]:
        """
        Validate multiple shells.

        Args:
            shell_descriptors: List of shell data dictionaries

        Returns:
            List of ShellIntegrityReport for each shell
        """
        return [self.validate_shell(sd) for sd in shell_descriptors]

    def _check_closure(
        self,
        shell_descriptor: Dict[str, Any],
        report: ShellIntegrityReport,
    ) -> None:
        """Check if shell is properly closed."""
        is_closed = shell_descriptor.get("is_closed", False)
        shell_id = shell_descriptor.get("shell_id", "unknown")

        if not is_closed:
            severity = ValidationSeverity.BLOCKING
            report.findings.append(
                ValidationFinding(
                    category=ValidationCategory.SHELL_CLOSURE,
                    severity=severity,
                    message=f"Shell '{shell_id}' is not closed (has open edges)",
                    location=shell_id,
                    details={"is_closed": False},
                )
            )

    def _check_manifold(
        self,
        shell_descriptor: Dict[str, Any],
        report: ShellIntegrityReport,
    ) -> None:
        """Check if shell is manifold."""
        is_manifold = shell_descriptor.get("is_manifold", False)
        shell_id = shell_descriptor.get("shell_id", "unknown")

        if not is_manifold:
            if self.tier == ValidationTier.PRODUCTION:
                severity = ValidationSeverity.BLOCKING
            else:
                severity = ValidationSeverity.MAJOR

            report.findings.append(
                ValidationFinding(
                    category=ValidationCategory.SHELL_MANIFOLD,
                    severity=severity,
                    message=f"Shell '{shell_id}' is non-manifold",
                    location=shell_id,
                    details={"is_manifold": False},
                )
            )

    def _check_structure(
        self,
        shell_descriptor: Dict[str, Any],
        report: ShellIntegrityReport,
    ) -> None:
        """Check structural validity (Euler characteristic, etc.)."""
        shell_id = shell_descriptor.get("shell_id", "unknown")
        surface_count = shell_descriptor.get("surface_count", 0)
        edge_count = shell_descriptor.get("edge_count", 0)
        vertex_count = shell_descriptor.get("vertex_count", 0)

        # Check for degenerate shell
        if surface_count == 0:
            report.findings.append(
                ValidationFinding(
                    category=ValidationCategory.TOPOLOGY_STRUCTURE,
                    severity=ValidationSeverity.BLOCKING,
                    message=f"Shell '{shell_id}' has no surfaces",
                    location=shell_id,
                    details={"surface_count": 0},
                )
            )
            return

        # Check Euler characteristic for closed manifold
        # V - E + F = 2 for a closed surface (sphere topology)
        # V - E + F = 0 for a torus
        if report.is_closed and report.is_manifold:
            euler = vertex_count - edge_count + surface_count
            if euler not in (0, 2):
                if self.tier == ValidationTier.PRODUCTION:
                    severity = ValidationSeverity.MAJOR
                else:
                    severity = ValidationSeverity.MINOR

                report.findings.append(
                    ValidationFinding(
                        category=ValidationCategory.TOPOLOGY_STRUCTURE,
                        severity=severity,
                        message=(
                            f"Shell '{shell_id}' has unusual Euler characteristic: "
                            f"V({vertex_count}) - E({edge_count}) + F({surface_count}) = {euler}"
                        ),
                        location=shell_id,
                        details={
                            "vertex_count": vertex_count,
                            "edge_count": edge_count,
                            "surface_count": surface_count,
                            "euler_characteristic": euler,
                        },
                    )
                )


def validate_shell_integrity(
    shell_descriptor: Dict[str, Any],
    tier: ValidationTier = ValidationTier.PROTOTYPE,
) -> ShellIntegrityReport:
    """
    Convenience function to validate a single shell.

    Args:
        shell_descriptor: Shell data dictionary
        tier: Validation tier

    Returns:
        ShellIntegrityReport
    """
    validator = ShellIntegrityValidator(tier=tier)
    return validator.validate_shell(shell_descriptor)


def validate_all_shells(
    shell_descriptors: List[Dict[str, Any]],
    tier: ValidationTier = ValidationTier.PROTOTYPE,
) -> List[ShellIntegrityReport]:
    """
    Convenience function to validate multiple shells.

    Args:
        shell_descriptors: List of shell data dictionaries
        tier: Validation tier

    Returns:
        List of ShellIntegrityReport
    """
    validator = ShellIntegrityValidator(tier=tier)
    return validator.validate_shells(shell_descriptors)
