"""
Runtime Capabilities.

Sprint: MRP-5V
Status: PROTOTYPE

The runtime capability federation layer.

This package provides:
  - CapabilityRegistry: Federation over domain-local sources
  - ExecutionPolicyFederation: Eligibility evaluation
  - CapabilityResolver: Resolution with policy checks
  - Capability manifests: Deterministic inventory

Usage:
    from app.cam.runtime_capabilities import (
        # Registry
        CapabilityRegistry,
        get_capability_registry,

        # Sources
        CapabilitySource,
        FederatedCapability,

        # Resolution
        CapabilityResolver,
        resolve_capability,
        can_use_capability,
        ResolutionContext,
        CapabilityResolutionResult,

        # Policies
        ExecutionPolicyFederation,
        get_policy_federation,

        # Manifest
        build_capability_manifest,
        CapabilityManifest,
    )

    # Register sources
    registry = get_capability_registry()
    registry.register_source(my_source)
    registry.freeze()

    # Resolve capability
    result = resolve_capability(
        "operation:nut_slot",
        ResolutionContext(require_replay_safe=True),
    )

    if result.is_allowed:
        # Proceed with execution
        ...

ARCHITECTURAL BOUNDARY:
    This package is the federation/eligibility layer.
    It does NOT:
    - Replace domain-local registries
    - Execute capabilities
    - Create capability semantics
    - Authorize machine execution

    Domain registries remain authoritative for their domain.
    This layer federates and gates.
"""

# Contracts
from .contracts import (
    # Enums
    CapabilityNamespace,
    GovernanceClassification,
    PolicyDecision,
    ResolutionStatus,
    # ID utilities
    make_capability_id,
    parse_capability_id,
    validate_capability_id,
    # Capability
    FederatedCapability,
    # Source interface
    CapabilitySource,
    # Resolution
    ResolutionContext,
    CompatibilitySummary,
    CapabilityResolutionResult,
)

# Exceptions
from .exceptions import (
    RuntimeCapabilityError,
    CapabilityNotFoundError,
    DuplicateCapabilityError,
    CapabilityDisabledError,
    ReplaySafetyViolationError,
    PolicyEvaluationError,
    CapabilityResolutionError,
    InvalidCapabilityIdError,
    SourceAdapterError,
    ManifestGenerationError,
)

# Registry
from .registry import (
    CapabilityRegistry,
    get_capability_registry,
    reset_capability_registry,
)

# Policies
from .policies import (
    ExecutionPolicy,
    PolicyEvaluationResult,
    EnabledPolicy,
    DeterministicPolicy,
    ReplaySafetyPolicy,
    CompatibilityTagsPolicy,
    RequiredTagsPolicy,
    ExecutionPolicyFederation,
    FederatedPolicyResult,
    get_policy_federation,
    reset_policy_federation,
)

# Resolution
from .resolution import (
    CapabilityResolver,
    get_capability_resolver,
    reset_capability_resolver,
    resolve_capability,
    can_use_capability,
)

# Manifest
from .manifest import (
    CapabilityManifestEntry,
    CapabilityManifest,
    build_capability_manifest,
    compare_manifests,
)

# Sources
from .sources import (
    CamOperationCapabilitySource,
    TranslatorCapabilitySource,
    AdapterCapabilitySource,
    create_default_sources,
    register_default_sources,
)

__all__ = [
    # Contracts - Enums
    "CapabilityNamespace",
    "GovernanceClassification",
    "PolicyDecision",
    "ResolutionStatus",
    # Contracts - ID utilities
    "make_capability_id",
    "parse_capability_id",
    "validate_capability_id",
    # Contracts - Capability
    "FederatedCapability",
    # Contracts - Source interface
    "CapabilitySource",
    # Contracts - Resolution
    "ResolutionContext",
    "CompatibilitySummary",
    "CapabilityResolutionResult",
    # Exceptions
    "RuntimeCapabilityError",
    "CapabilityNotFoundError",
    "DuplicateCapabilityError",
    "CapabilityDisabledError",
    "ReplaySafetyViolationError",
    "PolicyEvaluationError",
    "CapabilityResolutionError",
    "InvalidCapabilityIdError",
    "SourceAdapterError",
    "ManifestGenerationError",
    # Registry
    "CapabilityRegistry",
    "get_capability_registry",
    "reset_capability_registry",
    # Policies
    "ExecutionPolicy",
    "PolicyEvaluationResult",
    "EnabledPolicy",
    "DeterministicPolicy",
    "ReplaySafetyPolicy",
    "CompatibilityTagsPolicy",
    "RequiredTagsPolicy",
    "ExecutionPolicyFederation",
    "FederatedPolicyResult",
    "get_policy_federation",
    "reset_policy_federation",
    # Resolution
    "CapabilityResolver",
    "get_capability_resolver",
    "reset_capability_resolver",
    "resolve_capability",
    "can_use_capability",
    # Manifest
    "CapabilityManifestEntry",
    "CapabilityManifest",
    "build_capability_manifest",
    "compare_manifests",
    # Sources
    "CamOperationCapabilitySource",
    "TranslatorCapabilitySource",
    "AdapterCapabilitySource",
    "create_default_sources",
    "register_default_sources",
]
