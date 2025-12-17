"""
Parametric Generators Package - Bundle 31.0.2

Generators convert pattern parameters into RosetteParamSpec.
They are pure functions with no I/O.
"""

from .registry import (
    GENERATOR_REGISTRY,
    get_generator,
    list_generators,
    generate_spec,
)
from .basic_rings import basic_rings_v1
from .mosaic_band import mosaic_band_v1

__all__ = [
    "GENERATOR_REGISTRY",
    "get_generator",
    "list_generators",
    "generate_spec",
    "basic_rings_v1",
    "mosaic_band_v1",
]
