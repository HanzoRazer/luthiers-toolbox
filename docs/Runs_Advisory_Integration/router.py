from __future__ import annotations

import os
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from .schemas import RunArtifact, AdvisoryInputRef
from .store import RunStore

router = APIRouter(prefix="/api/rmos/runs", tags=["RMOS Runs"])


def _runs_dir() -> str:
    # Default keeps data local and easy to inspect
    return os.environ.get("RMOS_RUNS_DIR", "data/rmos_runs")


def _store() -> RunStore:
    return RunStore(_runs_dir())


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class RunCreateRequest(BaseModel):
    mode: str = "unknown"
    tool_id: str = "unknown"
    status: str = "OK"  # keep permissive here; schema enforces allowed values in RunArtifact
    request_summary: Dict[str, Any] = Field(default_factory=dict)
    feasibility: Dict[str, Any] = Field(default_factory=dict)
    meta: Dict[str, Any] = Field(default_factory=dict)


class RunPatchMetaRequest(BaseModel):
    meta_updates: Dict[str, Any] = Field(default_factory=dict)


class AttachAdvisoryRequest(BaseModel):
    advisory_id: str
    kind: str = "unknown"
    engine_id: Optional[str] = None
    engine_version: Optional[str] = None


class SuggestAndAttachRequest(BaseModel):
    """Request for sync explanation generation."""
    generate_explanation: bool = True
    explanation_detail: str = "summary"  # "summary" | "full"


# ---------------------------------------------------------------------------
# Basic CRUD Endpoints
# ---------------------------------------------------------------------------

@router.post("", response_model=RunArtifact)
def create_run(req: RunCreateRequest, request: Request) -> RunArtifact:
    run_id = f"run_{uuid.uuid4().hex[:12]}"
    req_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id")

    run = RunArtifact(
        run_id=run_id,
        mode=req.mode,
        tool_id=req.tool_id,
        status=req.status,  # RunArtifact will validate OK/BLOCKED/ERROR
        request_summary=req.request_summary,
        feasibility=req.feasibility,
        meta={**req.meta, **({"request_id": req_id} if req_id else {})},
    )

    st = _store()
    st.put(run)
    return run


@router.get("/{run_id}", response_model=RunArtifact)
def get_run(run_id: str) -> RunArtifact:
    st = _store()
    run = st.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    return run


@router.patch("/{run_id}/meta", response_model=RunArtifact)
def patch_run_meta(run_id: str, req: RunPatchMetaRequest) -> RunArtifact:
    st = _store()
    run = st.patch_meta(run_id, req.meta_updates)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    return run


# ---------------------------------------------------------------------------
# Advisory Integration Endpoints
# ---------------------------------------------------------------------------

@router.post("/{run_id}/attach-advisory", response_model=RunArtifact)
def attach_advisory(run_id: str, req: AttachAdvisoryRequest, request: Request) -> RunArtifact:
    """
    Attach an advisory asset reference to a run.
    
    GOVERNANCE: The advisory should be approved before attaching.
    This creates the audit link: Run -> Advisory
    """
    st = _store()
    req_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id")
    
    run = st.attach_advisory(
        run_id=run_id,
        advisory_id=req.advisory_id,
        kind=req.kind,
        engine_id=req.engine_id,
        engine_version=req.engine_version,
        request_id=req_id,
    )
    
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    
    return run


@router.get("/{run_id}/advisories")
def list_advisories(run_id: str) -> Dict[str, Any]:
    """List all advisory references attached to a run."""
    st = _store()
    run = st.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    
    return {
        "run_id": run_id,
        "advisory_inputs": [ref.model_dump(mode="json") for ref in run.advisory_inputs],
        "count": len(run.advisory_inputs),
        "explanation_status": run.explanation_status,
        "explanation_summary": run.explanation_summary,
    }


@router.post("/{run_id}/suggest-and-attach", response_model=RunArtifact)
def suggest_and_attach(run_id: str, req: SuggestAndAttachRequest, request: Request) -> RunArtifact:
    """
    Generate explanation for a run and attach as advisory.
    
    This is the sync explanation path (Hook 2 from integration plan):
    1. Get run's feasibility data
    2. Generate explanation using existing explain_gcode
    3. Store as AdvisoryAsset
    4. Attach reference to run
    5. Update explanation_status/summary
    """
    st = _store()
    run = st.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    
    if not req.generate_explanation:
        return run
    
    # Mark as pending
    st.set_explanation(run_id, "PENDING")
    
    try:
        # Import advisory store
        from app._experimental.ai_graphics.advisory_store import get_advisory_store
        from app._experimental.ai_graphics.schemas.advisory_schemas import (
            AdvisoryAsset,
            AdvisoryAssetType,
        )
        from .hashing import sha256_json
        
        # Generate explanation summary from feasibility data
        feasibility = run.feasibility
        decision = run.decision
        
        # Build explanation
        if decision.risk_level == "GREEN":
            summary = f"All checks passed. Score: {decision.score or 'N/A'}."
        elif decision.risk_level == "YELLOW":
            warnings = "; ".join(decision.warnings) if decision.warnings else "Minor concerns"
            summary = f"Caution advised: {warnings}. Score: {decision.score or 'N/A'}."
        elif decision.risk_level == "RED":
            reason = decision.block_reason or "Blocked"
            summary = f"Not recommended: {reason}. Score: {decision.score or 'N/A'}."
        else:
            summary = f"Analysis complete. Risk: {decision.risk_level or 'unknown'}."
        
        # Create advisory asset
        asset = AdvisoryAsset(
            asset_type=AdvisoryAssetType.ANALYSIS,
            source="ai_analysis",
            provider="local",
            model="feasibility_explainer_v1",
            prompt=f"Explain feasibility for run {run_id}",
            content_hash=sha256_json(feasibility),
            suggestion_data={
                "run_id": run_id,
                "explanation": summary,
                "detail_level": req.explanation_detail,
                "feasibility_snapshot": feasibility,
            },
            confidence=0.9,
        )
        
        # Save to advisory store
        advisory_store = get_advisory_store()
        advisory_store.save_asset(asset)
        
        # Auto-approve analysis (it's explanatory, not prescriptive)
        asset.reviewed = True
        asset.approved_for_workflow = True
        asset.reviewed_by = "system"
        advisory_store.update_asset(asset)
        
        # Attach to run
        req_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id")
        run = st.attach_advisory(
            run_id=run_id,
            advisory_id=asset.asset_id,
            kind="explanation",
            engine_id="feasibility_explainer_v1",
            engine_version="1.0.0",
            request_id=req_id,
        )
        
        # Update explanation status
        run = st.set_explanation(run_id, "READY", summary)
        
        return run
        
    except ImportError as e:
        st.set_explanation(run_id, "ERROR", f"Advisory store unavailable: {e}")
        run = st.get(run_id)
        return run
    except Exception as e:
        st.set_explanation(run_id, "ERROR", str(e))
        run = st.get(run_id)
        return run
