"""
Acoustic Semantic Fixture Corpus.

Sprint: MRP-5F
Status: SEMANTIC_ONLY (no runtime topology generation)

These fixtures contain Export Objects with acoustic cad_semantics
for testing schema validation, translator awareness, and regression
continuity. They do NOT represent runtime-generatable CAD geometry.

Classification: SEMANTIC_ONLY
No topology generation tests use these fixtures.

Temporary Location Note:
This location (tests/cam/fixtures/acoustic/) is provisional pending
corpus reconciliation with the full MRP-5D regression corpus structure.
"""

from .fixture_generator import (
    create_dreadnought_semantic_fixture,
    create_jumbo_semantic_fixture,
    create_parlor_semantic_fixture,
    create_hollowbody_semantic_fixture,
    ACOUSTIC_FIXTURE_MANIFEST,
)

__all__ = [
    "create_dreadnought_semantic_fixture",
    "create_jumbo_semantic_fixture",
    "create_parlor_semantic_fixture",
    "create_hollowbody_semantic_fixture",
    "ACOUSTIC_FIXTURE_MANIFEST",
]
