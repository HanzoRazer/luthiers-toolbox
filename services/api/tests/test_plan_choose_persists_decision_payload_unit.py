"""
Unit test for /api/saw/batch/plan/choose endpoint.

Tests:
1. Basic choose flow (no patch)
2. Choose with apply_recommended_patch=True
3. Verify decision payload contains expected fields
"""
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_store():
    """Mock the store functions."""
    with patch("app.saw_lab.batch_router_toolpaths.get_artifact") as mock_get, \
         patch("app.saw_lab.batch_router_toolpaths.store_artifact") as mock_store:
        yield mock_get, mock_store


@pytest.fixture
def sample_plan_artifact():
    """Sample plan artifact for testing."""
    return {
        "artifact_id": "plan-001",
        "kind": "saw_batch_plan",
        "payload": {
            "batch_label": "test_batch",
            "session_id": "session-001",
            "batch_spec_artifact_id": "spec-001",
            "setups": [
                {
                    "setup_key": "setup_1",
                    "tool_id": "saw:thin_140",
                    "ops": [
                        {"op_id": "op_1", "part_id": "part_1", "cut_type": "crosscut"},
                        {"op_id": "op_2", "part_id": "part_2", "cut_type": "crosscut"},
                    ],
                }
            ],
        },
    }


@pytest.fixture
def sample_spec_artifact():
    """Sample spec artifact for testing."""
    return {
        "artifact_id": "spec-001",
        "kind": "saw_batch_spec",
        "payload": {
            "batch_label": "test_batch",
            "session_id": "session-001",
            "tool_id": "saw:thin_140",
            "items": [
                {"part_id": "part_1", "material_id": "maple", "thickness_mm": 6.0},
                {"part_id": "part_2", "material_id": "maple", "thickness_mm": 6.0},
            ],
        },
    }


class TestPlanChooseBasic:
    """Basic plan/choose endpoint tests."""

    def test_choose_creates_decision_artifact(self, mock_store, sample_plan_artifact, sample_spec_artifact):
        """Verify /plan/choose creates a decision artifact."""
        mock_get, mock_store_fn = mock_store
        
        def get_artifact_side_effect(artifact_id):
            if artifact_id == "plan-001":
                return sample_plan_artifact
            if artifact_id == "spec-001":
                return sample_spec_artifact
            return None
        
        mock_get.side_effect = get_artifact_side_effect
        mock_store_fn.return_value = "decision-001"
        
        from app.saw_lab.batch_router import choose_batch_plan, BatchPlanChooseRequest
        
        req = BatchPlanChooseRequest(
            batch_plan_artifact_id="plan-001",
            selected_setup_key="setup_1",
            selected_op_ids=["op_1"],
            apply_recommended_patch=False,
            operator_note="test note",
        )
        
        response = choose_batch_plan(req)
        
        assert response.batch_decision_artifact_id == "decision-001"
        assert response.selected_setup_key == "setup_1"
        assert response.applied_context_patch is None
        assert response.applied_multipliers is None
        assert response.advisory_source_decision_artifact_id is None
        
        # Verify store was called with correct payload
        mock_store_fn.assert_called_once()
        call_kwargs = mock_store_fn.call_args[1]
        assert call_kwargs["kind"] == "saw_batch_decision"
        assert call_kwargs["parent_id"] == "plan-001"
        
        payload = call_kwargs["payload"]
        assert payload["selected_setup_key"] == "setup_1"
        assert payload["selected_op_ids"] == ["op_1"]
        assert payload["operator_note"] == "test note"
        assert payload["apply_recommended_patch"] is False

    def test_choose_with_patch_applies_multipliers(self, mock_store, sample_plan_artifact, sample_spec_artifact):
        """Verify /plan/choose applies patch when opt-in."""
        mock_get, mock_store_fn = mock_store

        def get_artifact_side_effect(artifact_id):
            if artifact_id == "plan-001":
                return sample_plan_artifact
            if artifact_id == "spec-001":
                return sample_spec_artifact
            return None

        mock_get.side_effect = get_artifact_side_effect
        mock_store_fn.return_value = "decision-002"

        # Mock the TuningDelta (Pydantic model with rpm_mul, feed_mul, doc_mul)
        from app.saw_lab.schemas_decision_intelligence import TuningDelta
        mock_delta = TuningDelta(rpm_mul=1.05, feed_mul=0.95, doc_mul=1.0)

        # Mock the latest approved decision lookup (returns tuple: decision_id, TuningDelta)
        mock_return = ("tuning-decision-001", mock_delta)

        # Create mock runs_store with the required attributes
        mock_runs_store = MagicMock()
        mock_runs_store.list_runs_filtered = MagicMock(return_value=[])
        mock_runs_store.persist_run_artifact = MagicMock(return_value=None)

        # Patch find_latest_approved_tuning_decision at its source module
        # and mock the runs_store module that gets imported
        with patch("app.saw_lab.decision_intel_apply_service.find_latest_approved_tuning_decision", return_value=mock_return), \
             patch.dict("sys.modules", {"app.rmos.runs_v2": MagicMock(store=mock_runs_store)}):
            from app.saw_lab.batch_router import choose_batch_plan, BatchPlanChooseRequest

            req = BatchPlanChooseRequest(
                batch_plan_artifact_id="plan-001",
                selected_setup_key="setup_1",
                selected_op_ids=["op_1", "op_2"],
                apply_recommended_patch=True,
                operator_note="applying tuning",
            )

            response = choose_batch_plan(req)

            assert response.batch_decision_artifact_id == "decision-002"
            assert response.advisory_source_decision_artifact_id == "tuning-decision-001"
            assert response.applied_multipliers is not None
            assert response.applied_multipliers["rpm_mul"] == 1.05
            assert response.applied_multipliers["feed_mul"] == 0.95

    def test_choose_plan_not_found(self, mock_store):
        """Verify 404 when plan not found."""
        mock_get, _ = mock_store
        mock_get.return_value = None
        
        from app.saw_lab.batch_router import choose_batch_plan, BatchPlanChooseRequest
        from fastapi import HTTPException
        
        req = BatchPlanChooseRequest(
            batch_plan_artifact_id="nonexistent",
            selected_setup_key="setup_1",
            selected_op_ids=["op_1"],
        )
        
        with pytest.raises(HTTPException) as exc_info:
            choose_batch_plan(req)
        
        assert exc_info.value.status_code == 404
        assert "Batch plan not found" in str(exc_info.value.detail)


class TestDecisionApplyService:
    """Tests for decision_apply_service.py"""

    def test_apply_decision_to_context_basic(self):
        """Verify apply_decision_to_context applies multipliers."""
        from app.saw_lab.decision_apply_service import apply_decision_to_context

        base_context = {
            "spindle_rpm": 3000.0,
            "feed_rate_mmpm": 600.0,
            "doc_mm": 3.0,
        }
        applied_multipliers = {
            "rpm_mul": 1.1,
            "feed_mul": 0.9,
            "doc_mul": 1.0,
        }

        # Function uses keyword-only args and returns (result, stamp) tuple
        result, stamp = apply_decision_to_context(
            base_context=base_context,
            applied_multipliers=applied_multipliers,
        )

        assert result["spindle_rpm"] == pytest.approx(3300.0)  # 3000 * 1.1
        assert result["feed_rate_mmpm"] == pytest.approx(540.0)  # 600 * 0.9
        assert result["doc_mm"] == pytest.approx(3.0)  # 3.0 * 1.0 (unchanged)

    def test_apply_decision_does_not_mutate_input(self):
        """Verify apply_decision_to_context doesn't mutate input."""
        from app.saw_lab.decision_apply_service import apply_decision_to_context

        base_context = {
            "spindle_rpm": 3000.0,
            "feed_rate_mmpm": 600.0,
        }
        applied_multipliers = {"rpm_mul": 1.1}

        original_rpm = base_context["spindle_rpm"]
        result, stamp = apply_decision_to_context(
            base_context=base_context,
            applied_multipliers=applied_multipliers,
        )

        assert base_context["spindle_rpm"] == original_rpm
        assert result["spindle_rpm"] == pytest.approx(3300.0)

    def test_get_multipliers_from_decision(self):
        """Verify multiplier extraction."""
        from app.saw_lab.decision_apply_service import get_multipliers_from_decision

        decision_payload = {
            "delta": {
                "rpm_mul": 1.05,
                "feed_mul": 0.95,
            }
        }

        result = get_multipliers_from_decision(decision_payload)

        assert result["rpm_mul"] == 1.05
        assert result["feed_mul"] == 0.95
        assert result["doc_mul"] == 1.0  # default


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
