"""Semantic validation tests for `validate_generator_record()` (GFR-001A).

Every guard is exercised on both sides. Branch coverage is a hard gate, and a
validator whose accept path is never taken is a validator nobody has shown is
usable — the failure mode where everything is rejected looks identical to a
correct one when only rejections are tested.

Structural type enforcement belongs to `test_generator_record.py`.
"""

from __future__ import annotations

import pytest

from app.generators.framework.capabilities import GeneratorCapability
from app.generators.framework.categories import GeneratorCategory
from app.generators.framework.errors import (
    GeneratorFrameworkError,
    GeneratorValidationError,
)
from app.generators.framework.generator_record import GeneratorRecordV1
from app.generators.framework.states import (
    GeneratorAuthority,
    GeneratorLifecycle,
)
from app.generators.framework.validation import validate_generator_record


def make_record(**overrides) -> GeneratorRecordV1:
    kwargs = dict(
        generator_id="neck.headstock",
        name="Neck and headstock generator",
        description="Generates neck, headstock and transition geometry.",
        category=GeneratorCategory.NECK_HEADSTOCK,
        implementation_path="app.generators.neck_headstock_generator",
    )
    kwargs.update(overrides)
    return GeneratorRecordV1(**kwargs)


class TestAcceptsValidRecords:
    """The fall-through path through every guard."""

    def test_minimal_record_validates(self):
        assert validate_generator_record(make_record()) is None

    def test_fully_populated_record_validates(self):
        record = make_record(
            capabilities=(
                GeneratorCapability.GEOMETRY_SYNTHESIS,
                GeneratorCapability.DXF_EXPORT,
            ),
            state=GeneratorLifecycle.ACTIVE,
            authority=GeneratorAuthority.CANONICAL,
            input_contracts=("neck_spec",),
            output_contracts=("neck_profile",),
            dependencies=("reference.profiles",),
            supported_workflows=("build.neck",),
            tags=("neck",),
        )
        assert validate_generator_record(record) is None

    def test_single_segment_id_validates(self):
        assert validate_generator_record(make_record(generator_id="body")) is None

    def test_deeply_dotted_id_validates(self):
        record = make_record(generator_id="cam.toolpath.pocket.rough")
        assert validate_generator_record(record) is None

    def test_id_with_digits_and_underscores_validates(self):
        record = make_record(generator_id="body_v2.outline_2d")
        assert validate_generator_record(record) is None

    def test_same_identifier_in_inputs_and_outputs_is_legal(self):
        """Duplicate rejection is per-field, deliberately.

        A transformation generator consumes and produces the same contract.
        Rejecting that would make a legitimate shape unrepresentable.
        """
        record = make_record(
            input_contracts=("body_outline",),
            output_contracts=("body_outline",),
        )
        assert validate_generator_record(record) is None


class TestIdentifierSyntax:
    """TC-20 — ids must survive URLs, filenames and log lines unquoted."""

    @pytest.mark.parametrize(
        "bad_id",
        [
            "Neck.Headstock",   # uppercase
            "1body",            # leading digit
            "neck..headstock",  # empty segment
            "neck.",            # trailing dot
            ".neck",            # leading dot
            "neck-headstock",   # hyphen
            "neck headstock",   # space
            "_neck",            # leading underscore
        ],
    )
    def test_malformed_id_is_rejected(self, bad_id):
        with pytest.raises(GeneratorValidationError, match="must be lowercase dotted"):
            validate_generator_record(make_record(generator_id=bad_id))

    def test_blank_id_is_rejected_before_syntax(self):
        """Blankness is reported as blankness, not as a syntax error."""
        with pytest.raises(GeneratorValidationError, match="generator_id must not be blank"):
            validate_generator_record(make_record(generator_id="   "))


class TestBlankStrings:
    """TC-21 — a present-but-empty string satisfies a type check while carrying
    no information, which is worse than a missing one."""

    @pytest.mark.parametrize("field_name", ["name", "description", "implementation_path"])
    def test_blank_scalar_is_rejected(self, field_name):
        with pytest.raises(GeneratorValidationError, match=f"{field_name} must not be blank"):
            validate_generator_record(make_record(**{field_name: "  "}))

    @pytest.mark.parametrize(
        "field_name",
        ["input_contracts", "output_contracts", "dependencies", "supported_workflows", "tags"],
    )
    def test_blank_tuple_member_is_rejected(self, field_name):
        with pytest.raises(GeneratorValidationError, match=rf"{field_name}\[0\] must not be blank"):
            validate_generator_record(make_record(**{field_name: ("",)}))

    def test_blank_member_index_is_reported(self):
        with pytest.raises(GeneratorValidationError, match=r"tags\[1\] must not be blank"):
            validate_generator_record(make_record(tags=("neck", " ")))


class TestImplementationPathSyntax:
    """TC-22 — syntax only. Existence is never checked, by design."""

    @pytest.mark.parametrize(
        "bad_path",
        ["app/generators/x", "app..generators", "app.", "1app.generators", "app generators"],
    )
    def test_malformed_path_is_rejected(self, bad_path):
        with pytest.raises(GeneratorValidationError, match="must be a dotted module path"):
            validate_generator_record(make_record(implementation_path=bad_path))

    def test_nonexistent_module_path_is_accepted(self):
        """A catalog records where an implementation *claims* to live.

        Proving the module is there is a runtime witness's job; this layer must
        not import anything to answer a validation question.
        """
        record = make_record(implementation_path="app.generators.does_not_exist")
        assert validate_generator_record(record) is None


class TestRecordVersion:
    """TC-19 — an unsupported version is rejected."""

    def test_unsupported_version_is_rejected(self):
        with pytest.raises(GeneratorValidationError, match="is not supported"):
            validate_generator_record(make_record(record_version="99"))

    def test_supported_version_is_accepted(self):
        assert validate_generator_record(make_record(record_version="1")) is None


class TestDuplicates:
    """TC-23 — duplicates rejected within each field, independently."""

    def test_duplicate_capability_is_rejected(self):
        record = make_record(
            capabilities=(GeneratorCapability.DXF_EXPORT, GeneratorCapability.DXF_EXPORT)
        )
        with pytest.raises(GeneratorValidationError, match="capabilities contains duplicate"):
            validate_generator_record(record)

    @pytest.mark.parametrize(
        "field_name",
        ["input_contracts", "output_contracts", "dependencies", "supported_workflows", "tags"],
    )
    def test_duplicate_string_entry_is_rejected(self, field_name):
        with pytest.raises(GeneratorValidationError, match=f"{field_name} contains duplicate"):
            validate_generator_record(make_record(**{field_name: ("a", "a")}))


class TestSelfDependency:
    """TC-24 — a generator cannot depend on itself."""

    def test_self_dependency_is_rejected(self):
        record = make_record(generator_id="neck.headstock", dependencies=("neck.headstock",))
        with pytest.raises(GeneratorValidationError, match="must not appear in its own"):
            validate_generator_record(record)

    def test_depending_on_something_else_is_accepted(self):
        record = make_record(generator_id="neck.headstock", dependencies=("body.outline",))
        assert validate_generator_record(record) is None


class TestLifecycleAuthorityConflicts:
    """TC-25 — only genuine contradictions are rejected."""

    def test_retired_cannot_be_canonical(self):
        record = make_record(
            state=GeneratorLifecycle.RETIRED, authority=GeneratorAuthority.CANONICAL
        )
        with pytest.raises(GeneratorValidationError, match="retired generator cannot be canonical"):
            validate_generator_record(record)

    def test_experimental_cannot_be_canonical(self):
        record = make_record(
            state=GeneratorLifecycle.EXPERIMENTAL, authority=GeneratorAuthority.CANONICAL
        )
        with pytest.raises(
            GeneratorValidationError, match="experimental generator cannot be canonical"
        ):
            validate_generator_record(record)

    def test_active_and_superseded_is_allowed(self):
        """Deliberately legal — the normal state of a working generator that
        something else has replaced, and the most useful thing to record."""
        record = make_record(
            state=GeneratorLifecycle.ACTIVE, authority=GeneratorAuthority.SUPERSEDED
        )
        assert validate_generator_record(record) is None

    def test_retired_non_canonical_is_allowed(self):
        record = make_record(
            state=GeneratorLifecycle.RETIRED, authority=GeneratorAuthority.SUPERSEDED
        )
        assert validate_generator_record(record) is None

    def test_experimental_advisory_is_allowed(self):
        record = make_record(
            state=GeneratorLifecycle.EXPERIMENTAL, authority=GeneratorAuthority.ADVISORY
        )
        assert validate_generator_record(record) is None

    def test_deprecated_canonical_is_allowed(self):
        """DEPRECATED still works and can still be the authority while a
        replacement lands. Only RETIRED and EXPERIMENTAL contradict CANONICAL."""
        record = make_record(
            state=GeneratorLifecycle.DEPRECATED, authority=GeneratorAuthority.CANONICAL
        )
        assert validate_generator_record(record) is None


class TestErrorHierarchy:
    """TC-26 — one root, and the ValueError mixin actually works."""

    def test_validation_error_is_a_framework_error(self):
        with pytest.raises(GeneratorFrameworkError):
            validate_generator_record(make_record(name=" "))

    def test_validation_error_is_a_value_error(self):
        """The mixin preserves ordinary `except ValueError` handling."""
        with pytest.raises(ValueError):
            validate_generator_record(make_record(name=" "))
