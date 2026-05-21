"""
Topology Validation Contracts.

Sprint: MRP-5I, MRP-5J
Status: PROTOTYPE

Defines data contracts for topology validation requests and results.
These contracts form the interface for the shell validation layer.

Key Principle: Validation is SEPARATE from construction.
The validator evaluates topology without mutating it.

MRP-5J Addition: CertifiedTopology
  A certified wrapper that can only be created when validation passes.
  Translators accept CertifiedTopology, not raw topology objects.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import hashlib
import json


class ValidationSeverity(str, Enum):
    """Severity levels for validation findings."""

    BLOCKING = "BLOCKING"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    INFO = "INFO"


class ValidationCategory(str, Enum):
    """Categories of validation checks."""

    SHELL_CLOSURE = "SHELL_CLOSURE"
    SHELL_MANIFOLD = "SHELL_MANIFOLD"
    CONTINUITY = "CONTINUITY"
    GEOMETRY_BOUNDS = "GEOMETRY_BOUNDS"
    TOPOLOGY_STRUCTURE = "TOPOLOGY_STRUCTURE"
    GEOMETRY_PRESERVATION = "GEOMETRY_PRESERVATION"


class ValidationTier(str, Enum):
    """Validation strictness tiers."""

    PROTOTYPE = "PROTOTYPE"
    PRODUCTION = "PRODUCTION"


@dataclass
class ValidationFinding:
    """A single validation finding."""

    category: ValidationCategory
    severity: ValidationSeverity
    message: str
    location: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "location": self.location,
            "details": self.details,
        }


@dataclass
class ShellIntegrityReport:
    """Report on shell integrity validation."""

    shell_id: str
    component_name: str
    is_closed: bool
    is_manifold: bool
    surface_count: int = 0
    edge_count: int = 0
    vertex_count: int = 0
    open_edge_count: int = 0
    non_manifold_edge_count: int = 0
    findings: List[ValidationFinding] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.is_closed and self.is_manifold

    def to_dict(self) -> Dict[str, Any]:
        return {
            "shell_id": self.shell_id,
            "component_name": self.component_name,
            "is_closed": self.is_closed,
            "is_manifold": self.is_manifold,
            "surface_count": self.surface_count,
            "edge_count": self.edge_count,
            "vertex_count": self.vertex_count,
            "open_edge_count": self.open_edge_count,
            "non_manifold_edge_count": self.non_manifold_edge_count,
            "passed": self.passed,
            "findings": [f.to_dict() for f in self.findings],
        }


@dataclass
class ContinuityReport:
    """Report on junction continuity validation."""

    junction_name: str
    target_level: str
    achieved_level: Optional[str] = None
    met_target: bool = False
    gap_mm: Optional[float] = None
    angle_deviation_deg: Optional[float] = None
    curvature_deviation: Optional[float] = None
    findings: List[ValidationFinding] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "junction_name": self.junction_name,
            "target_level": self.target_level,
            "achieved_level": self.achieved_level,
            "met_target": self.met_target,
            "gap_mm": self.gap_mm,
            "angle_deviation_deg": self.angle_deviation_deg,
            "curvature_deviation": self.curvature_deviation,
            "findings": [f.to_dict() for f in self.findings],
        }


@dataclass
class ValidationSignature:
    """Deterministic signature for validation results."""

    input_hash: str
    validation_hash: str
    tier: ValidationTier
    timestamp_iso: str
    version: str = "1.0.0"

    @classmethod
    def compute(
        cls,
        topology_dict: Dict[str, Any],
        result_dict: Dict[str, Any],
        tier: ValidationTier,
        timestamp_iso: str,
    ) -> "ValidationSignature":
        input_json = json.dumps(topology_dict, sort_keys=True)
        input_hash = hashlib.sha256(input_json.encode()).hexdigest()[:16]

        result_json = json.dumps(result_dict, sort_keys=True)
        validation_hash = hashlib.sha256(result_json.encode()).hexdigest()[:16]

        return cls(
            input_hash=input_hash,
            validation_hash=validation_hash,
            tier=tier,
            timestamp_iso=timestamp_iso,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_hash": self.input_hash,
            "validation_hash": self.validation_hash,
            "tier": self.tier.value,
            "timestamp_iso": self.timestamp_iso,
            "version": self.version,
        }


@dataclass
class ValidationRequest:
    """Request for topology validation."""

    request_id: str
    tier: ValidationTier = ValidationTier.PROTOTYPE
    topology_dict: Dict[str, Any] = field(default_factory=dict)
    shell_descriptors: List[Dict[str, Any]] = field(default_factory=list)
    continuity_targets: Dict[str, str] = field(default_factory=dict)
    options: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> Tuple[bool, List[str]]:
        errors = []
        if not self.request_id:
            errors.append("request_id is required")
        if not self.shell_descriptors and not self.topology_dict:
            errors.append("Either shell_descriptors or topology_dict required")
        return len(errors) == 0, errors


@dataclass
class ValidationResult:
    """Result of topology validation."""

    request_id: str
    passed: bool
    tier: ValidationTier
    shell_reports: List[ShellIntegrityReport] = field(default_factory=list)
    continuity_reports: List[ContinuityReport] = field(default_factory=list)
    findings: List[ValidationFinding] = field(default_factory=list)
    signature: Optional[ValidationSignature] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def blocking_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == ValidationSeverity.BLOCKING)

    @property
    def major_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == ValidationSeverity.MAJOR)

    @property
    def has_blocking_issues(self) -> bool:
        return self.blocking_count > 0

    def add_finding(self, finding: ValidationFinding) -> None:
        self.findings.append(finding)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "passed": self.passed,
            "tier": self.tier.value,
            "blocking_count": self.blocking_count,
            "major_count": self.major_count,
            "shell_reports": [r.to_dict() for r in self.shell_reports],
            "continuity_reports": [r.to_dict() for r in self.continuity_reports],
            "findings": [f.to_dict() for f in self.findings],
            "signature": self.signature.to_dict() if self.signature else None,
            "metadata": self.metadata,
        }

    @classmethod
    def success(
        cls,
        request_id: str,
        tier: ValidationTier,
        shell_reports: Optional[List[ShellIntegrityReport]] = None,
        continuity_reports: Optional[List[ContinuityReport]] = None,
    ) -> "ValidationResult":
        return cls(
            request_id=request_id,
            passed=True,
            tier=tier,
            shell_reports=shell_reports or [],
            continuity_reports=continuity_reports or [],
        )

    @classmethod
    def failure(
        cls,
        request_id: str,
        tier: ValidationTier,
        findings: List[ValidationFinding],
    ) -> "ValidationResult":
        return cls(
            request_id=request_id,
            passed=False,
            tier=tier,
            findings=findings,
        )


class CertifiedTopology:
    """
    Validation-certified topology wrapper.

    MRP-5J: This class can ONLY be instantiated by TopologyValidator.certify().
    """

    __slots__ = ("_topology_dict", "_validation", "_signature", "_certified")

    def __init__(self) -> None:
        raise TypeError(
            "CertifiedTopology cannot be instantiated directly. "
            "Use TopologyValidator.certify() instead."
        )

    @classmethod
    def _create(
        cls,
        topology_dict: Dict[str, Any],
        validation: "ValidationResult",
        signature: ValidationSignature,
    ) -> "CertifiedTopology":
        if not validation.passed:
            raise ValueError("Cannot certify topology that failed validation")

        instance = object.__new__(cls)
        instance._topology_dict = topology_dict
        instance._validation = validation
        instance._signature = signature
        instance._certified = True
        return instance

    @property
    def topology_dict(self) -> Dict[str, Any]:
        return self._topology_dict

    @property
    def validation(self) -> "ValidationResult":
        return self._validation

    @property
    def signature(self) -> ValidationSignature:
        return self._signature

    @property
    def request_id(self) -> str:
        return self._topology_dict.get("request_id", "unknown")

    @property
    def tier(self) -> ValidationTier:
        return self._validation.tier

    @property
    def shells(self) -> List[Dict[str, Any]]:
        return self._topology_dict.get("shells", [])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "certified": True,
            "request_id": self.request_id,
            "tier": self.tier.value,
            "topology": self._topology_dict,
            "validation_passed": self._validation.passed,
            "signature": self._signature.to_dict(),
        }
