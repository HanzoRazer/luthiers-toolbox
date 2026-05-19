"""
MRP-4A: Translator Abstraction Layer

Canonical abstraction for multi-target translation from Export Objects.

Design principles:
  - Translators serialize semantics, they do not create semantics
  - All translators consume the same Export Object canonically
  - Output is deterministic given the same input (excluding timestamps)
  - Provenance is embedded where format supports it
  - Gate status must be green or yellow to proceed

Package structure:
  - contracts.py: Protocol definitions and result types
  - capabilities.py: Capability declarations and categories
  - registry.py: Translator discovery and registration
  - negotiation.py: Target resolution and version selection
  - validation.py: Translation validation utilities
"""

from app.cam.translators.base.contracts import (
    ExportTranslator,
    BaseTranslator,
    TranslatorResult,
    TranslatorError,
    TranslatorErrorCode,
    TranslatorProvenance,
    TranslatorOptions,
)

from app.cam.translators.base.capabilities import (
    TranslatorCapabilities,
    TranslatorCategory,
    TranslatorMaturity,
    ExecutionState,
)

from app.cam.translators.base.registry import (
    TranslatorRegistry,
    get_translator_registry,
    register_translator,
    get_translator,
    list_translators,
    list_translators_for_target,
)

from app.cam.translators.base.negotiation import (
    resolve_translator,
    TranslatorResolutionError,
    TargetNotSupportedError,
    VersionNotSupportedError,
)

__all__ = [
    # Contracts
    "ExportTranslator",
    "BaseTranslator",
    "TranslatorResult",
    "TranslatorError",
    "TranslatorErrorCode",
    "TranslatorProvenance",
    "TranslatorOptions",
    # Capabilities
    "TranslatorCapabilities",
    "TranslatorCategory",
    "TranslatorMaturity",
    "ExecutionState",
    # Registry
    "TranslatorRegistry",
    "get_translator_registry",
    "register_translator",
    "get_translator",
    "list_translators",
    "list_translators_for_target",
    # Negotiation
    "resolve_translator",
    "TranslatorResolutionError",
    "TargetNotSupportedError",
    "VersionNotSupportedError",
]
