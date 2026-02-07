"""
Generator Registry - Bundle 31.0.2

Central registry for parametric generators.
Generators are versioned (e.g., basic_rings@1) to avoid breaking old patterns.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from ...schemas.rosette_params import RosetteParamSpec
from ...schemas.generator_requests import GeneratorDescriptor, GeneratorGenerateResponse


# Type alias for generator functions
GeneratorFn = Callable[[float, float, Dict[str, Any]], RosetteParamSpec]


# Registry: generator_key -> (callable, descriptor)
_REGISTRY: Dict[str, tuple[GeneratorFn, GeneratorDescriptor]] = {}


def register_generator(
    key: str,
    fn: GeneratorFn,
    name: str,
    description: str = "",
    param_hints: Optional[Dict[str, Any]] = None,
) -> None:
    """Register a generator function."""
    descriptor = GeneratorDescriptor(
        generator_key=key,
        name=name,
        description=description,
        param_hints=param_hints or {},
    )
    _REGISTRY[key] = (fn, descriptor)


def get_generator(key: str) -> Optional[GeneratorFn]:
    """Get a generator function by key."""
    entry = _REGISTRY.get(key)
    return entry[0] if entry else None


def list_generators() -> List[GeneratorDescriptor]:
    """List all available generators."""
    return [desc for (_, desc) in _REGISTRY.values()]


def generate_spec(
    generator_key: str,
    outer_diameter_mm: float,
    inner_diameter_mm: float,
    params: Dict[str, Any],
) -> GeneratorGenerateResponse:
    """
    Generate a RosetteParamSpec using the specified generator.

    Returns GeneratorGenerateResponse with spec and any warnings.
    """
    fn = get_generator(generator_key)
    if fn is None:
        raise ValueError(f"Unknown generator: {generator_key}")

    warnings: List[str] = []

    try:
        spec = fn(outer_diameter_mm, inner_diameter_mm, params)
    except (ValueError, TypeError, KeyError) as e:  # WP-1: narrowed from except Exception
        warnings.append(f"Generator error: {str(e)}")
        # Return a minimal fallback spec
        from ...schemas.rosette_params import RosetteParamSpec
        spec = RosetteParamSpec(
            outer_diameter_mm=outer_diameter_mm,
            inner_diameter_mm=inner_diameter_mm,
            ring_params=[],
        )

    return GeneratorGenerateResponse(
        spec=spec,
        generator_key=generator_key,
        warnings=warnings,
    )


# Convenience accessor for the registry
GENERATOR_REGISTRY = _REGISTRY
