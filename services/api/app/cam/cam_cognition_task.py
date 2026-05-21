"""
CAM Cognition Task

CAM Dev Order 7S: Worker-ready task model for manufacturing cognition.

7S invariants:
  - execution_authorized always False
  - machine_output_allowed always False
  - generates_gcode always False
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


TaskType = Literal["strategy_selection", "envelope_validation", "fixture_recommendation", "modality_classification", "workspace_validation", "clearance_analysis"]
TaskStatus = Literal["pending", "queued", "running", "completed", "failed", "cancelled"]
TaskPriority = Literal["low", "normal", "high", "critical"]


class TaskInput(BaseModel):
    """Input payload for a cognition task."""

    input_type: str
    data: Dict[str, Any] = Field(default_factory=dict)
    source_ids: List[str] = Field(default_factory=list)


class TaskResult(BaseModel):
    """Result payload from a cognition task."""

    result_type: str
    data: Dict[str, Any] = Field(default_factory=dict)
    output_artifact_ids: List[str] = Field(default_factory=list)
    summary: str = ""
    contains_gcode: bool = Field(default=False)

    @model_validator(mode="after")
    def enforce_no_gcode(self) -> "TaskResult":
        if self.contains_gcode:
            raise ValueError("7S invariant violation: contains_gcode must be False")
        return self


class TaskError(BaseModel):
    """Error information for failed tasks."""

    error_code: str
    error_message: str
    error_details: Dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CAMCognitionTask(BaseModel):
    """Worker-ready task model for manufacturing cognition."""

    task_id: str = Field(default_factory=lambda: f"task-{uuid4().hex[:12]}")
    task_type: TaskType
    title: str
    description: str = ""
    status: TaskStatus = "pending"
    priority: TaskPriority = "normal"

    input_payload: TaskInput
    result: Optional[TaskResult] = None
    error: Optional[TaskError] = None

    workspace_id: Optional[str] = None
    strategy_id: Optional[str] = None
    depends_on: List[str] = Field(default_factory=list)
    blocking: List[str] = Field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3

    execution_authorized: bool = Field(default=False)
    machine_output_allowed: bool = Field(default=False)
    generates_gcode: bool = Field(default=False)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    queued_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @model_validator(mode="after")
    def enforce_7s_invariants(self) -> "CAMCognitionTask":
        if self.execution_authorized:
            raise ValueError("7S invariant violation: execution_authorized must be False")
        if self.machine_output_allowed:
            raise ValueError("7S invariant violation: machine_output_allowed must be False")
        if self.generates_gcode:
            raise ValueError("7S invariant violation: generates_gcode must be False")
        return self


COGNITION_TASK_INDEX: Dict[str, CAMCognitionTask] = {}
COGNITION_TASK_QUEUE: List[str] = []


def create_cognition_task(
    task_type: TaskType,
    title: str,
    input_payload: TaskInput,
    priority: TaskPriority = "normal",
    workspace_id: Optional[str] = None,
    depends_on: Optional[List[str]] = None,
    description: str = "",
    tags: Optional[List[str]] = None,
) -> CAMCognitionTask:
    task = CAMCognitionTask(
        task_type=task_type,
        title=title,
        description=description,
        input_payload=input_payload,
        priority=priority,
        workspace_id=workspace_id,
        depends_on=depends_on or [],
    )
    COGNITION_TASK_INDEX[task.task_id] = task
    return task


def get_cognition_task(task_id: str) -> Optional[CAMCognitionTask]:
    return COGNITION_TASK_INDEX.get(task_id)


def list_cognition_tasks() -> List[CAMCognitionTask]:
    return list(COGNITION_TASK_INDEX.values())


def list_tasks_by_status(status: TaskStatus) -> List[CAMCognitionTask]:
    return [t for t in COGNITION_TASK_INDEX.values() if t.status == status]


def list_tasks_by_type(task_type: TaskType) -> List[CAMCognitionTask]:
    return [t for t in COGNITION_TASK_INDEX.values() if t.task_type == task_type]


def queue_task(task_id: str) -> Optional[CAMCognitionTask]:
    task = COGNITION_TASK_INDEX.get(task_id)
    if not task or task.status != "pending":
        return None
    unmet_deps = [d for d in task.depends_on if d in COGNITION_TASK_INDEX and COGNITION_TASK_INDEX[d].status != "completed"]
    if unmet_deps:
        return None
    task.status = "queued"
    task.queued_at = datetime.now(timezone.utc)
    if task_id not in COGNITION_TASK_QUEUE:
        if task.priority == "critical":
            COGNITION_TASK_QUEUE.insert(0, task_id)
        else:
            COGNITION_TASK_QUEUE.append(task_id)
    return task


def start_task(task_id: str) -> Optional[CAMCognitionTask]:
    task = COGNITION_TASK_INDEX.get(task_id)
    if not task or task.status != "queued":
        return None
    task.status = "running"
    task.started_at = datetime.now(timezone.utc)
    if task_id in COGNITION_TASK_QUEUE:
        COGNITION_TASK_QUEUE.remove(task_id)
    return task


def complete_task(task_id: str, result: TaskResult) -> Optional[CAMCognitionTask]:
    task = COGNITION_TASK_INDEX.get(task_id)
    if not task or task.status != "running":
        return None
    task.status = "completed"
    task.result = result
    task.completed_at = datetime.now(timezone.utc)
    return task


def fail_task(task_id: str, error: TaskError) -> Optional[CAMCognitionTask]:
    task = COGNITION_TASK_INDEX.get(task_id)
    if not task or task.status != "running":
        return None
    task.status = "failed"
    task.error = error
    task.completed_at = datetime.now(timezone.utc)
    return task


def cancel_task(task_id: str) -> Optional[CAMCognitionTask]:
    task = COGNITION_TASK_INDEX.get(task_id)
    if not task or task.status not in ("pending", "queued"):
        return None
    task.status = "cancelled"
    task.completed_at = datetime.now(timezone.utc)
    if task_id in COGNITION_TASK_QUEUE:
        COGNITION_TASK_QUEUE.remove(task_id)
    return task


def retry_task(task_id: str) -> Optional[CAMCognitionTask]:
    task = COGNITION_TASK_INDEX.get(task_id)
    if not task or task.status != "failed" or task.retry_count >= task.max_retries:
        return None
    task.status = "pending"
    task.retry_count += 1
    task.error = None
    task.started_at = None
    task.completed_at = None
    return task


def get_queue_depth() -> int:
    return len(COGNITION_TASK_QUEUE)


def get_task_stats() -> Dict[str, int]:
    stats = {"pending": 0, "queued": 0, "running": 0, "completed": 0, "failed": 0, "cancelled": 0}
    for task in COGNITION_TASK_INDEX.values():
        stats[task.status] += 1
    return stats


def clear_task_index() -> None:
    COGNITION_TASK_INDEX.clear()
    COGNITION_TASK_QUEUE.clear()
