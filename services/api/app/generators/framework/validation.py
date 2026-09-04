"""Semantic validation for `GeneratorRecordV1`.

The second rung of the responsibility ladder:

    __post_init__              structural — right Python types, tuples are tuples
    validate_generator_record  semantic   — do the values mean anything sensible
    catalog (GFR-001B)         storage and metadata queries
    execution subsystems       import / invoke / orchestrate

By the time a record reaches this function it is already structurally sound, so
nothing here re-checks types. What it checks is meaning: identifiers that parse,
strings that are not blank, no duplicates within a field, no self-dependency, a
version the framework understands, and a lifecycle/authority pairing that is not
self-contradictory.

Validation is **pure and total**: it raises `GeneratorValidationError` on the
first problem and otherwise returns `None`. It reads no files, imports no
implementation, and never touches `implementation_path` beyond checking that it
is shaped like a dotted module path. Whether that module exists is a runtime
question this layer deliberately cannot answer.
"""

from __future__ import annotations

import re
from typing import Sequence, Tuple

from .errors import GeneratorValidationError
from .generator_record import SUPPORTED_RECORD_VERSIONS, GeneratorRecordV1
from .states import GeneratorAuthority, GeneratorLifecycle

GENERATOR_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$")
"""Lowercase dotted segments, each starting with a letter.

Deliberately narrower than Python identifier rules. A catalog id appears in
URLs, filenames and log lines, so it is restricted to a form that survives all
three without quoting.
"""

MODULE_PATH_PATTERN = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$"
)
"""Dotted Python module path. Syntax only — existence is never checked."""


def _reject_blank(value: str, field_name: str) -> None:
    """A present-but-empty string is worse than a missing one: it satisfies a
    type check while carrying no information."""
    if not value.strip():
        raise GeneratorValidationError(f"{field_name} must not be blank")


def _reject_duplicates(values: Sequence[object], field_name: str) -> None:
    """Duplicates are rejected **within** each field, independently.

    Deliberately not across fields: the same identifier appearing once in
    `input_contracts` and once in `output_contracts` is exactly what a
    transformation or compatibility generator looks like, and rejecting it would
    make that legitimate shape unrepresentable.
    """
    seen: set = set()
    for item in values:
        if item in seen:
            raise GeneratorValidationError(
                f"{field_name} contains duplicate entry: {item!r}"
            )
        seen.add(item)


def _reject_blank_members(values: Tuple[str, ...], field_name: str) -> None:
    """No blank members inside a string tuple."""
    for index, item in enumerate(values):
        if not item.strip():
            raise GeneratorValidationError(
                f"{field_name}[{index}] must not be blank"
            )


def validate_generator_record(record: GeneratorRecordV1) -> None:
    """Validate a structurally-sound record's semantics.

    Raises:
        GeneratorValidationError: on the first semantic problem found. Also a
            `ValueError`, so ordinary `except ValueError` handling works.

    Returns:
        None. A record that returns is valid at this layer — which is a claim
        about the record's *values*, not about whether its implementation
        exists or is reachable.
    """
    _reject_blank(record.generator_id, "generator_id")
    if not GENERATOR_ID_PATTERN.match(record.generator_id):
        raise GeneratorValidationError(
            f"generator_id {record.generator_id!r} must be lowercase dotted "
            "segments, each starting with a letter"
        )

    _reject_blank(record.name, "name")
    _reject_blank(record.description, "description")

    _reject_blank(record.implementation_path, "implementation_path")
    if not MODULE_PATH_PATTERN.match(record.implementation_path):
        raise GeneratorValidationError(
            f"implementation_path {record.implementation_path!r} must be a "
            "dotted module path"
        )

    if record.record_version not in SUPPORTED_RECORD_VERSIONS:
        raise GeneratorValidationError(
            f"record_version {record.record_version!r} is not supported; "
            f"supported versions are {sorted(SUPPORTED_RECORD_VERSIONS)}"
        )

    _reject_duplicates(record.capabilities, "capabilities")
    for field_name in (
        "input_contracts",
        "output_contracts",
        "dependencies",
        "supported_workflows",
        "tags",
    ):
        values: Tuple[str, ...] = getattr(record, field_name)
        _reject_blank_members(values, field_name)
        _reject_duplicates(values, field_name)

    if record.generator_id in record.dependencies:
        raise GeneratorValidationError(
            f"generator_id {record.generator_id!r} must not appear in its own "
            "dependencies"
        )

    # Lifecycle/authority pairings that contradict themselves.
    #
    # Only genuine contradictions are rejected. ACTIVE + SUPERSEDED is allowed
    # on purpose — it is the normal state of a working generator that something
    # else has replaced, and the most useful thing a catalog can record.
    if (
        record.state is GeneratorLifecycle.RETIRED
        and record.authority is GeneratorAuthority.CANONICAL
    ):
        raise GeneratorValidationError(
            "a retired generator cannot be canonical: nothing can depend on an "
            "implementation that is no longer callable"
        )
    if (
        record.state is GeneratorLifecycle.EXPERIMENTAL
        and record.authority is GeneratorAuthority.CANONICAL
    ):
        raise GeneratorValidationError(
            "an experimental generator cannot be canonical: its contract may "
            "change without notice, so nothing can safely be built on it"
        )


__all__ = [
    "validate_generator_record",
    "GENERATOR_ID_PATTERN",
    "MODULE_PATH_PATTERN",
]
