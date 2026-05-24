"""
Runtime Service Adapter Registry.

Sprint: MRP-5Q/R
Status: PROTOTYPE

Provides adapter discovery and invocation for the runtime service.
Currently supports mock adapter only for deterministic prototype execution.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Protocol
import hashlib
import uuid

from app.cam.runtime_provenance import stable_json_dumps


class RuntimeAdapter(Protocol):
    """Protocol for runtime adapters."""

    @property
    def adapter_id(self) -> str:
        """Unique adapter identifier."""
        ...

    @property
    def is_deterministic(self) -> bool:
        """Whether adapter produces deterministic output."""
        ...

    def execute(
        self,
        topology_hash: str,
        artifact_intent: str,
        metadata: Dict[str, Any],
    ) -> "AdapterExecutionResult":
        """Execute adapter and produce artifact."""
        ...


@dataclass
class AdapterExecutionResult:
    """Result of adapter execution."""

    adapter_id: str
    artifact_id: str
    artifact_bytes: bytes
    artifact_hash: str
    artifact_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def artifact_size(self) -> int:
        return len(self.artifact_bytes)


class MockRuntimeAdapter:
    """
    Mock adapter for deterministic prototype execution.

    Produces deterministic STEP-like output based on topology hash.
    Used for testing and development without real CAD kernel.
    """

    def __init__(self):
        self._execution_count = 0

    @property
    def adapter_id(self) -> str:
        return "mock"

    @property
    def is_deterministic(self) -> bool:
        return True

    def execute(
        self,
        topology_hash: str,
        artifact_intent: str,
        metadata: Dict[str, Any],
    ) -> AdapterExecutionResult:
        """Execute mock adapter producing deterministic output."""
        self._execution_count += 1

        artifact_id = f"artifact-{uuid.uuid4()}"

        content = self._generate_deterministic_content(
            topology_hash=topology_hash,
            artifact_intent=artifact_intent,
            metadata=metadata,
        )

        content_bytes = content.encode("utf-8")
        content_hash = hashlib.sha256(content_bytes).hexdigest()[:16]

        return AdapterExecutionResult(
            adapter_id=self.adapter_id,
            artifact_id=artifact_id,
            artifact_bytes=content_bytes,
            artifact_hash=content_hash,
            artifact_type=artifact_intent,
            metadata={
                "mock_execution": True,
                "deterministic": True,
                **metadata,
            },
        )

    def _generate_deterministic_content(
        self,
        topology_hash: str,
        artifact_intent: str,
        metadata: Dict[str, Any],
    ) -> str:
        """Generate deterministic mock STEP content."""
        return f"""\
ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('Certified Runtime Service Mock Output'),'2;1');
FILE_NAME('certified_{topology_hash}.stp','2026-01-01T00:00:00',('CertifiedRuntimeService'),('Luthiers Toolbox'),'MRP-5Q/R Prototype','MockRuntimeAdapter','');
FILE_SCHEMA(('AUTOMOTIVE_DESIGN'));
ENDSEC;
DATA;
/* Deterministic mock artifact */
/* Topology hash: {topology_hash} */
/* Artifact intent: {artifact_intent} */
#1=PRODUCT('CertifiedMock','Certified Mock Product',$,(#2));
#2=PRODUCT_CONTEXT('',#3,'mechanical');
#3=APPLICATION_CONTEXT('certified runtime');
ENDSEC;
END-ISO-10303-21;
"""

    @property
    def execution_count(self) -> int:
        return self._execution_count


class AdapterRegistry:
    """
    Registry of available runtime adapters.

    MRP-5Q/R: Only mock adapter is registered.
    Future sprints may add CadQuery, Build123d adapters.
    """

    def __init__(self):
        self._adapters: Dict[str, Callable[[], RuntimeAdapter]] = {}
        self._register_defaults()

    def _register_defaults(self):
        """Register default adapters."""
        self.register("mock", MockRuntimeAdapter)

    def register(
        self,
        adapter_id: str,
        factory: Callable[[], RuntimeAdapter],
    ) -> None:
        """Register an adapter factory."""
        self._adapters[adapter_id] = factory

    def get(self, adapter_id: str) -> Optional[RuntimeAdapter]:
        """Get an adapter instance by ID."""
        factory = self._adapters.get(adapter_id)
        if factory:
            return factory()
        return None

    def is_available(self, adapter_id: str) -> bool:
        """Check if an adapter is available."""
        return adapter_id in self._adapters

    def list_available(self) -> List[str]:
        """List available adapter IDs."""
        return list(self._adapters.keys())


_global_registry: Optional[AdapterRegistry] = None


def get_adapter_registry() -> AdapterRegistry:
    """Get the global adapter registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = AdapterRegistry()
    return _global_registry


def get_adapter(adapter_id: str) -> Optional[RuntimeAdapter]:
    """Get an adapter instance from the global registry."""
    return get_adapter_registry().get(adapter_id)


def is_adapter_available(adapter_id: str) -> bool:
    """Check if an adapter is available in the global registry."""
    return get_adapter_registry().is_available(adapter_id)


def list_available_adapters() -> List[str]:
    """List available adapter IDs from the global registry."""
    return get_adapter_registry().list_available()
