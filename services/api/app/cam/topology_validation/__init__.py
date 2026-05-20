"""
Acoustic Shell Validation Layer.

Sprint: MRP-5I, MRP-5J
Status: PROTOTYPE

This package provides topology validation SEPARATE from construction.
It evaluates topology produced by topology_builder without mutating it.

Architecture:
    topology_builder (constructs topology)
        ↓
    topology_validation (this layer - evaluates topology)
        ↓
    translator (serializes topology)

MRP-5J Addition: CertifiedTopology
    TopologyValidator.certify() returns CertifiedTopology ONLY when
    validation passes. Translators accept CertifiedTopology, enforcing
    the boundary: validated topology → translator serialization.

Key Principles:
    - Validation is SEPARATE from construction
    - Validation does NOT mutate topology
    - Deterministic results given same input
    - Clear pass/fail with structured findings
    - Tier-aware strictness (PROTOTYPE vs PRODUCTION)
    - CertifiedTopology enforces translator input contract

Validation Categories:
    - SHELL_CLOSURE: Open edge detection
    - SHELL_MANIFOLD: Non-manifold geometry detection
    - CONTINUITY: G0/G1/G2 junction quality
    - GEOMETRY_BOUNDS: Bounding box sanity
    - TOPOLOGY_STRUCTURE: Shell/face/edge counts

Severity Levels:
    - BLOCKING: Cannot proceed, topology unusable
    - MAJOR: Significant issue, may proceed with warnings
    - MINOR: Cosmetic or informational
    - INFO: Observation, not a problem
"""

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
from .continuity_checker import (
    ContinuityChecker,
    check_all_continuity,
    check_continuity,
)
from .exceptions import (
    BoundsError,
    ContinuityError,
    ShellIntegrityError,
    TopologyStructureError,
    ValidationError,
    ValidationRequestError,
)
from .shell_integrity import (
    ShellIntegrityValidator,
    validate_all_shells,
    validate_shell_integrity,
)
from .validators import (
    TopologyValidator,
    certify_topology,
    validate_request,
    validate_topology,
)

__all__ = [
    # Contracts
    "CertifiedTopology",
    "ContinuityReport",
    "ShellIntegrityReport",
    "ValidationCategory",
    "ValidationFinding",
    "ValidationRequest",
    "ValidationResult",
    "ValidationSeverity",
    "ValidationSignature",
    "ValidationTier",
    # Validators
    "TopologyValidator",
    "certify_topology",
    "validate_topology",
    "validate_request",
    # Shell integrity
    "ShellIntegrityValidator",
    "validate_shell_integrity",
    "validate_all_shells",
    # Continuity
    "ContinuityChecker",
    "check_continuity",
    "check_all_continuity",
    # Exceptions
    "ValidationError",
    "ShellIntegrityError",
    "ContinuityError",
    "BoundsError",
    "TopologyStructureError",
    "ValidationRequestError",
]
