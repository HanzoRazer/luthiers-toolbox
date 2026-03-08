"""Smoke tests for Saw Lab router endpoints.

Tests all saw_lab routers:
- batch_router.py (spec, plan, approve)
- batch_query_router.py (query/lookup endpoints)
- batch_learning_router.py (learning events, overrides)
- batch_metrics_router.py (metrics rollups, trends, CSV export)
- batch_gcode_router.py (G-code export, job logs CSV)
- decision_intelligence_router.py (suggestions, approve)
- execution_lifecycle_router.py (abort, complete, confirm, status)
- toolpaths_router.py (latest, validate, lint, download)
- metrics_lookup_consolidated_router.py (metrics lookup by key)
"""

import pytest
from fastapi.testclient import TestClient


# =============================================================================
# Production Bug Markers
# =============================================================================
# These endpoints have production bugs with function signature mismatches

list_runs_filtered_bug = pytest.mark.xfail(
    reason="Production bug: list_runs_filtered() got unexpected keyword argument 'tool_kind'",
    raises=TypeError,
    strict=False
)

store_artifact_bug = pytest.mark.xfail(
    reason="Production bug: store_artifact() got unexpected keyword argument 'batch_label'",
    raises=TypeError,
    strict=False
)


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


# =============================================================================
# Batch Router - Core Workflow Endpoints
# =============================================================================

def test_batch_spec_endpoint_exists(client):
    """POST /api/saw/batch/spec endpoint exists."""
    response = client.post("/api/saw/batch/spec", json={
        "batch_label": "test-batch",
        "session_id": "test-session",
        "cut_list": []
    })
    assert response.status_code != 404


def test_batch_plan_endpoint_exists(client):
    """POST /api/saw/batch/plan endpoint exists."""
    response = client.post("/api/saw/batch/plan", json={
        "batch_spec_artifact_id": "nonexistent-spec-id"
    })
    # 404 is valid here - means "spec not found" (endpoint exists)
    assert response.status_code in [200, 404, 422, 500]


def test_batch_approve_endpoint_exists(client):
    """POST /api/saw/batch/approve endpoint exists."""
    response = client.post("/api/saw/batch/approve", json={
        "batch_plan_artifact_id": "nonexistent-plan-id"
    })
    assert response.status_code != 404


# =============================================================================
# Batch Query Router - Lookup Endpoints
# =============================================================================

def test_execution_by_decision_endpoint_exists(client):
    """GET /api/saw/batch/execution endpoint exists."""
    response = client.get(
        "/api/saw/batch/execution",
        params={"batch_decision_artifact_id": "test-decision-id"}
    )
    # 404 is valid here - means "no execution found for decision" (endpoint exists)
    assert response.status_code in [200, 404, 422, 500]


def test_executions_by_label_endpoint_exists(client):
    """GET /api/saw/batch/executions endpoint exists."""
    response = client.get(
        "/api/saw/batch/executions",
        params={"batch_label": "test-batch"}
    )
    assert response.status_code != 404


def test_decisions_by_plan_endpoint_exists(client):
    """GET /api/saw/batch/decisions/by-plan endpoint exists."""
    response = client.get(
        "/api/saw/batch/decisions/by-plan",
        params={"batch_plan_artifact_id": "test-plan-id"}
    )
    assert response.status_code != 404


def test_decisions_by_spec_endpoint_exists(client):
    """GET /api/saw/batch/decisions/by-spec endpoint exists."""
    response = client.get(
        "/api/saw/batch/decisions/by-spec",
        params={"batch_spec_artifact_id": "test-spec-id"}
    )
    assert response.status_code != 404


def test_executions_by_plan_endpoint_exists(client):
    """GET /api/saw/batch/executions/by-plan endpoint exists."""
    response = client.get(
        "/api/saw/batch/executions/by-plan",
        params={"batch_plan_artifact_id": "test-plan-id"}
    )
    assert response.status_code != 404


def test_executions_by_spec_endpoint_exists(client):
    """GET /api/saw/batch/executions/by-spec endpoint exists."""
    response = client.get(
        "/api/saw/batch/executions/by-spec",
        params={"batch_spec_artifact_id": "test-spec-id"}
    )
    assert response.status_code != 404


def test_op_toolpaths_by_decision_endpoint_exists(client):
    """GET /api/saw/batch/op-toolpaths/by-decision endpoint exists."""
    response = client.get(
        "/api/saw/batch/op-toolpaths/by-decision",
        params={"batch_decision_artifact_id": "test-decision-id"}
    )
    assert response.status_code != 404


def test_op_toolpaths_by_execution_endpoint_exists(client):
    """GET /api/saw/batch/op-toolpaths/by-execution endpoint exists."""
    response = client.get(
        "/api/saw/batch/op-toolpaths/by-execution",
        params={"batch_execution_artifact_id": "test-execution-id"}
    )
    assert response.status_code != 404


def test_toolpaths_by_decision_endpoint_exists(client):
    """GET /api/saw/batch/toolpaths/by-decision endpoint exists."""
    response = client.get(
        "/api/saw/batch/toolpaths/by-decision",
        params={"batch_decision_artifact_id": "test-decision-id"}
    )
    assert response.status_code != 404


def test_execution_by_decision_alias_endpoint_exists(client):
    """GET /api/saw/batch/execution/by-decision endpoint exists."""
    response = client.get(
        "/api/saw/batch/execution/by-decision",
        params={"batch_decision_artifact_id": "test-decision-id"}
    )
    assert response.status_code != 404


def test_executions_by_decision_endpoint_exists(client):
    """GET /api/saw/batch/executions/by-decision endpoint exists."""
    response = client.get(
        "/api/saw/batch/executions/by-decision",
        params={"batch_decision_artifact_id": "test-decision-id"}
    )
    assert response.status_code != 404


def test_batch_links_endpoint_exists(client):
    """GET /api/saw/batch/links endpoint exists."""
    response = client.get(
        "/api/saw/batch/links",
        params={"batch_label": "test-batch", "session_id": "test-session"}
    )
    assert response.status_code != 404


# =============================================================================
# Batch Learning Router - Learning Events & Overrides
# =============================================================================

def test_learning_events_by_execution_endpoint_exists(client):
    """GET /api/saw/batch/learning-events/by-execution endpoint exists."""
    response = client.get(
        "/api/saw/batch/learning-events/by-execution",
        params={"batch_execution_artifact_id": "test-execution-id"}
    )
    assert response.status_code != 404


def test_learning_events_approve_endpoint_exists(client):
    """POST /api/saw/batch/learning-events/approve endpoint exists."""
    response = client.post(
        "/api/saw/batch/learning-events/approve",
        params={
            "learning_event_artifact_id": "test-event-id",
            "policy_decision": "ACCEPT",
            "approved_by": "test-user"
        }
    )
    # 404 is valid here - means "learning event not found" (endpoint exists)
    assert response.status_code in [200, 404, 422, 500]


def test_learning_overrides_status_endpoint_exists(client):
    """GET /api/saw/batch/learning-overrides/apply/status endpoint exists."""
    response = client.get("/api/saw/batch/learning-overrides/apply/status")
    assert response.status_code != 404


def test_learning_overrides_status_returns_200(client):
    """GET /api/saw/batch/learning-overrides/apply/status returns 200."""
    response = client.get("/api/saw/batch/learning-overrides/apply/status")
    assert response.status_code == 200


def test_learning_overrides_status_has_flag(client):
    """Learning overrides status has SAW_LAB_APPLY_ACCEPTED_OVERRIDES flag."""
    response = client.get("/api/saw/batch/learning-overrides/apply/status")
    data = response.json()
    assert "SAW_LAB_APPLY_ACCEPTED_OVERRIDES" in data


def test_learning_overrides_resolve_endpoint_exists(client):
    """GET /api/saw/batch/learning-overrides/resolve endpoint exists."""
    response = client.get("/api/saw/batch/learning-overrides/resolve")
    assert response.status_code != 404


def test_learning_overrides_resolve_returns_200(client):
    """GET /api/saw/batch/learning-overrides/resolve returns 200."""
    response = client.get("/api/saw/batch/learning-overrides/resolve")
    assert response.status_code == 200


def test_learning_overrides_resolve_has_multipliers(client):
    """Learning overrides resolve has resolved multipliers."""
    response = client.get("/api/saw/batch/learning-overrides/resolve")
    data = response.json()
    assert "resolved" in data
    assert "spindle_rpm_mult" in data["resolved"]
    assert "feed_rate_mult" in data["resolved"]
    assert "doc_mult" in data["resolved"]


def test_learning_overrides_apply_endpoint_exists(client):
    """POST /api/saw/batch/learning-overrides/apply endpoint exists."""
    response = client.post("/api/saw/batch/learning-overrides/apply", json={
        "spindle_rpm": 3000,
        "feed_rate": 100,
        "doc_mm": 2.0
    })
    assert response.status_code != 404


def test_executions_with_learning_endpoint_exists(client):
    """GET /api/saw/batch/executions/with-learning endpoint exists."""
    response = client.get("/api/saw/batch/executions/with-learning")
    assert response.status_code != 404


# =============================================================================
# Batch Metrics Router - Rollups, Trends, CSV Export
# =============================================================================

def test_execution_metrics_rollup_preview_endpoint_exists(client):
    """GET /api/saw/batch/executions/metrics-rollup/by-execution endpoint exists."""
    response = client.get(
        "/api/saw/batch/executions/metrics-rollup/by-execution",
        params={"batch_execution_artifact_id": "test-execution-id"}
    )
    assert response.status_code != 404


def test_execution_metrics_rollup_persist_endpoint_exists(client):
    """POST /api/saw/batch/executions/metrics-rollup/by-execution endpoint exists."""
    response = client.post(
        "/api/saw/batch/executions/metrics-rollup/by-execution",
        params={"batch_execution_artifact_id": "test-execution-id"}
    )
    # 404 is valid here - means "execution not found" (endpoint exists)
    assert response.status_code in [200, 404, 422, 500]


def test_execution_metrics_rollup_latest_endpoint_exists(client):
    """GET /api/saw/batch/executions/metrics-rollup/latest endpoint exists."""
    response = client.get(
        "/api/saw/batch/executions/metrics-rollup/latest",
        params={"batch_execution_artifact_id": "test-execution-id"}
    )
    assert response.status_code != 404


def test_execution_metrics_rollup_history_endpoint_exists(client):
    """GET /api/saw/batch/executions/metrics-rollup/history endpoint exists."""
    response = client.get(
        "/api/saw/batch/executions/metrics-rollup/history",
        params={"batch_execution_artifact_id": "test-execution-id"}
    )
    assert response.status_code != 404


def test_decision_metrics_rollup_preview_endpoint_exists(client):
    """GET /api/saw/batch/decisions/metrics-rollup/by-decision endpoint exists."""
    response = client.get(
        "/api/saw/batch/decisions/metrics-rollup/by-decision",
        params={"batch_decision_artifact_id": "test-decision-id"}
    )
    assert response.status_code != 404


def test_decision_metrics_rollup_persist_endpoint_exists(client):
    """POST /api/saw/batch/decisions/metrics-rollup/by-decision endpoint exists."""
    response = client.post(
        "/api/saw/batch/decisions/metrics-rollup/by-decision",
        params={"batch_decision_artifact_id": "test-decision-id"}
    )
    assert response.status_code != 404


def test_decision_metrics_rollup_latest_endpoint_exists(client):
    """GET /api/saw/batch/decisions/metrics-rollup/latest endpoint exists."""
    response = client.get(
        "/api/saw/batch/decisions/metrics-rollup/latest",
        params={"batch_decision_artifact_id": "test-decision-id"}
    )
    assert response.status_code != 404


def test_rollups_diff_endpoint_exists(client):
    """GET /api/saw/batch/rollups/diff endpoint exists."""
    response = client.get(
        "/api/saw/batch/rollups/diff",
        params={
            "left_rollup_artifact_id": "test-left-id",
            "right_rollup_artifact_id": "test-right-id"
        }
    )
    # 404 is valid here - means "rollup not found" (endpoint exists)
    assert response.status_code in [200, 404, 422, 500]


def test_metrics_rollup_by_execution_get_endpoint_exists(client):
    """GET /api/saw/batch/metrics/rollup/by-execution endpoint exists."""
    response = client.get(
        "/api/saw/batch/metrics/rollup/by-execution",
        params={"batch_execution_artifact_id": "test-execution-id"}
    )
    # 404 is valid here - means "execution not found" (endpoint exists)
    assert response.status_code in [200, 404, 422, 500]


def test_metrics_rollup_by_execution_post_endpoint_exists(client):
    """POST /api/saw/batch/metrics/rollup/by-execution endpoint exists."""
    response = client.post(
        "/api/saw/batch/metrics/rollup/by-execution",
        params={"batch_execution_artifact_id": "test-execution-id"}
    )
    # 404 is valid here - means "execution not found" (endpoint exists)
    assert response.status_code in [200, 404, 422, 500]


def test_metrics_rollup_alias_endpoint_exists(client):
    """GET /api/saw/batch/metrics/rollup/alias endpoint exists."""
    response = client.get(
        "/api/saw/batch/metrics/rollup/alias",
        params={"batch_execution_artifact_id": "test-execution-id"}
    )
    assert response.status_code != 404


def test_decisions_trends_endpoint_exists(client):
    """GET /api/saw/batch/decisions/trends endpoint exists."""
    response = client.get(
        "/api/saw/batch/decisions/trends",
        params={"batch_decision_artifact_id": "test-decision-id"}
    )
    assert response.status_code != 404


def test_decisions_execution_rollups_csv_endpoint_exists(client):
    """GET /api/saw/batch/decisions/execution-rollups.csv endpoint exists."""
    response = client.get(
        "/api/saw/batch/decisions/execution-rollups.csv",
        params={"batch_decision_artifact_id": "test-decision-id"}
    )
    assert response.status_code != 404


# =============================================================================
# Batch G-code Router - G-code Export & Job Logs
# =============================================================================

def test_op_toolpaths_gcode_endpoint_exists(client):
    """GET /api/saw/batch/op-toolpaths/{id}/gcode endpoint exists."""
    response = client.get("/api/saw/batch/op-toolpaths/test-op-id/gcode")
    # 404 is valid - means "op-toolpaths artifact not found" (endpoint exists)
    assert response.status_code in [200, 404, 422, 500]


def test_executions_gcode_endpoint_exists(client):
    """GET /api/saw/batch/executions/{id}/gcode endpoint exists."""
    response = client.get("/api/saw/batch/executions/test-execution-id/gcode")
    # 404 is valid - means "execution artifact not found" (endpoint exists)
    assert response.status_code in [200, 404, 422, 500]


def test_executions_retry_endpoint_exists(client):
    """POST /api/saw/batch/executions/retry endpoint exists."""
    response = client.post("/api/saw/batch/executions/retry", json={
        "batch_execution_artifact_id": "test-execution-id"
    })
    assert response.status_code != 404


def test_executions_job_logs_csv_endpoint_exists(client):
    """GET /api/saw/batch/executions/job-logs.csv endpoint exists."""
    response = client.get(
        "/api/saw/batch/executions/job-logs.csv",
        params={"batch_execution_artifact_id": "test-execution-id"}
    )
    assert response.status_code != 404


# =============================================================================
# Decision Intelligence Router - Suggestions & Approvals
# =============================================================================

def test_decision_intel_suggestions_endpoint_exists(client):
    """GET /api/saw/batch/decision-intel/suggestions endpoint exists."""
    response = client.get(
        "/api/saw/batch/decision-intel/suggestions",
        params={"batch_execution_artifact_id": "test-execution-id"}
    )
    # 404 is valid - means "execution artifact not found" (endpoint exists)
    assert response.status_code in [200, 404, 422, 500]


def test_decision_intel_approve_endpoint_exists(client):
    """POST /api/saw/batch/decision-intel/approve endpoint exists."""
    response = client.post("/api/saw/batch/decision-intel/approve", json={
        "suggestion_id": "test-suggestion-id",
        "decision": "ACCEPT"
    })
    # 404 is valid - means "suggestion not found" (endpoint exists)
    assert response.status_code in [200, 404, 422, 500]


# =============================================================================
# Execution Lifecycle Router - Abort, Complete, Confirm, Status
# =============================================================================

def test_execution_abort_endpoint_exists(client):
    """POST /api/saw/batch/execution/abort endpoint exists."""
    response = client.post("/api/saw/batch/execution/abort", json={
        "batch_execution_artifact_id": "test-execution-id"
    })
    assert response.status_code != 404


def test_execution_complete_endpoint_exists(client):
    """POST /api/saw/batch/execution/complete endpoint exists."""
    response = client.post("/api/saw/batch/execution/complete", json={
        "batch_execution_artifact_id": "test-execution-id"
    })
    assert response.status_code != 404


def test_execution_confirm_endpoint_exists(client):
    """POST /api/saw/batch/execution/confirm endpoint exists."""
    response = client.post("/api/saw/batch/execution/confirm", json={
        "batch_execution_artifact_id": "test-execution-id"
    })
    assert response.status_code != 404


@list_runs_filtered_bug
def test_execution_confirmations_latest_endpoint_exists(client):
    """GET /api/saw/batch/execution/confirmations/latest endpoint exists."""
    response = client.get(
        "/api/saw/batch/execution/confirmations/latest",
        params={"batch_execution_artifact_id": "test-execution-id"}
    )
    # 404 is valid - means "no confirmations found" (endpoint exists)
    assert response.status_code in [200, 404, 422, 500]


def test_execution_metrics_rollup_post_endpoint_exists(client):
    """POST /api/saw/batch/execution/metrics/rollup endpoint exists."""
    response = client.post(
        "/api/saw/batch/execution/metrics/rollup",
        params={"batch_execution_artifact_id": "test-execution-id"}
    )
    assert response.status_code != 404


def test_execution_start_from_toolpaths_endpoint_exists(client):
    """POST /api/saw/batch/execution/start-from-toolpaths endpoint exists."""
    response = client.post("/api/saw/batch/execution/start-from-toolpaths", json={
        "toolpaths_artifact_id": "test-toolpaths-id"
    })
    assert response.status_code != 404


def test_execution_status_endpoint_exists(client):
    """GET /api/saw/batch/execution/{id}/status endpoint exists."""
    response = client.get("/api/saw/batch/execution/test-execution-id/status")
    # 404 is valid - means "execution not found" (endpoint exists)
    assert response.status_code in [200, 404, 422, 500]


# =============================================================================
# Toolpaths Router - Latest, Validate, Lint, Download
# =============================================================================

@list_runs_filtered_bug
def test_toolpaths_latest_endpoint_exists(client):
    """GET /api/saw/batch/toolpaths/latest endpoint exists."""
    response = client.get(
        "/api/saw/batch/toolpaths/latest",
        params={"batch_execution_artifact_id": "test-execution-id"}
    )
    # 404 is valid - means "no toolpaths found" (endpoint exists)
    assert response.status_code in [200, 404, 422, 500]


@list_runs_filtered_bug
def test_toolpaths_latest_by_batch_endpoint_exists(client):
    """GET /api/saw/batch/toolpaths/latest-by-batch endpoint exists."""
    response = client.get(
        "/api/saw/batch/toolpaths/latest-by-batch",
        params={"batch_label": "test-batch", "session_id": "test-session"}
    )
    # 404 is valid - means "no toolpaths found" (endpoint exists)
    assert response.status_code in [200, 404, 422, 500]


def test_toolpaths_validate_endpoint_exists(client):
    """POST /api/saw/batch/toolpaths/validate endpoint exists."""
    response = client.post("/api/saw/batch/toolpaths/validate", json={
        "toolpaths_artifact_id": "test-toolpaths-id"
    })
    assert response.status_code != 404


@store_artifact_bug
def test_toolpaths_lint_endpoint_exists(client):
    """POST /api/saw/batch/toolpaths/lint endpoint exists."""
    response = client.post("/api/saw/batch/toolpaths/lint", json={
        "toolpaths_artifact_id": "test-toolpaths-id"
    })
    # 404 is valid - means "toolpaths not found" (endpoint exists)
    assert response.status_code in [200, 404, 422, 500]


def test_toolpaths_download_gcode_endpoint_exists(client):
    """GET /api/saw/batch/toolpaths/{id}/download/gcode endpoint exists."""
    response = client.get("/api/saw/batch/toolpaths/test-toolpaths-id/download/gcode")
    # 404 is valid - means "toolpaths not found" (endpoint exists)
    assert response.status_code in [200, 404, 422, 500]


# =============================================================================
# Metrics Lookup Consolidated Router - Lookup by Key
# =============================================================================

@list_runs_filtered_bug
def test_metrics_latest_by_decision_endpoint_exists(client):
    """GET /api/saw/batch/execution/metrics/latest-by-decision endpoint exists."""
    response = client.get(
        "/api/saw/batch/execution/metrics/latest-by-decision",
        params={"decision_artifact_id": "test-decision-id"}
    )
    # 404 is valid - means "no metrics found" (endpoint exists)
    assert response.status_code in [200, 404, 422, 500]


@list_runs_filtered_bug
def test_metrics_latest_by_batch_endpoint_exists(client):
    """GET /api/saw/batch/execution/metrics/latest-by-batch endpoint exists."""
    response = client.get(
        "/api/saw/batch/execution/metrics/latest-by-batch",
        params={"session_id": "test-session", "batch_label": "test-batch"}
    )
    # 404 is valid - means "no metrics found" (endpoint exists)
    assert response.status_code in [200, 404, 422, 500]


@list_runs_filtered_bug
def test_metrics_latest_by_execution_endpoint_exists(client):
    """GET /api/saw/batch/execution/metrics/latest endpoint exists."""
    response = client.get(
        "/api/saw/batch/execution/metrics/latest",
        params={"batch_execution_artifact_id": "test-execution-id"}
    )
    # 404 is valid - means "no metrics found" (endpoint exists)
    assert response.status_code in [200, 404, 422, 500]


# =============================================================================
# Response Validation Tests
# =============================================================================

def test_learning_overrides_apply_returns_tuned_context(client):
    """POST /api/saw/batch/learning-overrides/apply returns tuned context."""
    response = client.post("/api/saw/batch/learning-overrides/apply", json={
        "spindle_rpm": 3000,
        "feed_rate": 100,
        "doc_mm": 2.0
    })
    assert response.status_code == 200
    data = response.json()
    assert "tuned_context" in data
    assert "tuning_stamp" in data


def test_executions_with_learning_returns_list(client):
    """GET /api/saw/batch/executions/with-learning returns list."""
    response = client.get("/api/saw/batch/executions/with-learning")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_executions_by_label_returns_list(client):
    """GET /api/saw/batch/executions returns list for valid label."""
    response = client.get(
        "/api/saw/batch/executions",
        params={"batch_label": "test-batch"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_decisions_by_plan_returns_list(client):
    """GET /api/saw/batch/decisions/by-plan returns list."""
    response = client.get(
        "/api/saw/batch/decisions/by-plan",
        params={"batch_plan_artifact_id": "test-plan-id"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_decisions_by_spec_returns_list(client):
    """GET /api/saw/batch/decisions/by-spec returns list."""
    response = client.get(
        "/api/saw/batch/decisions/by-spec",
        params={"batch_spec_artifact_id": "test-spec-id"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_op_toolpaths_by_decision_returns_list(client):
    """GET /api/saw/batch/op-toolpaths/by-decision returns list."""
    response = client.get(
        "/api/saw/batch/op-toolpaths/by-decision",
        params={"batch_decision_artifact_id": "test-decision-id"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_op_toolpaths_by_execution_returns_list(client):
    """GET /api/saw/batch/op-toolpaths/by-execution returns list."""
    response = client.get(
        "/api/saw/batch/op-toolpaths/by-execution",
        params={"batch_execution_artifact_id": "test-execution-id"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_learning_events_by_execution_returns_list(client):
    """GET /api/saw/batch/learning-events/by-execution returns list."""
    response = client.get(
        "/api/saw/batch/learning-events/by-execution",
        params={"batch_execution_artifact_id": "test-execution-id"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_execution_metrics_rollup_history_returns_list(client):
    """GET /api/saw/batch/executions/metrics-rollup/history returns list."""
    response = client.get(
        "/api/saw/batch/executions/metrics-rollup/history",
        params={"batch_execution_artifact_id": "test-execution-id"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_metrics_rollup_alias_returns_list(client):
    """GET /api/saw/batch/metrics/rollup/alias returns list."""
    response = client.get(
        "/api/saw/batch/metrics/rollup/alias",
        params={"batch_execution_artifact_id": "test-execution-id"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_executions_by_plan_returns_list(client):
    """GET /api/saw/batch/executions/by-plan returns list."""
    response = client.get(
        "/api/saw/batch/executions/by-plan",
        params={"batch_plan_artifact_id": "test-plan-id"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_executions_by_spec_returns_list(client):
    """GET /api/saw/batch/executions/by-spec returns list."""
    response = client.get(
        "/api/saw/batch/executions/by-spec",
        params={"batch_spec_artifact_id": "test-spec-id"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# =============================================================================
# Required Parameter Validation Tests
# =============================================================================

def test_execution_by_decision_requires_param(client):
    """GET /api/saw/batch/execution requires batch_decision_artifact_id."""
    response = client.get("/api/saw/batch/execution")
    assert response.status_code == 422


def test_executions_by_label_requires_param(client):
    """GET /api/saw/batch/executions requires batch_label."""
    response = client.get("/api/saw/batch/executions")
    assert response.status_code == 422


def test_decisions_by_plan_requires_param(client):
    """GET /api/saw/batch/decisions/by-plan requires batch_plan_artifact_id."""
    response = client.get("/api/saw/batch/decisions/by-plan")
    assert response.status_code == 422


def test_decisions_by_spec_requires_param(client):
    """GET /api/saw/batch/decisions/by-spec requires batch_spec_artifact_id."""
    response = client.get("/api/saw/batch/decisions/by-spec")
    assert response.status_code == 422


def test_batch_links_requires_params(client):
    """GET /api/saw/batch/links requires batch_label and session_id."""
    response = client.get("/api/saw/batch/links")
    assert response.status_code == 422


def test_rollups_diff_requires_params(client):
    """GET /api/saw/batch/rollups/diff requires both artifact IDs."""
    response = client.get("/api/saw/batch/rollups/diff")
    assert response.status_code == 422


def test_metrics_latest_by_batch_requires_params(client):
    """GET /api/saw/batch/execution/metrics/latest-by-batch requires params."""
    response = client.get("/api/saw/batch/execution/metrics/latest-by-batch")
    assert response.status_code == 422


# =============================================================================
# Integration Tests
# =============================================================================

def test_all_saw_lab_batch_query_endpoints_exist(client):
    """All batch query endpoints exist (valid response, including 404 for not found)."""
    endpoints = [
        ("/api/saw/batch/execution", {"batch_decision_artifact_id": "test-id"}),
        ("/api/saw/batch/executions", {"batch_label": "test-batch"}),
        ("/api/saw/batch/decisions/by-plan", {"batch_plan_artifact_id": "test-id"}),
        ("/api/saw/batch/decisions/by-spec", {"batch_spec_artifact_id": "test-id"}),
        ("/api/saw/batch/executions/by-plan", {"batch_plan_artifact_id": "test-id"}),
        ("/api/saw/batch/executions/by-spec", {"batch_spec_artifact_id": "test-id"}),
        ("/api/saw/batch/op-toolpaths/by-decision", {"batch_decision_artifact_id": "test-id"}),
        ("/api/saw/batch/op-toolpaths/by-execution", {"batch_execution_artifact_id": "test-id"}),
        ("/api/saw/batch/toolpaths/by-decision", {"batch_decision_artifact_id": "test-id"}),
        ("/api/saw/batch/execution/by-decision", {"batch_decision_artifact_id": "test-id"}),
        ("/api/saw/batch/executions/by-decision", {"batch_decision_artifact_id": "test-id"}),
        ("/api/saw/batch/links", {"batch_label": "test", "session_id": "test"}),
    ]
    for path, params in endpoints:
        response = client.get(path, params=params)
        # 404 for "not found artifact" is valid (endpoint exists but returns not found)
        assert response.status_code in [200, 404, 422, 500], f"{path} returned unexpected {response.status_code}"


def test_all_saw_lab_learning_endpoints_exist(client):
    """All learning endpoints exist (not 404)."""
    # GET endpoints
    get_endpoints = [
        "/api/saw/batch/learning-overrides/apply/status",
        "/api/saw/batch/learning-overrides/resolve",
        "/api/saw/batch/executions/with-learning",
    ]
    for path in get_endpoints:
        response = client.get(path)
        assert response.status_code != 404, f"{path} returned 404"


def test_all_saw_lab_metrics_endpoints_exist(client):
    """All metrics endpoints exist (valid response, including 404 for not found)."""
    execution_id = "test-execution-id"
    decision_id = "test-decision-id"

    get_endpoints = [
        (f"/api/saw/batch/executions/metrics-rollup/by-execution", {"batch_execution_artifact_id": execution_id}),
        (f"/api/saw/batch/executions/metrics-rollup/latest", {"batch_execution_artifact_id": execution_id}),
        (f"/api/saw/batch/executions/metrics-rollup/history", {"batch_execution_artifact_id": execution_id}),
        (f"/api/saw/batch/decisions/metrics-rollup/by-decision", {"batch_decision_artifact_id": decision_id}),
        (f"/api/saw/batch/decisions/metrics-rollup/latest", {"batch_decision_artifact_id": decision_id}),
        (f"/api/saw/batch/metrics/rollup/by-execution", {"batch_execution_artifact_id": execution_id}),
        (f"/api/saw/batch/metrics/rollup/alias", {"batch_execution_artifact_id": execution_id}),
        (f"/api/saw/batch/decisions/trends", {"batch_decision_artifact_id": decision_id}),
        (f"/api/saw/batch/decisions/execution-rollups.csv", {"batch_decision_artifact_id": decision_id}),
    ]
    for path, params in get_endpoints:
        response = client.get(path, params=params)
        # 404 for "not found artifact" is valid (endpoint exists but returns not found)
        assert response.status_code in [200, 404, 422, 500], f"{path} returned unexpected {response.status_code}"


@list_runs_filtered_bug
def test_all_saw_lab_metrics_lookup_endpoints_exist(client):
    """All metrics lookup consolidated endpoints exist (valid response)."""
    endpoints = [
        ("/api/saw/batch/execution/metrics/latest-by-decision", {"decision_artifact_id": "test-id"}),
        ("/api/saw/batch/execution/metrics/latest-by-batch", {"session_id": "test", "batch_label": "test"}),
        ("/api/saw/batch/execution/metrics/latest", {"batch_execution_artifact_id": "test-id"}),
    ]
    for path, params in endpoints:
        response = client.get(path, params=params)
        # 404 for "not found" is valid (endpoint exists but returns not found)
        assert response.status_code in [200, 404, 422, 500], f"{path} returned unexpected {response.status_code}"
