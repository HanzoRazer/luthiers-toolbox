"""`GeneratorRecordV1` — the immutable catalog record.

A record describes **where an implementation lives and what it claims to do**.
It is not the implementation, and the catalog never imports one:

    Catalog record       describes WHERE an implementation lives
    Execution subsystem  imports / invokes / orchestrates it

`implementation_path` is a dotted string precisely so that holding a record
costs nothing and proves nothing. The catalog must never import it to answer a
query. A record asserting `implementation_path="app.generators.does_not_exist"`
is structurally valid and semantically valid; discovering that the module is
missing is a job for a runtime witness, not a value contract.

Why a second type rather than reusing `GeneratorDescriptor`
-----------------------------------------------------------
`GeneratorDescriptor` already exists at
`app/art_studio/schemas/generator_requests.py` as an Art Studio domain contract
and is left unchanged. This is a different concept — a framework-level catalog
entry, not an Art Studio request schema — so it gets its own name and its own
module rather than overloading one that a live subsystem depends on.

Structural vs semantic
----------------------
`__post_init__` enforces **structure**: every field holds the right Python type,
and every tuple really is a tuple. It never coerces. An immutable record must
never successfully exist holding a mutable collection, so a list is rejected
rather than silently converted — silent coercion would mean the record you
validated is not the record you stored.

Everything about *meaning* — blank strings, identifier syntax, duplicates,
self-dependency, supported versions, contradictory lifecycle/authority pairings
— belongs to `validate_generator_record()` in `validation.py`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .capabilities import GeneratorCapability
from .categories import GeneratorCategory
from .states import GeneratorAuthority, GeneratorLifecycle

SUPPORTED_RECORD_VERSIONS = frozenset({"1"})
"""Record schema versions this framework understands.

`record_version` is constructor-settable rather than `init=False`, so a caller
can build a record claiming an unsupported version and have
`validate_generator_record()` reject it. A field nobody can set is a field
nobody can test.
"""


def _require_str(value: object, field_name: str) -> None:
    """Structural: the field must hold a `str`.

    `bool` is not special-cased here because it is not a `str` subclass; the
    isinstance check already rejects it.
    """
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a str, got {type(value).__name__}"
        )


def _require_enum(value: object, expected: type, field_name: str) -> None:
    """Structural: the field must hold a member of `expected`.

    A bare string is rejected even when it equals a member's value. The
    vocabularies are `(str, Enum)` so a string compares equal to a member, which
    makes it easy to store the string by accident and never notice — until
    something asks for `.name` and gets an AttributeError far from the cause.
    """
    if not isinstance(value, expected):
        raise TypeError(
            f"{field_name} must be a {expected.__name__}, "
            f"got {type(value).__name__}"
        )


def _require_tuple_of(value: object, member_type: type, field_name: str) -> None:
    """Structural: the field must be a tuple, and every member the right type.

    The tuple check comes first and is phrased as `<field> must be a tuple` —
    a list is the overwhelmingly common mistake, and the message needs to say so
    plainly rather than complaining about the members of something that is not a
    tuple at all.
    """
    if not isinstance(value, tuple):
        raise TypeError(
            f"{field_name} must be a tuple, got {type(value).__name__}"
        )
    for index, member in enumerate(value):
        if not isinstance(member, member_type):
            raise TypeError(
                f"{field_name}[{index}] must be a {member_type.__name__}, "
                f"got {type(member).__name__}"
            )


@dataclass(frozen=True)
class GeneratorRecordV1:
    """One catalog entry. Immutable, hashable-by-value, and inert.

    Construction enforces structure only. Call `validate_generator_record()` for
    semantics — the two are separate so that a structurally impossible record
    cannot exist at all, while a merely questionable one can be built,
    inspected, and reported on.
    """

    generator_id: str
    """Stable identifier, unique within a catalog. Syntax is checked
    semantically, not here."""

    name: str
    """Human-readable name."""

    description: str
    """What this generator produces, in prose."""

    category: GeneratorCategory
    """Output domain. Exactly one."""

    implementation_path: str
    """Dotted module path, e.g. `app.generators.neck_headstock_generator`.

    **Descriptive metadata.** The catalog never imports it."""

    capabilities: Tuple[GeneratorCapability, ...] = ()
    """What a caller can ask of it. Order is not significant; duplicates are
    rejected semantically."""

    state: GeneratorLifecycle = GeneratorLifecycle.EXPERIMENTAL
    """Lifecycle. Defaults to EXPERIMENTAL: a record that has not said otherwise
    has not earned a stability claim."""

    authority: GeneratorAuthority = GeneratorAuthority.SUPPLEMENTARY
    """Standing. Defaults to SUPPLEMENTARY: CANONICAL is a claim that must be
    made deliberately, never inherited from a default."""

    input_contracts: Tuple[str, ...] = ()
    """Identifiers of what it consumes."""

    output_contracts: Tuple[str, ...] = ()
    """Identifiers of what it produces. The same identifier may legally appear
    in both inputs and outputs — that is what a transformation generator looks
    like — so duplicate rejection is per-field, never across fields."""

    dependencies: Tuple[str, ...] = ()
    """Other generator identifiers this one depends on."""

    supported_workflows: Tuple[str, ...] = ()
    """Named workflows this generator participates in."""

    tags: Tuple[str, ...] = ()
    """Free-form labels for search. Carry no framework meaning."""

    record_version: str = "1"
    """Schema version of this record. Validated against
    `SUPPORTED_RECORD_VERSIONS`."""

    def __post_init__(self) -> None:
        """Structural type enforcement. Rejects; never coerces."""
        _require_str(self.generator_id, "generator_id")
        _require_str(self.name, "name")
        _require_str(self.description, "description")
        _require_str(self.implementation_path, "implementation_path")
        _require_str(self.record_version, "record_version")

        _require_enum(self.category, GeneratorCategory, "category")
        _require_enum(self.state, GeneratorLifecycle, "state")
        _require_enum(self.authority, GeneratorAuthority, "authority")

        _require_tuple_of(self.capabilities, GeneratorCapability, "capabilities")
        _require_tuple_of(self.input_contracts, str, "input_contracts")
        _require_tuple_of(self.output_contracts, str, "output_contracts")
        _require_tuple_of(self.dependencies, str, "dependencies")
        _require_tuple_of(self.supported_workflows, str, "supported_workflows")
        _require_tuple_of(self.tags, str, "tags")


__all__ = ["GeneratorRecordV1", "SUPPORTED_RECORD_VERSIONS"]
