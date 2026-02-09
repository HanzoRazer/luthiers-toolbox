"""RMOS Runs API Router v2 - Governance Compliant"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Header, Query, Request
from pydantic import BaseModel, Field

from .schemas import RunArtifact, RunDecision, Hashes
from .store import (
    get_run,
    list_runs_filtered,
    persist_run,
    create_run_id,
    query_recent,
    delete_run,
    DeleteRateLimitError,
)
from .diff import build_diff
from .hashing import summarize_request, compute_feasibility_hash
from app.rmos.api.response_utils import runs_list_response

router = APIRouter(prefix="/runs", tags=["runs"])

# Sub-routers
from .api_global_attachments import router as global_attachments_router
from .router_override import router as override_router
from .api_runs_advisory import router as advisory_router
from .api_runs_attachments import router as attachments_router
from .api_runs_variants import router as variants_router
from .api_runs_explain import router as explain_router

router.include_router(global_attachments_router)
router.include_router(override_router)
router.include_router(advisory_router)
router.include_router(attachments_router)
router.include_router(variants_router)
router.include_router(explain_router)

from .advisory_blob_schemas import AdvisoryBlobListResponse, SvgPreviewStatusResponse
from .advisory_blob_service import (
    list_advisory_blobs,
    download_advisory_blob,
    preview_svg,
    check_svg_preview_status,
    download_all_zip,
)

# --- Response Models ---

class RunArtifactSummary(BaseModel):
    """Summary view of a run artifact for list endpoints."""
    run_id: str
    created_at_utc: str
    event_type: str
    status: str
    mode: str
    tool_id: str
    material_id: Optional[str] = None
    machine_id: Optional[str] = None
    workflow_session_id: Optional[str] = None
    risk_level: Optional[str] = None
    feasibility_sha256: Optional[str] = None
    toolpaths_sha256: Optional[str] = None
    gcode_sha256: Optional[str] = None
    explanation_status: Optional[str] = None
    advisory_count: int = 0

def _to_summary(r: RunArtifact) -> RunArtifactSummary:
    """Convert RunArtifact to summary view."""
    created_at = r.created_at_utc
    if hasattr(created_at, "isoformat"):
        created_at = created_at.isoformat()

    return RunArtifactSummary(
        run_id=r.run_id, created_at_utc=created_at, event_type=r.event_type, status=r.status,
        mode=r.mode, tool_id=r.tool_id, material_id=r.material_id, machine_id=r.machine_id,
        workflow_session_id=r.workflow_session_id, risk_level=r.decision.risk_level if r.decision else None,
        feasibility_sha256=r.hashes.feasibility_sha256 if r.hashes else None,
        toolpaths_sha256=r.hashes.toolpaths_sha256 if r.hashes else None,
        gcode_sha256=r.hashes.gcode_sha256 if r.hashes else None,
        explanation_status=r.explanation_status, advisory_count=len(r.advisory_inputs) if r.advisory_inputs else 0,
    )

# --- Request Models ---

class RunCreateRequest(BaseModel):
    """Request body for creating a new run artifact."""

    mode: str = Field(
        default="unknown", description="Operation mode (cam, preview, simulation)"
    )
    tool_id: str = Field(default="unknown", description="Tool identifier")
    status: str = Field(default="OK", description="Run status (OK, BLOCKED, ERROR)")
    event_type: str = Field(
        default="unknown", description="Event type (approval, toolpaths, etc)"
    )
    request_summary: Dict[str, Any] = Field(
        default_factory=dict, description="Redacted request summary"
    )
    feasibility: Dict[str, Any] = Field(
        default_factory=dict, description="Feasibility evaluation result"
    )
    decision: Optional[Dict[str, Any]] = Field(
        default=None, description="Decision override (optional)"
    )
    meta: Dict[str, Any] = Field(default_factory=dict, description="Free-form metadata")

# --- Create Endpoint (Immutable) ---

@router.post("", response_model=Dict[str, Any], summary="Create a new run artifact.")
def create_run_endpoint(req: RunCreateRequest, request: Request):
    """Create a new run artifact."""
    run_id = create_run_id()
    req_id = getattr(request.state, "request_id", None) or request.headers.get(
        "x-request-id"
    )

    # Compute required feasibility hash
    feasibility_sha256 = compute_feasibility_hash(req.feasibility)

    # Build hashes
    hashes = Hashes(
        feasibility_sha256=feasibility_sha256,
    )

    # Build decision
    if req.decision:
        decision = RunDecision(
            risk_level=req.decision.get("risk_level", "UNKNOWN"),
            score=req.decision.get("score"),
            block_reason=req.decision.get("block_reason"),
            warnings=req.decision.get("warnings", []),
            details=req.decision.get("details", {}),
        )
    else:
        # Extract from feasibility if available
        risk_level = (
            req.feasibility.get("risk_bucket")
            or req.feasibility.get("risk_level")
            or "UNKNOWN"
        )
        decision = RunDecision(
            risk_level=risk_level,
            score=req.feasibility.get("score"),
            block_reason=req.feasibility.get("block_reason"),
            warnings=req.feasibility.get("warnings", []),
        )

    # Build the artifact
    artifact = RunArtifact(
        run_id=run_id,
        created_at_utc=datetime.now(timezone.utc),
        event_type=req.event_type,
        status=req.status,
        tool_id=req.tool_id,
        mode=req.mode,
        request_summary=(
            summarize_request(req.request_summary) if req.request_summary else {}
        ),
        feasibility=req.feasibility,
        decision=decision,
        hashes=hashes,
        meta={**req.meta, **({"request_id": req_id} if req_id else {})},
    )

    persist_run(artifact)
    return {"run_id": run_id, "status": "created", "feasibility_sha256": feasibility_sha256}

# --- List / Detail Endpoints ---

@router.get("", response_model=Dict[str, Any], summary="List run artifacts.")
def list_runs_endpoint(
    limit: int = Query(50, ge=1, le=500),
    event_type: Optional[str] = None,
    kind: Optional[str] = Query(None, description="Alias for event_type"),
    status: Optional[str] = None,
    tool_id: Optional[str] = None,
    mode: Optional[str] = None,
    batch_label: Optional[str] = Query(
        None, description="Filter runs by batch_label (from meta)"
    ),
    session_id: Optional[str] = Query(
        None, description="Filter runs by session_id (from meta)"
    ),
    parent_batch_plan_artifact_id: Optional[str] = Query(
        None, description="Filter runs by parent batch plan artifact ID"
    ),
    parent_batch_spec_artifact_id: Optional[str] = Query(
        None, description="Filter runs by parent batch spec artifact ID"
    ),
):
    """List run artifacts with optional filtering."""
    runs = list_runs_filtered(
        limit=limit,
        event_type=event_type,
        kind=kind,
        status=status,
        tool_id=tool_id,
        mode=mode,
        batch_label=batch_label,
        session_id=session_id,
        parent_batch_plan_artifact_id=parent_batch_plan_artifact_id,
        parent_batch_spec_artifact_id=parent_batch_spec_artifact_id,
    )
    items = [_to_summary(r).model_dump() for r in runs]
    return runs_list_response(items, limit=limit)

@router.get("/diff", summary="Diff two run artifacts by id.")
def diff_two_runs(
    left_id: str = Query(..., description="Left run artifact id"),
    right_id: str = Query(..., description="Right run artifact id"),
    preview_max_chars: int = Query(20000, ge=1000, le=200000),
    force_attachment: bool = Query(
        False, description="Always persist full diff as attachment"
    ),
) -> Dict[str, Any]:
    """Diff two runs."""
    from .diff_attachments import persist_diff_as_attachment_if_needed

    left = get_run(left_id)
    if left is None:
        raise HTTPException(status_code=404, detail=f"Run {left_id} not found")

    right = get_run(right_id)
    if right is None:
        raise HTTPException(status_code=404, detail=f"Run {right_id} not found")

    diff_text = build_diff(left, right)

    att = persist_diff_as_attachment_if_needed(
        left_id=left_id,
        right_id=right_id,
        diff_text=diff_text,
        preview_max_chars=preview_max_chars,
        force_attachment=force_attachment,
    )

    return {
        "left_id": left_id,
        "right_id": right_id,
        "diff_kind": "unified",
        "preview": att.preview,
        "truncated": att.truncated,
        "full_bytes": att.full_bytes,
        "diff_attachment": ({"run_id": right_id, "sha256": att.attachment_sha256, "content_type": att.attachment_content_type,
                             "filename": att.attachment_filename, "kind": "run_diff"} if att.attachment_sha256 else None),
    }

@router.get(
    "/{run_id}", response_model=Dict[str, Any], summary="Get run artifact details."
)
def read_run(run_id: str) -> Dict[str, Any]:
    """Get full details of a run artifact."""
    r = get_run(run_id)
    if r is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "RUN_NOT_FOUND", "run_id": run_id},
        )

    created_at = r.created_at_utc
    if hasattr(created_at, "isoformat"):
        created_at = created_at.isoformat()

    return {
        "run_id": r.run_id,
        "created_at_utc": created_at,
        "event_type": r.event_type,
        "status": r.status,
        "mode": r.mode,
        "tool_id": r.tool_id,
        # Context
        "workflow_session_id": r.workflow_session_id,
        "material_id": r.material_id,
        "machine_id": r.machine_id,
        "workflow_mode": r.workflow_mode,
        "toolchain_id": r.toolchain_id,
        "post_processor_id": r.post_processor_id,
        # Geometry
        "geometry_ref": r.geometry_ref,
        "geometry_hash": r.geometry_hash,
        # Hashes (v2 nested model)
        "hashes": {"feasibility_sha256": r.hashes.feasibility_sha256, "toolpaths_sha256": r.hashes.toolpaths_sha256,
                  "gcode_sha256": r.hashes.gcode_sha256, "opplan_sha256": r.hashes.opplan_sha256},
        # Decision (v2 nested model)
        "decision": {"risk_level": r.decision.risk_level, "score": r.decision.score,
                   "block_reason": r.decision.block_reason, "warnings": r.decision.warnings, "details": r.decision.details},
        # Feasibility
        "feasibility": r.feasibility,
        "request_summary": r.request_summary,
        # Outputs
        "outputs": {"gcode_text": r.outputs.gcode_text if r.outputs else None, "gcode_path": r.outputs.gcode_path if r.outputs else None,
                  "opplan_json": r.outputs.opplan_json if r.outputs else None, "opplan_path": r.outputs.opplan_path if r.outputs else None,
                  "preview_svg_path": r.outputs.preview_svg_path if r.outputs else None},
        # Advisory
        "advisory_inputs": [
            {"advisory_id": a.advisory_id, "kind": a.kind, "engine_id": a.engine_id,
             "engine_version": a.engine_version, "request_id": a.request_id,
             "created_at_utc": a.created_at_utc.isoformat() if hasattr(a.created_at_utc, "isoformat") else a.created_at_utc}
            for a in (r.advisory_inputs or [])
        ],
        "explanation_status": r.explanation_status,
        "explanation_summary": r.explanation_summary,
        # Attachments
        "attachments": [
            {"sha256": a.sha256, "kind": a.kind, "mime": a.mime, "filename": a.filename,
             "size_bytes": a.size_bytes, "created_at_utc": a.created_at_utc}
            for a in (r.attachments or [])
        ],
        # Drift
        "parent_run_id": r.parent_run_id,
        "drift_detected": r.drift_detected,
        "drift_summary": r.drift_summary,
        # Gating
        "gate_policy_id": r.gate_policy_id,
        "gate_decision": r.gate_decision,
        # Versions
        "engine_version": r.engine_version,
        "toolchain_version": r.toolchain_version,
        "config_fingerprint": r.config_fingerprint,
        # Notes
        "notes": r.notes,
        "errors": r.errors,
        # Meta
        "meta": r.meta,
    }

# -- Advisory Blob Browser (run-scoped) ----------------------------------------

@router.get("/{run_id}/advisory/blobs", response_model=AdvisoryBlobListResponse)
def list_run_advisory_blobs(run_id: str):
    """
    List all advisory blobs linked to this run.
    Source of truth: run.advisory_inputs[*].advisory_id
    """
    items = list_advisory_blobs(run_id)
    return AdvisoryBlobListResponse(run_id=run_id, count=len(items), items=items)

@router.get("/{run_id}/advisory/blobs/{sha256}/download")
def download_run_advisory_blob(run_id: str, sha256: str):
    """
    Download an advisory blob by sha256.
    Only allowed if sha256 is linked to this run's advisory_inputs.
    """
    return download_advisory_blob(run_id, sha256)

@router.get("/{run_id}/advisory/blobs/{sha256}/preview/svg")
def preview_run_advisory_svg(run_id: str, sha256: str):
    """
    Inline SVG preview (run-authorized).
    Applies safety gate (blocks script/foreignObject/image).
    """
    return preview_svg(run_id, sha256)

@router.get(
    "/{run_id}/advisory/blobs/{sha256}/preview/status",
    response_model=SvgPreviewStatusResponse,
)
def check_run_advisory_svg_status(run_id: str, sha256: str):
    """
    Check if SVG preview is available and safe.
    Returns status response with reason if blocked, plus recommended action.
    Useful for UI to show friendly message instead of error.
    """
    return check_svg_preview_status(run_id, sha256)

@router.get("/{run_id}/advisory/blobs/download-all.zip")
def download_all_run_advisory_blobs_zip(run_id: str, background_tasks: BackgroundTasks):
    """
    Download all advisory blobs linked to this run as a zip.
    """
    return download_all_zip(run_id, background_tasks)

# --- H3.4: Cursor-based Pagination Endpoint ---

@router.get("/query/recent", summary="Query runs with cursor pagination")
def query_runs_cursor_endpoint(
    limit: int = Query(50, ge=1, le=500, description="Max results per page"),
    cursor: Optional[str] = Query(
        None, description="Pagination cursor (format: timestamp|run_id)"
    ),
    mode: Optional[str] = Query(None, description="Filter by mode"),
    tool_id: Optional[str] = Query(None, description="Filter by tool_id"),
    status: Optional[str] = Query(
        None, description="Filter by status (OK, BLOCKED, ERROR)"
    ),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    source: Optional[str] = Query(None, description="Filter by source"),
):
    """Query runs with cursor-based pagination."""
    return query_recent(
        limit=limit,
        cursor=cursor,
        mode=mode,
        tool_id=tool_id,
        status=status,
        risk_level=risk_level,
        source=source,
    )

# --- H3.5/H3.6: DELETE Endpoint with Policy Enforcement ---

from .delete_policy import (
    get_delete_policy,
    is_admin_request,
    check_delete_allowed,
    resolve_effective_mode,
)
from .delete_audit import append_delete_audit, build_delete_audit_event

@router.delete("/{run_id}", summary="Delete a run artifact")
def delete_run_endpoint(
    request: Request,
    run_id: str,
    mode: Optional[str] = Query(
        None,
        description="Delete mode: 'soft' (tombstone, default) or 'hard' (remove files)",
    ),
    reason: str = Query(
        ...,
        min_length=6,
        max_length=500,
        description="Audit reason for deletion (required)",
    ),
    actor: Optional[str] = Query(None, description="Actor performing deletion"),
    cascade: bool = Query(True, description="Also delete advisory links"),
    x_rmos_admin: Optional[str] = Header(None, alias="X-RMOS-Admin"),
):
    """Delete a run artifact with policy enforcement and audit logging."""
    # Extract request context
    req_id = getattr(request.state, "request_id", None) or request.headers.get(
        "x-request-id"
    )
    client_ip = request.client.host if request.client else None
    effective_actor = actor.strip() if actor else None

    # Resolve policy and mode
    policy = get_delete_policy()
    effective_mode = resolve_effective_mode(mode, policy)
    is_admin = is_admin_request(x_rmos_admin)

    # Check policy
    allowed, deny_reason = check_delete_allowed(effective_mode, is_admin, policy)

    if not allowed:
        # Audit the forbidden attempt
        try:
            from .store import _get_default_store

            store = _get_default_store()
            event = build_delete_audit_event(
                run_id=run_id, mode=effective_mode, reason=reason, actor=effective_actor, request_id=req_id,
                index_updated=False, artifact_deleted=False, attachments_deleted=0, allowed_by_policy=False,
                allowed_by_rate_limit=True, client_ip=client_ip, outcome="forbidden", errors=deny_reason,
            )
            append_delete_audit(store_root=store.root, event=event)
        except (OSError, ValueError, TypeError, KeyError):  # WP-1: narrowed from except Exception
            pass  # Audit must never block
        raise HTTPException(status_code=403, detail=deny_reason)

    # Attempt delete
    try:
        result = delete_run(
            run_id,
            mode=effective_mode,
            reason=reason,
            actor=effective_actor,
            request_id=req_id,
            cascade=cascade,
        )

        return {"run_id": run_id, "mode": effective_mode, "deleted": result["deleted"],
                "tombstoned": result.get("index_updated") and effective_mode == "soft",
                "artifact_deleted": result.get("artifact_deleted", False),
                "advisory_links_deleted": result.get("advisory_links_deleted", 0),
                "reason": reason, "request_id": req_id}

    except KeyError:
        # Run not found - already audited by delete_run
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    except DeleteRateLimitError as e:
        # Rate limited - already audited by delete_run
        raise HTTPException(status_code=429, detail=str(e))

    except ValueError as e:
        # Invalid input (e.g., empty reason) - shouldn't happen due to Query validation
        raise HTTPException(status_code=400, detail=str(e))

