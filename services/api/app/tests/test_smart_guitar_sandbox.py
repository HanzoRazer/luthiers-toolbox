"""
Smart Guitar Sandbox Tests (SG-SBX-0.1)
=======================================

Unit tests for validator + plan determinism + required ops/templates.
"""

from __future__ import annotations

import pytest

from app.sandboxes.smart_guitar.planner import generate_plan
from app.sandboxes.smart_guitar.presets import standard_all, standard_headed, standard_headless
from app.sandboxes.smart_guitar.schemas import (
    BodyDims,
    CavityKind,
    ModelVariant,
    SmartGuitarSpec,
)
from app.sandboxes.smart_guitar.validators import REQUIRED_COMPONENT_IDS, validate_spec


class TestPresets:
    """Test preset configurations."""

    def test_standard_headed_has_all_required_components(self):
        """Standard headed preset includes all required electronics."""
        spec = standard_headed()
        component_ids = {c.id for c in spec.electronics}
        assert REQUIRED_COMPONENT_IDS <= component_ids

    def test_standard_headless_has_all_required_components(self):
        """Standard headless preset includes all required electronics."""
        spec = standard_headless()
        component_ids = {c.id for c in spec.electronics}
        assert REQUIRED_COMPONENT_IDS <= component_ids

    def test_standard_all_returns_both_variants(self):
        """standard_all() returns headed and headless."""
        presets = standard_all()
        assert "headed" in presets
        assert "headless" in presets
        assert presets["headed"].model_variant == ModelVariant.headed
        assert presets["headless"].model_variant == ModelVariant.headless


class TestValidator:
    """Test spec validation."""

    def test_standard_headed_spec_validates_ok(self):
        """Standard headed spec passes validation without errors."""
        spec = standard_headed()
        errors, warnings, _ = validate_spec(spec)
        assert len(errors) == 0, f"Unexpected errors: {errors}"

    def test_standard_headless_spec_validates_ok(self):
        """Standard headless spec passes validation without errors."""
        spec = standard_headless()
        errors, warnings, _ = validate_spec(spec)
        assert len(errors) == 0, f"Unexpected errors: {errors}"

    def test_vents_missing_warning(self):
        """Active fan without vents triggers warning."""
        spec = standard_headed()
        spec.thermal.vents_defined = False
        errors, warnings, _ = validate_spec(spec)
        warning_codes = [w.code for w in warnings]
        assert "vents_missing" in warning_codes

    def test_vents_defined_no_warning(self):
        """Active fan with vents defined produces no vents warning."""
        spec = standard_headed()
        spec.thermal.vents_defined = True
        errors, warnings, _ = validate_spec(spec)
        warning_codes = [w.code for w in warnings]
        assert "vents_missing" not in warning_codes

    def test_rim_too_thin_error(self):
        """Rim below minimum triggers error."""
        spec = standard_headed()
        spec.body.rim_in = 0.40  # Below 0.50 minimum
        errors, warnings, _ = validate_spec(spec)
        error_codes = [e.code for e in errors]
        assert "rim_too_thin" in error_codes

    def test_top_skin_too_thin_error(self):
        """Top skin below minimum triggers error."""
        spec = standard_headed()
        spec.body.top_skin_in = 0.25  # Below 0.30 minimum
        errors, warnings, _ = validate_spec(spec)
        error_codes = [e.code for e in errors]
        assert "top_skin_too_thin" in error_codes

    def test_spine_too_narrow_error(self):
        """Spine below minimum triggers error."""
        spec = standard_headed()
        spec.body.spine_w_in = 1.40  # Below 1.50 minimum
        errors, warnings, _ = validate_spec(spec)
        error_codes = [e.code for e in errors]
        assert "spine_too_narrow" in error_codes

    def test_hollow_depth_exceeds_budget_error(self):
        """Hollow depth exceeding budget triggers error."""
        spec = standard_headed()
        # thickness=1.50, top_skin=0.30 → max hollow = 1.20
        spec.target_hollow_depth_in = 1.30  # Exceeds max
        errors, warnings, _ = validate_spec(spec)
        error_codes = [e.code for e in errors]
        assert "hollow_depth_exceeds_budget" in error_codes

    def test_missing_components_error(self):
        """Missing required components triggers error."""
        spec = SmartGuitarSpec()  # Empty electronics list
        errors, warnings, _ = validate_spec(spec)
        error_codes = [e.code for e in errors]
        assert "missing_required_components" in error_codes


class TestPlanner:
    """Test CAM plan generation."""

    def test_generate_plan_produces_all_cavity_kinds(self):
        """Plan includes all 4 cavity kinds."""
        spec = standard_headed()
        plan = generate_plan(spec)
        cavity_kinds = {c.kind for c in plan.cavities}
        assert CavityKind.bass in cavity_kinds
        assert CavityKind.treble in cavity_kinds
        assert CavityKind.tail in cavity_kinds
        assert CavityKind.pod in cavity_kinds

    def test_generate_plan_produces_brackets_for_all_components(self):
        """Plan includes bracket for each electronics component."""
        spec = standard_headed()
        plan = generate_plan(spec)
        bracket_component_ids = {b.component_id for b in plan.brackets}
        spec_component_ids = {c.id for c in spec.electronics}
        assert bracket_component_ids == spec_component_ids

    def test_generate_plan_produces_channels(self):
        """Plan includes both route and drill channels."""
        spec = standard_headed()
        plan = generate_plan(spec)
        assert len(plan.channels) == 2  # route + drill

    def test_generate_plan_produces_5_ops(self):
        """Plan includes 5 toolpath operations."""
        spec = standard_headed()
        plan = generate_plan(spec)
        assert len(plan.ops) == 5
        op_ids = [op.op_id for op in plan.ops]
        assert op_ids == ["OP10", "OP20", "OP30", "OP40", "OP50"]

    def test_plan_determinism(self):
        """Same spec produces identical plan."""
        spec = standard_headed()
        plan1 = generate_plan(spec)
        plan2 = generate_plan(spec)
        assert plan1.model_dump() == plan2.model_dump()

    def test_plan_inherits_handedness(self):
        """Plan respects spec handedness."""
        spec = standard_headed()
        spec.handedness = spec.handedness.LH
        plan = generate_plan(spec)
        assert plan.handedness == spec.handedness
        # Pod template should be LH
        pod_cavity = next(c for c in plan.cavities if c.kind == CavityKind.pod)
        assert "lh" in pod_cavity.template_id.lower()

    def test_plan_inherits_variant(self):
        """Plan respects spec model variant."""
        spec = standard_headless()
        plan = generate_plan(spec)
        assert plan.model_variant == ModelVariant.headless

    def test_plan_with_errors_still_generates(self):
        """Plan is generated even with validation errors."""
        spec = SmartGuitarSpec()  # Missing components
        plan = generate_plan(spec)
        assert len(plan.errors) > 0
        assert len(plan.cavities) == 4  # Still generates structure
