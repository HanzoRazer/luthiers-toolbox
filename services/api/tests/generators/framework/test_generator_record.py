"""Structural enforcement tests for `GeneratorRecordV1` (GFR-001A).

`__post_init__` owns **structure**: right Python types, and tuples that really
are tuples. It rejects; it never coerces. Every guard below is exercised on both
sides — the rejection *and* the successful fall-through — because branch
coverage is a hard gate and a guard that is only ever tripped is a guard whose
pass path is unproven.

Semantics (blank strings, id syntax, duplicates, versions, lifecycle pairings)
belong to `test_validation.py`.
"""

from __future__ import annotations

import dataclasses

import pytest

from app.generators.framework.capabilities import GeneratorCapability
from app.generators.framework.categories import GeneratorCategory
from app.generators.framework.generator_record import (
    SUPPORTED_RECORD_VERSIONS,
    GeneratorRecordV1,
)
from app.generators.framework.states import (
    GeneratorAuthority,
    GeneratorLifecycle,
)


def make_record(**overrides) -> GeneratorRecordV1:
    """A minimal structurally-valid record, with targeted overrides."""
    kwargs = dict(
        generator_id="neck.headstock",
        name="Neck and headstock generator",
        description="Generates neck, headstock and transition geometry.",
        category=GeneratorCategory.NECK_HEADSTOCK,
        implementation_path="app.generators.neck_headstock_generator",
    )
    kwargs.update(overrides)
    return GeneratorRecordV1(**kwargs)


class TestConstructsWithValidStructure:
    """TC-10 — the fall-through path: every guard passes."""

    def test_minimal_record_constructs(self):
        record = make_record()
        assert record.generator_id == "neck.headstock"
        assert record.category is GeneratorCategory.NECK_HEADSTOCK

    def test_defaults_are_conservative(self):
        """A record that has not claimed stability or authority gets neither."""
        record = make_record()
        assert record.state is GeneratorLifecycle.EXPERIMENTAL
        assert record.authority is GeneratorAuthority.SUPPLEMENTARY
        assert record.record_version == "1"
        assert record.capabilities == ()
        assert record.input_contracts == ()
        assert record.output_contracts == ()
        assert record.dependencies == ()
        assert record.supported_workflows == ()
        assert record.tags == ()

    def test_fully_populated_record_constructs(self):
        """Exercises every tuple guard's member loop with real members."""
        record = make_record(
            capabilities=(
                GeneratorCapability.GEOMETRY_SYNTHESIS,
                GeneratorCapability.DXF_EXPORT,
            ),
            state=GeneratorLifecycle.ACTIVE,
            authority=GeneratorAuthority.CANONICAL,
            input_contracts=("neck_spec", "scale_length_mm"),
            output_contracts=("neck_profile", "headstock_outline"),
            dependencies=("reference.profiles",),
            supported_workflows=("build.neck",),
            tags=("neck", "headstock"),
            record_version="1",
        )
        assert len(record.capabilities) == 2
        assert record.authority is GeneratorAuthority.CANONICAL

    def test_record_is_frozen(self):
        record = make_record()
        with pytest.raises(dataclasses.FrozenInstanceError):
            record.generator_id = "other"  # type: ignore[misc]

    def test_records_compare_by_value(self):
        assert make_record() == make_record()


class TestRejectsWrongScalarTypes:
    """TC-11 — scalars are structurally type-checked, not only tuples."""

    @pytest.mark.parametrize(
        "field_name",
        [
            "generator_id",
            "name",
            "description",
            "implementation_path",
            "record_version",
        ],
    )
    def test_non_str_scalar_is_rejected(self, field_name):
        with pytest.raises(TypeError, match=f"{field_name} must be a str"):
            make_record(**{field_name: 123})

    def test_a_callable_where_a_string_belongs_is_rejected(self):
        """The catalog stores paths, never callables. Handing it the function
        itself is the mistake this guard exists to catch."""
        with pytest.raises(TypeError, match="implementation_path must be a str"):
            make_record(implementation_path=make_record)


class TestRejectsWrongEnumTypes:
    """TC-12 — enum fields must hold enum members, not equal-comparing strings.

    The vocabularies are `(str, Enum)`, so `"body_geometry" == GeneratorCategory
    .BODY_GEOMETRY` is True. That makes storing the bare string easy to do by
    accident and impossible to notice until something asks for `.name`.
    """

    def test_bare_string_category_is_rejected(self):
        with pytest.raises(TypeError, match="category must be a GeneratorCategory"):
            make_record(category="body_geometry")

    def test_bare_string_state_is_rejected(self):
        with pytest.raises(TypeError, match="state must be a GeneratorLifecycle"):
            make_record(state="active")

    def test_bare_string_authority_is_rejected(self):
        with pytest.raises(TypeError, match="authority must be a GeneratorAuthority"):
            make_record(authority="canonical")

    def test_wrong_enum_family_is_rejected(self):
        """A lifecycle member where a category belongs."""
        with pytest.raises(TypeError, match="category must be a GeneratorCategory"):
            make_record(category=GeneratorLifecycle.ACTIVE)


class TestRejectsNonTupleCollections:
    """TC-03 — a mutable collection must never enter an immutable record.

    Rejection, never coercion: silently converting a list would mean the record
    you validated is not the record you stored.
    """

    def test_list_capabilities_is_rejected(self):
        with pytest.raises(TypeError, match="capabilities must be a tuple"):
            make_record(capabilities=[GeneratorCapability.DXF_EXPORT])

    @pytest.mark.parametrize(
        "field_name",
        [
            "input_contracts",
            "output_contracts",
            "dependencies",
            "supported_workflows",
            "tags",
        ],
    )
    def test_list_string_field_is_rejected(self, field_name):
        with pytest.raises(TypeError, match=f"{field_name} must be a tuple"):
            make_record(**{field_name: ["value"]})

    def test_set_is_rejected(self):
        """A set is immutable in neither ordering nor membership."""
        with pytest.raises(TypeError, match="tags must be a tuple"):
            make_record(tags={"neck"})

    def test_bare_string_is_rejected_where_a_tuple_belongs(self):
        """A string is iterable, so coercion would have silently produced a
        tuple of single characters."""
        with pytest.raises(TypeError, match="tags must be a tuple"):
            make_record(tags="neck")

    def test_no_coercion_occurred(self):
        """The record must not exist at all — not exist with a fixed-up value."""
        with pytest.raises(TypeError):
            make_record(tags=["neck"])


class TestRejectsWrongTupleMemberTypes:
    """TC-13 — member types are checked, with the offending index reported."""

    def test_non_capability_member_is_rejected(self):
        with pytest.raises(
            TypeError, match=r"capabilities\[1\] must be a GeneratorCapability"
        ):
            make_record(
                capabilities=(GeneratorCapability.DXF_EXPORT, "svg_export")
            )

    def test_non_str_member_in_string_tuple_is_rejected(self):
        with pytest.raises(TypeError, match=r"tags\[0\] must be a str"):
            make_record(tags=(1,))

    def test_index_in_message_points_at_the_offender(self):
        with pytest.raises(TypeError, match=r"dependencies\[2\] must be a str"):
            make_record(dependencies=("a", "b", 3))


class TestSupportedVersions:
    """TC-14 — the version constant is a frozenset and includes "1"."""

    def test_supported_versions_contains_one(self):
        assert "1" in SUPPORTED_RECORD_VERSIONS

    def test_supported_versions_is_immutable(self):
        assert isinstance(SUPPORTED_RECORD_VERSIONS, frozenset)

    def test_record_version_is_constructor_settable(self):
        """Not `init=False` — a version nobody can set is a version nobody can
        test rejecting."""
        record = make_record(record_version="99")
        assert record.record_version == "99"
