"""
Test: Saw Toolpath Builder 2.0

End-to-end tests for the Saw Toolpath Builder integration with:
- Saw Path Planner 2.1
- RMOS Context conversion
- SawCutPlan → RmosToolpathPlan mapping

Run with: pytest services/api/tests/test_saw_toolpath_builder.py -v
"""
from __future__ import annotations

import pytest

# Import the modules under test
from app.toolpath.saw_engine import (
    plan_saw_toolpaths_for_design,
    _build_saw_cut_context_from_rmos,
    _map_saw_cut_plan_to_rmos,
    is_saw_mode,
    _parse_saw_tool_id,
)
from app.saw_lab.path_planner import (
    SawCutContext,
    SawCutPlan,
    SawCutOperation,
    SawPlannerConfig,
    SawBladeSpec,
    SawMaterialSpec,
    plan_saw_cuts_for_board,
)
from app.rmos.api_contracts import RmosContext, RmosToolpathPlan


# ---------------------------------------------------------------------------
# Mock RosetteParamSpec (since it may have import issues)
# ---------------------------------------------------------------------------

class MockRingParam:
    def __init__(self, ring_index: int, width_mm: float):
        self.ring_index = ring_index
        self.width_mm = width_mm


class MockRosetteParamSpec:
    def __init__(
        self,
        outer_diameter_mm: float = 100.0,
        inner_diameter_mm: float = 20.0,
        ring_params: list = None,
    ):
        self.outer_diameter_mm = outer_diameter_mm
        self.inner_diameter_mm = inner_diameter_mm
        self.ring_params = ring_params or []


# ---------------------------------------------------------------------------
# Tests: Tool ID Parsing
# ---------------------------------------------------------------------------

class TestToolIdParsing:
    """Tests for saw tool ID parsing."""
    
    def test_parse_basic_saw_tool_id(self):
        """Test parsing a standard saw:diameter_teeth_kerf format."""
        result = _parse_saw_tool_id("saw:10_24_3.0")
        assert result["blade_diameter_mm"] == 254.0  # 10 * 25.4
        assert result["tooth_count"] == 24
        assert result["blade_kerf_mm"] == 3.0
    
    def test_parse_saw_tool_id_with_different_diameter(self):
        """Test parsing with 12-inch blade."""
        result = _parse_saw_tool_id("saw:12_60_2.5")
        assert result["blade_diameter_mm"] == pytest.approx(304.8, rel=0.01)
        assert result["tooth_count"] == 60
        assert result["blade_kerf_mm"] == 2.5
    
    def test_parse_invalid_tool_id_returns_defaults(self):
        """Test that invalid IDs return defaults."""
        result = _parse_saw_tool_id("router:1/4")
        assert result["blade_diameter_mm"] == 254.0
        assert result["tooth_count"] == 24
        assert result["blade_kerf_mm"] == 3.0
    
    def test_parse_empty_tool_id_returns_defaults(self):
        """Test that empty ID returns defaults."""
        result = _parse_saw_tool_id("")
        assert result["blade_diameter_mm"] == 254.0
    
    def test_is_saw_mode_true(self):
        """Test saw mode detection."""
        ctx = RmosContext(tool_id="saw:10_24_3.0")
        assert is_saw_mode(ctx) is True
    
    def test_is_saw_mode_false(self):
        """Test non-saw mode detection."""
        ctx = RmosContext(tool_id="em_3.175")
        assert is_saw_mode(ctx) is False


# ---------------------------------------------------------------------------
# Tests: Path Planner 2.1
# ---------------------------------------------------------------------------

class TestPathPlanner21:
    """Tests for Saw Path Planner 2.1."""
    
    def test_basic_cut_plan(self):
        """Test basic single-piece cut plan."""
        ctx = SawCutContext(
            blade=SawBladeSpec(kerf_mm=3.0),
            stock_length_mm=200.0,
            desired_piece_lengths_mm=[50.0],
        )
        
        plan = plan_saw_cuts_for_board(ctx)
        
        assert plan.is_feasible is True
        assert plan.total_piece_length_mm == 50.0
        assert len(plan.operations) >= 1
    
    def test_multiple_pieces(self):
        """Test plan with multiple desired pieces."""
        ctx = SawCutContext(
            blade=SawBladeSpec(kerf_mm=3.0),
            stock_length_mm=300.0,
            desired_piece_lengths_mm=[50.0, 60.0, 70.0],
        )
        
        plan = plan_saw_cuts_for_board(ctx)
        
        assert plan.is_feasible is True
        assert plan.total_piece_length_mm == 180.0  # 50 + 60 + 70
        assert plan.total_kerf_loss_mm == 6.0  # 2 cuts * 3.0mm
        assert len(plan.operations) == 3
    
    def test_infeasible_plan(self):
        """Test that infeasible plans are flagged."""
        ctx = SawCutContext(
            blade=SawBladeSpec(kerf_mm=3.0),
            stock_length_mm=100.0,
            desired_piece_lengths_mm=[60.0, 60.0],  # Too much for 100mm stock
        )
        
        plan = plan_saw_cuts_for_board(ctx)
        
        assert plan.is_feasible is False
        assert len(plan.warnings) > 0
    
    def test_with_leading_trim(self):
        """Test plan with leading trim cut."""
        ctx = SawCutContext(
            blade=SawBladeSpec(kerf_mm=3.0),
            stock_length_mm=200.0,
            desired_piece_lengths_mm=[50.0],
        )
        planner_cfg = SawPlannerConfig(leading_trim_mm=10.0)
        
        plan = plan_saw_cuts_for_board(ctx, planner_cfg=planner_cfg)
        
        assert plan.is_feasible is True
        # Should have TRIM_LEAD + CUT_1
        trim_ops = [op for op in plan.operations if op.cut_type == "TRIM"]
        assert len(trim_ops) == 1
        assert trim_ops[0].op_id == "TRIM_LEAD"
    
    def test_ordering_longest_first(self):
        """Test LONGEST_FIRST ordering strategy."""
        ctx = SawCutContext(
            blade=SawBladeSpec(kerf_mm=3.0),
            stock_length_mm=300.0,
            desired_piece_lengths_mm=[30.0, 80.0, 50.0],
        )
        planner_cfg = SawPlannerConfig(ordering_strategy="LONGEST_FIRST")
        
        plan = plan_saw_cuts_for_board(ctx, planner_cfg=planner_cfg)
        
        assert plan.is_feasible is True
        # First cut should be longest (80mm)
        crosscuts = [op for op in plan.operations if op.cut_type == "CROSSCUT"]
        assert crosscuts[0].cut_length_mm == 80.0
    
    def test_min_scrap_enforcement(self):
        """Test minimum scrap length enforcement."""
        ctx = SawCutContext(
            blade=SawBladeSpec(kerf_mm=3.0),
            stock_length_mm=100.0,
            desired_piece_lengths_mm=[75.0],  # Leaves ~22mm (< 20mm with kerf)
        )
        planner_cfg = SawPlannerConfig(min_scrap_length_mm=30.0)
        
        plan = plan_saw_cuts_for_board(ctx, planner_cfg=planner_cfg)
        
        # Should be infeasible due to min scrap
        assert plan.is_feasible is False
        assert any("scrap" in w.lower() for w in plan.warnings)


# ---------------------------------------------------------------------------
# Tests: RMOS Integration
# ---------------------------------------------------------------------------

class TestRmosIntegration:
    """Tests for RMOS ↔ Saw Lab integration."""
    
    def test_build_saw_cut_context_basic(self):
        """Test building SawCutContext from RMOS inputs."""
        design = MockRosetteParamSpec(
            outer_diameter_mm=100.0,
            inner_diameter_mm=20.0,
            ring_params=[
                MockRingParam(0, 5.0),
                MockRingParam(1, 8.0),
                MockRingParam(2, 6.0),
            ],
        )
        ctx = RmosContext(tool_id="saw:10_24_3.0")
        
        cut_ctx = _build_saw_cut_context_from_rmos(design, ctx)
        
        assert cut_ctx.blade.kerf_mm == 3.0
        assert cut_ctx.blade.diameter_mm == 254.0
        assert len(cut_ctx.desired_piece_lengths_mm) == 3
        assert cut_ctx.desired_piece_lengths_mm == [5.0, 8.0, 6.0]
    
    def test_build_saw_cut_context_no_rings(self):
        """Test building context when no ring params provided."""
        design = MockRosetteParamSpec(
            outer_diameter_mm=100.0,
            inner_diameter_mm=20.0,
            ring_params=[],
        )
        ctx = RmosContext(tool_id="saw:10_24_3.0")
        
        cut_ctx = _build_saw_cut_context_from_rmos(design, ctx)
        
        # Should fall back to outer - inner = 80.0
        assert len(cut_ctx.desired_piece_lengths_mm) == 1
        assert cut_ctx.desired_piece_lengths_mm[0] == 80.0
    
    def test_map_saw_cut_plan_to_rmos(self):
        """Test mapping SawCutPlan to RmosToolpathPlan."""
        saw_plan = SawCutPlan(
            operations=[
                SawCutOperation(
                    op_id="CUT_1",
                    sequence_index=0,
                    cut_type="CROSSCUT",
                    start_offset_mm=0.0,
                    cut_length_mm=50.0,
                    kerf_mm=3.0,
                    description="Test cut",
                ),
            ],
            total_kerf_loss_mm=3.0,
            total_piece_length_mm=50.0,
            scrap_length_mm=47.0,
            material_utilization=0.5,
            is_feasible=True,
            warnings=[],
        )
        
        rmos_plan = _map_saw_cut_plan_to_rmos(saw_plan)
        
        assert isinstance(rmos_plan, RmosToolpathPlan)
        assert len(rmos_plan.toolpaths) == 1
        assert rmos_plan.toolpaths[0]["op_id"] == "CUT_1"
        assert rmos_plan.total_length_mm == 50.0


# ---------------------------------------------------------------------------
# Tests: End-to-End
# ---------------------------------------------------------------------------

class TestEndToEnd:
    """End-to-end tests for the full pipeline."""
    
    def test_plan_saw_toolpaths_basic(self):
        """Test full pipeline: RosetteParamSpec → RmosToolpathPlan."""
        design = MockRosetteParamSpec(
            outer_diameter_mm=80.0,
            inner_diameter_mm=15.0,
            ring_params=[
                MockRingParam(0, 10.0),
                MockRingParam(1, 12.0),
                MockRingParam(2, 8.0),
            ],
        )
        ctx = RmosContext(tool_id="saw:10_24_3.0")
        
        plan = plan_saw_toolpaths_for_design(design, ctx)
        
        assert isinstance(plan, RmosToolpathPlan)
        assert len(plan.toolpaths) > 0
        assert plan.total_length_mm > 0
        assert plan.estimated_time_seconds > 0
    
    def test_plan_saw_toolpaths_with_config(self):
        """Test pipeline with custom planner config."""
        design = MockRosetteParamSpec(
            outer_diameter_mm=100.0,
            inner_diameter_mm=20.0,
            ring_params=[
                MockRingParam(0, 15.0),
                MockRingParam(1, 20.0),
            ],
        )
        ctx = RmosContext(tool_id="saw:10_60_2.5")
        planner_cfg = SawPlannerConfig(
            leading_trim_mm=5.0,
            ordering_strategy="LONGEST_FIRST",
        )
        
        plan = plan_saw_toolpaths_for_design(design, ctx, planner_cfg=planner_cfg)
        
        assert isinstance(plan, RmosToolpathPlan)
        # Should have trim + 2 cuts
        assert len(plan.toolpaths) >= 2


# ---------------------------------------------------------------------------
# Run tests
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
