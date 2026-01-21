"""
Unit tests for Ingest Audit Log.

Bundle 1 of Evidence QA Gate + Quarantine Workflow.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

# Set up test log path before importing
_test_log_dir = tempfile.mkdtemp(prefix="ingest_audit_test_")
os.environ["ACOUSTICS_INGEST_AUDIT_LOG"] = str(Path(_test_log_dir) / "test_ingest_audit.jsonl")

from app.rmos.acoustics.ingest_audit import (
    IngestAuditRecord,
    IngestOutcome,
    log_ingest_event,
    query_ingest_events,
    get_ingest_event,
    count_ingest_events,
    generate_event_id,
    compute_bundle_sha256,
    create_accepted_record,
    create_rejected_record,
    create_error_record,
    _get_audit_log_path,
)


@pytest.fixture(autouse=True)
def clean_audit_log():
    """Clean up the audit log before each test."""
    path = _get_audit_log_path()
    if path.exists():
        path.unlink()
    yield
    if path.exists():
        path.unlink()


class TestIngestAuditRecord:
    """Tests for IngestAuditRecord dataclass."""
    
    def test_to_dict_serializes_all_fields(self):
        record = IngestAuditRecord(
            event_id="test-123",
            timestamp="2025-01-01T00:00:00Z",
            outcome=IngestOutcome.ACCEPTED.value,
            session_id="session-1",
            run_id="run-abc",
        )
        d = record.to_dict()
        assert d["event_id"] == "test-123"
        assert d["timestamp"] == "2025-01-01T00:00:00Z"
        assert d["outcome"] == "accepted"
        assert d["session_id"] == "session-1"
        assert d["run_id"] == "run-abc"
        assert d["error_excerpt"] == []
    
    def test_to_dict_with_error_excerpt(self):
        record = IngestAuditRecord(
            event_id="test-456",
            timestamp="2025-01-01T00:00:00Z",
            outcome=IngestOutcome.REJECTED.value,
            error_excerpt=["Error 1", "Error 2"],
        )
        d = record.to_dict()
        assert d["error_excerpt"] == ["Error 1", "Error 2"]


class TestLogAndQuery:
    """Tests for log_ingest_event and query_ingest_events."""
    
    def test_log_and_query_single_event(self):
        record = create_accepted_record(
            event_id="evt-001",
            session_id="session-1",
            batch_label="batch-a",
            run_id="run-xyz",
        )
        log_ingest_event(record)
        
        events = query_ingest_events()
        assert len(events) == 1
        assert events[0]["event_id"] == "evt-001"
        assert events[0]["outcome"] == "accepted"
        assert events[0]["run_id"] == "run-xyz"
    
    def test_query_filter_by_outcome(self):
        # Log one accepted, one rejected
        log_ingest_event(create_accepted_record(
            event_id="evt-a1",
            run_id="run-1",
        ))
        log_ingest_event(create_rejected_record(
            event_id="evt-r1",
            rejection_reason="passed_false",
            rejection_message="Validation failed",
        ))
        
        accepted = query_ingest_events(outcome="accepted")
        assert len(accepted) == 1
        assert accepted[0]["event_id"] == "evt-a1"
        
        rejected = query_ingest_events(outcome="rejected")
        assert len(rejected) == 1
        assert rejected[0]["event_id"] == "evt-r1"
    
    def test_query_filter_by_session_id(self):
        log_ingest_event(create_accepted_record(
            event_id="evt-s1",
            session_id="session-A",
            run_id="run-1",
        ))
        log_ingest_event(create_accepted_record(
            event_id="evt-s2",
            session_id="session-B",
            run_id="run-2",
        ))
        
        results = query_ingest_events(session_id="session-A")
        assert len(results) == 1
        assert results[0]["event_id"] == "evt-s1"
    
    def test_query_with_limit_and_offset(self):
        for i in range(5):
            log_ingest_event(create_accepted_record(
                event_id=f"evt-{i:03d}",
                run_id=f"run-{i}",
            ))
        
        results = query_ingest_events(limit=2, offset=0)
        assert len(results) == 2
        
        results = query_ingest_events(limit=2, offset=3)
        assert len(results) == 2
    
    def test_get_single_event(self):
        log_ingest_event(create_accepted_record(
            event_id="evt-single",
            run_id="run-single",
            bundle_sha256="abc123",
        ))
        
        event = get_ingest_event("evt-single")
        assert event is not None
        assert event["bundle_sha256"] == "abc123"
        
        # Non-existent
        assert get_ingest_event("does-not-exist") is None


class TestCounts:
    """Tests for count_ingest_events."""
    
    def test_count_by_outcome(self):
        log_ingest_event(create_accepted_record(event_id="a1", run_id="r1"))
        log_ingest_event(create_accepted_record(event_id="a2", run_id="r2"))
        log_ingest_event(create_rejected_record(
            event_id="r1",
            rejection_reason="test",
            rejection_message="test",
        ))
        log_ingest_event(create_error_record(
            event_id="e1",
            rejection_reason="error",
            rejection_message="error",
        ))
        
        counts = count_ingest_events()
        assert counts["accepted"] == 2
        assert counts["rejected"] == 1
        assert counts["error"] == 1
        assert counts["quarantined"] == 0
        assert counts["total"] == 4


class TestHelpers:
    """Tests for helper functions."""
    
    def test_generate_event_id_is_unique(self):
        ids = [generate_event_id() for _ in range(100)]
        assert len(set(ids)) == 100  # All unique
    
    def test_compute_bundle_sha256(self):
        data = b"test bundle content"
        sha = compute_bundle_sha256(data)
        assert len(sha) == 64  # SHA256 hex is 64 chars
        # Deterministic
        assert compute_bundle_sha256(data) == sha


class TestRecordCreators:
    """Tests for convenience record creation functions."""
    
    def test_create_accepted_record(self):
        record = create_accepted_record(
            event_id="test-1",
            run_id="run-abc",
            attachments_written=5,
            attachments_deduped=2,
        )
        assert record.outcome == "accepted"
        assert record.run_id == "run-abc"
        assert record.attachments_written == 5
        assert record.timestamp  # Should be set
    
    def test_create_rejected_record(self):
        record = create_rejected_record(
            event_id="test-2",
            rejection_reason="passed_false",
            rejection_message="Validation failed",
            errors_count=3,
            error_excerpt=["err1", "err2"],
        )
        assert record.outcome == "rejected"
        assert record.rejection_reason == "passed_false"
        assert record.errors_count == 3
        assert len(record.error_excerpt) == 2
    
    def test_create_error_record(self):
        record = create_error_record(
            event_id="test-3",
            rejection_reason="unexpected_error",
            rejection_message="Something went wrong",
        )
        assert record.outcome == "error"
        assert record.rejection_reason == "unexpected_error"
