"""
MRP-4A: Translator Registry

Central registry for translator discovery, registration, and lookup.

Wraps and extends the existing translator_capability_registry.py
to provide multi-target translation support.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Type

from app.cam.translators.base.contracts import ExportTranslator, BaseTranslator
from app.cam.translators.base.capabilities import (
    TranslatorCapabilities,
    TranslatorCategory,
    TranslatorMaturity,
    ExecutionState,
)


TranslatorFactory = Callable[[], ExportTranslator]


class TranslatorRegistry:
    """
    Central registry for governed translators.

    Provides:
      - Translator registration
      - Discovery by target format
      - Capability inspection
      - Factory-based instantiation
    """

    def __init__(self):
        self._translators: Dict[str, TranslatorFactory] = {}
        self._capabilities: Dict[str, TranslatorCapabilities] = {}
        self._targets: Dict[str, List[str]] = {}

    def register(
        self,
        translator_id: str,
        factory: TranslatorFactory,
        capabilities: TranslatorCapabilities,
    ) -> None:
        """
        Register a translator with the registry.

        Args:
            translator_id: Unique identifier for the translator
            factory: Callable that creates translator instances
            capabilities: Capability declaration for the translator
        """
        if translator_id != capabilities.translator_id:
            raise ValueError(
                f"Translator ID mismatch: {translator_id} != {capabilities.translator_id}"
            )

        self._translators[translator_id] = factory
        self._capabilities[translator_id] = capabilities

        target = capabilities.target_format
        if target not in self._targets:
            self._targets[target] = []
        if translator_id not in self._targets[target]:
            self._targets[target].append(translator_id)

    def unregister(self, translator_id: str) -> bool:
        """
        Unregister a translator.

        Args:
            translator_id: Translator to remove

        Returns:
            True if translator was removed, False if not found
        """
        if translator_id not in self._translators:
            return False

        cap = self._capabilities.get(translator_id)
        if cap:
            target = cap.target_format
            if target in self._targets and translator_id in self._targets[target]:
                self._targets[target].remove(translator_id)

        del self._translators[translator_id]
        del self._capabilities[translator_id]
        return True

    def get(self, translator_id: str) -> Optional[ExportTranslator]:
        """
        Get a translator instance by ID.

        Args:
            translator_id: Translator identifier

        Returns:
            Translator instance or None if not found
        """
        factory = self._translators.get(translator_id)
        if factory is None:
            return None
        return factory()

    def get_capabilities(self, translator_id: str) -> Optional[TranslatorCapabilities]:
        """
        Get capabilities for a translator.

        Args:
            translator_id: Translator identifier

        Returns:
            TranslatorCapabilities or None if not found
        """
        return self._capabilities.get(translator_id)

    def list_all(self) -> List[str]:
        """List all registered translator IDs."""
        return list(self._translators.keys())

    def list_targets(self) -> List[str]:
        """List all supported target formats."""
        return list(self._targets.keys())

    def list_for_target(self, target: str) -> List[str]:
        """
        List translator IDs for a target format.

        Args:
            target: Target format (e.g., 'dxf', 'svg')

        Returns:
            List of translator IDs supporting that target
        """
        return self._targets.get(target, [])

    def list_governed(self) -> List[str]:
        """List translator IDs with governed execution state."""
        return [
            tid for tid, cap in self._capabilities.items()
            if cap.execution_state == ExecutionState.GOVERNED_EXECUTION
        ]

    def list_by_category(self, category: TranslatorCategory) -> List[str]:
        """
        List translator IDs by category.

        Args:
            category: TranslatorCategory to filter by

        Returns:
            List of translator IDs in that category
        """
        return [
            tid for tid, cap in self._capabilities.items()
            if cap.category == category
        ]

    def list_by_maturity(self, maturity: TranslatorMaturity) -> List[str]:
        """
        List translator IDs by maturity level.

        Args:
            maturity: TranslatorMaturity to filter by

        Returns:
            List of translator IDs at that maturity
        """
        return [
            tid for tid, cap in self._capabilities.items()
            if cap.maturity == maturity
        ]

    def supports_target(self, target: str) -> bool:
        """Check if registry has any translators for a target."""
        return target in self._targets and len(self._targets[target]) > 0


# Global registry instance
_registry: Optional[TranslatorRegistry] = None


def get_translator_registry() -> TranslatorRegistry:
    """Get the global translator registry instance."""
    global _registry
    if _registry is None:
        _registry = TranslatorRegistry()
        _initialize_default_translators(_registry)
    return _registry


def _initialize_default_translators(registry: TranslatorRegistry) -> None:
    """Initialize registry with default translators."""
    from app.cam.translators.base.capabilities import (
        dxf_serialization_capabilities,
        svg_visualization_capabilities,
    )

    # DXF R12 translator
    from app.cam.translators.dxf import BodyOutlineDxfTranslator

    registry.register(
        "body_outline_dxf_r12",
        lambda: BodyOutlineDxfTranslator(dxf_version="R12"),
        dxf_serialization_capabilities("body_outline_dxf_r12", "R12"),
    )

    # DXF R2000 translator
    registry.register(
        "body_outline_dxf_r2000",
        lambda: BodyOutlineDxfTranslator(dxf_version="R2000"),
        dxf_serialization_capabilities("body_outline_dxf_r2000", "R2000"),
    )

    # SVG translator (will be created in this sprint)
    try:
        from app.cam.translators.svg import BodyOutlineSvgTranslator

        registry.register(
            "body_outline_svg",
            lambda: BodyOutlineSvgTranslator(),
            svg_visualization_capabilities("body_outline_svg"),
        )
    except ImportError:
        pass


# Convenience functions

def register_translator(
    translator_id: str,
    factory: TranslatorFactory,
    capabilities: TranslatorCapabilities,
) -> None:
    """Register a translator with the global registry."""
    get_translator_registry().register(translator_id, factory, capabilities)


def get_translator(translator_id: str) -> Optional[ExportTranslator]:
    """Get a translator instance from the global registry."""
    return get_translator_registry().get(translator_id)


def list_translators() -> List[str]:
    """List all registered translator IDs."""
    return get_translator_registry().list_all()


def list_translators_for_target(target: str) -> List[str]:
    """List translator IDs for a target format."""
    return get_translator_registry().list_for_target(target)
