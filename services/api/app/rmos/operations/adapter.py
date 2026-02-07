"""
RMOS Operation Adapter - Canonical Pattern Wrapper

LANE: OPERATION (governance-compliant)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md

This adapter wraps Bundle 01-03, 07 code to use canonical runs_v2 patterns:
- RunArtifact + persist_run() for artifact persistence
- create_run_id() for run ID generation
- sha256_of_obj() for deterministic hashing
- Proper event_type convention: {tool_id}_{operation}_{status}

All six governance checks are enforced:
1. Feasibility gate (blocks on RED/UNKNOWN risk)
2. Canonical artifact pattern (RunArtifact + persist_run)
3. Event type convention ({tool_id}_{operation}_execution/blocked/planned)
4. No new request schema shapes
5. Clean router mount patterns
6. Tests included in test_operations_adapter.py
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Protocol, Tuple

from pydantic import BaseModel, Field

# Canonical patterns from runs_v2
from app.rmos.runs_v2.schemas import (
    RunArtifact,
    Hashes,
    RunDecision,
    RunOutputs,
)
from app.rmos.runs_v2.store import (
    create_run_id,
    persist_run,
    get_run,
)
from app.rmos.runs_v2.hashing import (
    sha256_of_obj,
    sha256_of_text,
)


# =============================================================================
# Type Definitions
# =============================================================================

RiskLevel = Literal["GREEN", "YELLOW", "RED", "UNKNOWN", "ERROR"]
OperationStatus = Literal["OK", "BLOCKED", "ERROR"]
PlanStatus = Literal["PLANNED", "BLOCKED", "ERROR"]


class OperationRequest(BaseModel):
    """
    Canonical request for operation execution.

    Maps to Bundle 01-03 request format but enforces governance.
    """
    tool_id: str = Field(..., description="Tool identifier (e.g., 'saw_v1', 'cam_roughing_v1')")
    mode: str = Field(..., description="Operation mode (e.g., 'saw', 'cam', 'roughing')")
    cam_intent_v1: Dict[str, Any] = Field(..., description="CAM intent payload")
    feasibility: Dict[str, Any] = Field(..., description="Server-computed feasibility")

    # Optional metadata
    request_id: Optional[str] = Field(None, description="Request correlation ID")
    parent_plan_run_id: Optional[str] = Field(None, description="Parent plan artifact for lineage")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class OperationResult(BaseModel):
    """Result of operation execution."""
    run_id: str
    status: OperationStatus
    risk_level: RiskLevel
    event_type: str
    block_reason: Optional[str] = None
    gcode_text: Optional[str] = None
    gcode_sha256: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)


class PlanRequest(BaseModel):
    """
    Canonical request for operation planning.

    Maps to Bundle 07 request format.
    """
    tool_id: str = Field(..., description="Tool identifier")
    mode: str = Field(..., description="Operation mode")
    cam_intent_v1: Dict[str, Any] = Field(..., description="CAM intent payload")
    feasibility: Optional[Dict[str, Any]] = Field(None, description="Optional pre-computed feasibility")

    request_id: Optional[str] = Field(None, description="Request correlation ID")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class PlanResult(BaseModel):
    """Result of operation planning."""
    run_id: str
    status: PlanStatus
    risk_level: Optional[RiskLevel] = None
    event_type: str
    plan: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


# =============================================================================
# Tool Adapter Protocol
# =============================================================================

class ToolAdapter(Protocol):
    """
    Protocol for tool-specific adapters (saw, cam_roughing, etc.)

    Each tool type implements this to provide:
    - Feasibility computation
    - G-code generation
    - Plan generation
    """

    def compute_feasibility(
        self,
        cam_intent: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Compute feasibility for the given intent."""
        ...

    def generate_gcode(
        self,
        cam_intent: Dict[str, Any],
        feasibility: Dict[str, Any],
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate G-code. Returns (gcode_text, metadata)."""
        ...

    def generate_plan(
        self,
        cam_intent: Dict[str, Any],
        feasibility: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate operation plan."""
        ...


# =============================================================================
# Feasibility Gate
# =============================================================================

def extract_risk_level(feasibility: Dict[str, Any]) -> RiskLevel:
    """
    Extract risk level from feasibility payload.

    Supports multiple field names for compatibility.
    """
    risk = (
        feasibility.get("risk_level")
        or feasibility.get("risk")
        or feasibility.get("risk_bucket")
        or "UNKNOWN"
    )
    return risk.upper() if isinstance(risk, str) else "UNKNOWN"


def should_block(risk_level: RiskLevel) -> bool:
    """
    Determine if operation should be blocked based on risk.

    Blocks on: RED, UNKNOWN, ERROR
    Allows: GREEN, YELLOW
    """
    return risk_level in ("RED", "UNKNOWN", "ERROR")


def get_block_reason(risk_level: RiskLevel, feasibility: Dict[str, Any]) -> str:
    """Get human-readable block reason."""
    if risk_level == "RED":
        return feasibility.get("block_reason") or "Risk level RED: operation unsafe"
    if risk_level == "UNKNOWN":
        return "Risk level UNKNOWN: feasibility evaluation incomplete"
    if risk_level == "ERROR":
        return feasibility.get("error") or "Feasibility evaluation failed"
    return "Operation blocked"


# =============================================================================
# Event Type Convention
# =============================================================================

def make_event_type(tool_id: str, operation: str, status: str) -> str:
    """
    Generate canonical event type.

    Pattern: {tool_id}_{operation}_{status}

    Examples:
        - saw_v1_execution_ok
        - saw_v1_execution_blocked
        - cam_roughing_v1_plan_planned
    """
    # Normalize tool_id (remove version suffix for grouping)
    tool_base = tool_id.lower().replace("-", "_")
    op = operation.lower().replace("-", "_")
    st = status.lower()
    return f"{tool_base}_{op}_{st}"


# =============================================================================
# Operation Adapter
# =============================================================================

class OperationAdapter:
    """
    Adapter that wraps tool-specific logic with governance compliance.

    Enforces:
    1. Feasibility gate (blocks RED/UNKNOWN)
    2. Canonical artifact persistence (RunArtifact + persist_run)
    3. Proper event_type naming
    4. SHA256 hashing for audit
    """

    def __init__(self, tool_adapter: Optional[ToolAdapter] = None):
        """
        Initialize adapter with optional tool-specific implementation.

        Args:
            tool_adapter: Tool-specific adapter for feasibility/gcode generation
        """
        self.tool_adapter = tool_adapter

    def execute(self, request: OperationRequest) -> OperationResult:
        """
        Execute an operation with full governance compliance.

        Steps:
        1. Generate run_id
        2. Compute feasibility hash
        3. Check feasibility gate (block if RED/UNKNOWN)
        4. Generate G-code (if allowed)
        5. Create RunArtifact with proper event_type
        6. Persist using canonical pattern
        7. Return result
        """
        run_id = create_run_id()

        # Extract and validate feasibility
        feasibility = request.feasibility
        risk_level = extract_risk_level(feasibility)
        feasibility_sha256 = sha256_of_obj(feasibility)

        # Add hash to feasibility for downstream use
        feasibility_with_hash = {**feasibility, "sha256": feasibility_sha256}

        # Check feasibility gate
        if should_block(risk_level):
            return self._create_blocked_artifact(
                run_id=run_id,
                request=request,
                risk_level=risk_level,
                feasibility=feasibility_with_hash,
                feasibility_sha256=feasibility_sha256,
            )

        # Generate G-code
        gcode_text: Optional[str] = None
        gcode_sha256: Optional[str] = None
        gcode_meta: Dict[str, Any] = {}
        warnings: List[str] = []

        try:
            if self.tool_adapter:
                gcode_text, gcode_meta = self.tool_adapter.generate_gcode(
                    request.cam_intent_v1,
                    feasibility_with_hash,
                )
                gcode_sha256 = sha256_of_text(gcode_text) if gcode_text else None
            else:
                warnings.append("No tool adapter configured - G-code generation skipped")
        except (ValueError, TypeError, KeyError, OSError) as e:  # WP-1: narrowed from except Exception
            warnings.append(f"G-code generation error: {e}")

        # Create execution artifact
        event_type = make_event_type(request.tool_id, "execution", "ok")

        artifact = RunArtifact(
            run_id=run_id,
            request_id=request.request_id,
            mode=request.mode,
            tool_id=request.tool_id,
            status="OK",
            event_type=event_type,
            request_summary=self._summarize_request(request),
            feasibility=feasibility_with_hash,
            decision=RunDecision(
                risk_level=risk_level,
                score=feasibility.get("score"),
                warnings=warnings + feasibility.get("warnings", []),
                details=feasibility.get("details", {}),
            ),
            hashes=Hashes(
                feasibility_sha256=feasibility_sha256,
                gcode_sha256=gcode_sha256,
            ),
            outputs=RunOutputs(
                gcode_text=gcode_text if gcode_text and len(gcode_text) <= 200_000 else None,
                gcode_path=None,  # Set if stored externally
            ),
            meta={
                **request.meta,
                "gcode_meta": gcode_meta,
                "parent_plan_run_id": request.parent_plan_run_id,
            },
            parent_run_id=request.parent_plan_run_id,
        )

        # Persist using canonical pattern
        persist_run(artifact)

        return OperationResult(
            run_id=run_id,
            status="OK",
            risk_level=risk_level,
            event_type=event_type,
            gcode_text=gcode_text,
            gcode_sha256=gcode_sha256,
            warnings=warnings,
        )

    def _create_blocked_artifact(
        self,
        run_id: str,
        request: OperationRequest,
        risk_level: RiskLevel,
        feasibility: Dict[str, Any],
        feasibility_sha256: str,
    ) -> OperationResult:
        """Create and persist a BLOCKED artifact."""
        block_reason = get_block_reason(risk_level, feasibility)
        event_type = make_event_type(request.tool_id, "execution", "blocked")

        artifact = RunArtifact(
            run_id=run_id,
            request_id=request.request_id,
            mode=request.mode,
            tool_id=request.tool_id,
            status="BLOCKED",
            event_type=event_type,
            request_summary=self._summarize_request(request),
            feasibility=feasibility,
            decision=RunDecision(
                risk_level=risk_level,
                block_reason=block_reason,
                warnings=feasibility.get("warnings", []),
                details=feasibility.get("details", {}),
            ),
            hashes=Hashes(
                feasibility_sha256=feasibility_sha256,
            ),
            outputs=RunOutputs(),
            meta={
                **request.meta,
                "parent_plan_run_id": request.parent_plan_run_id,
            },
            parent_run_id=request.parent_plan_run_id,
        )

        persist_run(artifact)

        return OperationResult(
            run_id=run_id,
            status="BLOCKED",
            risk_level=risk_level,
            event_type=event_type,
            block_reason=block_reason,
            warnings=feasibility.get("warnings", []),
        )

    def plan(self, request: PlanRequest) -> PlanResult:
        """
        Create a plan artifact (pre-execution).

        Plans don't generate G-code - they capture intent and feasibility
        for later execution with lineage tracking.
        """
        run_id = create_run_id()

        # Compute or use provided feasibility
        feasibility = request.feasibility or {}
        risk_level: Optional[RiskLevel] = None
        feasibility_sha256: Optional[str] = None

        if feasibility:
            risk_level = extract_risk_level(feasibility)
            feasibility_sha256 = sha256_of_obj(feasibility)
            feasibility = {**feasibility, "sha256": feasibility_sha256}

        # Generate plan using tool adapter
        plan_data: Dict[str, Any] = {}
        warnings: List[str] = []

        try:
            if self.tool_adapter:
                plan_data = self.tool_adapter.generate_plan(
                    request.cam_intent_v1,
                    feasibility,
                )
            else:
                plan_data = {
                    "cam_intent_v1": request.cam_intent_v1,
                    "planned_at": datetime.now(timezone.utc).isoformat(),
                }
        except (ValueError, TypeError, KeyError, OSError) as e:  # WP-1: narrowed from except Exception
            warnings.append(f"Plan generation error: {e}")

        # Determine status
        status: PlanStatus = "PLANNED"
        if risk_level and should_block(risk_level):
            status = "BLOCKED"

        event_type = make_event_type(request.tool_id, "plan", status.lower())

        # Create artifact
        # Note: For plans, we use a lighter artifact without full outputs
        artifact = RunArtifact(
            run_id=run_id,
            request_id=request.request_id,
            mode=request.mode,
            tool_id=request.tool_id,
            status="OK" if status == "PLANNED" else "BLOCKED",
            event_type=event_type,
            request_summary=self._summarize_plan_request(request),
            feasibility=feasibility,
            decision=RunDecision(
                risk_level=risk_level or "UNKNOWN",
                score=feasibility.get("score") if feasibility else None,
                warnings=warnings,
                details={"plan_status": status},
            ),
            hashes=Hashes(
                feasibility_sha256=feasibility_sha256 or "0" * 64,
            ),
            outputs=RunOutputs(
                opplan_json=plan_data,
            ),
            meta={
                **request.meta,
                "plan": plan_data,
                "plan_status": status,
            },
        )

        persist_run(artifact)

        return PlanResult(
            run_id=run_id,
            status=status,
            risk_level=risk_level,
            event_type=event_type,
            plan=plan_data,
            warnings=warnings,
        )

    def _summarize_request(self, request: OperationRequest) -> Dict[str, Any]:
        """Create audit-safe request summary."""
        return {
            "tool_id": request.tool_id,
            "mode": request.mode,
            "cam_intent_keys": list(request.cam_intent_v1.keys()),
            "has_parent_plan": request.parent_plan_run_id is not None,
            # Note: Full cam_intent_v1 is in meta, not here
        }

    def _summarize_plan_request(self, request: PlanRequest) -> Dict[str, Any]:
        """Create audit-safe plan request summary."""
        return {
            "tool_id": request.tool_id,
            "mode": request.mode,
            "cam_intent_keys": list(request.cam_intent_v1.keys()),
        }


# =============================================================================
# Convenience Functions
# =============================================================================

def execute_operation(
    tool_id: str,
    mode: str,
    cam_intent_v1: Dict[str, Any],
    feasibility: Dict[str, Any],
    *,
    request_id: Optional[str] = None,
    parent_plan_run_id: Optional[str] = None,
    tool_adapter: Optional[ToolAdapter] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> OperationResult:
    """
    Execute an operation with governance compliance.

    This is the main entry point for Bundle 01-03.

    Args:
        tool_id: Tool identifier (e.g., 'saw_v1')
        mode: Operation mode (e.g., 'saw')
        cam_intent_v1: CAM intent payload
        feasibility: Server-computed feasibility
        request_id: Optional correlation ID
        parent_plan_run_id: Optional parent plan for lineage
        tool_adapter: Optional tool-specific adapter
        meta: Optional additional metadata

    Returns:
        OperationResult with run_id, status, and outputs
    """
    request = OperationRequest(
        tool_id=tool_id,
        mode=mode,
        cam_intent_v1=cam_intent_v1,
        feasibility=feasibility,
        request_id=request_id,
        parent_plan_run_id=parent_plan_run_id,
        meta=meta or {},
    )

    adapter = OperationAdapter(tool_adapter=tool_adapter)
    return adapter.execute(request)


def plan_operation(
    tool_id: str,
    mode: str,
    cam_intent_v1: Dict[str, Any],
    *,
    feasibility: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
    tool_adapter: Optional[ToolAdapter] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> PlanResult:
    """
    Create an operation plan with governance compliance.

    This is the main entry point for Bundle 07 (plan endpoints).

    Args:
        tool_id: Tool identifier
        mode: Operation mode
        cam_intent_v1: CAM intent payload
        feasibility: Optional pre-computed feasibility
        request_id: Optional correlation ID
        tool_adapter: Optional tool-specific adapter
        meta: Optional additional metadata

    Returns:
        PlanResult with run_id, status, and plan data
    """
    request = PlanRequest(
        tool_id=tool_id,
        mode=mode,
        cam_intent_v1=cam_intent_v1,
        feasibility=feasibility,
        request_id=request_id,
        meta=meta or {},
    )

    adapter = OperationAdapter(tool_adapter=tool_adapter)
    return adapter.plan(request)
