"""
Tests for CAM Lifecycle Audit Lineage (Dev Order 7R)

Test coverage:
  - cam_lifecycle_audit_ledger.py models and functions
  - lifecycle_lineage_engine.py verification and replay
  - lifecycle_audit_router.py HTTP endpoints

7R invariants verified:
  - execution_authorized always False
  - machine_output_allowed always False
  - immutable always True
  - Replay = verification, not re-execution
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch

from app.cam.cam_lifecycle_audit_ledger import (
    CAMLifecycleAuditLedgerEntry,
    AuditLedgerSummary,
    AuditCheckpointSummary,
    generate_lifecycle_audit_snapshot,
    register_audit_entry,
    get_audit_entry,
    list_audit_entries,
    clear_audit_indexes,
    LIFECYCLE_AUDIT_LEDGER_INDEX,
    LIFECYCLE_AUDIT_BY_EXPORT_INDEX,
)
from app.cam.lifecycle_lineage_engine import (
    LineageIntegrityStatus,
    ReplayContinuityStatus,
    build_lifecycle_audit_hash,
    verify_lifecycle_continuity,
    build_lifecycle_replay,
    reconstruct_ancestry,
    append_checkpoint_to_lifecycle,
    is_valid_lifecycle_transition,
    verify_checkpoint_continuity,
    generate_lineage_report,
)


@pytest.fixture(autouse=True)
def clear_indexes():
    """Clear indexes before each test."""
    clear_audit_indexes()
    yield
    clear_audit_indexes()


def create_test_entry(
    export_id: str = "test-export",
    lifecycle_gate: str = "green",
    parent_hashes: list = None,
    checkpoint_summary: AuditCheckpointSummary = None,
    continuity_valid: bool = True,
) -> CAMLifecycleAuditLedgerEntry:
    """Helper to create test entries with required fields."""
    entry = CAMLifecycleAuditLedgerEntry(
        export_id=export_id,
        lifecycle_gate=lifecycle_gate,
        parent_lifecycle_hashes=parent_hashes or [],
        checkpoint_summary=checkpoint_summary,
        continuity_integrity_valid=continuity_valid,
    )
    entry.deterministic_hash = entry.compute_deterministic_hash()
    return entry


class TestCAMLifecycleAuditLedgerEntry:
    """Tests for CAMLifecycleAuditLedgerEntry Pydantic model."""

    def test_entry_creation_basic(self):
        """Test basic entry creation with required fields."""
        entry = create_test_entry(export_id="basic-001", lifecycle_gate="green")
        assert entry.export_id == "basic-001"
        assert entry.lifecycle_gate == "green"
        assert entry.execution_authorized is False
        assert entry.machine_output_allowed is False
        assert entry.immutable is True

    def test_entry_rejects_execution_authorized_true(self):
        """7R invariant: execution_authorized=True must raise."""
        with pytest.raises(ValueError, match="execution_authorized must be False"):
            CAMLifecycleAuditLedgerEntry(
                export_id="inv-001",
                lifecycle_gate="green",
                execution_authorized=True,
            )

    def test_entry_rejects_machine_output_allowed_true(self):
        """7R invariant: machine_output_allowed=True must raise."""
        with pytest.raises(ValueError, match="machine_output_allowed must be False"):
            CAMLifecycleAuditLedgerEntry(
                export_id="inv-002",
                lifecycle_gate="green",
                machine_output_allowed=True,
            )

    def test_entry_rejects_immutable_false(self):
        """7R invariant: immutable=False must raise."""
        with pytest.raises(ValueError, match="immutable must be True"):
            CAMLifecycleAuditLedgerEntry(
                export_id="inv-003",
                lifecycle_gate="green",
                immutable=False,
            )

    def test_entry_with_parent_hashes(self):
        """Test entry with parent hash chain."""
        entry = create_test_entry(
            export_id="chain-001",
            parent_hashes=["parent_hash_1", "parent_hash_2"],
        )
        assert len(entry.parent_lifecycle_hashes) == 2
        assert "parent_hash_1" in entry.parent_lifecycle_hashes

    def test_entry_with_checkpoint_summary(self):
        """Test entry with checkpoint summary."""
        checkpoint = AuditCheckpointSummary(
            checkpoint_gate="yellow",
            checkpoint_passed=True,
            blocking_issues=[],
            warnings=["minor issue"],
            enforcement_hash="chk_hash",
            pathway="translator_dispatch:dxf_r12",
        )
        entry = create_test_entry(
            export_id="chk-001",
            checkpoint_summary=checkpoint,
        )
        assert entry.checkpoint_summary is not None
        assert entry.checkpoint_summary.checkpoint_gate == "yellow"

    def test_entry_red_checkpoint_requires_invalid_continuity(self):
        """7R invariant: RED checkpoint with valid continuity must raise."""
        checkpoint = AuditCheckpointSummary(
            checkpoint_gate="red",
            checkpoint_passed=False,
            blocking_issues=["blocked"],
            warnings=[],
            enforcement_hash="chk_hash",
            pathway="test",
        )
        with pytest.raises(ValueError, match="RED checkpoint requires"):
            CAMLifecycleAuditLedgerEntry(
                export_id="red-001",
                lifecycle_gate="red",
                checkpoint_summary=checkpoint,
                continuity_integrity_valid=True,
            )

    def test_entry_has_created_at(self):
        """Test entry has created_at timestamp."""
        entry = create_test_entry()
        assert entry.created_at is not None

    def test_entry_computes_deterministic_hash(self):
        """Test deterministic hash computation."""
        entry = create_test_entry()
        h = entry.compute_deterministic_hash()
        assert len(h) == 64


class TestGenerateLifecycleAuditSnapshot:
    """Tests for generate_lifecycle_audit_snapshot function."""

    def test_snapshot_basic(self):
        """Test basic snapshot generation."""
        mock_report = type("MockReport", (), {
            "gate": "GREEN",
            "lifecycle_gate": "green",
            "export_object_summary": type("MockSummary", (), {"export_id": "snap-001"})(),
            "blocking_issues": [],
            "warnings": [],
        })()
        mock_policy = type("MockPolicy", (), {"authorized": False})()
        mock_capability = type("MockCapability", (), {"operation": "translate"})()

        entry = generate_lifecycle_audit_snapshot(
            lifecycle_report=mock_report,
            policy_evaluation=mock_policy,
            operation_capability=mock_capability,
        )

        assert entry.export_id == "snap-001"
        assert entry.execution_authorized is False
        assert entry.machine_output_allowed is False
        assert entry.immutable is True

    def test_snapshot_registers_in_index(self):
        """Test snapshot is registered in ledger index."""
        mock_report = type("MockReport", (), {
            "lifecycle_gate": "green",
            "export_object_summary": type("MockSummary", (), {"export_id": "idx-001"})(),
            "blocking_issues": [],
            "warnings": [],
        })()
        mock_policy = type("MockPolicy", (), {})()
        mock_capability = type("MockCapability", (), {})()

        entry = generate_lifecycle_audit_snapshot(
            lifecycle_report=mock_report,
            policy_evaluation=mock_policy,
            operation_capability=mock_capability,
        )

        assert entry.ledger_entry_id in LIFECYCLE_AUDIT_LEDGER_INDEX


class TestBuildLifecycleAuditHash:
    """Tests for build_lifecycle_audit_hash function."""

    def test_hash_deterministic(self):
        """Test hash is deterministic for same inputs."""
        hash1 = build_lifecycle_audit_hash("report", "policy", "capability")
        hash2 = build_lifecycle_audit_hash("report", "policy", "capability")
        assert hash1 == hash2

    def test_hash_different_inputs(self):
        """Test different inputs produce different hashes."""
        hash1 = build_lifecycle_audit_hash("report_a", "policy", "capability")
        hash2 = build_lifecycle_audit_hash("report_b", "policy", "capability")
        assert hash1 != hash2

    def test_hash_with_checkpoint(self):
        """Test hash with checkpoint included."""
        hash1 = build_lifecycle_audit_hash("report", "policy", "capability")
        hash2 = build_lifecycle_audit_hash(
            "report", "policy", "capability",
            checkpoint_evaluation_hash="checkpoint"
        )
        assert hash1 != hash2

    def test_hash_with_parents(self):
        """Test hash with parent hashes."""
        hash1 = build_lifecycle_audit_hash("report", "policy", "capability")
        hash2 = build_lifecycle_audit_hash(
            "report", "policy", "capability",
            parent_hashes=["parent_1", "parent_2"]
        )
        assert hash1 != hash2

    def test_hash_length(self):
        """Test hash is SHA-256 (64 hex chars)."""
        h = build_lifecycle_audit_hash("report", "policy", "capability")
        assert len(h) == 64


class TestVerifyLifecycleContinuity:
    """Tests for verify_lifecycle_continuity function."""

    def test_verify_nonexistent_entry(self):
        """Test verification for non-existent entry."""
        result = verify_lifecycle_continuity("nonexistent_id")
        assert result.status == LineageIntegrityStatus.UNKNOWN
        assert result.parent_verified is False

    def test_verify_root_entry(self):
        """Test verification for root entry (no parents)."""
        entry = create_test_entry(export_id="root-001")
        LIFECYCLE_AUDIT_LEDGER_INDEX[entry.ledger_entry_id] = entry

        result = verify_lifecycle_continuity(entry.ledger_entry_id)
        assert result.status == LineageIntegrityStatus.VALID
        assert result.parent_verified is True
        assert result.chain_depth == 1

    def test_verify_entry_with_valid_parent(self):
        """Test verification with valid parent chain."""
        parent = create_test_entry(export_id="chain-parent")
        LIFECYCLE_AUDIT_LEDGER_INDEX[parent.ledger_entry_id] = parent

        child = create_test_entry(
            export_id="chain-child",
            parent_hashes=[parent.deterministic_hash],
        )
        LIFECYCLE_AUDIT_LEDGER_INDEX[child.ledger_entry_id] = child

        result = verify_lifecycle_continuity(child.ledger_entry_id)
        assert result.status == LineageIntegrityStatus.VALID
        assert result.parent_verified is True

    def test_verify_entry_with_missing_parent(self):
        """Test verification with missing parent."""
        entry = create_test_entry(
            export_id="orphan-001",
            parent_hashes=["missing_parent_hash"],
        )
        LIFECYCLE_AUDIT_LEDGER_INDEX[entry.ledger_entry_id] = entry

        result = verify_lifecycle_continuity(entry.ledger_entry_id)
        assert result.status == LineageIntegrityStatus.MISSING_PARENT
        assert result.parent_verified is False


class TestBuildLifecycleReplay:
    """Tests for build_lifecycle_replay function."""

    def test_replay_empty_export(self):
        """Test replay for export with no entries."""
        result = build_lifecycle_replay("nonexistent_export")
        assert result.status == ReplayContinuityStatus.INCOMPLETE
        assert result.entries_total == 0

    def test_replay_single_entry(self):
        """Test replay for export with single entry."""
        entry = create_test_entry(export_id="single-001")
        LIFECYCLE_AUDIT_LEDGER_INDEX[entry.ledger_entry_id] = entry

        result = build_lifecycle_replay("single-001")
        assert result.status == ReplayContinuityStatus.CONTINUOUS
        assert result.entries_total == 1
        assert entry.ledger_entry_id in result.timeline

    def test_replay_continuous_entries(self):
        """Test replay for continuous entries."""
        entry1 = create_test_entry(export_id="cont-export")
        entry1.created_at = datetime(2026, 5, 20, 10, 0, 0, tzinfo=timezone.utc)
        LIFECYCLE_AUDIT_LEDGER_INDEX[entry1.ledger_entry_id] = entry1

        entry2 = create_test_entry(
            export_id="cont-export",
            parent_hashes=[entry1.deterministic_hash],
        )
        entry2.created_at = datetime(2026, 5, 20, 10, 1, 0, tzinfo=timezone.utc)
        LIFECYCLE_AUDIT_LEDGER_INDEX[entry2.ledger_entry_id] = entry2

        result = build_lifecycle_replay("cont-export")
        assert result.status == ReplayContinuityStatus.CONTINUOUS
        assert result.entries_verified == 2

    def test_replay_with_gap(self):
        """Test replay for entries with gap."""
        entry1 = create_test_entry(export_id="gap-export")
        entry1.created_at = datetime(2026, 5, 20, 10, 0, 0, tzinfo=timezone.utc)
        LIFECYCLE_AUDIT_LEDGER_INDEX[entry1.ledger_entry_id] = entry1

        entry2 = create_test_entry(
            export_id="gap-export",
            parent_hashes=["wrong_parent"],
        )
        entry2.created_at = datetime(2026, 5, 20, 10, 1, 0, tzinfo=timezone.utc)
        LIFECYCLE_AUDIT_LEDGER_INDEX[entry2.ledger_entry_id] = entry2

        result = build_lifecycle_replay("gap-export")
        assert result.status == ReplayContinuityStatus.GAP_DETECTED
        assert len(result.gaps) > 0


class TestReconstructAncestry:
    """Tests for reconstruct_ancestry function."""

    def test_reconstruct_nonexistent(self):
        """Test reconstruction for non-existent entry."""
        result = reconstruct_ancestry("nonexistent")
        assert result.complete is False
        assert "nonexistent" in result.missing_links

    def test_reconstruct_root_entry(self):
        """Test reconstruction for root entry."""
        entry = create_test_entry(export_id="anc-root")
        LIFECYCLE_AUDIT_LEDGER_INDEX[entry.ledger_entry_id] = entry

        result = reconstruct_ancestry(entry.ledger_entry_id)
        assert result.complete is True
        assert result.chain_length == 1
        assert result.root_entry_id == entry.ledger_entry_id

    def test_reconstruct_chain(self):
        """Test reconstruction of ancestry chain."""
        grandparent = create_test_entry(export_id="anc-export")
        LIFECYCLE_AUDIT_LEDGER_INDEX[grandparent.ledger_entry_id] = grandparent

        parent = create_test_entry(
            export_id="anc-export",
            parent_hashes=[grandparent.deterministic_hash],
        )
        LIFECYCLE_AUDIT_LEDGER_INDEX[parent.ledger_entry_id] = parent

        child = create_test_entry(
            export_id="anc-export",
            parent_hashes=[parent.deterministic_hash],
        )
        LIFECYCLE_AUDIT_LEDGER_INDEX[child.ledger_entry_id] = child

        result = reconstruct_ancestry(child.ledger_entry_id)
        assert result.complete is True
        assert result.chain_length == 3
        assert result.root_entry_id == grandparent.ledger_entry_id


class TestAppendCheckpointToLifecycle:
    """Tests for append_checkpoint_to_lifecycle function."""

    def test_append_to_nonexistent(self):
        """Test append to non-existent entry."""
        result = append_checkpoint_to_lifecycle(
            "nonexistent",
            "translator_dispatch:dxf_r12",
            "green",
            "checkpoint_hash",
        )
        assert result is False

    def test_append_checkpoint(self):
        """Test appending checkpoint to entry."""
        entry = create_test_entry(export_id="append-001")
        LIFECYCLE_AUDIT_LEDGER_INDEX[entry.ledger_entry_id] = entry

        result = append_checkpoint_to_lifecycle(
            entry.ledger_entry_id,
            "translator_dispatch:dxf_r12",
            "green",
            "checkpoint_hash",
        )

        assert result is True
        new_entries = [e for e in LIFECYCLE_AUDIT_LEDGER_INDEX.values()
                      if e.checkpoint_summary is not None]
        assert len(new_entries) == 1


class TestIsValidLifecycleTransition:
    """Tests for is_valid_lifecycle_transition function."""

    def test_transition_source_not_found(self):
        """Test transition with missing source."""
        valid, reason = is_valid_lifecycle_transition("missing_from", "to_id")
        assert valid is False
        assert "not found" in reason

    def test_transition_target_not_found(self):
        """Test transition with missing target."""
        entry = create_test_entry(export_id="trans-from")
        LIFECYCLE_AUDIT_LEDGER_INDEX[entry.ledger_entry_id] = entry

        valid, reason = is_valid_lifecycle_transition(
            entry.ledger_entry_id, "missing_to"
        )
        assert valid is False
        assert "not found" in reason

    def test_valid_transition(self):
        """Test valid transition."""
        from_entry = create_test_entry(export_id="trans-export")
        from_entry.created_at = datetime(2026, 5, 20, 10, 0, 0, tzinfo=timezone.utc)
        LIFECYCLE_AUDIT_LEDGER_INDEX[from_entry.ledger_entry_id] = from_entry

        to_entry = create_test_entry(
            export_id="trans-export",
            parent_hashes=[from_entry.deterministic_hash],
        )
        to_entry.created_at = datetime(2026, 5, 20, 10, 1, 0, tzinfo=timezone.utc)
        LIFECYCLE_AUDIT_LEDGER_INDEX[to_entry.ledger_entry_id] = to_entry

        valid, reason = is_valid_lifecycle_transition(
            from_entry.ledger_entry_id, to_entry.ledger_entry_id
        )
        assert valid is True

    def test_invalid_transition_no_parent_ref(self):
        """Test invalid transition without parent reference."""
        from_entry = create_test_entry(export_id="inv-trans-export")
        from_entry.created_at = datetime(2026, 5, 20, 10, 0, 0, tzinfo=timezone.utc)
        LIFECYCLE_AUDIT_LEDGER_INDEX[from_entry.ledger_entry_id] = from_entry

        to_entry = create_test_entry(
            export_id="inv-trans-export",
            parent_hashes=["wrong_hash"],
        )
        to_entry.created_at = datetime(2026, 5, 20, 10, 1, 0, tzinfo=timezone.utc)
        LIFECYCLE_AUDIT_LEDGER_INDEX[to_entry.ledger_entry_id] = to_entry

        valid, reason = is_valid_lifecycle_transition(
            from_entry.ledger_entry_id, to_entry.ledger_entry_id
        )
        assert valid is False
        assert "does not reference" in reason


class TestVerifyCheckpointContinuity:
    """Tests for verify_checkpoint_continuity function."""

    def test_empty_ledger(self):
        """Test checkpoint continuity on empty ledger."""
        result = verify_checkpoint_continuity("translator_dispatch:dxf_r12")
        assert result.entries_with_checkpoint == 0
        assert result.entries_without_checkpoint == 0
        assert result.continuity_maintained is True

    def test_all_with_checkpoints(self):
        """Test continuity when all entries have checkpoints."""
        checkpoint = AuditCheckpointSummary(
            checkpoint_gate="green",
            checkpoint_passed=True,
            blocking_issues=[],
            warnings=[],
            enforcement_hash="chk",
            pathway="test",
        )
        entry1 = create_test_entry(export_id="chk-001", checkpoint_summary=checkpoint)
        entry2 = create_test_entry(export_id="chk-002", checkpoint_summary=checkpoint)
        LIFECYCLE_AUDIT_LEDGER_INDEX[entry1.ledger_entry_id] = entry1
        LIFECYCLE_AUDIT_LEDGER_INDEX[entry2.ledger_entry_id] = entry2

        result = verify_checkpoint_continuity("translator_dispatch:dxf_r12")
        assert result.entries_with_checkpoint == 2
        assert result.entries_without_checkpoint == 0
        assert result.continuity_maintained is True


class TestGenerateLineageReport:
    """Tests for generate_lineage_report function."""

    def test_report_empty_ledger(self):
        """Test report for empty ledger."""
        report = generate_lineage_report()
        assert report["total_entries"] == 0
        assert report["integrity_percentage"] == 100.0

    def test_report_with_entries(self):
        """Test report with ledger entries."""
        entry = create_test_entry(export_id="report-001")
        LIFECYCLE_AUDIT_LEDGER_INDEX[entry.ledger_entry_id] = entry

        report = generate_lineage_report()
        assert report["total_entries"] == 1
        assert report["valid_entries"] == 1
        assert "generated_at" in report


class TestLifecycleAuditRouter:
    """Tests for lifecycle_audit_router HTTP endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.routers.cam.lifecycle_audit_router import router

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    @pytest.mark.allow_missing_request_id
    def test_list_entries_empty(self, client):
        """Test listing entries on empty ledger."""
        response = client.get("/api/cam/lifecycle-audit/entries")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.allow_missing_request_id
    def test_list_entries_with_data(self, client):
        """Test listing entries with data."""
        entry = create_test_entry(export_id="api-001")
        LIFECYCLE_AUDIT_LEDGER_INDEX[entry.ledger_entry_id] = entry

        response = client.get("/api/cam/lifecycle-audit/entries")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["export_id"] == "api-001"

    @pytest.mark.allow_missing_request_id
    def test_get_entry_not_found(self, client):
        """Test getting non-existent entry."""
        response = client.get("/api/cam/lifecycle-audit/entries/nonexistent")
        assert response.status_code == 404

    @pytest.mark.allow_missing_request_id
    def test_get_entry_found(self, client):
        """Test getting existing entry."""
        entry = create_test_entry(export_id="get-001")
        LIFECYCLE_AUDIT_LEDGER_INDEX[entry.ledger_entry_id] = entry

        response = client.get(f"/api/cam/lifecycle-audit/entries/{entry.ledger_entry_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["export_id"] == "get-001"
        assert data["execution_authorized"] is False
        assert data["machine_output_allowed"] is False
        assert data["immutable"] is True

    @pytest.mark.allow_missing_request_id
    def test_verify_entry_lineage(self, client):
        """Test lineage verification endpoint."""
        entry = create_test_entry(export_id="verify-001")
        LIFECYCLE_AUDIT_LEDGER_INDEX[entry.ledger_entry_id] = entry

        response = client.get(f"/api/cam/lifecycle-audit/verify/{entry.ledger_entry_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "valid"
        assert data["parent_verified"] is True

    @pytest.mark.allow_missing_request_id
    def test_replay_export(self, client):
        """Test replay endpoint."""
        entry = create_test_entry(export_id="replay-001")
        LIFECYCLE_AUDIT_LEDGER_INDEX[entry.ledger_entry_id] = entry

        response = client.get("/api/cam/lifecycle-audit/replay/replay-001")
        assert response.status_code == 200
        data = response.json()
        assert data["export_id"] == "replay-001"
        assert data["status"] == "continuous"

    @pytest.mark.allow_missing_request_id
    def test_get_ancestry(self, client):
        """Test ancestry endpoint."""
        entry = create_test_entry(export_id="ancestry-001")
        LIFECYCLE_AUDIT_LEDGER_INDEX[entry.ledger_entry_id] = entry

        response = client.get(f"/api/cam/lifecycle-audit/ancestry/{entry.ledger_entry_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["entry_id"] == entry.ledger_entry_id
        assert data["complete"] is True

    @pytest.mark.allow_missing_request_id
    def test_validate_transition(self, client):
        """Test transition validation endpoint."""
        from_entry = create_test_entry(export_id="trans-001")
        from_entry.created_at = datetime(2026, 5, 20, 10, 0, 0, tzinfo=timezone.utc)
        LIFECYCLE_AUDIT_LEDGER_INDEX[from_entry.ledger_entry_id] = from_entry

        to_entry = create_test_entry(
            export_id="trans-001",
            parent_hashes=[from_entry.deterministic_hash],
        )
        to_entry.created_at = datetime(2026, 5, 20, 10, 1, 0, tzinfo=timezone.utc)
        LIFECYCLE_AUDIT_LEDGER_INDEX[to_entry.ledger_entry_id] = to_entry

        response = client.post(
            "/api/cam/lifecycle-audit/validate-transition",
            json={
                "from_entry_id": from_entry.ledger_entry_id,
                "to_entry_id": to_entry.ledger_entry_id,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True

    @pytest.mark.allow_missing_request_id
    def test_get_lineage_report(self, client):
        """Test lineage report endpoint."""
        response = client.get("/api/cam/lifecycle-audit/report")
        assert response.status_code == 200
        data = response.json()
        assert "total_entries" in data
        assert "integrity_percentage" in data

    @pytest.mark.allow_missing_request_id
    def test_get_audit_summary(self, client):
        """Test audit summary endpoint."""
        response = client.get("/api/cam/lifecycle-audit/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_entries" in data
        assert "integrity_verified" in data


class TestInvariantEnforcement:
    """Tests for 7R invariant enforcement."""

    def test_all_entries_have_execution_authorized_false(self):
        """Verify all created entries have execution_authorized=False."""
        for i in range(10):
            entry = create_test_entry(export_id=f"inv-exec-{i}")
            assert entry.execution_authorized is False

    def test_all_entries_have_machine_output_allowed_false(self):
        """Verify all created entries have machine_output_allowed=False."""
        for i in range(10):
            entry = create_test_entry(export_id=f"inv-machine-{i}")
            assert entry.machine_output_allowed is False

    def test_all_entries_have_immutable_true(self):
        """Verify all created entries have immutable=True."""
        for i in range(10):
            entry = create_test_entry(export_id=f"inv-immut-{i}")
            assert entry.immutable is True
