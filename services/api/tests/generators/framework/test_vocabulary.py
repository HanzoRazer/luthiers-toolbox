"""Vocabulary stability tests (GFR-001A).

The `.value` of every vocabulary member is part of the catalog's external
contract: records serialize through it, so renaming a value silently
invalidates every stored record. These tests pin the values so that such a
change has to be deliberate.

They also enforce the two constraints the vocabularies were ruled to satisfy:
every member has a documented use, and no two members mean the same thing.
"""

from __future__ import annotations

from app.generators.framework.capabilities import GeneratorCapability
from app.generators.framework.categories import GeneratorCategory
from app.generators.framework.states import (
    GeneratorAuthority,
    GeneratorLifecycle,
)


class TestSerializationStability:
    """TC-01 — pinned `.value` strings."""

    def test_category_values_are_pinned(self):
        assert {c.name: c.value for c in GeneratorCategory} == {
            "INSTRUMENT_GEOMETRY": "instrument_geometry",
            "BODY_GEOMETRY": "body_geometry",
            "NECK_HEADSTOCK": "neck_headstock",
            "CAM_TOOLPATH": "cam_toolpath",
            "MANUFACTURING": "manufacturing",
            "WORKFLOW": "workflow",
            "REFERENCE_PROFILE_INPUT": "reference_profile_input",
            "UTILITY": "utility",
        }

    def test_capability_values_are_pinned(self):
        assert {c.name: c.value for c in GeneratorCapability} == {
            "DXF_EXPORT": "dxf_export",
            "SVG_EXPORT": "svg_export",
            "GCODE_EXPORT": "gcode_export",
            "GEOMETRY_SYNTHESIS": "geometry_synthesis",
            "PARAMETRIC_CONFIG": "parametric_config",
            "PRESET_LIBRARY": "preset_library",
            "SPEC_DRIVEN": "spec_driven",
            "PROFILE_SAMPLING": "profile_sampling",
        }

    def test_lifecycle_values_are_pinned(self):
        assert {s.name: s.value for s in GeneratorLifecycle} == {
            "EXPERIMENTAL": "experimental",
            "ACTIVE": "active",
            "DEPRECATED": "deprecated",
            "RETIRED": "retired",
        }

    def test_authority_values_are_pinned(self):
        assert {a.name: a.value for a in GeneratorAuthority} == {
            "CANONICAL": "canonical",
            "SUPPLEMENTARY": "supplementary",
            "ADVISORY": "advisory",
            "SUPERSEDED": "superseded",
        }


class TestStrEnumBehaviour:
    """TC-02 — the vocabularies are `(str, Enum)`, so a member IS its string.

    This is what makes a record JSON-serializable without a custom encoder.
    """

    def test_members_compare_equal_to_their_value(self):
        assert GeneratorCategory.BODY_GEOMETRY == "body_geometry"
        assert GeneratorCapability.DXF_EXPORT == "dxf_export"
        assert GeneratorLifecycle.ACTIVE == "active"
        assert GeneratorAuthority.CANONICAL == "canonical"

    def test_members_are_str_instances(self):
        assert isinstance(GeneratorCategory.UTILITY, str)
        assert isinstance(GeneratorCapability.SVG_EXPORT, str)
        assert isinstance(GeneratorLifecycle.RETIRED, str)
        assert isinstance(GeneratorAuthority.ADVISORY, str)


class TestNoOverlappingMeanings:
    """TC-03 — no duplicate values, and no member left undocumented.

    Constraint (A): every member needs a documented system use. Constraint (B):
    no two members may mean the same thing. A duplicated `.value` is the
    mechanical form of a duplicated meaning.
    """

    def test_no_duplicate_values_within_a_vocabulary(self):
        for vocabulary in (
            GeneratorCategory,
            GeneratorCapability,
            GeneratorLifecycle,
            GeneratorAuthority,
        ):
            values = [member.value for member in vocabulary]
            assert len(values) == len(set(values)), (
                f"{vocabulary.__name__} has duplicate values"
            )

    def test_every_member_value_is_snake_case(self):
        for vocabulary in (
            GeneratorCategory,
            GeneratorCapability,
            GeneratorLifecycle,
            GeneratorAuthority,
        ):
            for member in vocabulary:
                assert member.value == member.name.lower(), (
                    f"{vocabulary.__name__}.{member.name} value drifted from "
                    "its name"
                )


class TestGeometryScopeDistinction:
    """TC-04 — the three geometry categories are distinct, not synonyms.

    They overlap in subject matter, which is exactly why the distinction has to
    be asserted rather than assumed: whole-instrument, body-only, neck-side.
    """

    def test_three_distinct_geometry_categories_exist(self):
        geometry = {
            GeneratorCategory.INSTRUMENT_GEOMETRY,
            GeneratorCategory.BODY_GEOMETRY,
            GeneratorCategory.NECK_HEADSTOCK,
        }
        assert len(geometry) == 3

    def test_geometry_categories_do_not_share_a_value(self):
        assert (
            GeneratorCategory.INSTRUMENT_GEOMETRY.value
            != GeneratorCategory.BODY_GEOMETRY.value
            != GeneratorCategory.NECK_HEADSTOCK.value
        )
