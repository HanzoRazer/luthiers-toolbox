"""
CAM Assist Router

CAM Dev Order 7S: HTTP endpoints for governed manufacturing cognition.

7S invariants:
  - execution_authorized always False
  - machine_output_allowed always False
  - No G-code generation
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.cam.cam_cognition_task import (
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

router = APIRouter(prefix="/api/cam/assist", tags=["CAM", "Assist", "Cognition"])


class CAMAssistMeta(BaseModel):
    version: str = "7S"
    execution_authorized: bool = False
    machine_output_allowed: bool = False
    description: str = "Governed manufacturing cognition — no execution"


@router.get("/", response_model=CAMAssistMeta)
async def get_meta() -> CAMAssistMeta:
    return CAMAssistMeta()


# Modality endpoints
@router.get("/modalities", response_model=List[CAMOperationModality])
async def list_modalities():
    return list_operation_modalities()


@router.get("/modalities/{modality_id}", response_model=CAMOperationModality)
async def get_modality(modality_id: str):
    m = get_operation_modality(modality_id)
    if not m:
        raise HTTPException(404, f"Modality '{modality_id}' not found")
    return m


@router.get("/modalities/family/{cutter_family}", response_model=List[CAMOperationModality])
async def get_modalities_by_family(cutter_family: CutterFamily):
    return list_modalities_by_cutter_family(cutter_family)


@router.get("/modalities/luthier", response_model=List[CAMOperationModality])
async def get_luthier_modalities():
    return list_luthier_modalities()


# Envelope endpoints
@router.get("/envelopes", response_model=List[CAMMachineEnvelope])
async def list_envelopes():
    return list_machine_envelopes()


@router.get("/envelopes/{machine_id}", response_model=CAMMachineEnvelope)
async def get_envelope(machine_id: str):
    e = get_machine_envelope(machine_id)
    if not e:
        raise HTTPException(404, f"Envelope '{machine_id}' not found")
    return e


class EvaluateBoundsRequest(BaseModel):
    machine_id: str
    bounds: Dict[str, float]
    subject_id: str = "unknown"


@router.post("/envelopes/evaluate", response_model=CAMEnvelopeValidationEvaluation)
async def evaluate_envelope(request: EvaluateBoundsRequest):
    envelope = get_machine_envelope(request.machine_id)
    if not envelope:
        raise HTTPException(404, f"Envelope '{request.machine_id}' not found")
    bounds = extract_bounds_from_dict(request.bounds)
    if not bounds:
        raise HTTPException(400, "Invalid bounds format")
    return evaluate_bounds_against_envelope(bounds, envelope, request.subject_id)


# Strategy endpoints
@router.get("/strategies", response_model=List[LuthierManufacturingStrategy])
async def list_strategies():
    return list_manufacturing_strategies()


@router.get("/strategies/{strategy_id}", response_model=LuthierManufacturingStrategy)
async def get_strategy(strategy_id: str):
    s = get_manufacturing_strategy(strategy_id)
    if not s:
        raise HTTPException(404, f"Strategy '{strategy_id}' not found")
    return s


class CreateStrategyRequest(BaseModel):
    operation_family: OperationFamily
    title: str
    description: str = ""
    modality_id: Optional[str] = None
    operation_sequence: Optional[List[str]] = None
    fixture_assumptions: Optional[List[str]] = None
    keepout_notes: Optional[List[str]] = None


@router.post("/strategies", response_model=LuthierManufacturingStrategy)
async def create_strategy(request: CreateStrategyRequest):
    return create_manufacturing_strategy(
        operation_family=request.operation_family,
        title=request.title,
        description=request.description,
        modality_id=request.modality_id or "",
        operation_sequence=request.operation_sequence,
        fixture_assumptions=request.fixture_assumptions,
        keepout_notes=request.keepout_notes,
    )


@router.get("/strategy-hints/{family}", response_model=StrategyFamilyHint)
async def get_strategy_hints(family: OperationFamily):
    hints = get_family_hints(family)
    if not hints:
        raise HTTPException(404, f"No hints for family '{family}'")
    return hints


# Workspace endpoints
@router.get("/workspaces", response_model=List[LuthierOperationWorkspaceV1])
async def list_all_workspaces(family: Optional[OperationFamily] = None, status: Optional[WorkspaceStatus] = None):
    if family:
        return list_workspaces_by_family(family)
    if status:
        return list_workspaces_by_status(status)
    return list_workspaces()


@router.get("/workspaces/{workspace_id}", response_model=LuthierOperationWorkspaceV1)
async def get_workspace_by_id(workspace_id: str):
    ws = get_workspace(workspace_id)
    if not ws:
        raise HTTPException(404, f"Workspace '{workspace_id}' not found")
    return ws


class CreateWorkspaceRequest(BaseModel):
    title: str
    operation_family: OperationFamily
    modality_id: Optional[str] = None
    description: str = ""
    tags: Optional[List[str]] = None


@router.post("/workspaces", response_model=LuthierOperationWorkspaceV1)
async def create_new_workspace(request: CreateWorkspaceRequest):
    return create_workspace(
        title=request.title,
        operation_family=request.operation_family,
        modality_id=request.modality_id,
        description=request.description,
        tags=request.tags,
    )


class AddGeometryRequest(BaseModel):
    reference_type: str
    source_id: str
    layer_name: Optional[str] = None
    description: str = ""


@router.post("/workspaces/{workspace_id}/geometry", response_model=LuthierOperationWorkspaceV1)
async def add_geometry(workspace_id: str, request: AddGeometryRequest):
    ref = GeometryReference(reference_type=request.reference_type, source_id=request.source_id, layer_name=request.layer_name, description=request.description)  # type: ignore
    ws = add_geometry_reference(workspace_id, ref)
    if not ws:
        raise HTTPException(404, f"Workspace '{workspace_id}' not found")
    return ws


@router.post("/workspaces/{workspace_id}/strategies/{strategy_id}", response_model=LuthierOperationWorkspaceV1)
async def attach_strategy_to_workspace(workspace_id: str, strategy_id: str):
    ws = attach_strategy(workspace_id, strategy_id)
    if not ws:
        raise HTTPException(404, f"Workspace '{workspace_id}' not found")
    return ws


@router.post("/workspaces/{workspace_id}/validate")
async def validate_workspace_endpoint(workspace_id: str):
    result = validate_workspace(workspace_id)
    if not result:
        raise HTTPException(404, f"Workspace '{workspace_id}' not found")
    return result.model_dump()


@router.post("/workspaces/{workspace_id}/promote", response_model=LuthierOperationWorkspaceV1)
async def promote_workspace(workspace_id: str):
    ws = promote_to_export_ready(workspace_id)
    if not ws:
        raise HTTPException(400, f"Workspace '{workspace_id}' not found or not validated")
    return ws


@router.post("/workspaces/{workspace_id}/archive", response_model=LuthierOperationWorkspaceV1)
async def archive_workspace_endpoint(workspace_id: str):
    ws = archive_workspace(workspace_id)
    if not ws:
        raise HTTPException(404, f"Workspace '{workspace_id}' not found")
    return ws


# Fixture endpoints
@router.get("/fixtures", response_model=List[CAMGoldenFixture])
async def list_fixtures(fixture_type: Optional[FixtureType] = None, luthier_only: bool = False):
    if luthier_only:
        return list_luthier_fixtures()
    return list_golden_fixtures()


@router.get("/fixtures/{fixture_id}", response_model=CAMGoldenFixture)
async def get_fixture(fixture_id: str):
    f = get_golden_fixture(fixture_id)
    if not f:
        raise HTTPException(404, f"Fixture '{fixture_id}' not found")
    return f


class FindCompatibleFixturesRequest(BaseModel):
    workpiece_shape: WorkpieceShape
    thickness_mm: Optional[float] = None
    requires_flat_bottom: bool = False


@router.post("/fixtures/compatible", response_model=List[CAMGoldenFixture])
async def find_compatible(request: FindCompatibleFixturesRequest):
    return find_compatible_fixtures(request.workpiece_shape, request.thickness_mm, request.requires_flat_bottom)


class EvaluateClearanceRequest(BaseModel):
    fixture_id: str
    tool_path_points: List[List[float]]


@router.post("/fixtures/clearance")
async def evaluate_clearance(request: EvaluateClearanceRequest):
    points = [(p[0], p[1]) for p in request.tool_path_points]
    return evaluate_fixture_clearance(request.fixture_id, points)


# Task endpoints
@router.get("/tasks")
async def list_tasks(status: Optional[TaskStatus] = None, task_type: Optional[TaskType] = None):
    if status:
        return list_tasks_by_status(status)
    if task_type:
        return list_tasks_by_type(task_type)
    return list_cognition_tasks()


@router.get("/tasks/stats")
async def get_stats():
    return {"stats": get_task_stats(), "queue_depth": get_queue_depth()}


@router.get("/tasks/{task_id}")
async def get_task(task_id: str):
    t = get_cognition_task(task_id)
    if not t:
        raise HTTPException(404, f"Task '{task_id}' not found")
    return t


class CreateTaskRequest(BaseModel):
    task_type: TaskType
    title: str
    input_type: str
    input_data: Dict[str, Any] = Field(default_factory=dict)
    source_ids: List[str] = Field(default_factory=list)
    priority: TaskPriority = "normal"
    workspace_id: Optional[str] = None
    depends_on: Optional[List[str]] = None
    description: str = ""


@router.post("/tasks")
async def create_task(request: CreateTaskRequest):
    input_payload = TaskInput(input_type=request.input_type, data=request.input_data, source_ids=request.source_ids)
    return create_cognition_task(
        task_type=request.task_type,
        title=request.title,
        input_payload=input_payload,
        priority=request.priority,
        workspace_id=request.workspace_id,
        depends_on=request.depends_on,
        description=request.description,
    )


@router.post("/tasks/{task_id}/queue")
async def queue_task_endpoint(task_id: str):
    t = queue_task(task_id)
    if not t:
        raise HTTPException(400, f"Task '{task_id}' not found or not pending")
    return t


@router.post("/tasks/{task_id}/cancel")
async def cancel_task_endpoint(task_id: str):
    t = cancel_task(task_id)
    if not t:
        raise HTTPException(400, f"Task '{task_id}' not found or not cancellable")
    return t
