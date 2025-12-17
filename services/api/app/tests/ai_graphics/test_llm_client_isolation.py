"""
Dependency enforcement tests for llm_client.py

This test ensures that llm_client.py (transport layer) does NOT import
from providers.py (high-level adapter). The dependency must be one-way:

    providers.py → llm_client.py  (OK)
    llm_client.py → providers.py  (FORBIDDEN)

This architectural constraint ensures:
1. Clean separation of concerns
2. Transport layer has no business logic dependencies
3. Easy testing of transport layer in isolation
"""
import ast
import re
from pathlib import Path

import pytest


# Path to the llm_client.py file
LLM_CLIENT_PATH = Path(__file__).parent.parent.parent / "_experimental" / "ai_graphics" / "services" / "llm_client.py"
PROVIDERS_PATH = Path(__file__).parent.parent.parent / "_experimental" / "ai_graphics" / "services" / "providers.py"


class TestLLMClientIsolation:
    """Tests ensuring llm_client.py has no forbidden imports."""

    def test_llm_client_does_not_import_providers(self):
        """
        llm_client.py must NOT import from providers.py.

        This enforces the one-way dependency: providers → llm_client.
        """
        assert LLM_CLIENT_PATH.exists(), f"llm_client.py not found at {LLM_CLIENT_PATH}"

        source = LLM_CLIENT_PATH.read_text(encoding="utf-8")

        # Parse the source as AST
        tree = ast.parse(source)

        # Collect all import statements
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                imports.append(module)

        # Check that no import references 'providers'
        forbidden_patterns = ["providers", "provider"]
        violations = []

        for imp in imports:
            for pattern in forbidden_patterns:
                if pattern in imp.lower():
                    violations.append(imp)

        assert not violations, (
            f"llm_client.py has forbidden imports from providers: {violations}\n"
            "The transport layer (llm_client.py) must not import from the "
            "high-level adapter (providers.py). This is a one-way dependency."
        )

    def test_llm_client_has_no_domain_model_imports(self):
        """
        llm_client.py should not import domain models like RosetteParamSpec.

        Domain-specific types belong in providers.py, not the transport layer.
        """
        assert LLM_CLIENT_PATH.exists(), f"llm_client.py not found at {LLM_CLIENT_PATH}"

        source = LLM_CLIENT_PATH.read_text(encoding="utf-8")

        # Domain models that should NOT be in llm_client.py
        forbidden_types = [
            "RosetteParamSpec",
            "RingParam",
            "AiRosetteSuggestion",
            "AiFeasibilitySnapshot",
        ]

        for dtype in forbidden_types:
            assert dtype not in source, (
                f"llm_client.py imports forbidden domain type: {dtype}\n"
                "Transport layer should not know about domain models."
            )

    def test_providers_imports_llm_client(self):
        """
        providers.py SHOULD import from llm_client.py.

        This verifies the correct dependency direction.
        """
        assert PROVIDERS_PATH.exists(), f"providers.py not found at {PROVIDERS_PATH}"

        source = PROVIDERS_PATH.read_text(encoding="utf-8")

        assert "from .llm_client import" in source or "import llm_client" in source, (
            "providers.py should import from llm_client.py\n"
            "The high-level adapter should use the transport layer."
        )

    def test_llm_client_exports_transport_primitives(self):
        """
        llm_client.py should export transport-related classes and functions.
        """
        assert LLM_CLIENT_PATH.exists(), f"llm_client.py not found at {LLM_CLIENT_PATH}"

        source = LLM_CLIENT_PATH.read_text(encoding="utf-8")

        # Expected transport-layer exports
        expected_exports = [
            "LLMClient",
            "LLMConfig",
            "LLMResponse",
            "LLMClientError",
        ]

        for export in expected_exports:
            assert export in source, (
                f"llm_client.py missing expected export: {export}\n"
                "Transport layer should define transport primitives."
            )


class TestProviderInterface:
    """Tests for the providers.py interface."""

    def test_providers_exports_protocol(self):
        """providers.py should export the AiProvider protocol."""
        assert PROVIDERS_PATH.exists(), f"providers.py not found at {PROVIDERS_PATH}"

        source = PROVIDERS_PATH.read_text(encoding="utf-8")

        assert "class AiProvider" in source, (
            "providers.py should define AiProvider protocol"
        )
        assert "Protocol" in source, (
            "providers.py should use typing.Protocol for AiProvider"
        )

    def test_providers_has_stub_implementation(self):
        """providers.py should have a StubProvider for testing."""
        assert PROVIDERS_PATH.exists(), f"providers.py not found at {PROVIDERS_PATH}"

        source = PROVIDERS_PATH.read_text(encoding="utf-8")

        assert "class StubProvider" in source, (
            "providers.py should define StubProvider for testing"
        )

    def test_providers_has_registry_functions(self):
        """providers.py should have get_provider/set_provider registry."""
        assert PROVIDERS_PATH.exists(), f"providers.py not found at {PROVIDERS_PATH}"

        source = PROVIDERS_PATH.read_text(encoding="utf-8")

        assert "def get_provider" in source, (
            "providers.py should define get_provider() function"
        )
        assert "def set_provider" in source, (
            "providers.py should define set_provider() function"
        )

    def test_backward_compatible_function(self):
        """
        providers.py should export generate_rosette_param_candidates
        for backward compatibility.
        """
        assert PROVIDERS_PATH.exists(), f"providers.py not found at {PROVIDERS_PATH}"

        source = PROVIDERS_PATH.read_text(encoding="utf-8")

        assert "def generate_rosette_param_candidates" in source, (
            "providers.py should define generate_rosette_param_candidates "
            "for backward compatibility"
        )
