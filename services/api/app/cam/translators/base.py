"""
MRP-3A/4A: Export Translator Protocol — Compatibility Shim

DEPRECATION NOTICE:
  base.py is retained for backward compatibility with MRP-3A/MRP-3B imports.
  New translator code should import from app.cam.translators.base.*

This module re-exports all types from the new base/ package structure
created in MRP-4A.

Original MRP-3A imports continue to work:
  from app.cam.translators.base import ExportTranslator, BaseTranslator

New MRP-4A imports are preferred:
  from app.cam.translators.base import (
      ExportTranslator,
      BaseTranslator,
      TranslatorRegistry,
      resolve_translator,
  )
"""

from app.cam.translators.base.contracts import (
    ExportTranslator,
    BaseTranslator,
    TranslatorResult,
    TranslatorError,
    TranslatorErrorCode,
    TranslatorProvenance,
    TranslatorOptions,
    ExportObjectType,
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
    validate_target,
    get_supported_targets,
    get_supported_versions,
)


__all__ = [
    # Contracts (MRP-3A compatibility)
    "ExportTranslator",
    "BaseTranslator",
    "TranslatorResult",
    "TranslatorError",
    "TranslatorErrorCode",
    "TranslatorProvenance",
    "TranslatorOptions",
    "ExportObjectType",
    # Capabilities (MRP-4A)
    "TranslatorCapabilities",
    "TranslatorCategory",
    "TranslatorMaturity",
    "ExecutionState",
    # Registry (MRP-4A)
    "TranslatorRegistry",
    "get_translator_registry",
    "register_translator",
    "get_translator",
    "list_translators",
    "list_translators_for_target",
    # Negotiation (MRP-4A)
    "resolve_translator",
    "TranslatorResolutionError",
    "TargetNotSupportedError",
    "VersionNotSupportedError",
    "validate_target",
    "get_supported_targets",
    "get_supported_versions",
]
