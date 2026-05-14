"""
CAM Translators

MRP-3A/4A: Governed translator layer for Export Object consumption.

Translators serialize Export Objects into specific output formats.
They do not create semantics — they serialize existing semantics.

Key principle: Translators are downstream of Export Objects, not
upstream with geometry generation.

MRP-4A additions:
  - Multi-target abstraction (base/ package)
  - SVG translator
  - Target negotiation and registry
"""

from app.cam.translators.base import (
    # Contracts
    ExportTranslator,
    BaseTranslator,
    TranslatorResult,
    TranslatorError,
    TranslatorErrorCode,
    TranslatorProvenance,
    TranslatorOptions,
    # Capabilities
    TranslatorCapabilities,
    TranslatorCategory,
    TranslatorMaturity,
    ExecutionState,
    # Registry
    TranslatorRegistry,
    get_translator_registry,
    register_translator,
    get_translator,
    list_translators,
    list_translators_for_target,
    # Negotiation
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
