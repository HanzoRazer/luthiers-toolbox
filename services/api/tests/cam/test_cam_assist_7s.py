"""
Tests for CAM Dev Order 7S: Governed Manufacturing Cognition Layer.

Tests cover:
  - Operation modality vocabulary (7S invariants)
  - Machine envelope validation (GREEN/YELLOW/RED gates)
  - Manufacturing strategy model
  - Workspace artifact lifecycle
  - Golden fixture registry
  - Cognition task model
  - CAM Assist router endpoints

All tests verify 7S invariants:
  - execution_authorized always False
  - machine_output_allowed always False
  - No G-code generation

Test count: 65+ tests
"""

import json
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.cam.cam_cognition_task import (
    COGNITION_TASK_INDEX,
    COGNITION_TASK_QUEUE,
    CAMCognitionTask,
    TaskError,
    TaskInput,
    TaskResult,
    cancel_task,
    clear_task_index,
    complete_task,
    create_cognition_task,
    fail_task,
    get_cognition_task,
    get_next_queued_task,
    get_queue_depth,
    get_task_stats,
    list_cognition_tasks,
    list_tasks_by_status,
    queue_task,
    retry_task,
    start_task,
)
from app.cam.cam_envelope_validation import (
    CAM_ENVELOPE_EVALUATION_INDEX,
    CAMBounds2D,
    CAMEnvelopeValidationEvaluation,
    CAMMachineEnvelope,
    clear_envelope_evaluation_index,
    evaluate_bounds_against_envelope,
    extract_bounds_from_dict,
    get_envelope_evaluation,
    get_machine_envelope,
    list_envelope_evaluations,
    list_machine_envelopes,
    register_machine_envelope,
)
from app.cam.cam_golden_artifact_fixtures import (
    GOLDEN_FIXTURE_INDEX,
    CAMGoldenFixture,
    ClearanceZone,
    FixtureCompatibilityHints,
    clear_fixture_index,
    evaluate_fixture_clearance,
    find_compatible_fixtures,
    get_golden_fixture,
    list_golden_fixtures,
    list_luthier_fixtures,
    register_custom_fixture,
)
from app.cam.cam_operation_modality import (
    CAM_OPERATION_MODALITY_INDEX,
    CAMOperationModality,
    classify_modality_for_operation,
    get_operation_modality,
    get_safety_warnings_for_modality,
    list_luthier_modalities,
    list_modalities_by_cutter_family,
    list_operation_modalities,
)
from app.cam.luthier_manufacturing_strategy import (
    LUTHIER_MANUFACTURING_STRATEGY_INDEX,
    LuthierManufacturingStrategy,
    clear_strategy_index,
    create_manufacturing_strategy,
    get_family_hints,
    get_manufacturing_strategy,
    list_manufacturing_strategies,
    list_strategies_by_family,
    list_strategies_by_review_status,
    update_strategy_review_status,
)
from app.cam.luthier_operation_workspace import (
    LUTHIER_WORKSPACE_INDEX,
    GeometryReference,
    LuthierOperationWorkspaceV1,
    WorkspaceValidationResult,
    add_geometry_reference,
    archive_workspace,
    attach_strategy,
    bind_export_object,
    clear_workspace_index,
    create_workspace,
    deserialize_workspace,
    get_workspace,
    list_workspaces,
    list_workspaces_by_family,
    list_workspaces_by_status,
    promote_to_export_ready,
    serialize_workspace,
    validate_workspace,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture(autouse=True)
def reset_indexes():
    """Reset all indexes before each test."""
    clear_envelope_evaluation_index()
    clear_strategy_index()
    clear_workspace_index()
    clear_task_index()
    yield


# ============================================================================
# OPERATION MODALITY TESTS
# ============================================================================


class TestCAMOperationModality:
    """Tests for operation modality vocabulary."""

    def test_modality_registry_seeded(self):
        """Registry has seeded modalities."""
        modalities = list_operation_modalities()
        assert len(modalities) >= 12
        assert any(m.modality_id == "router_profile" for m in modalities)
        assert any(m.modality_id == "laser_vector" for m in modalities)
        assert any(m.modality_id == "luthier_rosette_strategy" for m in modalities)

    def test_modality_7s_invariants_enforced(self):
        """7S invariants are enforced on modality models."""
        with pytest.raises(ValidationError) as exc:
            CAMOperationModality(
                modality_id="test_bad",
                display_name="Test Bad",
                cutter_family="router",
                executable_modality=True,
            )
        assert "executable_modality" in str(exc.value)

    def test_modality_machine_output_invariant(self):
        """machine_output_allowed invariant is enforced."""
        with pytest.raises(ValidationError) as exc:
            CAMOperationModality(
                modality_id="test_bad2",
                display_name="Test Bad 2",
                cutter_family="router",
                machine_output_allowed=True,
            )
        assert "machine_output_allowed" in str(exc.value)

    def test_get_modality_by_id(self):
        """Can retrieve modality by ID."""
        modality = get_operation_modality("router_profile")
        assert modality is not None
        assert modality.display_name == "Router Profile"
        assert modality.cutter_family == "router"

    def test_list_modalities_by_cutter_family(self):
        """Can filter modalities by cutter family."""
        laser = list_modalities_by_cutter_family("laser")
        assert len(laser) >= 2
        assert all(m.cutter_family == "laser" for m in laser)

    def test_list_luthier_modalities(self):
        """Can list luthier-specific modalities."""
        luthier = list_luthier_modalities()
        assert len(luthier) >= 5
        assert all(m.luthier_specific for m in luthier)

    def test_classify_modality_for_operation(self):
        """Can classify operation names to modalities."""
        modality_id = classify_modality_for_operation("rosette_channel")
        assert modality_id == "luthier_rosette_strategy"

        modality_id = classify_modality_for_operation("laser_cut")
        assert modality_id == "laser_vector"

    def test_classify_modality_returns_none_for_unknown(self):
        """Classification returns None for unknown operations."""
        modality_id = classify_modality_for_operation("unknown_operation_xyz")
        assert modality_id is None

    def test_get_safety_warnings(self):
        """Can get safety warnings for a modality."""
        warnings = get_safety_warnings_for_modality("router_profile")
        assert len(warnings) > 0
        assert any("cutter" in w.lower() for w in warnings)


# ============================================================================
# ENVELOPE VALIDATION TESTS
# ============================================================================


class TestCAMEnvelopeValidation:
    """Tests for envelope validation."""

    def test_envelope_registry_seeded(self):
        """Registry has seeded machine envelopes."""
        envelopes = list_machine_envelopes()
        assert len(envelopes) >= 5
        assert any(e.machine_id == "luthier_body_router" for e in envelopes)

    def test_get_machine_envelope(self):
        """Can get machine envelope by ID."""
        envelope = get_machine_envelope("generic_3018")
        assert envelope is not None
        assert envelope.max_x_mm == 300.0
        assert envelope.max_y_mm == 180.0

    def test_register_custom_envelope(self):
        """Can register custom machine envelope."""
        custom = CAMMachineEnvelope(
            machine_id="test_custom",
            display_name="Test Custom",
            max_x_mm=500.0,
            max_y_mm=300.0,
        )
        register_machine_envelope(custom)
        retrieved = get_machine_envelope("test_custom")
        assert retrieved is not None
        assert retrieved.max_x_mm == 500.0

    def test_evaluate_bounds_green_gate(self):
        """Bounds safely within envelope get GREEN gate."""
        envelope = get_machine_envelope("generic_6040")
        bounds = CAMBounds2D(
            min_x_mm=50.0,
            max_x_mm=300.0,
            min_y_mm=50.0,
            max_y_mm=200.0,
        )
        result = evaluate_bounds_against_envelope(bounds, envelope)
        assert result.gate == "green"
        assert len(result.blocking_issues) == 0

    def test_evaluate_bounds_yellow_gate(self):
        """Bounds near edges get YELLOW gate."""
        envelope = get_machine_envelope("generic_6040")
        bounds = CAMBounds2D(
            min_x_mm=2.0,
            max_x_mm=300.0,
            min_y_mm=50.0,
            max_y_mm=200.0,
        )
        result = evaluate_bounds_against_envelope(bounds, envelope)
        assert result.gate == "yellow"
        assert len(result.warnings) > 0

    def test_evaluate_bounds_red_gate(self):
        """Bounds exceeding envelope get RED gate."""
        envelope = get_machine_envelope("generic_3018")
        bounds = CAMBounds2D(
            min_x_mm=0.0,
            max_x_mm=500.0,
            min_y_mm=0.0,
            max_y_mm=200.0,
        )
        result = evaluate_bounds_against_envelope(bounds, envelope)
        assert result.gate == "red"
        assert len(result.blocking_issues) > 0

    def test_evaluation_7s_invariants(self):
        """Envelope evaluation enforces 7S invariants."""
        with pytest.raises(ValidationError) as exc:
            CAMEnvelopeValidationEvaluation(
                subject_id="test",
                gate="green",
                bounds_checked=CAMBounds2D(
                    min_x_mm=0, max_x_mm=100, min_y_mm=0, max_y_mm=100
                ),
                machine_envelope=get_machine_envelope("generic_3018"),
                execution_authorized=True,
            )
        assert "execution_authorized" in str(exc.value)

    def test_evaluation_stored_in_index(self):
        """Evaluations are stored in index."""
        envelope = get_machine_envelope("generic_3018")
        bounds = CAMBounds2D(
            min_x_mm=10.0,
            max_x_mm=100.0,
            min_y_mm=10.0,
            max_y_mm=100.0,
        )
        result = evaluate_bounds_against_envelope(bounds, envelope, subject_id="test_subject")
        retrieved = get_envelope_evaluation(result.evaluation_id)
        assert retrieved is not None
        assert retrieved.subject_id == "test_subject"

    def test_extract_bounds_from_dict(self):
        """Can extract bounds from dictionary."""
        data = {
            "min_x_mm": 10.0,
            "max_x_mm": 200.0,
            "min_y_mm": 20.0,
            "max_y_mm": 150.0,
        }
        bounds = extract_bounds_from_dict(data)
        assert bounds is not None
        assert bounds.width_mm == 190.0


# ============================================================================
# MANUFACTURING STRATEGY TESTS
# ============================================================================


class TestLuthierManufacturingStrategy:
    """Tests for manufacturing strategy model."""

    def test_create_strategy_with_hints(self):
        """Strategy creation applies family hints."""
        strategy = create_manufacturing_strategy(
            operation_family="rosette",
            title="Test Rosette Strategy",
        )
        assert strategy.operation_family == "rosette"
        assert len(strategy.operation_sequence) > 0
        assert len(strategy.keepout_notes) > 0

    def test_strategy_7s_invariants(self):
        """Strategy enforces 7S invariants."""
        with pytest.raises(ValidationError) as exc:
            LuthierManufacturingStrategy(
                operation_family="rosette",
                title="Bad Strategy",
                execution_authorized=True,
            )
        assert "execution_authorized" in str(exc.value)

    def test_strategy_gcode_invariant(self):
        """Strategy enforces no G-code generation."""
        with pytest.raises(ValidationError) as exc:
            LuthierManufacturingStrategy(
                operation_family="rosette",
                title="Bad Strategy",
                generates_gcode=True,
            )
        assert "generates_gcode" in str(exc.value)

    def test_strategy_stored_in_index(self):
        """Strategies are stored in index."""
        strategy = create_manufacturing_strategy(
            operation_family="binding_channel",
            title="Test Binding Strategy",
        )
        retrieved = get_manufacturing_strategy(strategy.strategy_id)
        assert retrieved is not None
        assert retrieved.display_name == "Test Binding Strategy"

    def test_list_strategies_by_family(self):
        """Can list strategies by family."""
        create_manufacturing_strategy("rosette", "Rosette 1")
        create_manufacturing_strategy("rosette", "Rosette 2")
        create_manufacturing_strategy("neck_profile", "Neck 1")

        rosette_strategies = list_strategies_by_family("rosette")
        assert len(rosette_strategies) == 2

    def test_update_review_status(self):
        """Can update strategy review status."""
        strategy = create_manufacturing_strategy("fret_slotting", "Fret Test")
        updated = update_strategy_review_status(
            strategy.strategy_id,
            review_status="approved_for_export_review",
            review_notes="Reviewed by test",
        )
        assert updated is not None
        assert updated.review_status == "approved_for_export_review"
        assert "Reviewed by test" in updated.review_notes

    def test_get_family_hints(self):
        """Can get hints for operation families."""
        hints = get_family_hints("soundhole")
        assert hints is not None
        assert len(hints.typical_sequence) > 0
        assert len(hints.common_keepouts) > 0


# ============================================================================
# WORKSPACE TESTS
# ============================================================================


class TestLuthierOperationWorkspace:
    """Tests for workspace artifact."""

    def test_create_workspace(self):
        """Can create workspace in draft status."""
        workspace = create_workspace(
            title="Test Workspace",
            operation_family="body_outline",
        )
        assert workspace.status == "draft"
        assert workspace.title == "Test Workspace"
        assert len(workspace.deterministic_hash) > 0

    def test_workspace_7s_invariants(self):
        """Workspace enforces 7S invariants."""
        with pytest.raises(ValidationError) as exc:
            LuthierOperationWorkspaceV1(
                title="Bad Workspace",
                operation_family="rosette",
                executable_payload_present=True,
            )
        assert "executable_payload_present" in str(exc.value)

    def test_workspace_gcode_invariant(self):
        """Workspace enforces no G-code storage."""
        with pytest.raises(ValidationError) as exc:
            LuthierOperationWorkspaceV1(
                title="Bad Workspace",
                operation_family="rosette",
                gcode_content="G0 X0 Y0",
            )
        assert "gcode_content" in str(exc.value)

    def test_add_geometry_reference(self):
        """Can add geometry reference to workspace."""
        workspace = create_workspace("Geo Test", "neck_profile")
        ref = GeometryReference(
            reference_type="export_object",
            source_id="exp-123",
            description="Test reference",
        )
        updated = add_geometry_reference(workspace.workspace_id, ref)
        assert updated is not None
        assert len(updated.geometry_references) == 1
        assert updated.status == "geometry_bound"

    def test_attach_strategy(self):
        """Can attach strategy to workspace."""
        workspace = create_workspace("Strategy Test", "rosette")
        strategy = create_manufacturing_strategy("rosette", "Test Strategy")

        ref = GeometryReference(
            reference_type="ibg_layer",
            source_id="ibg-layer-1",
        )
        add_geometry_reference(workspace.workspace_id, ref)
        updated = attach_strategy(workspace.workspace_id, strategy.strategy_id)

        assert updated is not None
        assert strategy.strategy_id in updated.strategy_ids
        assert updated.status == "strategy_attached"

    def test_workspace_validation(self):
        """Can validate workspace completeness."""
        workspace = create_workspace("Validate Test", "binding_channel")
        result = validate_workspace(workspace.workspace_id)
        assert result is not None
        assert result.valid is False
        assert "No geometry references" in result.issues[0]

    def test_workspace_promotion(self):
        """Can promote validated workspace to export_ready."""
        workspace = create_workspace("Promote Test", "fret_slotting")
        ref = GeometryReference(reference_type="contour", source_id="c-1")
        add_geometry_reference(workspace.workspace_id, ref)
        strategy = create_manufacturing_strategy("fret_slotting", "Fret Strat")
        attach_strategy(workspace.workspace_id, strategy.strategy_id)
        validate_workspace(workspace.workspace_id)

        promoted = promote_to_export_ready(workspace.workspace_id)
        assert promoted is not None
        assert promoted.status == "export_ready"

    def test_workspace_serialization(self):
        """Can serialize and deserialize workspace."""
        workspace = create_workspace("Serialize Test", "inspection")
        json_str = serialize_workspace(workspace.workspace_id)
        assert json_str is not None

        clear_workspace_index()

        restored = deserialize_workspace(json_str)
        assert restored.title == "Serialize Test"
        assert restored.operation_family == "inspection"

    def test_workspace_archive(self):
        """Can archive workspace."""
        workspace = create_workspace("Archive Test", "custom")
        archived = archive_workspace(workspace.workspace_id)
        assert archived is not None
        assert archived.status == "archived"


# ============================================================================
# GOLDEN FIXTURE TESTS
# ============================================================================


class TestCAMGoldenFixtures:
    """Tests for golden fixture registry."""

    def test_fixture_registry_seeded(self):
        """Registry has seeded fixtures."""
        fixtures = list_golden_fixtures()
        assert len(fixtures) >= 6
        assert any(f.fixture_id == "luthier_body_vacuum" for f in fixtures)

    def test_fixture_7s_invariants(self):
        """Fixture enforces 7S invariants."""
        with pytest.raises(ValidationError) as exc:
            CAMGoldenFixture(
                display_name="Bad Fixture",
                fixture_type="vacuum_table",
                execution_authorized=True,
            )
        assert "execution_authorized" in str(exc.value)

    def test_fixture_generates_motion_invariant(self):
        """Fixture enforces generates_motion invariant."""
        with pytest.raises(ValidationError) as exc:
            CAMGoldenFixture(
                display_name="Bad Fixture",
                fixture_type="vacuum_table",
                generates_motion=True,
            )
        assert "generates_motion" in str(exc.value)

    def test_get_fixture_by_id(self):
        """Can get fixture by ID."""
        fixture = get_golden_fixture("luthier_neck_side_clamp")
        assert fixture is not None
        assert fixture.fixture_type == "side_clamp"
        assert len(fixture.clearance_zones) > 0

    def test_list_luthier_fixtures(self):
        """Can list luthier-specific fixtures."""
        luthier = list_luthier_fixtures()
        assert len(luthier) >= 4
        assert all(f.luthier_specific for f in luthier)

    def test_find_compatible_fixtures(self):
        """Can find compatible fixtures for workpiece."""
        compatible = find_compatible_fixtures(
            workpiece_shape="neck_blank",
            thickness_mm=25.0,
        )
        assert len(compatible) > 0
        assert any(f.fixture_id == "luthier_neck_side_clamp" for f in compatible)

    def test_find_compatible_excludes_incompatible(self):
        """Compatible fixture search excludes incompatible shapes."""
        compatible = find_compatible_fixtures(
            workpiece_shape="body_blank",
            thickness_mm=50.0,
        )
        assert not any(f.fixture_id == "luthier_neck_side_clamp" for f in compatible)

    def test_evaluate_fixture_clearance(self):
        """Can evaluate tool path against fixture clearance."""
        points = [
            (50.0, 100.0),
            (75.0, 200.0),
            (-20.0, 100.0),
        ]
        result = evaluate_fixture_clearance("luthier_neck_side_clamp", points)
        assert result["fixture_found"]
        assert result["violations_found"] > 0

    def test_clearance_zone_contains_point(self):
        """Clearance zone correctly checks point containment."""
        zone = ClearanceZone(
            zone_type="clamp",
            min_x_mm=0.0,
            max_x_mm=10.0,
            min_y_mm=0.0,
            max_y_mm=10.0,
        )
        assert zone.contains_point(5.0, 5.0)
        assert not zone.contains_point(15.0, 5.0)


# ============================================================================
# COGNITION TASK TESTS
# ============================================================================


class TestCAMCognitionTask:
    """Tests for cognition task model."""

    def test_create_task(self):
        """Can create cognition task."""
        task = create_cognition_task(
            task_type="envelope_validation",
            title="Test Validation Task",
            input_payload=TaskInput(
                input_type="bounds",
                data={"min_x": 0, "max_x": 100},
            ),
        )
        assert task.status == "pending"
        assert task.task_type == "envelope_validation"

    def test_task_7s_invariants(self):
        """Task enforces 7S invariants."""
        with pytest.raises(ValidationError) as exc:
            CAMCognitionTask(
                task_type="strategy_selection",
                title="Bad Task",
                input_payload=TaskInput(input_type="test"),
                execution_authorized=True,
            )
        assert "execution_authorized" in str(exc.value)

    def test_task_gcode_invariant(self):
        """Task enforces generates_gcode invariant."""
        with pytest.raises(ValidationError) as exc:
            CAMCognitionTask(
                task_type="strategy_selection",
                title="Bad Task",
                input_payload=TaskInput(input_type="test"),
                generates_gcode=True,
            )
        assert "generates_gcode" in str(exc.value)

    def test_task_result_gcode_invariant(self):
        """Task result enforces no G-code."""
        with pytest.raises(ValidationError) as exc:
            TaskResult(
                result_type="test",
                contains_gcode=True,
            )
        assert "contains_gcode" in str(exc.value)

    def test_queue_task(self):
        """Can queue a pending task."""
        task = create_cognition_task(
            task_type="fixture_recommendation",
            title="Queue Test",
            input_payload=TaskInput(input_type="workpiece"),
        )
        queued = queue_task(task.task_id)
        assert queued is not None
        assert queued.status == "queued"
        assert task.task_id in COGNITION_TASK_QUEUE

    def test_queue_respects_priority(self):
        """Queue respects task priority."""
        t1 = create_cognition_task(
            task_type="envelope_validation",
            title="Normal",
            input_payload=TaskInput(input_type="bounds"),
            priority="normal",
        )
        queue_task(t1.task_id)

        t2 = create_cognition_task(
            task_type="envelope_validation",
            title="Critical",
            input_payload=TaskInput(input_type="bounds"),
            priority="critical",
        )
        queue_task(t2.task_id)

        assert COGNITION_TASK_QUEUE[0] == t2.task_id

    def test_task_lifecycle(self):
        """Task moves through lifecycle states."""
        task = create_cognition_task(
            task_type="clearance_analysis",
            title="Lifecycle Test",
            input_payload=TaskInput(input_type="fixture"),
        )
        assert task.status == "pending"

        queue_task(task.task_id)
        assert task.status == "queued"

        start_task(task.task_id)
        assert task.status == "running"

        result = TaskResult(result_type="clearance_ok", summary="All clear")
        complete_task(task.task_id, result)
        assert task.status == "completed"
        assert task.result is not None

    def test_task_failure_and_retry(self):
        """Can fail and retry tasks."""
        task = create_cognition_task(
            task_type="modality_classification",
            title="Fail Test",
            input_payload=TaskInput(input_type="operation"),
        )
        queue_task(task.task_id)
        start_task(task.task_id)

        error = TaskError(error_code="TEST_ERROR", error_message="Test failure")
        fail_task(task.task_id, error)
        assert task.status == "failed"

        retried = retry_task(task.task_id)
        assert retried is not None
        assert retried.status == "pending"
        assert retried.retry_count == 1

    def test_cancel_task(self):
        """Can cancel pending/queued tasks."""
        task = create_cognition_task(
            task_type="workspace_validation",
            title="Cancel Test",
            input_payload=TaskInput(input_type="workspace"),
        )
        cancelled = cancel_task(task.task_id)
        assert cancelled is not None
        assert cancelled.status == "cancelled"

    def test_task_dependencies(self):
        """Tasks respect dependencies."""
        t1 = create_cognition_task(
            task_type="envelope_validation",
            title="First",
            input_payload=TaskInput(input_type="bounds"),
        )
        t2 = create_cognition_task(
            task_type="strategy_selection",
            title="Second",
            input_payload=TaskInput(input_type="envelope_result"),
            depends_on=[t1.task_id],
        )

        queued = queue_task(t2.task_id)
        assert queued is None

        queue_task(t1.task_id)
        start_task(t1.task_id)
        complete_task(t1.task_id, TaskResult(result_type="done"))

        t2_updated = get_cognition_task(t2.task_id)
        assert t2_updated.status == "pending"

    def test_get_task_stats(self):
        """Can get task statistics."""
        create_cognition_task("envelope_validation", "T1", TaskInput(input_type="a"))
        create_cognition_task("envelope_validation", "T2", TaskInput(input_type="b"))

        stats = get_task_stats()
        assert stats["pending"] == 2
        assert stats["completed"] == 0


# ============================================================================
# ROUTER TESTS
# ============================================================================


class TestCAMAssistRouter:
    """Tests for CAM Assist HTTP router."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        try:
            from app.main import app
            return TestClient(app)
        except ModuleNotFoundError:
            pytest.skip("app.main has missing dependencies")

    def test_get_meta(self, client):
        """GET /api/cam/assist/ returns metadata."""
        response = client.get("/api/cam/assist/")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "7S"
        assert data["execution_authorized"] is False
        assert data["machine_output_allowed"] is False

    def test_list_modalities(self, client):
        """GET /api/cam/assist/modalities returns modalities."""
        response = client.get("/api/cam/assist/modalities")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 12

    def test_get_modality(self, client):
        """GET /api/cam/assist/modalities/{id} returns specific modality."""
        response = client.get("/api/cam/assist/modalities/router_profile")
        assert response.status_code == 200
        data = response.json()
        assert data["modality_id"] == "router_profile"

    def test_list_envelopes(self, client):
        """GET /api/cam/assist/envelopes returns envelopes."""
        response = client.get("/api/cam/assist/envelopes")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 5

    def test_evaluate_envelope(self, client):
        """POST /api/cam/assist/envelopes/evaluate validates bounds."""
        response = client.post(
            "/api/cam/assist/envelopes/evaluate",
            json={
                "machine_id": "generic_3018",
                "bounds": {
                    "min_x_mm": 10.0,
                    "max_x_mm": 100.0,
                    "min_y_mm": 10.0,
                    "max_y_mm": 100.0,
                },
                "subject_id": "test",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["gate"] == "green"

    def test_create_strategy(self, client):
        """POST /api/cam/assist/strategies creates strategy."""
        response = client.post(
            "/api/cam/assist/strategies",
            json={
                "operation_family": "rosette",
                "title": "API Test Rosette",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["operation_family"] == "rosette"
        assert len(data["operation_sequence"]) > 0

    def test_create_workspace(self, client):
        """POST /api/cam/assist/workspaces creates workspace."""
        response = client.post(
            "/api/cam/assist/workspaces",
            json={
                "title": "API Test Workspace",
                "operation_family": "body_outline",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "draft"

    def test_list_fixtures(self, client):
        """GET /api/cam/assist/fixtures returns fixtures."""
        response = client.get("/api/cam/assist/fixtures")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 6

    def test_find_compatible_fixtures(self, client):
        """POST /api/cam/assist/fixtures/compatible finds compatible fixtures."""
        response = client.post(
            "/api/cam/assist/fixtures/compatible",
            json={
                "workpiece_shape": "fretboard_blank",
                "thickness_mm": 8.0,
                "requires_flat_bottom": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

    def test_create_task(self, client):
        """POST /api/cam/assist/tasks creates task."""
        response = client.post(
            "/api/cam/assist/tasks",
            json={
                "task_type": "envelope_validation",
                "title": "API Test Task",
                "input_type": "bounds",
                "input_data": {"test": True},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert data["execution_authorized"] is False

    def test_task_stats(self, client):
        """GET /api/cam/assist/tasks/stats returns statistics."""
        response = client.get("/api/cam/assist/tasks/stats")
        assert response.status_code == 200
        data = response.json()
        assert "stats" in data
        assert "queue_depth" in data
