"""
MRP-4A: Target Negotiation

Target resolution and version selection for multi-target translation.

Provides deterministic translator selection based on target format,
version requirements, and capability constraints.
"""

from __future__ import annotations

from typing import Optional

from app.cam.translators.base.contracts import ExportTranslator, TranslatorErrorCode
from app.cam.translators.base.capabilities import ExecutionState


class TranslatorResolutionError(Exception):
    """Base error for translator resolution failures."""
    def __init__(self, message: str, code: TranslatorErrorCode):
        super().__init__(message)
        self.code = code


class TargetNotSupportedError(TranslatorResolutionError):
    """Raised when target format is not supported."""
    def __init__(self, target: str):
        super().__init__(
            f"Target format '{target}' is not supported",
            TranslatorErrorCode.UNSUPPORTED_TARGET,
        )
        self.target = target


class VersionNotSupportedError(TranslatorResolutionError):
    """Raised when target version is not supported."""
    def __init__(self, target: str, version: str, available_versions: list):
        super().__init__(
            f"Version '{version}' not supported for target '{target}'. "
            f"Available: {available_versions}",
            TranslatorErrorCode.UNSUPPORTED_VERSION,
        )
        self.target = target
        self.version = version
        self.available_versions = available_versions


# Target-to-translator mapping with version support
TARGET_TRANSLATOR_MAP = {
    "dxf": {
        "r12": "body_outline_dxf_r12",
        "r2000": "body_outline_dxf_r2000",
        "default": "body_outline_dxf_r12",
    },
    "svg": {
        "1.1": "body_outline_svg",
        "default": "body_outline_svg",
    },
}


def get_supported_targets() -> list:
    """Get list of supported target formats."""
    return list(TARGET_TRANSLATOR_MAP.keys())


def get_supported_versions(target: str) -> list:
    """Get list of supported versions for a target format."""
    if target not in TARGET_TRANSLATOR_MAP:
        return []
    versions = list(TARGET_TRANSLATOR_MAP[target].keys())
    versions.remove("default")
    return versions


def get_default_version(target: str) -> Optional[str]:
    """Get the default version for a target format."""
    if target not in TARGET_TRANSLATOR_MAP:
        return None
    mapping = TARGET_TRANSLATOR_MAP[target]
    default_translator = mapping.get("default")
    for version, translator_id in mapping.items():
        if version != "default" and translator_id == default_translator:
            return version
    return None


def resolve_translator(
    target: str,
    version: Optional[str] = None,
    require_governed: bool = True,
) -> ExportTranslator:
    """
    Resolve a translator for a target format and optional version.

    Args:
        target: Target format (e.g., 'dxf', 'svg')
        version: Optional version (e.g., 'r12', 'r2000')
        require_governed: If True, only return governed translators

    Returns:
        ExportTranslator instance

    Raises:
        TargetNotSupportedError: If target is not supported
        VersionNotSupportedError: If version is not supported
        TranslatorResolutionError: If no suitable translator found
    """
    from app.cam.translators.base.registry import (
        get_translator_registry,
        get_translator,
    )

    target_lower = target.lower()

    if target_lower not in TARGET_TRANSLATOR_MAP:
        raise TargetNotSupportedError(target)

    mapping = TARGET_TRANSLATOR_MAP[target_lower]
    available_versions = [v for v in mapping.keys() if v != "default"]

    if version is not None:
        version_lower = version.lower()
        if version_lower not in mapping:
            raise VersionNotSupportedError(target, version, available_versions)
        translator_id = mapping[version_lower]
    else:
        translator_id = mapping.get("default")
        if translator_id is None:
            raise TranslatorResolutionError(
                f"No default translator for target '{target}'",
                TranslatorErrorCode.TRANSLATOR_NOT_FOUND,
            )

    registry = get_translator_registry()
    translator = registry.get(translator_id)

    if translator is None:
        raise TranslatorResolutionError(
            f"Translator '{translator_id}' not found in registry",
            TranslatorErrorCode.TRANSLATOR_NOT_FOUND,
        )

    if require_governed:
        cap = registry.get_capabilities(translator_id)
        if cap is None or cap.execution_state != ExecutionState.GOVERNED_EXECUTION:
            raise TranslatorResolutionError(
                f"Translator '{translator_id}' is not governed",
                TranslatorErrorCode.GOVERNANCE_VIOLATION,
            )

    return translator


def validate_target(target: str, version: Optional[str] = None) -> bool:
    """
    Validate that a target/version combination is supported.

    Args:
        target: Target format
        version: Optional version

    Returns:
        True if supported, False otherwise
    """
    target_lower = target.lower()

    if target_lower not in TARGET_TRANSLATOR_MAP:
        return False

    if version is not None:
        version_lower = version.lower()
        return version_lower in TARGET_TRANSLATOR_MAP[target_lower]

    return True


def get_translator_id_for_target(
    target: str,
    version: Optional[str] = None,
) -> Optional[str]:
    """
    Get translator ID for a target/version without instantiating.

    Args:
        target: Target format
        version: Optional version

    Returns:
        Translator ID or None if not found
    """
    target_lower = target.lower()

    if target_lower not in TARGET_TRANSLATOR_MAP:
        return None

    mapping = TARGET_TRANSLATOR_MAP[target_lower]

    if version is not None:
        version_lower = version.lower()
        return mapping.get(version_lower)

    return mapping.get("default")
