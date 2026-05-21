"""
Topology Validation.

Sprint: MRP-5I, MRP-5J
Status: PROTOTYPE

Provides topology validation and certification.
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
from .exceptions import (
    ShellIntegrityError,
    ValidationError,
    ValidationRequestError,
)
from .validators import (
    TopologyValidator,
    certify_topology,
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
    # Exceptions
    "ShellIntegrityError",
    "ValidationError",
    "ValidationRequestError",
    # Validators
    "TopologyValidator",
    "certify_topology",
    "validate_topology",
]
