"""
Feasibility Engine Unit Tests

Tests determinism and RED/YELLOW rule behavior for the pre-CAM feasibility check.
Locks behavior before integrating into wrapper.

Contract: Feasibility must be:
- Deterministic: same input → same hash (excluding computed_at_utc)
- Rule-based: RED blocks, YELLOW warns, GREEN passes
"""
from __future__ import annotations

import hashlib
import json

import pytest

from app.rmos.feasibility import (
    FeasibilityInput,
    FeasibilityResult,
    RiskLevel,
    compute_feasibility,
)


def _minimal_valid_input() -> FeasibilityInput:
    """Returns a minimal valid FeasibilityInput that should pass all rules."""
    return FeasibilityInput(
        tool_d=6.0,
        stepover=0.45,
        stepdown=1.5,
        z_rough=-3.0,
        feed_xy=1200.0,
        feed_z=300.0,
        rapid=3000.0,
        safe_z=5.0,
        strategy="Spiral",
        layer_name="GEOMETRY",
        climb=True,
        smoothing=0.1,
        margin=0.0,
    )


def _hash_result_deterministic(result: FeasibilityResult) -> str:
    """Hash result excluding non-deterministic fields."""
    d = result.model_dump()
    d.pop("computed_at_utc", None)
    # Sort keys for deterministic JSON
    return hashlib.sha256(
        json.dumps(d, sort_keys=True, default=str).encode()
    ).hexdigest()


class TestFeasibilityDeterminism:
    """Verify feasibility computation is deterministic."""

    def test_feasibility_hash_is_deterministic(self):
        """Same FeasibilityInput → same hash (excluding computed_at_utc)."""
        fi = _minimal_valid_input()

        result1 = compute_feasibility(fi)
        result2 = compute_feasibility(fi)

        hash1 = _hash_result_deterministic(result1)
        hash2 = _hash_result_deterministic(result2)

        assert hash1 == hash2, "Feasibility must be deterministic"
        assert len(hash1) == 64, "Hash must be 64 hex chars"

    def test_different_input_produces_different_hash(self):
        """Different input that changes outcome → different hash."""
        fi1 = _minimal_valid_input()
        fi2 = _minimal_valid_input()
        fi2.feed_z = 1500  # Makes feed_z > feed_xy → triggers YELLOW

        result1 = compute_feasibility(fi1)
        result2 = compute_feasibility(fi2)

        # Verify they have different risk levels
        assert result1.risk_level == RiskLevel.GREEN
        assert result2.risk_level == RiskLevel.YELLOW

        hash1 = _hash_result_deterministic(result1)
        hash2 = _hash_result_deterministic(result2)

        assert hash1 != hash2, "Different outcomes should produce different hashes"


class TestRedRules:
    """RED rules should block and set risk_level=RED."""

    def test_red_invalid_tool_d_zero(self):
        """tool_d=0 → RED."""
        fi = _minimal_valid_input()
        fi.tool_d = 0

        result = compute_feasibility(fi)

        assert result.risk_level == RiskLevel.RED
        assert result.blocking is True
        assert any("tool_d" in r.lower() for r in result.blocking_reasons)

    def test_red_invalid_tool_d_negative(self):
        """tool_d=-1 → RED."""
        fi = _minimal_valid_input()
        fi.tool_d = -1

        result = compute_feasibility(fi)

        assert result.risk_level == RiskLevel.RED
        assert result.blocking is True

    def test_red_invalid_stepover_zero(self):
        """stepover=0 → RED."""
        fi = _minimal_valid_input()
        fi.stepover = 0

        result = compute_feasibility(fi)

        assert result.risk_level == RiskLevel.RED
        assert result.blocking is True
        assert any("stepover" in r.lower() for r in result.blocking_reasons)

    def test_red_invalid_stepover_too_high(self):
        """stepover=1.0 → RED (must be ≤0.95)."""
        fi = _minimal_valid_input()
        fi.stepover = 1.0

        result = compute_feasibility(fi)

        assert result.risk_level == RiskLevel.RED
        assert result.blocking is True

    def test_red_invalid_stepdown_zero(self):
        """stepdown=0 → RED."""
        fi = _minimal_valid_input()
        fi.stepdown = 0

        result = compute_feasibility(fi)

        assert result.risk_level == RiskLevel.RED
        assert result.blocking is True
        assert any("stepdown" in r.lower() for r in result.blocking_reasons)

    def test_red_invalid_z_rough_positive(self):
        """z_rough=1 (positive) → RED (must be negative cutting depth)."""
        fi = _minimal_valid_input()
        fi.z_rough = 1.0

        result = compute_feasibility(fi)

        assert result.risk_level == RiskLevel.RED
        assert result.blocking is True
        assert any("z_rough" in r.lower() for r in result.blocking_reasons)

    def test_red_invalid_z_rough_zero(self):
        """z_rough=0 → RED."""
        fi = _minimal_valid_input()
        fi.z_rough = 0

        result = compute_feasibility(fi)

        assert result.risk_level == RiskLevel.RED
        assert result.blocking is True

    def test_red_invalid_safe_z_zero(self):
        """safe_z=0 → RED."""
        fi = _minimal_valid_input()
        fi.safe_z = 0

        result = compute_feasibility(fi)

        assert result.risk_level == RiskLevel.RED
        assert result.blocking is True
        assert any("safe_z" in r.lower() for r in result.blocking_reasons)

    def test_red_invalid_safe_z_negative(self):
        """safe_z=-1 → RED."""
        fi = _minimal_valid_input()
        fi.safe_z = -1

        result = compute_feasibility(fi)

        assert result.risk_level == RiskLevel.RED
        assert result.blocking is True

    def test_red_no_closed_paths(self):
        """has_closed_paths=False → RED."""
        fi = _minimal_valid_input()
        fi.has_closed_paths = False

        result = compute_feasibility(fi)

        assert result.risk_level == RiskLevel.RED
        assert result.blocking is True
        assert any("closed" in r.lower() for r in result.blocking_reasons)

    def test_red_loop_count_zero(self):
        """loop_count_hint=0 → RED."""
        fi = _minimal_valid_input()
        fi.loop_count_hint = 0

        result = compute_feasibility(fi)

        assert result.risk_level == RiskLevel.RED
        assert result.blocking is True


class TestYellowRules:
    """YELLOW rules should warn but not block."""

    def test_yellow_feed_z_gt_feed_xy(self):
        """feed_z > feed_xy → YELLOW warning."""
        fi = _minimal_valid_input()
        fi.feed_z = 1500  # Greater than feed_xy=1200

        result = compute_feasibility(fi)

        assert result.risk_level == RiskLevel.YELLOW
        assert result.blocking is False
        assert len(result.warnings) > 0
        assert any("feed_z" in w.lower() for w in result.warnings)

    def test_yellow_stepdown_large(self):
        """stepdown > 3mm → YELLOW warning."""
        fi = _minimal_valid_input()
        fi.stepdown = 5.0

        result = compute_feasibility(fi)

        assert result.risk_level == RiskLevel.YELLOW
        assert result.blocking is False
        assert any("stepdown" in w.lower() for w in result.warnings)

    def test_yellow_loop_count_high(self):
        """loop_count_hint > 1000 → YELLOW warning."""
        fi = _minimal_valid_input()
        fi.loop_count_hint = 2000

        result = compute_feasibility(fi)

        assert result.risk_level == RiskLevel.YELLOW
        assert result.blocking is False
        assert any("loop" in w.lower() for w in result.warnings)

    def test_yellow_tool_too_large(self):
        """tool_d > smallest_feature_mm → YELLOW warning."""
        fi = _minimal_valid_input()
        fi.tool_d = 10.0
        fi.smallest_feature_mm = 5.0

        result = compute_feasibility(fi)

        assert result.risk_level == RiskLevel.YELLOW
        assert result.blocking is False
        assert any("tool" in w.lower() for w in result.warnings)


class TestGreenPath:
    """GREEN when all rules pass."""

    def test_green_when_valid_minimal(self):
        """Minimal valid input → GREEN."""
        fi = _minimal_valid_input()

        result = compute_feasibility(fi)

        assert result.risk_level == RiskLevel.GREEN
        assert result.blocking is False
        assert len(result.blocking_reasons) == 0
        assert len(result.warnings) == 0

    def test_green_with_optional_fields_none(self):
        """GREEN when optional preflight fields are None (unknown)."""
        fi = _minimal_valid_input()
        fi.has_closed_paths = None  # Unknown
        fi.loop_count_hint = None
        fi.entity_count = None
        fi.bbox = None
        fi.smallest_feature_mm = None

        result = compute_feasibility(fi)

        assert result.risk_level == RiskLevel.GREEN
        assert result.blocking is False

    def test_green_with_known_good_geometry(self):
        """GREEN when geometry info is known and valid."""
        fi = _minimal_valid_input()
        fi.has_closed_paths = True
        fi.loop_count_hint = 5
        fi.entity_count = 10
        fi.bbox = {"x_min": 0, "y_min": 0, "x_max": 100, "y_max": 100}

        result = compute_feasibility(fi)

        assert result.risk_level == RiskLevel.GREEN
        assert result.blocking is False


class TestResultStructure:
    """Verify FeasibilityResult structure."""

    def test_result_has_engine_version(self):
        """Result includes engine_version."""
        fi = _minimal_valid_input()
        result = compute_feasibility(fi)

        assert result.engine_version == "feasibility_engine_v1"

    def test_result_has_computed_at_utc(self):
        """Result includes computed_at_utc timestamp."""
        fi = _minimal_valid_input()
        result = compute_feasibility(fi)

        assert result.computed_at_utc is not None
        assert "T" in result.computed_at_utc  # ISO format

    def test_result_details_include_input_context(self):
        """Result details include input context for audit."""
        fi = _minimal_valid_input()
        fi.layer_name = "TEST_LAYER"
        result = compute_feasibility(fi)

        assert result.details.get("layer_name") == "TEST_LAYER"
        assert result.details.get("pipeline_id") == "mvp_dxf_to_grbl_v1"

    def test_constraints_populated_for_yellow(self):
        """YELLOW rules populate constraints list."""
        fi = _minimal_valid_input()
        fi.tool_d = 10.0
        fi.smallest_feature_mm = 5.0

        result = compute_feasibility(fi)

        assert len(result.constraints) > 0
        assert any("tool_d" in c for c in result.constraints)
