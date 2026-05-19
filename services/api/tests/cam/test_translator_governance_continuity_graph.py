"""
Tests for Translator Governance Continuity Graph (7L)

CAM Dev Order 7L: Governance review continuity replay infrastructure.

7L invariants:
  - replayable = true (always)
  - immutable = true (always)
  - execution_authorized = false (always)
  - machine_output_allowed = false (always)

Guardrail:
  7L continuity graph remains immutable replay infrastructure only.
  No mutation, approval, execution, serializer invocation,
  or machine-output semantics.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.main import app
from app.cam.translator_governance_continuity_graph import (
    TranslatorGovernanceContinuityGraph,
    GovernanceReplayResult,
    GovernanceContinuityGraphSummary,
    CONTINUITY_GRAPH_INDEX,
    build_governance_continuity_graph,
    build_continuity_graph_for_translator,
    register_continuity_graph,
    get_continuity_graph,
    list_continuity_graphs,
    list_continuity_graphs_for_translator,
    clear_continuity_graph_index,
    replay_governance_trace,
    get_continuity_chain,
    get_root_review_trace,
    validate_continuity_integrity,
    to_summary,
    ContinuityGraphBuildError,
    MixedTranslatorError,
    DuplicateContinuityGraphError,
    _compute_continuity_graph_id,
    _compute_deterministic_continuity_hash,
    _validate_continuity_integrity,
)
from app.cam.translator_governance_review_ledger import (
    TranslatorGovernanceReviewLedgerEntry,
    REVIEW_LEDGER_INDEX,
    clear_review_ledger_index,
    register_review_ledger_entry,
)


client = TestClient(app)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_indexes():
    """Clear both indexes before each test."""
    clear_continuity_graph_index()
    clear_review_ledger_index()
    yield
    clear_continuity_graph_index()
    clear_review_ledger_index()


def _create_ledger_entry(
    ledger_entry_id: str,
    translator_id: str = "body_outline_dxf_r12",
    review_trace_hash: str = None,
    parent_ledger_hashes: list = None,
    dossier_hash: str = "dossier_hash",
    provenance_hash: str = "provenance_hash",
    readiness_hash: str = "readiness_hash",
    quarantine_hash: str = "quarantine_hash",
    governance_constraints: list = None,
    review_state: str = "future_escalation_required",
    created_at: datetime = None,
) -> TranslatorGovernanceReviewLedgerEntry:
    """Create a ledger entry for testing."""
    if review_trace_hash is None:
        review_trace_hash = f"trace_{ledger_entry_id}"
    if parent_ledger_hashes is None:
        parent_ledger_hashes = []
    if governance_constraints is None:
        governance_constraints = ["no_dxf", "no_gcode"]
    if created_at is None:
        created_at = datetime.now(timezone.utc)

    return TranslatorGovernanceReviewLedgerEntry(
        ledger_entry_id=ledger_entry_id,
        review_matrix_id=f"matrix_{ledger_entry_id}",
        dossier_id=f"dossier_{ledger_entry_id}",
        translator_id=translator_id,
        review_gate="green",
        review_readiness_score=100,
        review_state=review_state,
        provenance_hash=provenance_hash,
        readiness_hash=readiness_hash,
        quarantine_hash=quarantine_hash,
        authorization_hash="auth_hash",
        dossier_hash=dossier_hash,
        review_matrix_hash="matrix_hash",
        parent_ledger_hashes=parent_ledger_hashes,
        governance_constraints=governance_constraints,
        review_trace_hash=review_trace_hash,
        created_at=created_at,
    )


def _create_entry_chain(
    translator_id: str = "body_outline_dxf_r12",
    count: int = 3,
) -> list[TranslatorGovernanceReviewLedgerEntry]:
    """Create a chain of ledger entries with proper parent linkage."""
    entries = []
    for i in range(count):
        parent_hashes = []
        if entries:
            parent_hashes = [entries[-1].review_trace_hash]

        entry = _create_ledger_entry(
            ledger_entry_id=f"entry-{i}",
            translator_id=translator_id,
            review_trace_hash=f"trace-{i}",
            parent_ledger_hashes=parent_hashes,
            dossier_hash=f"dossier-{i}",
            provenance_hash=f"prov-{i}",
            readiness_hash=f"read-{i}",
            quarantine_hash=f"quar-{i}",
            created_at=datetime(2026, 5, 15, 10, 0, i, tzinfo=timezone.utc),
        )
        entries.append(entry)
    return entries


# -----------------------------------------------------------------------------
# Test 7L Invariants
# -----------------------------------------------------------------------------

class TestContinuityGraphInvariants:
    """Test 7L model-enforced invariants."""

    def test_7l_invariant_replayable_always_true(self):
        """replayable must always be true."""
        entries = _create_entry_chain(count=2)
        graph = build_governance_continuity_graph(entries)
        assert graph.replayable is True

    def test_7l_invariant_immutable_always_true(self):
        """immutable must always be true."""
        entries = _create_entry_chain(count=2)
        graph = build_governance_continuity_graph(entries)
        assert graph.immutable is True

    def test_7l_invariant_execution_authorized_always_false(self):
        """execution_authorized must always be false."""
        entries = _create_entry_chain(count=2)
        graph = build_governance_continuity_graph(entries)
        assert graph.execution_authorized is False

    def test_7l_invariant_machine_output_always_false(self):
        """machine_output_allowed must always be false."""
        entries = _create_entry_chain(count=2)
        graph = build_governance_continuity_graph(entries)
        assert graph.machine_output_allowed is False

    def test_cannot_create_non_replayable_graph(self):
        """Creating a graph with replayable=false must fail."""
        with pytest.raises(ValueError, match="7L invariant violation"):
            TranslatorGovernanceContinuityGraph(
                continuity_graph_id="test-graph",
                translator_id="test_translator",
                root_review_trace_hash="root",
                current_review_trace_hash="current",
                continuity_integrity_valid=True,
                deterministic_continuity_hash="hash",
                chain_length=1,
                replayable=False,  # Must fail
            )

    def test_cannot_create_mutable_graph(self):
        """Creating a graph with immutable=false must fail."""
        with pytest.raises(ValueError, match="7L invariant violation"):
            TranslatorGovernanceContinuityGraph(
                continuity_graph_id="test-graph",
                translator_id="test_translator",
                root_review_trace_hash="root",
                current_review_trace_hash="current",
                continuity_integrity_valid=True,
                deterministic_continuity_hash="hash",
                chain_length=1,
                immutable=False,  # Must fail
            )

    def test_cannot_create_execution_authorized_graph(self):
        """Creating a graph with execution_authorized=true must fail."""
        with pytest.raises(ValueError, match="7L invariant violation"):
            TranslatorGovernanceContinuityGraph(
                continuity_graph_id="test-graph",
                translator_id="test_translator",
                root_review_trace_hash="root",
                current_review_trace_hash="current",
                continuity_integrity_valid=True,
                deterministic_continuity_hash="hash",
                chain_length=1,
                execution_authorized=True,  # Must fail
            )

    def test_cannot_create_machine_output_allowed_graph(self):
        """Creating a graph with machine_output_allowed=true must fail."""
        with pytest.raises(ValueError, match="7L invariant violation"):
            TranslatorGovernanceContinuityGraph(
                continuity_graph_id="test-graph",
                translator_id="test_translator",
                root_review_trace_hash="root",
                current_review_trace_hash="current",
                continuity_integrity_valid=True,
                deterministic_continuity_hash="hash",
                chain_length=1,
                machine_output_allowed=True,  # Must fail
            )


# -----------------------------------------------------------------------------
# Test Deterministic Hashing
# -----------------------------------------------------------------------------

class TestDeterministicHashing:
    """Test deterministic continuity hashing."""

    def test_same_lineage_produces_same_continuity_hash(self):
        """Same governance lineage produces same continuity hash."""
        entries = _create_entry_chain(count=3)
        graph1 = build_governance_continuity_graph(entries)
        graph2 = build_governance_continuity_graph(entries)

        assert graph1.deterministic_continuity_hash == graph2.deterministic_continuity_hash

    def test_changing_lineage_changes_hash(self):
        """Changing lineage changes continuity hash."""
        entries1 = _create_entry_chain(count=2)
        entries2 = _create_entry_chain(count=3)

        graph1 = build_governance_continuity_graph(entries1)
        graph2 = build_governance_continuity_graph(entries2)

        assert graph1.deterministic_continuity_hash != graph2.deterministic_continuity_hash

    def test_same_inputs_produce_same_graph_id(self):
        """Same translator + root + current produces same graph ID."""
        id1 = _compute_continuity_graph_id("trans-1", "root-hash", "current-hash")
        id2 = _compute_continuity_graph_id("trans-1", "root-hash", "current-hash")
        assert id1 == id2

    def test_different_inputs_produce_different_graph_id(self):
        """Different inputs produce different graph ID."""
        id1 = _compute_continuity_graph_id("trans-1", "root-1", "current-1")
        id2 = _compute_continuity_graph_id("trans-1", "root-2", "current-2")
        assert id1 != id2

    def test_graph_id_is_deterministic(self):
        """Graph ID is deterministic from inputs."""
        entries = _create_entry_chain(count=2)
        graph1 = build_governance_continuity_graph(entries)
        graph2 = build_governance_continuity_graph(entries)

        assert graph1.continuity_graph_id == graph2.continuity_graph_id

    def test_hash_is_sha256(self):
        """Continuity hash is valid SHA256."""
        entries = _create_entry_chain(count=2)
        graph = build_governance_continuity_graph(entries)

        assert len(graph.deterministic_continuity_hash) == 64
        assert all(c in "0123456789abcdef" for c in graph.deterministic_continuity_hash)


# -----------------------------------------------------------------------------
# Test Pure Builder
# -----------------------------------------------------------------------------

class TestContinuityGraphBuilder:
    """Test pure continuity graph builder."""

    def test_builder_creates_graph(self):
        """Builder creates continuity graph successfully."""
        entries = _create_entry_chain(count=3)
        graph = build_governance_continuity_graph(entries)

        assert graph.translator_id == "body_outline_dxf_r12"
        assert graph.chain_length == 3
        assert graph.replayable is True
        assert graph.immutable is True
        assert graph.execution_authorized is False
        assert graph.machine_output_allowed is False

    def test_builder_requires_entries(self):
        """Builder requires non-empty entries list."""
        with pytest.raises(ContinuityGraphBuildError, match="cannot be empty"):
            build_governance_continuity_graph([])

    def test_builder_rejects_mixed_translator_ids(self):
        """Builder rejects entries with mixed translator_ids."""
        entry1 = _create_ledger_entry("e1", translator_id="trans-A")
        entry2 = _create_ledger_entry("e2", translator_id="trans-B")

        with pytest.raises(MixedTranslatorError):
            build_governance_continuity_graph([entry1, entry2])

    def test_builder_preserves_hash_chain_order(self):
        """Builder preserves exact hash chain order."""
        entries = _create_entry_chain(count=3)
        graph = build_governance_continuity_graph(entries)

        assert len(graph.review_trace_chain) == 3
        assert len(graph.dossier_hash_chain) == 3
        assert len(graph.provenance_hash_chain) == 3
        assert len(graph.readiness_hash_chain) == 3
        assert len(graph.quarantine_hash_chain) == 3

        # Verify positional correlation
        for i in range(3):
            assert graph.review_trace_chain[i] == f"trace-{i}"
            assert graph.dossier_hash_chain[i] == f"dossier-{i}"
            assert graph.provenance_hash_chain[i] == f"prov-{i}"
            assert graph.readiness_hash_chain[i] == f"read-{i}"
            assert graph.quarantine_hash_chain[i] == f"quar-{i}"

    def test_builder_identifies_root_and_current(self):
        """Builder correctly identifies root and current trace hashes."""
        entries = _create_entry_chain(count=3)
        graph = build_governance_continuity_graph(entries)

        assert graph.root_review_trace_hash == "trace-0"
        assert graph.current_review_trace_hash == "trace-2"

    def test_builder_aggregates_governance_constraints(self):
        """Builder aggregates governance constraints from all entries."""
        entries = _create_entry_chain(count=2)
        graph = build_governance_continuity_graph(entries)

        assert "no_dxf" in graph.governance_constraints
        assert "no_gcode" in graph.governance_constraints


# -----------------------------------------------------------------------------
# Test Integrity Validation
# -----------------------------------------------------------------------------

class TestIntegrityValidation:
    """Test comprehensive integrity validation."""

    def test_valid_chain_passes_integrity(self):
        """Valid chain with proper linkage passes integrity."""
        entries = _create_entry_chain(count=3)
        graph = build_governance_continuity_graph(entries)

        assert graph.continuity_integrity_valid is True
        assert len(graph.integrity_violations) == 0

    def test_broken_parent_linkage_fails_integrity(self):
        """Broken parent linkage fails integrity."""
        entry0 = _create_ledger_entry(
            "e0", review_trace_hash="trace-0",
            created_at=datetime(2026, 5, 15, 10, 0, 0, tzinfo=timezone.utc),
        )
        entry1 = _create_ledger_entry(
            "e1", review_trace_hash="trace-1",
            parent_ledger_hashes=["wrong-parent"],  # Broken linkage
            created_at=datetime(2026, 5, 15, 10, 0, 1, tzinfo=timezone.utc),
        )

        graph = build_governance_continuity_graph([entry0, entry1])

        assert graph.continuity_integrity_valid is False
        assert any("broken parent linkage" in v for v in graph.integrity_violations)

    def test_duplicate_review_traces_fails_integrity(self):
        """Duplicate review traces in chain fails integrity."""
        entry0 = _create_ledger_entry(
            "e0", review_trace_hash="same-trace",
            created_at=datetime(2026, 5, 15, 10, 0, 0, tzinfo=timezone.utc),
        )
        entry1 = _create_ledger_entry(
            "e1", review_trace_hash="same-trace",  # Duplicate
            parent_ledger_hashes=["same-trace"],
            created_at=datetime(2026, 5, 15, 10, 0, 1, tzinfo=timezone.utc),
        )

        graph = build_governance_continuity_graph([entry0, entry1])

        assert graph.continuity_integrity_valid is False
        assert any("duplicate" in v for v in graph.integrity_violations)


# -----------------------------------------------------------------------------
# Test Replay Traversal
# -----------------------------------------------------------------------------

class TestReplayTraversal:
    """Test governance replay traversal."""

    def test_replay_returns_structured_result(self):
        """Replay returns GovernanceReplayResult."""
        entries = _create_entry_chain(count=3)
        graph = build_governance_continuity_graph(entries)

        result = replay_governance_trace(graph, entries)

        assert isinstance(result, GovernanceReplayResult)
        assert result.translator_id == graph.translator_id
        assert result.replay_length == 3
        assert result.execution_authorized is False
        assert result.machine_output_allowed is False

    def test_replay_chain_in_order(self):
        """Replay chain is in correct order (oldest to newest)."""
        entries = _create_entry_chain(count=3)
        graph = build_governance_continuity_graph(entries)

        result = replay_governance_trace(graph, entries)

        assert len(result.replay_chain) == 3
        assert result.replay_chain[0].review_trace_hash == "trace-0"
        assert result.replay_chain[2].review_trace_hash == "trace-2"

    def test_replay_includes_hashes(self):
        """Replay includes trace and continuity hashes."""
        entries = _create_entry_chain(count=2)
        graph = build_governance_continuity_graph(entries)

        result = replay_governance_trace(graph, entries)

        assert result.replay_trace_hash
        assert result.continuity_hash == graph.deterministic_continuity_hash
        assert result.root_review_trace_hash == graph.root_review_trace_hash
        assert result.current_review_trace_hash == graph.current_review_trace_hash

    def test_replay_validates_integrity(self):
        """Replay validates integrity."""
        entries = _create_entry_chain(count=2)
        graph = build_governance_continuity_graph(entries)

        result = replay_governance_trace(graph, entries)

        assert result.replay_integrity_valid == graph.continuity_integrity_valid

    def test_replay_invariants_enforced(self):
        """Replay result enforces 7L invariants."""
        entries = _create_entry_chain(count=2)
        graph = build_governance_continuity_graph(entries)

        result = replay_governance_trace(graph, entries)

        assert result.execution_authorized is False
        assert result.machine_output_allowed is False


# -----------------------------------------------------------------------------
# Test Index Operations
# -----------------------------------------------------------------------------

class TestIndexOperations:
    """Test in-memory index operations."""

    def test_register_and_get(self):
        """Register and retrieve a continuity graph."""
        entries = _create_entry_chain(count=2)
        graph = build_governance_continuity_graph(entries)
        register_continuity_graph(graph)

        retrieved = get_continuity_graph(graph.continuity_graph_id)
        assert retrieved is not None
        assert retrieved.continuity_graph_id == graph.continuity_graph_id

    def test_duplicate_registration_fails(self):
        """Registering duplicate graph ID fails."""
        entries = _create_entry_chain(count=2)
        graph = build_governance_continuity_graph(entries)
        register_continuity_graph(graph)

        with pytest.raises(DuplicateContinuityGraphError):
            register_continuity_graph(graph)

    def test_list_graphs(self):
        """List all continuity graphs."""
        entries1 = _create_entry_chain(translator_id="trans-1", count=2)
        entries2 = _create_entry_chain(translator_id="trans-2", count=2)

        graph1 = build_governance_continuity_graph(entries1)
        graph2 = build_governance_continuity_graph(entries2)
        register_continuity_graph(graph1)
        register_continuity_graph(graph2)

        graphs = list_continuity_graphs()
        assert len(graphs) == 2

    def test_list_by_translator(self):
        """List graphs for a specific translator."""
        entries1 = _create_entry_chain(translator_id="trans-A", count=2)
        entries2 = _create_entry_chain(translator_id="trans-B", count=2)

        graph1 = build_governance_continuity_graph(entries1)
        graph2 = build_governance_continuity_graph(entries2)
        register_continuity_graph(graph1)
        register_continuity_graph(graph2)

        graphs_a = list_continuity_graphs_for_translator("trans-A")
        graphs_b = list_continuity_graphs_for_translator("trans-B")

        assert len(graphs_a) == 1
        assert len(graphs_b) == 1
        assert graphs_a[0].translator_id == "trans-A"

    def test_clear_index(self):
        """Clear index removes all graphs."""
        entries = _create_entry_chain(count=2)
        graph = build_governance_continuity_graph(entries)
        register_continuity_graph(graph)

        assert len(list_continuity_graphs()) > 0
        clear_continuity_graph_index()
        assert len(list_continuity_graphs()) == 0


# -----------------------------------------------------------------------------
# Test Helper for Index Lookup
# -----------------------------------------------------------------------------

class TestIndexLookupHelper:
    """Test build_continuity_graph_for_translator helper."""

    def test_helper_builds_from_index(self):
        """Helper builds graph from ledger index."""
        entries = _create_entry_chain(count=3)
        for entry in entries:
            register_review_ledger_entry(entry)

        graph = build_continuity_graph_for_translator(
            "body_outline_dxf_r12",
            register=False,
        )

        assert graph.translator_id == "body_outline_dxf_r12"
        assert graph.chain_length == 3

    def test_helper_raises_for_no_entries(self):
        """Helper raises error if no entries found."""
        with pytest.raises(ContinuityGraphBuildError, match="No ledger entries"):
            build_continuity_graph_for_translator("nonexistent-translator")

    def test_helper_registers_when_requested(self):
        """Helper registers graph when register=True."""
        entries = _create_entry_chain(count=2)
        for entry in entries:
            register_review_ledger_entry(entry)

        graph = build_continuity_graph_for_translator(
            "body_outline_dxf_r12",
            register=True,
        )

        retrieved = get_continuity_graph(graph.continuity_graph_id)
        assert retrieved is not None


# -----------------------------------------------------------------------------
# Test Summary Model
# -----------------------------------------------------------------------------

class TestSummaryModel:
    """Test continuity graph summary model."""

    def test_to_summary_preserves_key_fields(self):
        """Summary preserves key fields."""
        entries = _create_entry_chain(count=2)
        graph = build_governance_continuity_graph(entries)
        summary = to_summary(graph)

        assert summary.continuity_graph_id == graph.continuity_graph_id
        assert summary.translator_id == graph.translator_id
        assert summary.chain_length == graph.chain_length
        assert summary.continuity_integrity_valid == graph.continuity_integrity_valid
        assert summary.deterministic_continuity_hash == graph.deterministic_continuity_hash

    def test_summary_enforces_invariants(self):
        """Summary enforces 7L invariants."""
        summary = GovernanceContinuityGraphSummary(
            continuity_graph_id="test-graph",
            translator_id="test_translator",
            root_review_trace_hash="root",
            current_review_trace_hash="current",
            chain_length=1,
            continuity_integrity_valid=True,
            deterministic_continuity_hash="hash",
            continuity_state="review_only",
            created_at=datetime.now(timezone.utc),
            replayable=False,  # Will be forced to True
            immutable=False,  # Will be forced to True
            execution_authorized=True,  # Will be forced to False
            machine_output_allowed=True,  # Will be forced to False
        )
        assert summary.replayable is True
        assert summary.immutable is True
        assert summary.execution_authorized is False
        assert summary.machine_output_allowed is False


# -----------------------------------------------------------------------------
# Test Endpoints
# -----------------------------------------------------------------------------

class TestEndpoints:
    """Test REST API endpoints."""

    def test_get_policy_endpoint(self):
        """GET /policy returns continuity policy."""
        response = client.get(
            "/api/cam/translators/governance-continuity/policy"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["replayable"] is True
        assert data["immutable"] is True
        assert data["execution_authorized"] is False
        assert data["machine_output_allowed"] is False
        assert data["per_translator_scope"] is True
        assert data["dev_order"] == "7L"

    def test_list_graphs_endpoint(self):
        """GET / returns list of graphs."""
        response = client.get(
            "/api/cam/translators/governance-continuity"
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_build_endpoint(self):
        """POST /build creates continuity graph."""
        entries = _create_entry_chain(count=2)
        for entry in entries:
            register_review_ledger_entry(entry)

        response = client.post(
            "/api/cam/translators/governance-continuity/build",
            json={"translator_id": "body_outline_dxf_r12"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["translator_id"] == "body_outline_dxf_r12"
        assert data["chain_length"] == 2
        assert data["replayable"] is True
        assert data["immutable"] is True
        assert data["execution_authorized"] is False
        assert data["machine_output_allowed"] is False

    def test_build_endpoint_no_entries_returns_400(self):
        """POST /build with no entries returns 400."""
        response = client.post(
            "/api/cam/translators/governance-continuity/build",
            json={"translator_id": "nonexistent-translator"}
        )
        assert response.status_code == 400

    def test_get_graph_endpoint(self):
        """GET /{id} returns graph."""
        entries = _create_entry_chain(count=2)
        graph = build_governance_continuity_graph(entries)
        register_continuity_graph(graph)

        response = client.get(
            f"/api/cam/translators/governance-continuity/{graph.continuity_graph_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["continuity_graph_id"] == graph.continuity_graph_id

    def test_get_graph_not_found(self):
        """GET /{id} returns 404 for unknown ID."""
        response = client.get(
            "/api/cam/translators/governance-continuity/unknown-graph-id"
        )
        assert response.status_code == 404

    def test_replay_endpoint(self):
        """GET /{id}/replay returns replay result."""
        entries = _create_entry_chain(count=3)
        for entry in entries:
            register_review_ledger_entry(entry)
        graph = build_governance_continuity_graph(entries)
        register_continuity_graph(graph)

        response = client.get(
            f"/api/cam/translators/governance-continuity/{graph.continuity_graph_id}/replay"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["translator_id"] == graph.translator_id
        assert data["replay_length"] == 3
        assert data["execution_authorized"] is False
        assert data["machine_output_allowed"] is False

    def test_by_translator_endpoint(self):
        """GET /by-translator/{id} returns graphs for translator."""
        entries = _create_entry_chain(translator_id="test-trans", count=2)
        graph = build_governance_continuity_graph(entries)
        register_continuity_graph(graph)

        response = client.get(
            "/api/cam/translators/governance-continuity/by-translator/test-trans"
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1


# -----------------------------------------------------------------------------
# Test Safety Assertions
# -----------------------------------------------------------------------------

class TestSafetyAssertions:
    """Test that 7L never produces execution artifacts."""

    def test_no_dxf_tokens_in_graph(self):
        """Graph contains no DXF generation tokens."""
        entries = _create_entry_chain(count=2)
        graph = build_governance_continuity_graph(entries)
        response_text = graph.model_dump_json()

        dxf_tokens = ["SECTION", "ENTITIES", "ENDSEC", "EOF", "LINE", "LWPOLYLINE"]
        for token in dxf_tokens:
            assert token not in response_text

    def test_no_gcode_tokens_in_graph(self):
        """Graph contains no G-code tokens."""
        entries = _create_entry_chain(count=2)
        graph = build_governance_continuity_graph(entries)
        response_text = graph.model_dump_json()

        gcode_tokens = ["G00", "G01", "G02", "G03", "M03", "M05", "M30"]
        for token in gcode_tokens:
            assert token not in response_text

    def test_no_dxf_tokens_in_replay(self):
        """Replay result contains no DXF generation tokens."""
        entries = _create_entry_chain(count=2)
        graph = build_governance_continuity_graph(entries)
        result = replay_governance_trace(graph, entries)
        response_text = result.model_dump_json()

        dxf_tokens = ["SECTION", "ENTITIES", "ENDSEC", "EOF", "LINE", "LWPOLYLINE"]
        for token in dxf_tokens:
            assert token not in response_text

    def test_all_endpoints_enforce_invariants(self):
        """All endpoint responses enforce invariants."""
        response = client.get(
            "/api/cam/translators/governance-continuity/policy"
        )
        data = response.json()
        assert data["replayable"] is True
        assert data["immutable"] is True
        assert data["execution_authorized"] is False
        assert data["machine_output_allowed"] is False
