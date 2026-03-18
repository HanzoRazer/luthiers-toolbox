"""
Tests for Constraint-First Search Service.

Tests Mode B (Constraint-First) search that proposes feasible rosette designs
given operator constraints.
"""
import pytest
from unittest.mock import patch, MagicMock

from app.rmos.services.constraint_search import (
    ConstraintSearchParams,
    ConstraintSearchResult,
    RosetteParamSpec,
    _passes_constraints,
    search_constraint_first,
)
from app.rmos.api_contracts import RmosFeasibilityResult, RiskBucket


class TestConstraintSearchParams:
    """Tests for ConstraintSearchParams dataclass."""

    def test_params_with_required_fields(self):
        """Should create params with required fields."""
        params = ConstraintSearchParams(
            material_id="hardwood_walnut",
            tool_id="tool_6mm",
            outer_diameter_mm_min=80.0,
            outer_diameter_mm_max=120.0,
        )
        assert params.material_id == "hardwood_walnut"
        assert params.tool_id == "tool_6mm"
        assert params.outer_diameter_mm_min == 80.0
        assert params.outer_diameter_mm_max == 120.0

    def test_params_defaults(self):
        """Should have sensible defaults."""
        params = ConstraintSearchParams(
            material_id="wood",
            tool_id="tool",
            outer_diameter_mm_min=50,
            outer_diameter_mm_max=100,
        )
        assert params.ring_count_min == 1
        assert params.ring_count_max == 4
        assert params.max_candidates == 12
        assert params.max_trials == 40
        assert params.max_cut_time_min is None
        assert params.waste_tolerance is None

    def test_params_with_optional_constraints(self):
        """Should accept optional constraints."""
        params = ConstraintSearchParams(
            material_id="wood",
            tool_id="tool",
            outer_diameter_mm_min=50,
            outer_diameter_mm_max=100,
            max_cut_time_min=30.0,
            waste_tolerance=0.15,
        )
        assert params.max_cut_time_min == 30.0
        assert params.waste_tolerance == 0.15


class TestRosetteParamSpec:
    """Tests for RosetteParamSpec model (art_studio schema)."""

    def test_param_spec_with_required_fields(self):
        """Should create spec with required fields."""
        spec = RosetteParamSpec(
            outer_diameter_mm=100.0,
            inner_diameter_mm=90.0,
            ring_params=[],
        )
        assert spec.outer_diameter_mm == 100.0
        assert spec.inner_diameter_mm == 90.0
        assert spec.ring_params == []

    def test_param_spec_with_rings(self):
        """Should accept ring params as dicts."""
        spec = RosetteParamSpec(
            outer_diameter_mm=120.0,
            inner_diameter_mm=100.0,
            ring_params=[{"ring_index": 0, "width_mm": 2.5}],
        )
        assert spec.outer_diameter_mm == 120.0
        assert len(spec.ring_params) == 1


class TestPassesConstraints:
    """Tests for _passes_constraints function."""

    def test_green_passes(self):
        """GREEN risk bucket should pass."""
        result = RmosFeasibilityResult(
            score=80.0,
            risk_bucket=RiskBucket.GREEN,
            efficiency=0.9,
            estimated_cut_time_seconds=600,
        )
        params = ConstraintSearchParams(
            material_id="wood",
            tool_id="tool",
            outer_diameter_mm_min=80,
            outer_diameter_mm_max=120,
        )
        assert _passes_constraints(result, params) is True

    def test_yellow_passes(self):
        """YELLOW risk bucket should pass (not blocked)."""
        result = RmosFeasibilityResult(
            score=60.0,
            risk_bucket=RiskBucket.YELLOW,
            efficiency=0.85,
            estimated_cut_time_seconds=900,
        )
        params = ConstraintSearchParams(
            material_id="wood",
            tool_id="tool",
            outer_diameter_mm_min=80,
            outer_diameter_mm_max=120,
        )
        assert _passes_constraints(result, params) is True

    def test_red_fails(self):
        """RED risk bucket should fail."""
        result = RmosFeasibilityResult(
            score=20.0,
            risk_bucket=RiskBucket.RED,
            efficiency=0.5,
            estimated_cut_time_seconds=300,
        )
        params = ConstraintSearchParams(
            material_id="wood",
            tool_id="tool",
            outer_diameter_mm_min=80,
            outer_diameter_mm_max=120,
        )
        assert _passes_constraints(result, params) is False

    def test_cut_time_constraint_passes(self):
        """Should pass when cut time is under max."""
        result = RmosFeasibilityResult(
            score=80.0,
            risk_bucket=RiskBucket.GREEN,
            efficiency=0.9,
            estimated_cut_time_seconds=1200,  # 20 minutes
        )
        params = ConstraintSearchParams(
            material_id="wood",
            tool_id="tool",
            outer_diameter_mm_min=80,
            outer_diameter_mm_max=120,
            max_cut_time_min=30.0,  # 30 minute limit
        )
        assert _passes_constraints(result, params) is True

    def test_cut_time_constraint_fails(self):
        """Should fail when cut time exceeds max."""
        result = RmosFeasibilityResult(
            score=80.0,
            risk_bucket=RiskBucket.GREEN,
            efficiency=0.9,
            estimated_cut_time_seconds=2400,  # 40 minutes
        )
        params = ConstraintSearchParams(
            material_id="wood",
            tool_id="tool",
            outer_diameter_mm_min=80,
            outer_diameter_mm_max=120,
            max_cut_time_min=30.0,  # 30 minute limit
        )
        assert _passes_constraints(result, params) is False

    def test_waste_tolerance_passes(self):
        """Should pass when waste is under tolerance."""
        result = RmosFeasibilityResult(
            score=80.0,
            risk_bucket=RiskBucket.GREEN,
            efficiency=0.9,  # 10% waste
            estimated_cut_time_seconds=600,
        )
        params = ConstraintSearchParams(
            material_id="wood",
            tool_id="tool",
            outer_diameter_mm_min=80,
            outer_diameter_mm_max=120,
            waste_tolerance=0.15,  # 15% waste tolerance
        )
        assert _passes_constraints(result, params) is True

    def test_waste_tolerance_fails(self):
        """Should fail when waste exceeds tolerance."""
        result = RmosFeasibilityResult(
            score=80.0,
            risk_bucket=RiskBucket.GREEN,
            efficiency=0.8,  # 20% waste
            estimated_cut_time_seconds=600,
        )
        params = ConstraintSearchParams(
            material_id="wood",
            tool_id="tool",
            outer_diameter_mm_min=80,
            outer_diameter_mm_max=120,
            waste_tolerance=0.15,  # 15% waste tolerance
        )
        assert _passes_constraints(result, params) is False


class TestSearchConstraintFirst:
    """Tests for search_constraint_first function."""

    def _mock_design(self):
        """Create a mock design for testing."""
        return RosetteParamSpec(
            outer_diameter_mm=100.0,
            inner_diameter_mm=90.0,
            ring_params=[{"ring_index": 0, "width_mm": 2.5}],
        )

    @patch("app.rmos.services.constraint_search._generate_candidate_design")
    @patch("app.rmos.services.constraint_search._evaluate_candidate")
    def test_returns_sorted_by_score(self, mock_evaluate, mock_generate):
        """Results should be sorted by score descending."""
        mock_generate.return_value = self._mock_design()

        # Return varying scores
        scores = [60.0, 80.0, 70.0, 90.0, 50.0]
        mock_evaluate.side_effect = [
            RmosFeasibilityResult(
                score=score,
                risk_bucket=RiskBucket.GREEN,
                efficiency=0.9,
                estimated_cut_time_seconds=600,
            )
            for score in scores
        ]

        params = ConstraintSearchParams(
            material_id="wood",
            tool_id="tool",
            outer_diameter_mm_min=80,
            outer_diameter_mm_max=120,
            max_trials=5,
            max_candidates=5,
        )
        results = search_constraint_first(params)

        # Should be sorted by score descending
        assert len(results) == 5
        assert results[0].feasibility.score == 90.0
        assert results[1].feasibility.score == 80.0
        assert results[2].feasibility.score == 70.0

    @patch("app.rmos.services.constraint_search._generate_candidate_design")
    @patch("app.rmos.services.constraint_search._evaluate_candidate")
    def test_assigns_ranks(self, mock_evaluate, mock_generate):
        """Results should have rank assigned (1-indexed)."""
        mock_generate.return_value = self._mock_design()
        mock_evaluate.return_value = RmosFeasibilityResult(
            score=80.0,
            risk_bucket=RiskBucket.GREEN,
            efficiency=0.9,
            estimated_cut_time_seconds=600,
        )

        params = ConstraintSearchParams(
            material_id="wood",
            tool_id="tool",
            outer_diameter_mm_min=80,
            outer_diameter_mm_max=120,
            max_trials=5,
            max_candidates=5,
        )
        results = search_constraint_first(params)

        for i, result in enumerate(results):
            assert result.rank == i + 1

    @patch("app.rmos.services.constraint_search._generate_candidate_design")
    @patch("app.rmos.services.constraint_search._evaluate_candidate")
    def test_filters_red_risk(self, mock_evaluate, mock_generate):
        """RED risk results should be filtered out."""
        mock_generate.return_value = self._mock_design()
        mock_evaluate.side_effect = [
            RmosFeasibilityResult(
                score=20.0,
                risk_bucket=RiskBucket.RED,  # Should be filtered
                efficiency=0.5,
                estimated_cut_time_seconds=600,
            ),
            RmosFeasibilityResult(
                score=80.0,
                risk_bucket=RiskBucket.GREEN,  # Should pass
                efficiency=0.9,
                estimated_cut_time_seconds=600,
            ),
        ]

        params = ConstraintSearchParams(
            material_id="wood",
            tool_id="tool",
            outer_diameter_mm_min=80,
            outer_diameter_mm_max=120,
            max_trials=2,
            max_candidates=5,
        )
        results = search_constraint_first(params)

        assert len(results) == 1
        assert results[0].feasibility.risk_bucket == RiskBucket.GREEN

    @patch("app.rmos.services.constraint_search._generate_candidate_design")
    @patch("app.rmos.services.constraint_search._evaluate_candidate")
    def test_respects_max_candidates(self, mock_evaluate, mock_generate):
        """Should return at most max_candidates results."""
        mock_generate.return_value = self._mock_design()
        mock_evaluate.return_value = RmosFeasibilityResult(
            score=80.0,
            risk_bucket=RiskBucket.GREEN,
            efficiency=0.9,
            estimated_cut_time_seconds=600,
        )

        params = ConstraintSearchParams(
            material_id="wood",
            tool_id="tool",
            outer_diameter_mm_min=80,
            outer_diameter_mm_max=120,
            max_trials=20,
            max_candidates=3,
        )
        results = search_constraint_first(params)

        assert len(results) <= 3

    @patch("app.rmos.services.constraint_search._generate_candidate_design")
    @patch("app.rmos.services.constraint_search._evaluate_candidate")
    def test_handles_evaluation_errors(self, mock_evaluate, mock_generate):
        """Should skip candidates that fail evaluation."""
        mock_generate.return_value = self._mock_design()
        mock_evaluate.side_effect = [
            ValueError("Evaluation failed"),  # Error
            RmosFeasibilityResult(
                score=80.0,
                risk_bucket=RiskBucket.GREEN,
                efficiency=0.9,
                estimated_cut_time_seconds=600,
            ),
        ]

        params = ConstraintSearchParams(
            material_id="wood",
            tool_id="tool",
            outer_diameter_mm_min=80,
            outer_diameter_mm_max=120,
            max_trials=2,
            max_candidates=5,
        )
        results = search_constraint_first(params)

        # Should have 1 result (error was skipped)
        assert len(results) == 1

    @patch("app.rmos.services.constraint_search._generate_candidate_design")
    @patch("app.rmos.services.constraint_search._evaluate_candidate")
    def test_empty_when_all_fail_constraints(self, mock_evaluate, mock_generate):
        """Should return empty when all candidates fail constraints."""
        mock_generate.return_value = self._mock_design()
        mock_evaluate.return_value = RmosFeasibilityResult(
            score=20.0,
            risk_bucket=RiskBucket.RED,
            efficiency=0.5,
            estimated_cut_time_seconds=600,
        )

        params = ConstraintSearchParams(
            material_id="wood",
            tool_id="tool",
            outer_diameter_mm_min=80,
            outer_diameter_mm_max=120,
            max_trials=5,
            max_candidates=5,
        )
        results = search_constraint_first(params)

        assert results == []

    @patch("app.rmos.services.constraint_search._generate_candidate_design")
    @patch("app.rmos.services.constraint_search._evaluate_candidate")
    def test_early_exit_when_enough_candidates(self, mock_evaluate, mock_generate):
        """Should exit early when enough candidates found."""
        mock_generate.return_value = self._mock_design()
        call_count = [0]

        def counting_mock(*args, **kwargs):
            call_count[0] += 1
            return RmosFeasibilityResult(
                score=80.0,
                risk_bucket=RiskBucket.GREEN,
                efficiency=0.9,
                estimated_cut_time_seconds=600,
            )

        mock_evaluate.side_effect = counting_mock

        params = ConstraintSearchParams(
            material_id="wood",
            tool_id="tool",
            outer_diameter_mm_min=80,
            outer_diameter_mm_max=120,
            max_trials=100,  # High trial limit
            max_candidates=3,  # But only need 3
        )
        results = search_constraint_first(params)

        # Early exit happens at max_candidates * 2 = 6
        assert call_count[0] <= 6
        assert len(results) <= 3


class TestConstraintSearchResult:
    """Tests for ConstraintSearchResult dataclass."""

    def test_result_fields(self):
        """Should store all fields correctly."""
        design = RosetteParamSpec(
            outer_diameter_mm=100.0,
            inner_diameter_mm=90.0,
            ring_params=[],
        )
        feasibility = RmosFeasibilityResult(
            score=85.0,
            risk_bucket=RiskBucket.GREEN,
            efficiency=0.9,
            estimated_cut_time_seconds=600,
        )

        result = ConstraintSearchResult(
            design=design,
            feasibility=feasibility,
            rank=1,
        )

        assert result.design.outer_diameter_mm == 100.0
        assert result.feasibility.score == 85.0
        assert result.rank == 1

    def test_result_default_rank(self):
        """Rank should default to 0."""
        design = RosetteParamSpec(
            outer_diameter_mm=100.0,
            inner_diameter_mm=90.0,
            ring_params=[],
        )
        feasibility = RmosFeasibilityResult(
            score=80.0,
            risk_bucket=RiskBucket.GREEN,
        )

        result = ConstraintSearchResult(design=design, feasibility=feasibility)
        assert result.rank == 0
