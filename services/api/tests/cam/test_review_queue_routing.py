"""
Tests for CAM Dev Order 8E: Governed Review Queue Routing.

Covers:
  - ReviewQueueItem model and validation
  - ReviewDecisionRecord model and validation
  - Decision-to-status mapping
  - Registry operations
  - CI summary evaluation
  - Router endpoints

8E invariants tested:
  - human_review_required: always True (queue item)
  - decision_authorized: always False
  - implementation_authorized: always False
  - execution_authorized: always False
  - machine_output_allowed: always False
  - human_review_recorded: always True (decision)
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.cam.review_queue_item import (
    ReviewQueueItem,
    create_review_queue_item,
    validate_review_queue_item,
    get_queue_item_summary,
    build_review_queue_hash,
)
from app.cam.review_decision_record import (
    ReviewDecisionRecord,
    create_review_decision_record,
    validate_review_decision_record,
    get_decision_record_summary,
    get_resulting_status,
    DECISION_TO_STATUS_MAP,
)
from app.cam.review_queue_registry import (
    register_review_queue_item,
    get_review_queue_item,
    list_review_queue_items,
    list_review_queue_by_status,
    list_review_queue_by_priority,
    get_review_queue_item_count,
    register_review_decision_record,
    get_review_decision_record,
    list_review_decision_records,
    list_decisions_for_queue_item,
    record_review_decision,
    build_review_queue_from_panel,
    sort_queue_items_by_priority,
    detect_unassigned_critical_reviews,
    detect_stale_review_items,
    get_open_review_items,
    clear_review_queue_indexes_for_tests,
    get_review_queue_index_counts,
)
from app.cam.review_queue_ci import (
    ReviewQueueCISummary,
    count_by_status,
    count_open_by_priority,
    count_blocking_issues,
    count_missing_assignments,
    detect_authorization_violations,
    classify_review_queue_ci_status,
    evaluate_review_queue_ci,
    get_ci_summary_dict,
)
from app.cam.manufacturing_review_panel import create_manufacturing_review_panel
from app.cam.review_attention_priority import create_review_attention_priority
from app.cam.review_ux_registry import (
    register_review_panel,
    register_review_attention_priority,
    clear_review_ux_indexes_for_tests,
)


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_indexes():
    """Clear all indexes before each test."""
    clear_review_queue_indexes_for_tests()
    clear_review_ux_indexes_for_tests()
    yield
    clear_review_queue_indexes_for_tests()
    clear_review_ux_indexes_for_tests()


# ─────────────────────────────────────────────────────────────────────────────
# ReviewQueueItem model tests
# ─────────────────────────────────────────────────────────────────────────────

class TestReviewQueueItemModel:
    """Tests for ReviewQueueItem model."""

    def test_create_queue_item_defaults(self):
        """Queue item has sensible defaults."""
        item = ReviewQueueItem(review_reason="Test review")
        assert item.review_reason == "Test review"
        assert item.review_status == "queued"
        assert item.review_priority == "medium"
        assert item.source_layer == "review_ux"
        assert item.human_review_required is True
        assert item.decision_authorized is False
        assert item.implementation_authorized is False
        assert item.execution_authorized is False
        assert item.machine_output_allowed is False

    def test_create_queue_item_with_options(self):
        """Queue item accepts all options."""
        item = create_review_queue_item(
            review_reason="Critical review",
            source_layer="manufacturing_cognition",
            review_priority="critical",
            panel_id="panel-123",
            assigned_role="senior_reviewer",
            blocking_issues=["Issue 1"],
            warnings=["Warning 1"],
        )
        assert item.review_priority == "critical"
        assert item.source_layer == "manufacturing_cognition"
        assert item.panel_id == "panel-123"
        assert item.assigned_role == "senior_reviewer"
        assert len(item.blocking_issues) == 1
        assert len(item.warnings) == 1

    def test_queue_item_invariant_human_review_required(self):
        """Queue item rejects human_review_required=False."""
        with pytest.raises(ValueError, match="8E invariant violation"):
            ReviewQueueItem(
                review_reason="Test",
                human_review_required=False,
            )

    def test_queue_item_invariant_decision_authorized(self):
        """Queue item rejects decision_authorized=True."""
        with pytest.raises(ValueError, match="8E invariant violation"):
            ReviewQueueItem(
                review_reason="Test",
                decision_authorized=True,
            )

    def test_queue_item_invariant_implementation_authorized(self):
        """Queue item rejects implementation_authorized=True."""
        with pytest.raises(ValueError, match="8E invariant violation"):
            ReviewQueueItem(
                review_reason="Test",
                implementation_authorized=True,
            )

    def test_queue_item_invariant_execution_authorized(self):
        """Queue item rejects execution_authorized=True."""
        with pytest.raises(ValueError, match="8E invariant violation"):
            ReviewQueueItem(
                review_reason="Test",
                execution_authorized=True,
            )

    def test_queue_item_invariant_machine_output_allowed(self):
        """Queue item rejects machine_output_allowed=True."""
        with pytest.raises(ValueError, match="8E invariant violation"):
            ReviewQueueItem(
                review_reason="Test",
                machine_output_allowed=True,
            )

    def test_queue_item_compute_hash(self):
        """Queue item computes deterministic hash."""
        item1 = create_review_queue_item(
            review_reason="Test",
            review_priority="high",
        )
        item2 = create_review_queue_item(
            review_reason="Test",
            review_priority="high",
        )
        assert item1.compute_hash() == item2.compute_hash()

    def test_queue_item_hash_changes_with_priority(self):
        """Different priorities produce different hashes."""
        item1 = create_review_queue_item(review_reason="Test", review_priority="high")
        item2 = create_review_queue_item(review_reason="Test", review_priority="low")
        assert item1.compute_hash() != item2.compute_hash()

    def test_validate_queue_item_valid(self):
        """Valid queue item passes validation."""
        item = create_review_queue_item(review_reason="Valid item")
        is_valid, issues = validate_review_queue_item(item)
        assert is_valid is True
        assert issues == []

    def test_validate_queue_item_missing_reason(self):
        """Missing review_reason fails validation."""
        item = ReviewQueueItem(review_reason="x")
        item.review_reason = ""
        is_valid, issues = validate_review_queue_item(item)
        assert is_valid is False
        assert "review_reason is required" in issues

    def test_get_queue_item_summary(self):
        """get_queue_item_summary returns expected fields."""
        item = create_review_queue_item(
            review_reason="Summary test",
            review_priority="high",
        )
        summary = get_queue_item_summary(item)
        assert summary["review_reason"] == "Summary test"
        assert summary["review_priority"] == "high"
        assert summary["human_review_required"] is True


# ─────────────────────────────────────────────────────────────────────────────
# ReviewDecisionRecord model tests
# ─────────────────────────────────────────────────────────────────────────────

class TestReviewDecisionRecordModel:
    """Tests for ReviewDecisionRecord model."""

    def test_create_decision_record(self):
        """Decision record creation works."""
        record = create_review_decision_record(
            queue_item_id="qid-123",
            decision_type="acknowledge",
            decision_rationale="Acknowledged for review",
        )
        assert record.queue_item_id == "qid-123"
        assert record.decision_type == "acknowledge"
        assert record.resulting_review_status == "in_review"
        assert record.human_review_recorded is True

    def test_decision_to_status_acknowledge(self):
        """acknowledge maps to in_review."""
        assert get_resulting_status("acknowledge") == "in_review"

    def test_decision_to_status_request_more_evidence(self):
        """request_more_evidence maps to needs_more_evidence."""
        assert get_resulting_status("request_more_evidence") == "needs_more_evidence"

    def test_decision_to_status_defer(self):
        """defer maps to deferred."""
        assert get_resulting_status("defer") == "deferred"

    def test_decision_to_status_reject(self):
        """reject maps to rejected."""
        assert get_resulting_status("reject") == "rejected"

    def test_decision_to_status_mark_reviewed(self):
        """mark_reviewed maps to reviewed."""
        assert get_resulting_status("mark_reviewed") == "reviewed"

    def test_decision_invariant_human_review_recorded(self):
        """Decision rejects human_review_recorded=False."""
        with pytest.raises(ValueError, match="8E invariant violation"):
            ReviewDecisionRecord(
                queue_item_id="qid",
                decision_type="acknowledge",
                resulting_review_status="in_review",
                human_review_recorded=False,
            )

    def test_decision_invariant_implementation_authorized(self):
        """Decision rejects implementation_authorized=True."""
        with pytest.raises(ValueError, match="8E invariant violation"):
            ReviewDecisionRecord(
                queue_item_id="qid",
                decision_type="acknowledge",
                resulting_review_status="in_review",
                implementation_authorized=True,
            )

    def test_decision_invariant_execution_authorized(self):
        """Decision rejects execution_authorized=True."""
        with pytest.raises(ValueError, match="8E invariant violation"):
            ReviewDecisionRecord(
                queue_item_id="qid",
                decision_type="acknowledge",
                resulting_review_status="in_review",
                execution_authorized=True,
            )

    def test_decision_invariant_machine_output_allowed(self):
        """Decision rejects machine_output_allowed=True."""
        with pytest.raises(ValueError, match="8E invariant violation"):
            ReviewDecisionRecord(
                queue_item_id="qid",
                decision_type="acknowledge",
                resulting_review_status="in_review",
                machine_output_allowed=True,
            )

    def test_decision_compute_hash(self):
        """Decision computes deterministic hash."""
        record1 = create_review_decision_record(
            queue_item_id="qid",
            decision_type="reject",
            decision_rationale="Not valid",
        )
        record2 = create_review_decision_record(
            queue_item_id="qid",
            decision_type="reject",
            decision_rationale="Not valid",
        )
        assert record1.compute_hash() == record2.compute_hash()


# ─────────────────────────────────────────────────────────────────────────────
# Registry tests
# ─────────────────────────────────────────────────────────────────────────────

class TestRegistry:
    """Tests for registry operations."""

    def test_register_queue_item(self):
        """Queue item registration succeeds."""
        item = create_review_queue_item(review_reason="Test")
        success, error = register_review_queue_item(item)
        assert success is True
        assert error is None
        assert get_review_queue_item_count() == 1

    def test_register_queue_item_duplicate_fails(self):
        """Duplicate queue item registration fails."""
        item = create_review_queue_item(review_reason="Test")
        register_review_queue_item(item)
        success, error = register_review_queue_item(item)
        assert success is False
        assert "already exists" in error

    def test_get_review_queue_item(self):
        """Queue item retrieval by ID works."""
        item = create_review_queue_item(review_reason="Test")
        register_review_queue_item(item)
        retrieved = get_review_queue_item(item.queue_item_id)
        assert retrieved is not None
        assert retrieved.review_reason == "Test"

    def test_list_review_queue_items(self):
        """Queue item listing preserves order."""
        item1 = create_review_queue_item(review_reason="First")
        item2 = create_review_queue_item(review_reason="Second")
        register_review_queue_item(item1)
        register_review_queue_item(item2)
        items = list_review_queue_items()
        assert len(items) == 2
        assert items[0].review_reason == "First"
        assert items[1].review_reason == "Second"

    def test_list_review_queue_by_status(self):
        """Queue item filtering by status works."""
        item1 = create_review_queue_item(review_reason="Queued")
        item2 = create_review_queue_item(review_reason="Reviewed")
        item2.review_status = "reviewed"
        register_review_queue_item(item1)
        register_review_queue_item(item2)

        queued = list_review_queue_by_status("queued")
        reviewed = list_review_queue_by_status("reviewed")
        assert len(queued) == 1
        assert len(reviewed) == 1

    def test_list_review_queue_by_priority(self):
        """Queue item filtering by priority works."""
        item1 = create_review_queue_item(review_reason="High", review_priority="high")
        item2 = create_review_queue_item(review_reason="Low", review_priority="low")
        register_review_queue_item(item1)
        register_review_queue_item(item2)

        high = list_review_queue_by_priority("high")
        low = list_review_queue_by_priority("low")
        assert len(high) == 1
        assert len(low) == 1

    def test_register_decision_record(self):
        """Decision record registration succeeds."""
        record = create_review_decision_record(
            queue_item_id="qid",
            decision_type="acknowledge",
        )
        success, error = register_review_decision_record(record)
        assert success is True
        assert error is None

    def test_list_decisions_for_queue_item(self):
        """Decision filtering by queue item works."""
        item = create_review_queue_item(review_reason="Test")
        register_review_queue_item(item)

        record_review_decision(item.queue_item_id, "acknowledge")
        record_review_decision(item.queue_item_id, "mark_reviewed")

        decisions = list_decisions_for_queue_item(item.queue_item_id)
        assert len(decisions) == 2

    def test_record_review_decision_updates_status(self):
        """Recording decision updates queue item status."""
        item = create_review_queue_item(review_reason="Test")
        register_review_queue_item(item)
        assert item.review_status == "queued"

        record, success, error = record_review_decision(
            item.queue_item_id,
            "acknowledge",
        )
        assert success is True
        assert item.review_status == "in_review"

    def test_record_review_decision_missing_item(self):
        """Recording decision for missing item fails."""
        record, success, error = record_review_decision(
            "nonexistent",
            "acknowledge",
        )
        assert success is False
        assert "not found" in error

    def test_sort_queue_items_by_priority(self):
        """Sorting places critical first, low last."""
        items = [
            create_review_queue_item(review_reason="Low", review_priority="low"),
            create_review_queue_item(review_reason="Critical", review_priority="critical"),
            create_review_queue_item(review_reason="Medium", review_priority="medium"),
        ]
        sorted_items = sort_queue_items_by_priority(items)
        assert sorted_items[0].review_priority == "critical"
        assert sorted_items[-1].review_priority == "low"

    def test_detect_unassigned_critical_reviews(self):
        """Detects critical items without assignment."""
        item1 = create_review_queue_item(
            review_reason="Critical unassigned",
            review_priority="critical",
        )
        item2 = create_review_queue_item(
            review_reason="Critical assigned",
            review_priority="critical",
            assigned_role="reviewer",
        )
        register_review_queue_item(item1)
        register_review_queue_item(item2)

        unassigned = detect_unassigned_critical_reviews()
        assert len(unassigned) == 1
        assert unassigned[0].queue_item_id == item1.queue_item_id

    def test_get_open_review_items(self):
        """Gets only open items."""
        item1 = create_review_queue_item(review_reason="Queued")
        item2 = create_review_queue_item(review_reason="Reviewed")
        item2.review_status = "reviewed"
        register_review_queue_item(item1)
        register_review_queue_item(item2)

        open_items = get_open_review_items()
        assert len(open_items) == 1

    def test_clear_indexes(self):
        """clear_review_queue_indexes_for_tests clears all indexes."""
        item = create_review_queue_item(review_reason="Test")
        register_review_queue_item(item)
        record_review_decision(item.queue_item_id, "acknowledge")

        clear_review_queue_indexes_for_tests()
        counts = get_review_queue_index_counts()
        assert counts["queue_items"] == 0
        assert counts["decision_records"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# Panel-to-queue tests
# ─────────────────────────────────────────────────────────────────────────────

class TestPanelToQueue:
    """Tests for panel-to-queue item builder."""

    def test_build_from_panel_success(self):
        """Building queue item from panel works."""
        panel = create_manufacturing_review_panel(
            panel_name="Test Panel",
            context_artifact_ids=["a1"],
        )
        register_review_panel(panel)

        item, success, error = build_review_queue_from_panel(panel.panel_id)
        assert success is True
        assert item is not None
        assert item.panel_id == panel.panel_id
        assert "manufacturing review panel" in item.review_reason.lower()

    def test_build_from_panel_with_priority(self):
        """Building queue item uses associated priority."""
        panel = create_manufacturing_review_panel(panel_name="Test Panel")
        register_review_panel(panel)

        priority = create_review_attention_priority(
            panel_id=panel.panel_id,
            component_scores={"urgency": 0.9},
        )
        register_review_attention_priority(priority)

        item, success, error = build_review_queue_from_panel(panel.panel_id)
        assert success is True
        assert item.priority_id == priority.priority_id
        assert item.review_priority == "critical"

    def test_build_from_panel_missing(self):
        """Building from missing panel fails."""
        item, success, error = build_review_queue_from_panel("nonexistent")
        assert success is False
        assert "not found" in error


# ─────────────────────────────────────────────────────────────────────────────
# CI summary tests
# ─────────────────────────────────────────────────────────────────────────────

class TestCISummary:
    """Tests for CI summary evaluation."""

    def test_ci_summary_defaults(self):
        """CI summary has expected defaults."""
        summary = ReviewQueueCISummary()
        assert summary.status == "pass"
        assert summary.total_queue_items == 0
        assert summary.implementation_authorized is False
        assert summary.execution_authorized is False
        assert summary.machine_output_allowed is False

    def test_ci_summary_invariants(self):
        """CI summary enforces invariants."""
        with pytest.raises(ValueError, match="8E invariant violation"):
            ReviewQueueCISummary(implementation_authorized=True)

    def test_count_by_status(self):
        """count_by_status counts correctly."""
        items = [
            create_review_queue_item(review_reason="Q1"),
            create_review_queue_item(review_reason="Q2"),
        ]
        items[1].review_status = "reviewed"

        counts = count_by_status(items)
        assert counts["queued"] == 1
        assert counts["reviewed"] == 1

    def test_count_open_by_priority(self):
        """count_open_by_priority counts only open items."""
        items = [
            create_review_queue_item(review_reason="C", review_priority="critical"),
            create_review_queue_item(review_reason="H", review_priority="high"),
        ]
        items[1].review_status = "reviewed"

        counts = count_open_by_priority(items)
        assert counts["critical"] == 1
        assert counts["high"] == 0

    def test_count_missing_assignments(self):
        """count_missing_assignments counts unassigned open items."""
        items = [
            create_review_queue_item(review_reason="Unassigned"),
            create_review_queue_item(
                review_reason="Assigned",
                assigned_role="reviewer",
            ),
        ]
        count = count_missing_assignments(items)
        assert count == 1

    def test_classify_ci_status_pass(self):
        """Clean state is PASS."""
        status, blocking, warnings = classify_review_queue_ci_status(
            critical_open_count=0,
            high_open_count=0,
            missing_assignment_count=0,
            needs_more_evidence_count=0,
            blocking_issue_count=0,
            authorization_violations=[],
        )
        assert status == "pass"
        assert blocking == []
        assert warnings == []

    def test_classify_ci_status_warn_critical_open(self):
        """Critical open item is WARN."""
        status, blocking, warnings = classify_review_queue_ci_status(
            critical_open_count=1,
            high_open_count=0,
            missing_assignment_count=0,
            needs_more_evidence_count=0,
            blocking_issue_count=0,
            authorization_violations=[],
        )
        assert status == "warn"
        assert len(warnings) >= 1

    def test_classify_ci_status_warn_high_open(self):
        """High open item is WARN."""
        status, blocking, warnings = classify_review_queue_ci_status(
            critical_open_count=0,
            high_open_count=1,
            missing_assignment_count=0,
            needs_more_evidence_count=0,
            blocking_issue_count=0,
            authorization_violations=[],
        )
        assert status == "warn"

    def test_classify_ci_status_warn_missing_assignment(self):
        """Missing assignment is WARN."""
        status, blocking, warnings = classify_review_queue_ci_status(
            critical_open_count=0,
            high_open_count=0,
            missing_assignment_count=1,
            needs_more_evidence_count=0,
            blocking_issue_count=0,
            authorization_violations=[],
        )
        assert status == "warn"

    def test_classify_ci_status_fail_authorization_violation(self):
        """Authorization violation is FAIL."""
        status, blocking, warnings = classify_review_queue_ci_status(
            critical_open_count=0,
            high_open_count=0,
            missing_assignment_count=0,
            needs_more_evidence_count=0,
            blocking_issue_count=0,
            authorization_violations=["[qid] execution_authorized=True"],
        )
        assert status == "fail"
        assert len(blocking) >= 1

    def test_evaluate_review_queue_ci_empty(self):
        """Empty queue evaluates to PASS."""
        summary = evaluate_review_queue_ci([], [])
        assert summary.status == "pass"
        assert summary.total_queue_items == 0

    def test_evaluate_review_queue_ci_with_items(self):
        """Queue with items evaluates correctly."""
        items = [
            create_review_queue_item(review_reason="C", review_priority="critical"),
        ]
        summary = evaluate_review_queue_ci(items, [])
        assert summary.status == "warn"
        assert summary.critical_open_count == 1


# ─────────────────────────────────────────────────────────────────────────────
# Router endpoint tests
# ─────────────────────────────────────────────────────────────────────────────

class TestRouterEndpoints:
    """Tests for router endpoints."""

    def test_create_queue_item_endpoint(self):
        """POST /items creates queue item."""
        response = client.post(
            "/api/cam/review-queue/items",
            json={
                "review_reason": "API test item",
                "review_priority": "high",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "queue_item_id" in data

    def test_list_items_endpoint(self):
        """GET /items returns list."""
        client.post(
            "/api/cam/review-queue/items",
            json={"review_reason": "Test 1"},
        )
        client.post(
            "/api/cam/review-queue/items",
            json={"review_reason": "Test 2"},
        )

        response = client.get("/api/cam/review-queue/items")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    def test_get_item_endpoint(self):
        """GET /items/{id} returns item."""
        create_response = client.post(
            "/api/cam/review-queue/items",
            json={"review_reason": "Find me"},
        )
        queue_item_id = create_response.json()["queue_item_id"]

        response = client.get(f"/api/cam/review-queue/items/{queue_item_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["summary"]["review_reason"] == "Find me"

    def test_get_item_not_found(self):
        """GET /items/{id} returns 404 for missing."""
        response = client.get("/api/cam/review-queue/items/nonexistent")
        assert response.status_code == 404

    def test_create_decision_endpoint(self):
        """POST /decisions records decision."""
        create_response = client.post(
            "/api/cam/review-queue/items",
            json={"review_reason": "Decide on me"},
        )
        queue_item_id = create_response.json()["queue_item_id"]

        response = client.post(
            "/api/cam/review-queue/decisions",
            json={
                "queue_item_id": queue_item_id,
                "decision_type": "acknowledge",
                "decision_rationale": "Starting review",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["summary"]["decision_type"] == "acknowledge"
        assert data["summary"]["resulting_review_status"] == "in_review"

    def test_get_item_decisions_endpoint(self):
        """GET /items/{id}/decisions returns decisions."""
        create_response = client.post(
            "/api/cam/review-queue/items",
            json={"review_reason": "Multiple decisions"},
        )
        queue_item_id = create_response.json()["queue_item_id"]

        client.post(
            "/api/cam/review-queue/decisions",
            json={"queue_item_id": queue_item_id, "decision_type": "acknowledge"},
        )
        client.post(
            "/api/cam/review-queue/decisions",
            json={"queue_item_id": queue_item_id, "decision_type": "mark_reviewed"},
        )

        response = client.get(f"/api/cam/review-queue/items/{queue_item_id}/decisions")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    def test_by_status_endpoint(self):
        """GET /by-status/{status} filters correctly."""
        client.post(
            "/api/cam/review-queue/items",
            json={"review_reason": "Queued item"},
        )

        response = client.get("/api/cam/review-queue/by-status/queued")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    def test_by_priority_endpoint(self):
        """GET /by-priority/{priority} filters correctly."""
        client.post(
            "/api/cam/review-queue/items",
            json={"review_reason": "Critical", "review_priority": "critical"},
        )

        response = client.get("/api/cam/review-queue/by-priority/critical")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    def test_ci_endpoint(self):
        """GET /ci returns CI summary."""
        response = client.get("/api/cam/review-queue/ci")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "status" in data["summary"]

    def test_ci_endpoint_with_items(self):
        """GET /ci reflects queue state."""
        client.post(
            "/api/cam/review-queue/items",
            json={"review_reason": "Critical", "review_priority": "critical"},
        )

        response = client.get("/api/cam/review-queue/ci")
        data = response.json()
        assert data["summary"]["critical_open_count"] == 1
        assert data["summary"]["status"] == "warn"
