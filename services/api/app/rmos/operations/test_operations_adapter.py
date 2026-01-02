"""
Tests for RMOS Operation Adapter

Verifies governance compliance:
1. Feasibility gate (blocks RED/UNKNOWN)
2. Canonical artifact pattern
3. Event type convention
4. SHA256 hashing
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import Any, Dict, Tuple

from .adapter import (
    OperationAdapter,
    OperationRequest,
    PlanRequest,
    execute_operation,
    plan_operation,
    extract_risk_level,
    should_block,
    make_event_type,
    ToolAdapter,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def green_feasibility() -> Dict[str, Any]:
    """Feasibility payload that should ALLOW execution."""
    return {
        "risk_level": "GREEN",
        "score": 95.0,
        "warnings": [],
        "details": {"checked_at": "2025-12-31T00:00:00Z"},
    }


@pytest.fixture
def red_feasibility() -> Dict[str, Any]:
    """Feasibility payload that should BLOCK execution."""
    return {
        "risk_level": "RED",
        "score": 15.0,
        "block_reason": "Depth exceeds safe limit",
        "warnings": ["Depth too deep"],
        "details": {"depth": 2.0, "max_safe": 0.5},
    }


@pytest.fixture
def unknown_feasibility() -> Dict[str, Any]:
    """Feasibility payload with unknown risk."""
    return {
        "risk_level": "UNKNOWN",
        "warnings": ["Could not determine risk"],
    }


@pytest.fixture
def sample_cam_intent() -> Dict[str, Any]:
    """Sample CAM intent payload."""
    return {
        "mode": "saw",
        "tool": {"tool_id": "blade_123"},
        "params": {"units": "inch", "feed_ipm": 12, "depth_in": 0.03},
        "job": {"name": "test_job"},
    }


@pytest.fixture
def mock_tool_adapter() -> MagicMock:
    """Mock tool adapter for testing."""
    adapter = MagicMock(spec=ToolAdapter)
    adapter.generate_gcode.return_value = (
        "G21\nG0 X0 Y0\nG1 Z-1 F100\nM30",
        {"generated_at": "2025-12-31T00:00:00Z"},
    )
    adapter.generate_plan.return_value = {
        "operations": [{"type": "cut", "depth": 0.03}],
        "planned_at": "2025-12-31T00:00:00Z",
    }
    return adapter


# =============================================================================
# Unit Tests: Risk Level Extraction
# =============================================================================

class TestExtractRiskLevel:
    """Tests for extract_risk_level function."""

    def test_extracts_risk_level(self):
        assert extract_risk_level({"risk_level": "GREEN"}) == "GREEN"
        assert extract_risk_level({"risk_level": "RED"}) == "RED"
        assert extract_risk_level({"risk_level": "YELLOW"}) == "YELLOW"

    def test_supports_alternative_keys(self):
        assert extract_risk_level({"risk": "GREEN"}) == "GREEN"
        assert extract_risk_level({"risk_bucket": "RED"}) == "RED"

    def test_defaults_to_unknown(self):
        assert extract_risk_level({}) == "UNKNOWN"
        assert extract_risk_level({"other": "value"}) == "UNKNOWN"

    def test_normalizes_case(self):
        assert extract_risk_level({"risk_level": "green"}) == "GREEN"
        assert extract_risk_level({"risk_level": "Red"}) == "RED"


# =============================================================================
# Unit Tests: Feasibility Gate
# =============================================================================

class TestShouldBlock:
    """Tests for should_block function."""

    def test_blocks_red(self):
        assert should_block("RED") is True

    def test_blocks_unknown(self):
        assert should_block("UNKNOWN") is True

    def test_blocks_error(self):
        assert should_block("ERROR") is True

    def test_allows_green(self):
        assert should_block("GREEN") is False

    def test_allows_yellow(self):
        assert should_block("YELLOW") is False


# =============================================================================
# Unit Tests: Event Type Convention
# =============================================================================

class TestMakeEventType:
    """Tests for make_event_type function."""

    def test_execution_ok(self):
        result = make_event_type("saw_v1", "execution", "ok")
        assert result == "saw_v1_execution_ok"

    def test_execution_blocked(self):
        result = make_event_type("saw_v1", "execution", "blocked")
        assert result == "saw_v1_execution_blocked"

    def test_plan_planned(self):
        result = make_event_type("cam_roughing_v1", "plan", "planned")
        assert result == "cam_roughing_v1_plan_planned"

    def test_normalizes_case(self):
        result = make_event_type("SAW_V1", "EXECUTION", "OK")
        assert result == "saw_v1_execution_ok"

    def test_replaces_hyphens(self):
        result = make_event_type("cam-roughing-v1", "execution", "ok")
        assert result == "cam_roughing_v1_execution_ok"


# =============================================================================
# Integration Tests: Execute Operation
# =============================================================================

class TestExecuteOperation:
    """Tests for execute_operation with mocked persistence."""

    @patch("app.rmos.operations.adapter.persist_run")
    @patch("app.rmos.operations.adapter.create_run_id")
    def test_green_feasibility_allows_execution(
        self,
        mock_create_run_id,
        mock_persist_run,
        green_feasibility,
        sample_cam_intent,
        mock_tool_adapter,
    ):
        """GREEN feasibility should allow execution and produce G-code."""
        mock_create_run_id.return_value = "run_test123"

        result = execute_operation(
            tool_id="saw_v1",
            mode="saw",
            cam_intent_v1=sample_cam_intent,
            feasibility=green_feasibility,
            tool_adapter=mock_tool_adapter,
        )

        assert result.status == "OK"
        assert result.run_id == "run_test123"
        assert result.risk_level == "GREEN"
        assert result.event_type == "saw_v1_execution_ok"
        assert result.gcode_text is not None
        assert result.block_reason is None

        # Verify artifact was persisted
        mock_persist_run.assert_called_once()
        artifact = mock_persist_run.call_args[0][0]
        assert artifact.status == "OK"
        assert artifact.event_type == "saw_v1_execution_ok"

    @patch("app.rmos.operations.adapter.persist_run")
    @patch("app.rmos.operations.adapter.create_run_id")
    def test_red_feasibility_blocks_execution(
        self,
        mock_create_run_id,
        mock_persist_run,
        red_feasibility,
        sample_cam_intent,
        mock_tool_adapter,
    ):
        """RED feasibility should block execution with 409 equivalent."""
        mock_create_run_id.return_value = "run_blocked123"

        result = execute_operation(
            tool_id="saw_v1",
            mode="saw",
            cam_intent_v1=sample_cam_intent,
            feasibility=red_feasibility,
            tool_adapter=mock_tool_adapter,
        )

        assert result.status == "BLOCKED"
        assert result.run_id == "run_blocked123"
        assert result.risk_level == "RED"
        assert result.event_type == "saw_v1_execution_blocked"
        assert result.gcode_text is None
        assert "Depth exceeds safe limit" in result.block_reason

        # Verify BLOCKED artifact was still persisted (for audit)
        mock_persist_run.assert_called_once()
        artifact = mock_persist_run.call_args[0][0]
        assert artifact.status == "BLOCKED"

    @patch("app.rmos.operations.adapter.persist_run")
    @patch("app.rmos.operations.adapter.create_run_id")
    def test_unknown_feasibility_blocks_execution(
        self,
        mock_create_run_id,
        mock_persist_run,
        unknown_feasibility,
        sample_cam_intent,
    ):
        """UNKNOWN feasibility should block execution."""
        mock_create_run_id.return_value = "run_unknown123"

        result = execute_operation(
            tool_id="saw_v1",
            mode="saw",
            cam_intent_v1=sample_cam_intent,
            feasibility=unknown_feasibility,
        )

        assert result.status == "BLOCKED"
        assert result.risk_level == "UNKNOWN"
        assert "incomplete" in result.block_reason.lower()

    @patch("app.rmos.operations.adapter.persist_run")
    @patch("app.rmos.operations.adapter.create_run_id")
    def test_lineage_parent_plan_tracked(
        self,
        mock_create_run_id,
        mock_persist_run,
        green_feasibility,
        sample_cam_intent,
        mock_tool_adapter,
    ):
        """Parent plan run_id should be tracked in artifact meta."""
        mock_create_run_id.return_value = "run_child123"

        result = execute_operation(
            tool_id="saw_v1",
            mode="saw",
            cam_intent_v1=sample_cam_intent,
            feasibility=green_feasibility,
            parent_plan_run_id="run_plan456",
            tool_adapter=mock_tool_adapter,
        )

        assert result.status == "OK"

        # Verify lineage is tracked
        artifact = mock_persist_run.call_args[0][0]
        assert artifact.meta.get("parent_plan_run_id") == "run_plan456"
        assert artifact.parent_run_id == "run_plan456"


# =============================================================================
# Integration Tests: Plan Operation
# =============================================================================

class TestPlanOperation:
    """Tests for plan_operation with mocked persistence."""

    @patch("app.rmos.operations.adapter.persist_run")
    @patch("app.rmos.operations.adapter.create_run_id")
    def test_creates_plan_artifact(
        self,
        mock_create_run_id,
        mock_persist_run,
        sample_cam_intent,
        mock_tool_adapter,
    ):
        """Plan should create artifact with PLANNED status."""
        mock_create_run_id.return_value = "run_plan123"

        result = plan_operation(
            tool_id="saw_v1",
            mode="saw",
            cam_intent_v1=sample_cam_intent,
            tool_adapter=mock_tool_adapter,
        )

        assert result.status == "PLANNED"
        assert result.run_id == "run_plan123"
        assert result.event_type == "saw_v1_plan_planned"
        assert result.plan is not None

        # Verify artifact was persisted
        mock_persist_run.assert_called_once()

    @patch("app.rmos.operations.adapter.persist_run")
    @patch("app.rmos.operations.adapter.create_run_id")
    def test_plan_with_red_feasibility_blocked(
        self,
        mock_create_run_id,
        mock_persist_run,
        red_feasibility,
        sample_cam_intent,
    ):
        """Plan with RED feasibility should be BLOCKED."""
        mock_create_run_id.return_value = "run_plan_blocked"

        result = plan_operation(
            tool_id="cam_roughing_v1",
            mode="roughing",
            cam_intent_v1=sample_cam_intent,
            feasibility=red_feasibility,
        )

        assert result.status == "BLOCKED"
        assert result.risk_level == "RED"
        assert result.event_type == "cam_roughing_v1_plan_blocked"


# =============================================================================
# Tests: SHA256 Hashing
# =============================================================================

class TestHashing:
    """Tests for SHA256 hashing in artifacts."""

    @patch("app.rmos.operations.adapter.persist_run")
    @patch("app.rmos.operations.adapter.create_run_id")
    def test_feasibility_sha256_computed(
        self,
        mock_create_run_id,
        mock_persist_run,
        green_feasibility,
        sample_cam_intent,
        mock_tool_adapter,
    ):
        """Feasibility SHA256 should be computed and stored."""
        mock_create_run_id.return_value = "run_hash123"

        execute_operation(
            tool_id="saw_v1",
            mode="saw",
            cam_intent_v1=sample_cam_intent,
            feasibility=green_feasibility,
            tool_adapter=mock_tool_adapter,
        )

        artifact = mock_persist_run.call_args[0][0]
        assert artifact.hashes.feasibility_sha256 is not None
        assert len(artifact.hashes.feasibility_sha256) == 64  # SHA256 hex length

    @patch("app.rmos.operations.adapter.persist_run")
    @patch("app.rmos.operations.adapter.create_run_id")
    def test_gcode_sha256_computed(
        self,
        mock_create_run_id,
        mock_persist_run,
        green_feasibility,
        sample_cam_intent,
        mock_tool_adapter,
    ):
        """G-code SHA256 should be computed when G-code is generated."""
        mock_create_run_id.return_value = "run_gcode123"

        result = execute_operation(
            tool_id="saw_v1",
            mode="saw",
            cam_intent_v1=sample_cam_intent,
            feasibility=green_feasibility,
            tool_adapter=mock_tool_adapter,
        )

        assert result.gcode_sha256 is not None
        assert len(result.gcode_sha256) == 64

        artifact = mock_persist_run.call_args[0][0]
        assert artifact.hashes.gcode_sha256 == result.gcode_sha256
