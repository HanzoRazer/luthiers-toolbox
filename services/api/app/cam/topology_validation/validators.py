"""
Topology Validation Orchestrator.

Sprint: MRP-5I, MRP-5J
Status: PROTOTYPE

Orchestrates shell integrity and continuity validation,
producing unified ValidationResult with deterministic signatures.

MRP-5J Addition: certify() method
  Returns CertifiedTopology only when validation passes.
  Translators accept CertifiedTopology, enforcing the boundary.

Architecture:
    PrototypeTopologyObject
        ↓
    TopologyValidator.validate() → ValidationResult
    TopologyValidator.certify()  → CertifiedTopology (if passes)
        ↓
    Translator (accepts only CertifiedTopology)
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .contracts import (
    CertifiedTopology,
    ContinuityReport,
    ShellIntegrityReport,
    ValidationCategory,
    ValidationFinding,
    ValidationRequest,
    ValidationResult,
    ValidationSeverity,
    ValidationSignature,
    ValidationTier,
)
from .continuity_checker import ContinuityChecker
from .exceptions import ValidationError, ValidationRequestError
from .shell_integrity import ShellIntegrityValidator


class TopologyValidator:
    """
    Orchestrates topology validation.

    Combines shell integrity validation and continuity checking
    into a unified validation pipeline with deterministic signatures.
    """

    def __init__(self, tier: ValidationTier = ValidationTier.PROTOTYPE):
        """
        Initialize the validator.

        Args:
            tier: Validation tier affecting strictness
        """
        self.tier = tier
        self._shell_validator = ShellIntegrityValidator(tier=tier)
        self._continuity_checker = ContinuityChecker(tier=tier)

    def validate(self, request: ValidationRequest) -> ValidationResult:
        """
        Validate topology from a ValidationRequest.

        Args:
            request: The validation request

        Returns:
            ValidationResult with all findings and signature
        """
        # Validate the request itself
        is_valid, errors = request.validate()
        if not is_valid:
            raise ValidationRequestError(
                message=f"Invalid validation request: {'; '.join(errors)}",
                errors=errors,
            )

        # Create result
        result = ValidationResult(
            request_id=request.request_id,
            passed=True,
            tier=request.tier,
        )

        # Validate shells
        shell_reports = self._validate_shells(request.shell_descriptors)
        result.shell_reports = shell_reports

        # Collect shell findings
        for report in shell_reports:
            result.findings.extend(report.findings)

        # Validate continuity if targets specified
        if request.continuity_targets:
            continuity_metadata = self._extract_continuity_metadata(
                request.shell_descriptors
            )
            continuity_reports = self._validate_continuity(
                request.continuity_targets, continuity_metadata
            )
            result.continuity_reports = continuity_reports

            # Collect continuity findings
            for report in continuity_reports:
                result.findings.extend(report.findings)

        # Determine pass/fail
        result.passed = not result.has_blocking_issues

        # In PRODUCTION tier, MAJOR issues also cause failure
        if request.tier == ValidationTier.PRODUCTION and result.major_count > 0:
            result.passed = False

        # Compute deterministic signature
        result.signature = self._compute_signature(request, result)

        return result

    def validate_topology_object(
        self,
        topology_dict: Dict[str, Any],
        continuity_targets: Optional[Dict[str, str]] = None,
    ) -> ValidationResult:
        """
        Validate a topology object dictionary directly.

        Convenience method for validating without creating a full request.

        Args:
            topology_dict: Topology object as dictionary
            continuity_targets: Optional continuity requirements

        Returns:
            ValidationResult
        """
        request_id = topology_dict.get("request_id", "direct_validation")
        tier_str = topology_dict.get("tier", "PROTOTYPE")
        tier = ValidationTier(tier_str) if tier_str in ValidationTier.__members__ else ValidationTier.PROTOTYPE

        shell_descriptors = topology_dict.get("shells", [])

        request = ValidationRequest(
            request_id=request_id,
            tier=tier,
            topology_dict=topology_dict,
            shell_descriptors=shell_descriptors,
            continuity_targets=continuity_targets or {},
        )

        return self.validate(request)

    def _validate_shells(
        self,
        shell_descriptors: List[Dict[str, Any]],
    ) -> List[ShellIntegrityReport]:
        """Validate all shells."""
        if not shell_descriptors:
            return []
        return self._shell_validator.validate_shells(shell_descriptors)

    def _validate_continuity(
        self,
        continuity_targets: Dict[str, str],
        continuity_metadata: Optional[List[Dict[str, Any]]],
    ) -> List[ContinuityReport]:
        """Validate continuity at all target junctions."""
        return self._continuity_checker.check_junctions(
            continuity_targets, continuity_metadata
        )

    def _extract_continuity_metadata(
        self,
        shell_descriptors: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Extract continuity metadata from shell descriptors."""
        metadata = []
        for sd in shell_descriptors:
            continuity = sd.get("continuity", [])
            for cm in continuity:
                if isinstance(cm, dict):
                    metadata.append(cm)
        return metadata

    def _compute_signature(
        self,
        request: ValidationRequest,
        result: ValidationResult,
    ) -> ValidationSignature:
        """Compute deterministic validation signature."""
        timestamp = datetime.now(timezone.utc).isoformat()

        # Build topology dict for hashing
        topology_dict = request.topology_dict or {
            "shells": request.shell_descriptors,
            "continuity_targets": request.continuity_targets,
        }

        # Build result dict for hashing
        result_dict = {
            "passed": result.passed,
            "blocking_count": result.blocking_count,
            "major_count": result.major_count,
            "shell_reports": [r.to_dict() for r in result.shell_reports],
            "continuity_reports": [r.to_dict() for r in result.continuity_reports],
        }

        return ValidationSignature.compute(
            topology_dict=topology_dict,
            result_dict=result_dict,
            tier=request.tier,
            timestamp_iso=timestamp,
        )

    def certify(
        self,
        topology_dict: Dict[str, Any],
        continuity_targets: Optional[Dict[str, str]] = None,
    ) -> CertifiedTopology:
        """
        Validate and certify topology for translator consumption.

        MRP-5J: This is the ONLY way to create a CertifiedTopology.
        Translators accept CertifiedTopology, not raw topology objects.

        Args:
            topology_dict: Topology object as dictionary
            continuity_targets: Optional continuity requirements

        Returns:
            CertifiedTopology if validation passes

        Raises:
            ValidationError: If validation fails (topology cannot be certified)
        """
        result = self.validate_topology_object(topology_dict, continuity_targets)

        if not result.passed:
            raise ValidationError(
                message=(
                    f"Cannot certify topology: validation failed with "
                    f"{result.blocking_count} blocking issues"
                ),
                classification="CERTIFICATION_DENIED",
                details={
                    "request_id": result.request_id,
                    "blocking_count": result.blocking_count,
                    "major_count": result.major_count,
                    "findings": [f.to_dict() for f in result.findings],
                },
            )

        return CertifiedTopology._create(
            topology_dict=topology_dict,
            validation=result,
            signature=result.signature,
        )


def validate_topology(
    topology_dict: Dict[str, Any],
    tier: ValidationTier = ValidationTier.PROTOTYPE,
    continuity_targets: Optional[Dict[str, str]] = None,
) -> ValidationResult:
    """
    Convenience function to validate a topology dictionary.

    Args:
        topology_dict: Topology object as dictionary
        tier: Validation tier
        continuity_targets: Optional continuity requirements

    Returns:
        ValidationResult
    """
    validator = TopologyValidator(tier=tier)
    return validator.validate_topology_object(topology_dict, continuity_targets)


def validate_request(request: ValidationRequest) -> ValidationResult:
    """
    Convenience function to validate from a request object.

    Args:
        request: The validation request

    Returns:
        ValidationResult
    """
    validator = TopologyValidator(tier=request.tier)
    return validator.validate(request)


def certify_topology(
    topology_dict: Dict[str, Any],
    tier: ValidationTier = ValidationTier.PROTOTYPE,
    continuity_targets: Optional[Dict[str, str]] = None,
) -> CertifiedTopology:
    """
    Convenience function to validate and certify topology.

    MRP-5J: Returns CertifiedTopology only if validation passes.
    Use this to prepare topology for translator consumption.

    Args:
        topology_dict: Topology object as dictionary
        tier: Validation tier
        continuity_targets: Optional continuity requirements

    Returns:
        CertifiedTopology if validation passes

    Raises:
        ValidationError: If validation fails
    """
    validator = TopologyValidator(tier=tier)
    return validator.certify(topology_dict, continuity_targets)
