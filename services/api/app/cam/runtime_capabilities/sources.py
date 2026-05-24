"""
Capability Source Adapters.

Sprint: MRP-5V
Status: PROTOTYPE

Lightweight adapters that wrap existing domain-local registries.

Design principles:
  - Adapters do NOT modify source registries
  - Adapters translate to FederatedCapability
  - Source registries remain authoritative for their domain
"""

from __future__ import annotations

from typing import List, Optional

from .contracts import (
    CapabilityNamespace,
    CapabilitySource,
    FederatedCapability,
    GovernanceClassification,
    make_capability_id,
)


# -----------------------------------------------------------------------------
# CAM Operation Source Adapter
# -----------------------------------------------------------------------------

class CamOperationCapabilitySource(CapabilitySource):
    """
    Adapter for CAM operation registry (cam_operation_registry.py).

    Wraps CAM_OPERATION_REGISTRY without modifying it.
    """

    @property
    def source_name(self) -> str:
        return "cam_operation_registry"

    @property
    def namespace(self) -> CapabilityNamespace:
        return CapabilityNamespace.OPERATION

    def list_capability_ids(self) -> List[str]:
        """List all operation IDs from the CAM registry."""
        from app.cam.cam_operation_registry import list_supported_operations
        return list_supported_operations()

    def get_capability(self, local_id: str) -> Optional[FederatedCapability]:
        """Get a CAM operation as FederatedCapability."""
        from app.cam.cam_operation_registry import get_operation_capability

        cap = get_operation_capability(local_id)
        if cap is None:
            return None

        return self._to_federated(cap)

    def _to_federated(self, cap) -> FederatedCapability:
        """Convert CAMOperationCapability to FederatedCapability."""
        # Map maturity to governance classification
        maturity_to_governance = {
            "experimental": GovernanceClassification.INTERNAL_ONLY,
            "candidate": GovernanceClassification.DEVELOPER_EXPERIMENTAL,
            "governed": GovernanceClassification.PUBLIC_GOVERNED,
            "canonical": GovernanceClassification.PUBLIC_GOVERNED,
        }

        governance = maturity_to_governance.get(
            cap.maturity,
            GovernanceClassification.INTERNAL_ONLY,
        )

        # Build compatibility tags from operation capabilities
        compat_tags = set()
        if cap.lifecycle_supported:
            compat_tags.add("lifecycle")
        if cap.export_object_supported:
            compat_tags.add("export_object")
        if cap.machine_validation_supported:
            compat_tags.add("machine_validation")
        if cap.translator_validation_supported:
            compat_tags.add("translator_validation")
        if cap.rmos_persistence_supported:
            compat_tags.add("rmos_persistence")

        # Add geometry types as tags
        for geom in cap.supported_geometry_types:
            compat_tags.add(f"geometry:{geom}")

        return FederatedCapability(
            capability_id=make_capability_id(CapabilityNamespace.OPERATION, cap.operation),
            namespace=CapabilityNamespace.OPERATION,
            local_id=cap.operation,
            version="1.0.0",
            source_name=self.source_name,
            display_name=cap.operation.replace("_", " ").title(),
            description=cap.notes or "",
            governance_classification=governance,
            enabled=cap.lifecycle_supported,
            deterministic=True,
            replay_safe=True,
            compatibility_tags=compat_tags,
            domain_metadata={
                "maturity": cap.maturity,
                "exportability_class": cap.exportability_class,
                "preview_route": cap.preview_route,
                "lifecycle_route": cap.lifecycle_route,
                "machine_ready": cap.machine_ready,
                "machine_output_supported": cap.machine_output_supported,
                "required_machine_capabilities": cap.required_machine_capabilities,
                "required_translator_features": cap.required_translator_features,
                "test_coverage_score": cap.test_coverage_score,
                "lifecycle_stability_score": cap.lifecycle_stability_score,
            },
        )


# -----------------------------------------------------------------------------
# Translator Source Adapter
# -----------------------------------------------------------------------------

class TranslatorCapabilitySource(CapabilitySource):
    """
    Adapter for translator capability registry (translator_capability_registry.py).

    Wraps TRANSLATOR_CAPABILITY_REGISTRY without modifying it.
    """

    @property
    def source_name(self) -> str:
        return "translator_capability_registry"

    @property
    def namespace(self) -> CapabilityNamespace:
        return CapabilityNamespace.TRANSLATOR

    def list_capability_ids(self) -> List[str]:
        """List all translator IDs from the registry."""
        from app.cam.translator_capability_registry import list_translator_ids
        return list_translator_ids()

    def get_capability(self, local_id: str) -> Optional[FederatedCapability]:
        """Get a translator as FederatedCapability."""
        from app.cam.translator_capability_registry import get_translator_capability

        cap = get_translator_capability(local_id)
        if cap is None:
            return None

        return self._to_federated(cap)

    def _to_federated(self, cap) -> FederatedCapability:
        """Convert TranslatorCapability to FederatedCapability."""
        # Map maturity to governance classification
        maturity_to_governance = {
            "placeholder": GovernanceClassification.INTERNAL_ONLY,
            "candidate": GovernanceClassification.DEVELOPER_EXPERIMENTAL,
            "governed": GovernanceClassification.PUBLIC_GOVERNED,
            "canonical": GovernanceClassification.PUBLIC_GOVERNED,
        }

        governance = maturity_to_governance.get(
            cap.maturity,
            GovernanceClassification.INTERNAL_ONLY,
        )

        # Build compatibility tags
        compat_tags = set()

        # Output class
        compat_tags.add(f"output:{cap.output_class}")
        if cap.output_format_version:
            compat_tags.add(f"format:{cap.output_format_version}")

        # Category
        compat_tags.add(f"category:{cap.translator_category}")

        # Execution state
        compat_tags.add(f"state:{cap.execution_state}")

        # Supported operations
        for op in cap.supported_operations:
            compat_tags.add(f"supports:{op}")

        # Geometry types
        for geom in cap.supported_geometry_types:
            compat_tags.add(f"geometry:{geom}")

        # Unit systems
        for unit in cap.supported_units:
            compat_tags.add(f"unit:{unit}")

        # Determine enabled based on execution state
        enabled = cap.execution_state in ("governed_execution", "execution_planned")

        # Determine replay safety
        replay_safe = cap.execution_state != "execution_disabled"

        return FederatedCapability(
            capability_id=make_capability_id(CapabilityNamespace.TRANSLATOR, cap.translator_id),
            namespace=CapabilityNamespace.TRANSLATOR,
            local_id=cap.translator_id,
            version=cap.translator_version,
            source_name=self.source_name,
            display_name=cap.translator_name,
            description=cap.description or "",
            governance_classification=governance,
            enabled=enabled,
            deterministic=True,
            replay_safe=replay_safe,
            compatibility_tags=compat_tags,
            domain_metadata={
                "maturity": cap.maturity,
                "translator_category": cap.translator_category,
                "output_class": cap.output_class,
                "output_format_version": cap.output_format_version,
                "execution_state": cap.execution_state,
                "execution_supported": cap.execution_supported,
                "artifact_generation_supported": cap.artifact_generation_supported,
                "machine_output_supported": cap.machine_output_supported,
                "authorization_required": cap.authorization_required,
                "supported_operations": cap.supported_operations,
                "notes": cap.notes,
            },
        )


# -----------------------------------------------------------------------------
# Adapter Source Adapter
# -----------------------------------------------------------------------------

class AdapterCapabilitySource(CapabilitySource):
    """
    Adapter for runtime adapters (runtime_service/adapters.py).

    Wraps the adapter registry without modifying it.
    """

    @property
    def source_name(self) -> str:
        return "runtime_adapter_registry"

    @property
    def namespace(self) -> CapabilityNamespace:
        return CapabilityNamespace.ADAPTER

    def list_capability_ids(self) -> List[str]:
        """List all adapter IDs from the registry."""
        from app.cam.runtime_service import list_available_adapters
        return list_available_adapters()

    def get_capability(self, local_id: str) -> Optional[FederatedCapability]:
        """Get an adapter as FederatedCapability."""
        from app.cam.runtime_service import get_adapter, is_adapter_available

        if not is_adapter_available(local_id):
            return None

        adapter = get_adapter(local_id)
        if adapter is None:
            return None

        return self._to_federated(local_id, adapter)

    def _to_federated(self, local_id: str, adapter) -> FederatedCapability:
        """Convert RuntimeAdapter to FederatedCapability."""
        # Build compatibility tags
        compat_tags = {
            "runtime_adapter",
            f"adapter:{local_id}",
        }

        # Check if it's a mock adapter
        is_mock = "mock" in local_id.lower()
        if is_mock:
            compat_tags.add("mock")

        return FederatedCapability(
            capability_id=make_capability_id(CapabilityNamespace.ADAPTER, local_id),
            namespace=CapabilityNamespace.ADAPTER,
            local_id=local_id,
            version="1.0.0",
            source_name=self.source_name,
            display_name=local_id.replace("_", " ").title(),
            description=f"Runtime adapter: {local_id}",
            governance_classification=GovernanceClassification.DEVELOPER_EXPERIMENTAL,
            enabled=True,
            deterministic=True,
            replay_safe=True,
            compatibility_tags=compat_tags,
            domain_metadata={
                "is_mock": is_mock,
            },
        )


# -----------------------------------------------------------------------------
# Factory
# -----------------------------------------------------------------------------

def create_default_sources() -> List[CapabilitySource]:
    """
    Create the default set of capability sources.

    Returns:
        List of source adapters for existing registries
    """
    return [
        CamOperationCapabilitySource(),
        TranslatorCapabilitySource(),
        AdapterCapabilitySource(),
    ]


def register_default_sources(registry) -> None:
    """
    Register all default sources with a registry.

    Args:
        registry: CapabilityRegistry to populate
    """
    for source in create_default_sources():
        registry.register_source(source)
