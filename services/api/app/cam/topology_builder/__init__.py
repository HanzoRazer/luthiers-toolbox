"""
Acoustic Topology Builder Layer.

Sprint: MRP-5H
Status: PROTOTYPE

This package provides deterministic topology construction from approved
geometry and acoustic semantic descriptors. It sits between cad_semantics
and translators in the authority chain.

Architecture:
    cad_semantics (semantic descriptors)
        ↓
    TopologyBuilder (this layer)
        ↓
    Translator (serialization)

Key Principles:
    - Topology Builder CONSTRUCTS topology
    - Translator SERIALIZES topology
    - BOE geometry is IMMUTABLE
    - No AI/adaptive topology generation
    - Explicit runtime classification
    - No silent degradation

Runtime Classifications:
    - SUPPORTED_PROTOTYPE: Can generate prototype topology
    - PARTIAL_PROTOTYPE: Some features supported, others skipped
    - UNSUPPORTED_RUNTIME: Cannot generate, clean rejection
    - RESEARCH_REQUIRED: Future capability needed
"""

from .contracts import (
    TopologyRequest,
    TopologyResult,
    PrototypeTopologyObject,
    ShellDescriptor,
    ProfileStack,
    ContinuityMetadata,
)
from .runtime_support import (
    TopologyRuntimeSupport,
    classify_topology_runtime,
)
from .builder import (
    TopologyBuilder,
    AcousticTopologyBuilder,
)
from .exceptions import (
    TopologyBuildError,
    GeometryMutationError,
    UnsupportedTopologyError,
    ContinuityValidationError,
    ShellClosureError,
    ProfileValidationError,
    KernelAdapterError,
)
from .validation import (
    validate_topology_request,
    validate_shell_closure,
    validate_geometry_preservation,
    validate_continuity,
    validate_profile_data,
    validate_topology_result,
)
from .kernel_adapters import MockKernelAdapter

__all__ = [
    # Contracts
    "TopologyRequest",
    "TopologyResult",
    "PrototypeTopologyObject",
    "ShellDescriptor",
    "ProfileStack",
    "ContinuityMetadata",
    # Runtime support
    "TopologyRuntimeSupport",
    "classify_topology_runtime",
    # Builder
    "TopologyBuilder",
    "AcousticTopologyBuilder",
    # Exceptions
    "TopologyBuildError",
    "GeometryMutationError",
    "UnsupportedTopologyError",
    "ContinuityValidationError",
    "ShellClosureError",
    "ProfileValidationError",
    "KernelAdapterError",
    # Validation
    "validate_topology_request",
    "validate_shell_closure",
    "validate_geometry_preservation",
    "validate_continuity",
    "validate_profile_data",
    "validate_topology_result",
    # Kernel adapters
    "MockKernelAdapter",
]
