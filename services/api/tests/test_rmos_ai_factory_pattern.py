"""
Test RMOS AI domain factory pattern integrity.

This test ensures that the generator factory pattern is preserved across
migrations and refactors. The factory pattern is critical for RMOS AI search
functionality.

Key invariants:
1. make_candidate_generator_for_request() returns a callable generator
2. The generator can be invoked without crashing
3. Factory does NOT return direct JSON (must be a callable)

Run:
  cd services/api
  pytest tests/test_rmos_ai_factory_pattern.py -v
"""

from __future__ import annotations

from typing import Any, Dict

import pytest


def test_factory_returns_callable_not_json():
    """
    Ensure make_candidate_generator_for_request() returns a callable generator.
    
    This protects against refactors that accidentally replace the factory pattern
    with direct JSON generation (e.g., replacing with generate_json()).
    """
    from app.rmos.ai import make_candidate_generator_for_request
    
    # Import actual types
    try:
        from app.rmos.context import RmosContext
        from app.rmos.models import SearchBudgetSpec
        
        # Create real instances if possible
        ctx: Any = {"material_palette": "walnut_maple"}  # Minimal dict fallback
        budget: Any = SearchBudgetSpec(max_attempts=5, deterministic=True)
    except (ImportError, AttributeError, TypeError) as e:
        # Fallback to minimal mocks
        pytest.skip(f"Could not import RMOS types for test: {e}")
    
    # Factory should return a callable, not a direct result
    generator = make_candidate_generator_for_request(
        ctx=ctx,
        budget=budget,
    )
    
    assert callable(generator), (
        "Factory must return a callable generator, not direct JSON. "
        "This ensures the RMOS search loop can control invocation timing."
    )
    
    # The generator should be invocable with (prev, attempt) signature
    try:
        result = generator(prev=None, attempt=0)
        # Result should exist (even if stubbed/minimal under test)
        assert result is not None, "Generator invocation should return a result"
    except Exception as e:
        pytest.fail(f"Generator invocation failed: {e}")


def test_canonical_location_is_app_rmos_ai():
    """
    Verify that the canonical import resolves to app.rmos.ai module.
    
    This ensures we're not accidentally importing from the shim.
    """
    from app.rmos.ai import make_candidate_generator_for_request
    
    # Check module location
    module_name = make_candidate_generator_for_request.__module__
    
    assert module_name == "app.rmos.ai.generators", (
        f"Function should be from app.rmos.ai.generators, got: {module_name}"
    )


def test_constraints_from_context_exists():
    """
    Verify that constraints_from_context is properly exported.
    
    This function is used by RMOS production code to build generator constraints.
    """
    from app.rmos.ai import constraints_from_context
    
    assert callable(constraints_from_context), "constraints_from_context must be callable"
    
    # Verify it's from the canonical location
    assert constraints_from_context.__module__ == "app.rmos.ai.constraints"


def test_coerce_to_rosette_spec_exists():
    """
    Verify that coerce_to_rosette_spec is properly exported.
    
    This domain coercion function is used by RMOS AI search.
    """
    from app.rmos.ai import coerce_to_rosette_spec
    
    assert callable(coerce_to_rosette_spec), "coerce_to_rosette_spec must be callable"
    
    # Verify it's from the canonical location (not old safety module)
    assert coerce_to_rosette_spec.__module__ == "app.rmos.ai.coercion"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
