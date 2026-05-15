"""
Tests for Topology Runtime Classification.

Sprint: MRP-5H
Status: PROTOTYPE
"""

import pytest

from app.cam.topology_builder.contracts import TopologyTier
from app.cam.topology_builder.runtime_support import (
    BODY_CATEGORY_SUPPORT,
    TopologyRuntimeSupport,
    can_generate_topology,
    classify_topology_runtime,
    get_unsupported_reason,
)


class TestBodyCategorySupport:
    """Tests for body category support mapping."""

    def test_flat_body_supported(self):
        """Flat body is fully supported for prototype."""
        assert BODY_CATEGORY_SUPPORT["flat_body"] == TopologyRuntimeSupport.SUPPORTED_PROTOTYPE

    def test_acoustic_flat_top_supported(self):
        """Acoustic flat top is fully supported for prototype."""
        assert BODY_CATEGORY_SUPPORT["acoustic_flat_top"] == TopologyRuntimeSupport.SUPPORTED_PROTOTYPE

    def test_hollow_electric_partial(self):
        """Hollow electric is partially supported."""
        assert BODY_CATEGORY_SUPPORT["hollow_electric"] == TopologyRuntimeSupport.PARTIAL_PROTOTYPE

    def test_archtop_research_required(self):
        """Archtop requires research."""
        assert BODY_CATEGORY_SUPPORT["archtop"] == TopologyRuntimeSupport.RESEARCH_REQUIRED

    def test_unknown_unsupported(self):
        """Unknown category is unsupported."""
        assert BODY_CATEGORY_SUPPORT["unknown"] == TopologyRuntimeSupport.UNSUPPORTED_RUNTIME


class TestClassifyTopologyRuntime:
    """Tests for classify_topology_runtime function."""

    def test_flat_body_no_semantics(self):
        """Flat body without semantics is supported."""
        support, supported, unsupported = classify_topology_runtime("flat_body")

        assert support == TopologyRuntimeSupport.SUPPORTED_PROTOTYPE
        assert "body_category:flat_body" in supported
        assert unsupported == []

    def test_unknown_category(self):
        """Unknown category is unsupported."""
        support, supported, unsupported = classify_topology_runtime("unknown")

        assert support == TopologyRuntimeSupport.UNSUPPORTED_RUNTIME
        assert "body_category:unknown" in unsupported

    def test_unrecognized_category(self):
        """Unrecognized category defaults to unsupported."""
        support, supported, unsupported = classify_topology_runtime("something_new")

        assert support == TopologyRuntimeSupport.UNSUPPORTED_RUNTIME

    def test_flat_body_with_uniform_thickness(self):
        """Flat body with uniform thickness is supported."""
        semantics = {
            "acoustic": {
                "thickness": {"level": 1, "uniform_mm": 3.0},
            }
        }
        support, supported, unsupported = classify_topology_runtime(
            "acoustic_flat_top", semantics
        )

        assert support == TopologyRuntimeSupport.SUPPORTED_PROTOTYPE
        assert "thickness_uniform" in supported

    def test_flat_body_with_component_thickness(self):
        """Flat body with component thickness is supported."""
        semantics = {
            "acoustic": {
                "thickness": {"level": 2, "top_mm": 2.5, "back_mm": 2.0},
            }
        }
        support, supported, unsupported = classify_topology_runtime(
            "acoustic_flat_top", semantics
        )

        assert support == TopologyRuntimeSupport.SUPPORTED_PROTOTYPE
        assert "thickness_component" in supported

    def test_flat_body_with_zonal_thickness(self):
        """Flat body with zonal thickness is partial support."""
        semantics = {
            "acoustic": {
                "thickness": {"level": 3, "zones": {}},
            }
        }
        support, supported, unsupported = classify_topology_runtime(
            "acoustic_flat_top", semantics
        )

        # Zonal is partial in PROTOTYPE
        assert support in (
            TopologyRuntimeSupport.SUPPORTED_PROTOTYPE,
            TopologyRuntimeSupport.PARTIAL_PROTOTYPE,
        )

    def test_flat_body_with_continuous_thickness(self):
        """Flat body with continuous thickness is partial/unsupported."""
        semantics = {
            "acoustic": {
                "thickness": {"level": 4, "field": {}},
            }
        }
        support, supported, unsupported = classify_topology_runtime(
            "acoustic_flat_top", semantics
        )

        assert support == TopologyRuntimeSupport.PARTIAL_PROTOTYPE
        assert "thickness_continuous" in unsupported

    def test_production_tier_stricter(self):
        """Production tier is stricter about unsupported features."""
        semantics = {
            "acoustic": {
                "thickness": {"level": 4, "field": {}},
            }
        }
        support, supported, unsupported = classify_topology_runtime(
            "acoustic_flat_top", semantics, TopologyTier.PRODUCTION
        )

        assert support == TopologyRuntimeSupport.UNSUPPORTED_RUNTIME

    def test_flat_profile_supported(self):
        """Flat side profile is supported."""
        semantics = {
            "acoustic": {
                "side_profile": {"profile_type": "flat"},
            }
        }
        support, supported, unsupported = classify_topology_runtime(
            "acoustic_flat_top", semantics
        )

        assert "profile_flat" in supported

    def test_graduated_arch_unsupported(self):
        """Graduated arch profile is research required."""
        semantics = {
            "acoustic": {
                "side_profile": {"profile_type": "graduated_arch"},
            }
        }
        support, supported, unsupported = classify_topology_runtime(
            "acoustic_flat_top", semantics
        )

        assert "profile_graduated_arch" in unsupported

    def test_g0_continuity_supported(self):
        """G0 continuity is supported."""
        semantics = {
            "acoustic": {
                "continuity_targets": {"rim_to_top": "g0"},
            }
        }
        support, supported, unsupported = classify_topology_runtime(
            "acoustic_flat_top", semantics
        )

        assert support == TopologyRuntimeSupport.SUPPORTED_PROTOTYPE
        assert "rim_to_top:g0" in supported

    def test_g2_continuity_research_required(self):
        """G2 continuity requires research."""
        semantics = {
            "acoustic": {
                "continuity_targets": {"rim_to_top": "g2"},
            }
        }
        support, supported, unsupported = classify_topology_runtime(
            "acoustic_flat_top", semantics
        )

        assert "rim_to_top:g2" in unsupported


class TestCanGenerateTopology:
    """Tests for can_generate_topology helper."""

    def test_supported_prototype_can_generate(self):
        """Supported prototype can generate."""
        assert can_generate_topology(TopologyRuntimeSupport.SUPPORTED_PROTOTYPE)

    def test_partial_prototype_can_generate(self):
        """Partial prototype can generate."""
        assert can_generate_topology(TopologyRuntimeSupport.PARTIAL_PROTOTYPE)

    def test_unsupported_cannot_generate(self):
        """Unsupported cannot generate."""
        assert not can_generate_topology(TopologyRuntimeSupport.UNSUPPORTED_RUNTIME)

    def test_research_required_cannot_generate(self):
        """Research required cannot generate."""
        assert not can_generate_topology(TopologyRuntimeSupport.RESEARCH_REQUIRED)


class TestGetUnsupportedReason:
    """Tests for get_unsupported_reason helper."""

    def test_supported_reason(self):
        """Supported has positive message."""
        reason = get_unsupported_reason(
            TopologyRuntimeSupport.SUPPORTED_PROTOTYPE, []
        )
        assert "supported" in reason.lower()

    def test_partial_with_features(self):
        """Partial support lists skipped features."""
        reason = get_unsupported_reason(
            TopologyRuntimeSupport.PARTIAL_PROTOTYPE,
            ["thickness_continuous", "profile_recurve"],
        )
        assert "partial" in reason.lower()
        assert "thickness_continuous" in reason

    def test_unsupported_with_features(self):
        """Unsupported lists blocking features."""
        reason = get_unsupported_reason(
            TopologyRuntimeSupport.UNSUPPORTED_RUNTIME,
            ["body_category:unknown"],
        )
        assert "cannot" in reason.lower()
        assert "body_category:unknown" in reason

    def test_research_required(self):
        """Research required mentions implementation needed."""
        reason = get_unsupported_reason(
            TopologyRuntimeSupport.RESEARCH_REQUIRED, []
        )
        assert "research" in reason.lower()
