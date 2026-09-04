"""GFR — the generator framework's catalog value contracts.

**This package is a catalog and discovery authority, not an execution registry.**

It describes where generator implementations live and what they claim to do. It
does not call, wrap, or replace any of them. In particular it does not touch the
Art Studio rosette registry (`app.art_studio.services.generators.registry`),
whose contract is `Callable[[float, float, Dict], RosetteParamSpec]` and which
remains authoritative for its own execution.

    one top-level catalog authority
    domain registries stay authoritative for execution

GFR-001A ships the value contracts only:

    categories.py        GeneratorCategory      what a generator produces
    capabilities.py      GeneratorCapability    what a caller can ask of it
    states.py            GeneratorLifecycle     how far along it is
                         GeneratorAuthority     how much weight it carries
    errors.py            the single error hierarchy
    generator_record.py  GeneratorRecordV1      the immutable record
    validation.py        validate_generator_record()

The catalog itself — storage, duplicate-id rejection, and metadata queries —
arrives in GFR-001B. There is deliberately no `registry.py`, `discovery.py` or
`inventory.py` here yet: the catalog has to be written against a contract that
already exists and is already tested.

Zero registered records is the expected initial state, not a failure. Discovery,
when it lands, is opt-in only — a module joins the catalog by exposing a
`GENERATOR_RECORD`, never by being named suggestively.
"""

from __future__ import annotations

from .capabilities import GeneratorCapability
from .categories import GeneratorCategory
from .errors import (
    DuplicateGeneratorIdError,
    GeneratorCatalogError,
    GeneratorFrameworkError,
    GeneratorNotFoundError,
    GeneratorValidationError,
)
from .generator_record import SUPPORTED_RECORD_VERSIONS, GeneratorRecordV1
from .states import GeneratorAuthority, GeneratorLifecycle
from .validation import validate_generator_record

__all__ = [
    "GeneratorCategory",
    "GeneratorCapability",
    "GeneratorLifecycle",
    "GeneratorAuthority",
    "GeneratorRecordV1",
    "SUPPORTED_RECORD_VERSIONS",
    "validate_generator_record",
    "GeneratorFrameworkError",
    "GeneratorValidationError",
    "GeneratorCatalogError",
    "DuplicateGeneratorIdError",
    "GeneratorNotFoundError",
]
