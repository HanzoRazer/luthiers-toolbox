"""
CAM Cognition Task

CAM Dev Order 7S: Worker-ready task model for manufacturing cognition.

Provides:
  - CAMCognitionTask model for queued cognition work
  - Task lifecycle (pending → running → completed/failed)
  - Task result artifacts
  - Task priority and dependencies

7S invariants:
  - execution_authorized always False
  - machine_output_allowed always False
  - generates_gcode always False

Workers are NOT implemented in 7S. This module defines the task model
for future worker integration. Tasks represent cognition work only —
strategy selection, envelope evaluation, fixture recommendation.
Tasks do NOT represent machine execution or G-code generation.

Salvaged pattern:
  Queue/worker pattern from OpenBuilds-CAM concept, adapted for
  cognition-only workloads. Implementation is repo-native.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


TaskType = Literal[
    "strategy_selection",
    "envelope_validation",
    "fixture_recommendation",
    "modality_classification",
    "workspace_validation",
    "clearance_analysis",
    "topology_check",
    "batch_validation",
]

TaskStatus = Literal[
    "pending",
    "queued",
    "running",
    "completed",
    "failed",
    "cancelled",
]

TaskPriority = Literal[
    "low",
    "normal",
    "high",
    "critical",
]


class TaskInput(BaseModel):
    """
    Input payload for a cognition task.
    """

    input_type: str = Field(..., description="Type of input data")
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Input data payload"
    )
    source_ids: List[str] = Field(
        default_factory=list,
        description="IDs of source artifacts"
    )


class TaskResult(BaseModel):
    """
    Result payload from a cognition task.

    Results contain cognition outputs only — recommendations,
    evaluations, classifications. Never machine code.
    """

    result_type: str = Field(..., description="Type of result")
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Result data payload"
    )
    output_artifact_ids: List[str] = Field(
        default_factory=list,
        description="IDs of generated artifacts"
    )
    summary: str = Field(default="", description="Human-readable summary")

    contains_gcode: bool = Field(
        default=False,
        description="Always False — cognition tasks never produce G-code"
    )

    @model_validator(mode="after")
    def enforce_no_gcode(self) -> "TaskResult":
        """Enforce that results never contain G-code."""
        if self.contains_gcode:
            raise ValueError(
                "7S invariant violation: contains_gcode must be False — "
                "cognition tasks never produce G-code"
            )
        return self


class TaskError(BaseModel):
    """
    Error information for failed tasks.
    """

    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Error message")
    error_details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional error details"
    )
    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When error occurred"
    )


class CAMCognitionTask(BaseModel):
    """
    Worker-ready task model for manufacturing cognition.

    Tasks represent units of cognition work — strategy selection,
    envelope validation, fixture recommendation. Tasks do NOT
    represent machine execution or G-code generation.

    7S invariants (model-enforced):
      - execution_authorized always False
      - machine_output_allowed always False
      - generates_gcode always False

    Workers are not implemented in 7S. This model defines the
    interface for future worker integration.
    """

    task_id: str = Field(
        default_factory=lambda: f"task-{uuid4().hex[:12]}",
        description="Unique task identifier"
    )

    task_type: TaskType = Field(..., description="Type of cognition task")
    title: str = Field(..., description="Human-readable task title")
    description: str = Field(default="", description="Task description")

    status: TaskStatus = Field(
        default="pending",
        description="Current task status"
    )
    priority: TaskPriority = Field(
        default="normal",
        description="Task priority"
    )

    input_payload: TaskInput = Field(
        ..., description="Task input payload"
    )
    result: Optional[TaskResult] = Field(
        default=None,
        description="Task result (when completed)"
    )
    error: Optional[TaskError] = Field(
        default=None,
        description="Error info (when failed)"
    )

    workspace_id: Optional[str] = Field(
        default=None,
        description="Associated workspace ID"
    )
    strategy_id: Optional[str] = Field(
        default=None,
        description="Associated strategy ID"
    )
    fixture_id: Optional[str] = Field(
        default=None,
        description="Associated fixture ID"
    )

    depends_on: List[str] = Field(
        default_factory=list,
        description="Task IDs this task depends on"
    )
    blocking: List[str] = Field(
        default_factory=list,
        description="Task IDs blocked by this task"
    )

    retry_count: int = Field(
        default=0,
        description="Number of retry attempts"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts"
    )

    tags: List[str] = Field(
        default_factory=list,
        description="User-defined tags"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extensible metadata"
    )

    execution_authorized: bool = Field(
        default=False,
        description="Always False — 7S does not authorize execution"
    )
    machine_output_allowed: bool = Field(
        default=False,
        description="Always False — 7S does not allow machine output"
    )
    generates_gcode: bool = Field(
        default=False,
        description="Always False — cognition tasks never generate G-code"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )
    queued_at: Optional[datetime] = Field(
        default=None,
        description="When task was queued"
    )
    started_at: Optional[datetime] = Field(
        default=None,
        description="When task started running"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When task completed/failed"
    )

    deterministic_hash: str = Field(
        default="",
        description="Deterministic hash of task definition"
    )

    @model_validator(mode="after")
    def enforce_7s_invariants(self) -> "CAMCognitionTask":
        """
        Enforce 7S invariants:
        - execution_authorized must be False
        - machine_output_allowed must be False
        - generates_gcode must be False
        """
        if self.execution_authorized:
            raise ValueError(
                "7S invariant violation: execution_authorized must be False — "
                "7S does not authorize execution"
            )

        if self.machine_output_allowed:
            raise ValueError(
                "7S invariant violation: machine_output_allowed must be False — "
                "7S does not allow machine output"
            )

        if self.generates_gcode:
            raise ValueError(
                "7S invariant violation: generates_gcode must be False — "
                "cognition tasks never generate G-code"
            )

        return self

    def compute_hash(self) -> str:
        """Compute deterministic hash of task definition."""
        hash_input = {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "input": {
                "input_type": self.input_payload.input_type,
                "source_ids": sorted(self.input_payload.source_ids),
            },
            "depends_on": sorted(self.depends_on),
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


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
    """
    Create a new cognition task.

    Args:
        task_type: Type of cognition task
        title: Human-readable title
        input_payload: Task input
        priority: Task priority
        workspace_id: Optional associated workspace
        depends_on: Optional dependency task IDs
        description: Optional description
        tags: Optional tags

    Returns: Created task in pending status
    """
    task = CAMCognitionTask(
        task_type=task_type,
        title=title,
        description=description,
        input_payload=input_payload,
        priority=priority,
        workspace_id=workspace_id,
        depends_on=depends_on or [],
        tags=tags or [],
    )

    task.deterministic_hash = task.compute_hash()

    COGNITION_TASK_INDEX[task.task_id] = task

    return task


def get_cognition_task(task_id: str) -> Optional[CAMCognitionTask]:
    """Get a cognition task by ID."""
    return COGNITION_TASK_INDEX.get(task_id)


def list_cognition_tasks() -> List[CAMCognitionTask]:
    """List all cognition tasks."""
    return list(COGNITION_TASK_INDEX.values())


def list_tasks_by_status(status: TaskStatus) -> List[CAMCognitionTask]:
    """List tasks by status."""
    return [t for t in COGNITION_TASK_INDEX.values() if t.status == status]


def list_tasks_by_type(task_type: TaskType) -> List[CAMCognitionTask]:
    """List tasks by type."""
    return [t for t in COGNITION_TASK_INDEX.values() if t.task_type == task_type]


def list_tasks_for_workspace(workspace_id: str) -> List[CAMCognitionTask]:
    """List tasks associated with a workspace."""
    return [
        t for t in COGNITION_TASK_INDEX.values()
        if t.workspace_id == workspace_id
    ]


def queue_task(task_id: str) -> Optional[CAMCognitionTask]:
    """
    Queue a pending task for processing.

    Args:
        task_id: Task to queue

    Returns: Updated task or None if not found/not pending
    """
    task = COGNITION_TASK_INDEX.get(task_id)
    if not task or task.status != "pending":
        return None

    unmet_deps = [
        dep_id for dep_id in task.depends_on
        if dep_id in COGNITION_TASK_INDEX
        and COGNITION_TASK_INDEX[dep_id].status != "completed"
    ]

    if unmet_deps:
        return None

    task.status = "queued"
    task.queued_at = datetime.now(timezone.utc)

    if task_id not in COGNITION_TASK_QUEUE:
        if task.priority == "critical":
            COGNITION_TASK_QUEUE.insert(0, task_id)
        elif task.priority == "high":
            insert_pos = 0
            for i, tid in enumerate(COGNITION_TASK_QUEUE):
                t = COGNITION_TASK_INDEX.get(tid)
                if t and t.priority not in ("critical", "high"):
                    insert_pos = i
                    break
                insert_pos = i + 1
            COGNITION_TASK_QUEUE.insert(insert_pos, task_id)
        else:
            COGNITION_TASK_QUEUE.append(task_id)

    return task


def start_task(task_id: str) -> Optional[CAMCognitionTask]:
    """
    Mark a queued task as running.

    Note: Workers are not implemented in 7S. This is the interface
    for future worker integration.

    Args:
        task_id: Task to start

    Returns: Updated task or None if not found/not queued
    """
    task = COGNITION_TASK_INDEX.get(task_id)
    if not task or task.status != "queued":
        return None

    task.status = "running"
    task.started_at = datetime.now(timezone.utc)

    if task_id in COGNITION_TASK_QUEUE:
        COGNITION_TASK_QUEUE.remove(task_id)

    return task


def complete_task(
    task_id: str,
    result: TaskResult,
) -> Optional[CAMCognitionTask]:
    """
    Mark a running task as completed with result.

    Args:
        task_id: Task to complete
        result: Task result

    Returns: Updated task or None if not found/not running
    """
    task = COGNITION_TASK_INDEX.get(task_id)
    if not task or task.status != "running":
        return None

    task.status = "completed"
    task.result = result
    task.completed_at = datetime.now(timezone.utc)

    for blocking_id in task.blocking:
        blocking_task = COGNITION_TASK_INDEX.get(blocking_id)
        if blocking_task and blocking_task.status == "pending":
            all_deps_complete = all(
                COGNITION_TASK_INDEX.get(dep_id) and
                COGNITION_TASK_INDEX[dep_id].status == "completed"
                for dep_id in blocking_task.depends_on
            )
            if all_deps_complete:
                queue_task(blocking_id)

    return task


def fail_task(
    task_id: str,
    error: TaskError,
) -> Optional[CAMCognitionTask]:
    """
    Mark a running task as failed with error.

    Args:
        task_id: Task to fail
        error: Error information

    Returns: Updated task or None if not found/not running
    """
    task = COGNITION_TASK_INDEX.get(task_id)
    if not task or task.status != "running":
        return None

    task.status = "failed"
    task.error = error
    task.completed_at = datetime.now(timezone.utc)

    return task


def cancel_task(task_id: str) -> Optional[CAMCognitionTask]:
    """
    Cancel a pending or queued task.

    Args:
        task_id: Task to cancel

    Returns: Updated task or None if not found/not cancellable
    """
    task = COGNITION_TASK_INDEX.get(task_id)
    if not task or task.status not in ("pending", "queued"):
        return None

    task.status = "cancelled"
    task.completed_at = datetime.now(timezone.utc)

    if task_id in COGNITION_TASK_QUEUE:
        COGNITION_TASK_QUEUE.remove(task_id)

    return task


def retry_task(task_id: str) -> Optional[CAMCognitionTask]:
    """
    Retry a failed task.

    Args:
        task_id: Task to retry

    Returns: Updated task or None if not found/not retryable
    """
    task = COGNITION_TASK_INDEX.get(task_id)
    if not task or task.status != "failed":
        return None

    if task.retry_count >= task.max_retries:
        return None

    task.status = "pending"
    task.retry_count += 1
    task.error = None
    task.started_at = None
    task.completed_at = None

    return task


def get_next_queued_task() -> Optional[CAMCognitionTask]:
    """
    Get the next task from the queue.

    Returns: Next queued task or None if queue is empty
    """
    if not COGNITION_TASK_QUEUE:
        return None

    task_id = COGNITION_TASK_QUEUE[0]
    return COGNITION_TASK_INDEX.get(task_id)


def get_queue_depth() -> int:
    """Get current queue depth."""
    return len(COGNITION_TASK_QUEUE)


def get_task_stats() -> Dict[str, int]:
    """Get task statistics by status."""
    stats: Dict[str, int] = {
        "pending": 0,
        "queued": 0,
        "running": 0,
        "completed": 0,
        "failed": 0,
        "cancelled": 0,
    }

    for task in COGNITION_TASK_INDEX.values():
        stats[task.status] += 1

    return stats


def clear_task_index() -> None:
    """Clear task index and queue (for testing)."""
    COGNITION_TASK_INDEX.clear()
    COGNITION_TASK_QUEUE.clear()
