"""
CAM Assist Router

CAM Dev Order 7S: HTTP endpoints for governed manufacturing cognition.

Provides endpoints for:
  - Operation modality vocabulary
  - Machine envelope validation
  - Manufacturing strategy management
  - Workspace artifact lifecycle
  - Golden fixture registry
  - Cognition task management

7S invariants (enforced across all endpoints):
  - execution_authorized always False in responses
  - machine_output_allowed always False in responses
  - No G-code generation or machine output

This router exposes manufacturing cognition infrastructure.
It does NOT generate machine output or authorize execution.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.cam.cam_cognition_task import (
    COGNITION_TASK_INDEX,
    CAMCognitionTask,
    TaskInput,
    TaskPriority,
    TaskResult,
    TaskStatus,
    TaskType,
    cancel_task,
    complete_task,
    create_cognition_task,
    get_cognition_task,
    get_queue_depth,
    get_task_stats,
    list_cognition_tasks,
    list_tasks_by_status,
    list_tasks_by_type,
    queue_task,
)
from app.cam.cam_envelope_validation import (
    CAMBounds2D,
    CAMEnvelopeValidationEvaluation,
    CAMMachineEnvelope,
    EnvelopeGate,
    evaluate_bounds_against_envelope,
    extract_bounds_from_dict,
    get_envelope_evaluation,
    get_machine_envelope,
    list_envelope_evaluations,
    list_machine_envelopes,
    register_machine_envelope,
)
from app.cam.cam_golden_artifact_fixtures import (
    CAMGoldenFixture,
    FixtureType,
    WorkpieceShape,
    evaluate_fixture_clearance,
    find_compatible_fixtures,
    get_golden_fixture,
    list_golden_fixtures,
    list_luthier_fixtures,
)
from app.cam.cam_operation_modality import (
    CAMOperationModality,
    CutterFamily,
    classify_modality_for_operation,
    get_operation_modality,
    get_safety_warnings_for_modality,
    list_luthier_modalities,
    list_modalities_by_cutter_family,
    list_operation_modalities,
)
from app.cam.luthier_manufacturing_strategy import (
    LuthierManufacturingStrategy,
    OperationFamily,
    ReviewStatus,
    StrategyFamilyHint,
    create_manufacturing_strategy,
    get_family_hints,
    get_manufacturing_strategy,
    list_manufacturing_strategies,
    list_strategies_by_family,
    list_strategies_by_review_status,
    update_strategy_review_status,
)
from app.cam.luthier_operation_workspace import (
    GeometryReference,
    LuthierOperationWorkspaceV1,
    WorkspaceStatus,
    add_geometry_reference,
    archive_workspace,
    attach_strategy,
    bind_export_object,
    create_workspace,
    get_workspace,
    list_workspaces,
    list_workspaces_by_family,
    list_workspaces_by_status,
    promote_to_export_ready,
    serialize_workspace,
    validate_workspace,
)

router = APIRouter(
    prefix="/api/cam/assist",
    tags=["CAM", "Assist", "Cognition"],
)


class CAMAssistMeta(BaseModel):
    """Metadata for CAM Assist API."""

    version: str = "7S"
    execution_authorized: bool = False
    machine_output_allowed: bool = False
    description: str = "Governed manufacturing cognition — no execution"


@router.get("/", response_model=CAMAssistMeta)
async def get_cam_assist_meta() -> CAMAssistMeta:
    """Get CAM Assist API metadata."""
    return CAMAssistMeta()


# ============================================================================
# MODALITY ENDPOINTS
# ============================================================================


@router.get("/modalities", response_model=List[CAMOperationModality])
async def list_modalities() -> List[CAMOperationModality]:
    """List all registered operation modalities."""
    return list_operation_modalities()


@router.get("/modalities/{modality_id}", response_model=CAMOperationModality)
async def get_modality(modality_id: str) -> CAMOperationModality:
    """Get a specific modality by ID."""
    modality = get_operation_modality(modality_id)
    if not modality:
        raise HTTPException(404, f"Modality '{modality_id}' not found")
    return modality


@router.get("/modalities/family/{cutter_family}", response_model=List[CAMOperationModality])
async def get_modalities_by_family(cutter_family: CutterFamily) -> List[CAMOperationModality]:
    """List modalities by cutter family."""
    return list_modalities_by_cutter_family(cutter_family)


@router.get("/modalities/luthier", response_model=List[CAMOperationModality])
async def get_luthier_modalities() -> List[CAMOperationModality]:
    """List luthier-specific modalities."""
    return list_luthier_modalities()


class ClassifyModalityRequest(BaseModel):
    """Request to classify an operation to a modality."""

    operation_name: str = Field(..., description="Operation name to classify")
    hints: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional classification hints"
    )


class ClassifyModalityResponse(BaseModel):
    """Response from modality classification."""

    operation_name: str
    modality_id: Optional[str]
    modality: Optional[CAMOperationModality]
    safety_warnings: List[str]


@router.post("/modalities/classify", response_model=ClassifyModalityResponse)
async def classify_operation_modality(
    request: ClassifyModalityRequest,
) -> ClassifyModalityResponse:
    """Classify an operation name to a modality (best-effort heuristic)."""
    modality_id = classify_modality_for_operation(
        request.operation_name, request.hints
    )

    modality = get_operation_modality(modality_id) if modality_id else None
    warnings = get_safety_warnings_for_modality(modality_id) if modality_id else []

    return ClassifyModalityResponse(
        operation_name=request.operation_name,
        modality_id=modality_id,
        modality=modality,
        safety_warnings=warnings,
    )


# ============================================================================
# ENVELOPE VALIDATION ENDPOINTS
# ============================================================================


@router.get("/envelopes", response_model=List[CAMMachineEnvelope])
async def list_envelopes() -> List[CAMMachineEnvelope]:
    """List all registered machine envelopes."""
    return list_machine_envelopes()


@router.get("/envelopes/{machine_id}", response_model=CAMMachineEnvelope)
async def get_envelope(machine_id: str) -> CAMMachineEnvelope:
    """Get a specific machine envelope by ID."""
    envelope = get_machine_envelope(machine_id)
    if not envelope:
        raise HTTPException(404, f"Machine envelope '{machine_id}' not found")
    return envelope


class RegisterEnvelopeRequest(BaseModel):
    """Request to register a custom machine envelope."""

    machine_id: str
    display_name: str
    max_x_mm: float
    max_y_mm: float
    max_z_mm: Optional[float] = None
    margin_mm: float = 5.0
    description: str = ""


@router.post("/envelopes", response_model=CAMMachineEnvelope)
async def register_envelope(request: RegisterEnvelopeRequest) -> CAMMachineEnvelope:
    """Register a custom machine envelope."""
    envelope = CAMMachineEnvelope(
        machine_id=request.machine_id,
        display_name=request.display_name,
        max_x_mm=request.max_x_mm,
        max_y_mm=request.max_y_mm,
        max_z_mm=request.max_z_mm,
        margin_mm=request.margin_mm,
        description=request.description,
    )
    register_machine_envelope(envelope)
    return envelope


class EvaluateBoundsRequest(BaseModel):
    """Request to evaluate bounds against an envelope."""

    machine_id: str = Field(..., description="Machine envelope ID")
    bounds: Dict[str, float] = Field(
        ...,
        description="Bounds dict with min_x_mm, max_x_mm, min_y_mm, max_y_mm, optional min_z_mm, max_z_mm",
    )
    subject_id: str = Field(default="unknown", description="Subject identifier")


@router.post("/envelopes/evaluate", response_model=CAMEnvelopeValidationEvaluation)
async def evaluate_envelope(
    request: EvaluateBoundsRequest,
) -> CAMEnvelopeValidationEvaluation:
    """Evaluate bounds against a machine envelope."""
    envelope = get_machine_envelope(request.machine_id)
    if not envelope:
        raise HTTPException(404, f"Machine envelope '{request.machine_id}' not found")

    bounds = extract_bounds_from_dict(request.bounds)
    if not bounds:
        raise HTTPException(400, "Invalid bounds format")

    return evaluate_bounds_against_envelope(
        bounds=bounds,
        envelope=envelope,
        subject_id=request.subject_id,
    )


@router.get("/envelopes/evaluations", response_model=List[CAMEnvelopeValidationEvaluation])
async def list_evaluations() -> List[CAMEnvelopeValidationEvaluation]:
    """List all envelope evaluations."""
    return list_envelope_evaluations()


@router.get("/envelopes/evaluations/{evaluation_id}", response_model=CAMEnvelopeValidationEvaluation)
async def get_evaluation(evaluation_id: str) -> CAMEnvelopeValidationEvaluation:
    """Get a specific envelope evaluation by ID."""
    evaluation = get_envelope_evaluation(evaluation_id)
    if not evaluation:
        raise HTTPException(404, f"Evaluation '{evaluation_id}' not found")
    return evaluation


# ============================================================================
# STRATEGY ENDPOINTS
# ============================================================================


@router.get("/strategies", response_model=List[LuthierManufacturingStrategy])
async def list_strategies() -> List[LuthierManufacturingStrategy]:
    """List all manufacturing strategies."""
    return list_manufacturing_strategies()


@router.get("/strategies/{strategy_id}", response_model=LuthierManufacturingStrategy)
async def get_strategy(strategy_id: str) -> LuthierManufacturingStrategy:
    """Get a specific strategy by ID."""
    strategy = get_manufacturing_strategy(strategy_id)
    if not strategy:
        raise HTTPException(404, f"Strategy '{strategy_id}' not found")
    return strategy


@router.get("/strategies/family/{family}", response_model=List[LuthierManufacturingStrategy])
async def get_strategies_by_family(
    family: OperationFamily,
) -> List[LuthierManufacturingStrategy]:
    """List strategies by operation family."""
    return list_strategies_by_family(family)


@router.get("/strategies/review/{status}", response_model=List[LuthierManufacturingStrategy])
async def get_strategies_by_review(
    status: ReviewStatus,
) -> List[LuthierManufacturingStrategy]:
    """List strategies by review status."""
    return list_strategies_by_review_status(status)


class CreateStrategyRequest(BaseModel):
    """Request to create a manufacturing strategy."""

    operation_family: OperationFamily
    title: str
    description: str = ""
    modality_id: Optional[str] = None
    operation_sequence: Optional[List[str]] = None
    fixture_assumptions: Optional[List[str]] = None
    keepout_notes: Optional[List[str]] = None


@router.post("/strategies", response_model=LuthierManufacturingStrategy)
async def create_strategy(request: CreateStrategyRequest) -> LuthierManufacturingStrategy:
    """Create a new manufacturing strategy with hints from family."""
    return create_manufacturing_strategy(
        operation_family=request.operation_family,
        title=request.title,
        description=request.description,
        modality_id=request.modality_id,
        operation_sequence=request.operation_sequence,
        fixture_assumptions=request.fixture_assumptions,
        keepout_notes=request.keepout_notes,
    )


class UpdateReviewStatusRequest(BaseModel):
    """Request to update strategy review status."""

    review_status: ReviewStatus
    review_notes: Optional[str] = None


@router.patch("/strategies/{strategy_id}/review", response_model=LuthierManufacturingStrategy)
async def update_review(
    strategy_id: str,
    request: UpdateReviewStatusRequest,
) -> LuthierManufacturingStrategy:
    """Update strategy review status."""
    strategy = update_strategy_review_status(
        strategy_id=strategy_id,
        review_status=request.review_status,
        review_notes=request.review_notes,
    )
    if not strategy:
        raise HTTPException(404, f"Strategy '{strategy_id}' not found")
    return strategy


@router.get("/strategy-hints/{family}", response_model=StrategyFamilyHint)
async def get_strategy_hints(family: OperationFamily) -> StrategyFamilyHint:
    """Get strategy hints for an operation family."""
    hints = get_family_hints(family)
    if not hints:
        raise HTTPException(404, f"No hints for family '{family}'")
    return hints


# ============================================================================
# WORKSPACE ENDPOINTS
# ============================================================================


@router.get("/workspaces", response_model=List[LuthierOperationWorkspaceV1])
async def list_all_workspaces(
    family: Optional[OperationFamily] = None,
    status: Optional[WorkspaceStatus] = None,
) -> List[LuthierOperationWorkspaceV1]:
    """List workspaces with optional filters."""
    if family:
        return list_workspaces_by_family(family)
    if status:
        return list_workspaces_by_status(status)
    return list_workspaces()


@router.get("/workspaces/{workspace_id}", response_model=LuthierOperationWorkspaceV1)
async def get_workspace_by_id(workspace_id: str) -> LuthierOperationWorkspaceV1:
    """Get a specific workspace by ID."""
    workspace = get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(404, f"Workspace '{workspace_id}' not found")
    return workspace


class CreateWorkspaceRequest(BaseModel):
    """Request to create a workspace."""

    title: str
    operation_family: OperationFamily
    modality_id: Optional[str] = None
    description: str = ""
    tags: Optional[List[str]] = None


@router.post("/workspaces", response_model=LuthierOperationWorkspaceV1)
async def create_new_workspace(
    request: CreateWorkspaceRequest,
) -> LuthierOperationWorkspaceV1:
    """Create a new workspace artifact."""
    return create_workspace(
        title=request.title,
        operation_family=request.operation_family,
        modality_id=request.modality_id,
        description=request.description,
        tags=request.tags,
    )


class AddGeometryRequest(BaseModel):
    """Request to add geometry reference."""

    reference_type: str
    source_id: str
    layer_name: Optional[str] = None
    description: str = ""


@router.post("/workspaces/{workspace_id}/geometry", response_model=LuthierOperationWorkspaceV1)
async def add_geometry(
    workspace_id: str,
    request: AddGeometryRequest,
) -> LuthierOperationWorkspaceV1:
    """Add geometry reference to a workspace."""
    ref = GeometryReference(
        reference_type=request.reference_type,  # type: ignore
        source_id=request.source_id,
        layer_name=request.layer_name,
        description=request.description,
    )
    workspace = add_geometry_reference(workspace_id, ref)
    if not workspace:
        raise HTTPException(404, f"Workspace '{workspace_id}' not found")
    return workspace


@router.post("/workspaces/{workspace_id}/strategies/{strategy_id}", response_model=LuthierOperationWorkspaceV1)
async def attach_strategy_to_workspace(
    workspace_id: str,
    strategy_id: str,
) -> LuthierOperationWorkspaceV1:
    """Attach a strategy to a workspace."""
    workspace = attach_strategy(workspace_id, strategy_id)
    if not workspace:
        raise HTTPException(404, f"Workspace '{workspace_id}' not found")
    return workspace


@router.post("/workspaces/{workspace_id}/export-objects/{export_object_id}", response_model=LuthierOperationWorkspaceV1)
async def bind_export_object_to_workspace(
    workspace_id: str,
    export_object_id: str,
) -> LuthierOperationWorkspaceV1:
    """Bind an export object to a workspace."""
    workspace = bind_export_object(workspace_id, export_object_id)
    if not workspace:
        raise HTTPException(404, f"Workspace '{workspace_id}' not found")
    return workspace


@router.post("/workspaces/{workspace_id}/validate")
async def validate_workspace_endpoint(workspace_id: str) -> Dict[str, Any]:
    """Validate a workspace for completeness."""
    result = validate_workspace(workspace_id)
    if not result:
        raise HTTPException(404, f"Workspace '{workspace_id}' not found")
    return result.model_dump()


@router.post("/workspaces/{workspace_id}/promote", response_model=LuthierOperationWorkspaceV1)
async def promote_workspace(workspace_id: str) -> LuthierOperationWorkspaceV1:
    """Promote a validated workspace to export_ready status."""
    workspace = promote_to_export_ready(workspace_id)
    if not workspace:
        raise HTTPException(
            400,
            f"Workspace '{workspace_id}' not found or not in validated status",
        )
    return workspace


@router.post("/workspaces/{workspace_id}/archive", response_model=LuthierOperationWorkspaceV1)
async def archive_workspace_endpoint(workspace_id: str) -> LuthierOperationWorkspaceV1:
    """Archive a workspace."""
    workspace = archive_workspace(workspace_id)
    if not workspace:
        raise HTTPException(404, f"Workspace '{workspace_id}' not found")
    return workspace


@router.get("/workspaces/{workspace_id}/serialize")
async def serialize_workspace_endpoint(workspace_id: str) -> Dict[str, str]:
    """Serialize a workspace to JSON for local storage."""
    json_str = serialize_workspace(workspace_id)
    if not json_str:
        raise HTTPException(404, f"Workspace '{workspace_id}' not found")
    return {"workspace_id": workspace_id, "json": json_str}


# ============================================================================
# FIXTURE ENDPOINTS
# ============================================================================


@router.get("/fixtures", response_model=List[CAMGoldenFixture])
async def list_fixtures(
    fixture_type: Optional[FixtureType] = None,
    luthier_only: bool = False,
) -> List[CAMGoldenFixture]:
    """List golden fixtures with optional filters."""
    if luthier_only:
        return list_luthier_fixtures()
    if fixture_type:
        from app.cam.cam_golden_artifact_fixtures import list_fixtures_by_type
        return list_fixtures_by_type(fixture_type)
    return list_golden_fixtures()


@router.get("/fixtures/{fixture_id}", response_model=CAMGoldenFixture)
async def get_fixture(fixture_id: str) -> CAMGoldenFixture:
    """Get a specific golden fixture by ID."""
    fixture = get_golden_fixture(fixture_id)
    if not fixture:
        raise HTTPException(404, f"Fixture '{fixture_id}' not found")
    return fixture


class FindCompatibleFixturesRequest(BaseModel):
    """Request to find compatible fixtures."""

    workpiece_shape: WorkpieceShape
    thickness_mm: Optional[float] = None
    requires_flat_bottom: bool = False


@router.post("/fixtures/compatible", response_model=List[CAMGoldenFixture])
async def find_compatible(
    request: FindCompatibleFixturesRequest,
) -> List[CAMGoldenFixture]:
    """Find fixtures compatible with a workpiece."""
    return find_compatible_fixtures(
        workpiece_shape=request.workpiece_shape,
        thickness_mm=request.thickness_mm,
        requires_flat_bottom=request.requires_flat_bottom,
    )


class EvaluateClearanceRequest(BaseModel):
    """Request to evaluate tool path clearance."""

    fixture_id: str
    tool_path_points: List[List[float]]


@router.post("/fixtures/clearance")
async def evaluate_clearance(request: EvaluateClearanceRequest) -> Dict[str, Any]:
    """Evaluate tool path points against fixture clearance zones."""
    points = [(p[0], p[1]) for p in request.tool_path_points]
    return evaluate_fixture_clearance(request.fixture_id, points)


# ============================================================================
# COGNITION TASK ENDPOINTS
# ============================================================================


@router.get("/tasks", response_model=List[CAMCognitionTask])
async def list_tasks(
    status: Optional[TaskStatus] = None,
    task_type: Optional[TaskType] = None,
) -> List[CAMCognitionTask]:
    """List cognition tasks with optional filters."""
    if status:
        return list_tasks_by_status(status)
    if task_type:
        return list_tasks_by_type(task_type)
    return list_cognition_tasks()


@router.get("/tasks/stats")
async def get_stats() -> Dict[str, Any]:
    """Get task statistics."""
    return {
        "stats": get_task_stats(),
        "queue_depth": get_queue_depth(),
    }


@router.get("/tasks/{task_id}", response_model=CAMCognitionTask)
async def get_task(task_id: str) -> CAMCognitionTask:
    """Get a specific task by ID."""
    task = get_cognition_task(task_id)
    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")
    return task


class CreateTaskRequest(BaseModel):
    """Request to create a cognition task."""

    task_type: TaskType
    title: str
    input_type: str
    input_data: Dict[str, Any] = Field(default_factory=dict)
    source_ids: List[str] = Field(default_factory=list)
    priority: TaskPriority = "normal"
    workspace_id: Optional[str] = None
    depends_on: Optional[List[str]] = None
    description: str = ""
    tags: Optional[List[str]] = None


@router.post("/tasks", response_model=CAMCognitionTask)
async def create_task(request: CreateTaskRequest) -> CAMCognitionTask:
    """Create a new cognition task."""
    input_payload = TaskInput(
        input_type=request.input_type,
        data=request.input_data,
        source_ids=request.source_ids,
    )
    return create_cognition_task(
        task_type=request.task_type,
        title=request.title,
        input_payload=input_payload,
        priority=request.priority,
        workspace_id=request.workspace_id,
        depends_on=request.depends_on,
        description=request.description,
        tags=request.tags,
    )


@router.post("/tasks/{task_id}/queue", response_model=CAMCognitionTask)
async def queue_task_endpoint(task_id: str) -> CAMCognitionTask:
    """Queue a pending task for processing."""
    task = queue_task(task_id)
    if not task:
        raise HTTPException(
            400,
            f"Task '{task_id}' not found, not pending, or has unmet dependencies",
        )
    return task


@router.post("/tasks/{task_id}/cancel", response_model=CAMCognitionTask)
async def cancel_task_endpoint(task_id: str) -> CAMCognitionTask:
    """Cancel a pending or queued task."""
    task = cancel_task(task_id)
    if not task:
        raise HTTPException(
            400,
            f"Task '{task_id}' not found or not cancellable",
        )
    return task


class CompleteTaskRequest(BaseModel):
    """Request to complete a task with result."""

    result_type: str
    result_data: Dict[str, Any] = Field(default_factory=dict)
    output_artifact_ids: List[str] = Field(default_factory=list)
    summary: str = ""


@router.post("/tasks/{task_id}/complete", response_model=CAMCognitionTask)
async def complete_task_endpoint(
    task_id: str,
    request: CompleteTaskRequest,
) -> CAMCognitionTask:
    """Complete a running task with result (for testing/manual completion)."""
    result = TaskResult(
        result_type=request.result_type,
        data=request.result_data,
        output_artifact_ids=request.output_artifact_ids,
        summary=request.summary,
    )
    task = complete_task(task_id, result)
    if not task:
        raise HTTPException(
            400,
            f"Task '{task_id}' not found or not running",
        )
    return task
