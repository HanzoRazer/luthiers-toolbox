# RMOS Runs Gap Analysis
## Patch vs Existing Implementation Comparison

**Date:** December 18, 2025
**Status:** Analysis Complete - Merge Recommended

---

## Executive Summary

The existing RMOS Runs implementation is **more complete** than the proposed patch in most areas (attachments, diffing, filtering, thread safety). However, the patch introduces several **valuable features** that should be added to the existing implementation rather than replacing it.

**Recommendation:** Extend existing implementation with missing features from patch.

---

## Detailed Comparison

### 1. Schema Features

#### Patch Proposes (Pydantic BaseModel)
```python
class RunArtifact(BaseModel):
    run_id: str
    created_at_utc: datetime
    mode: str
    tool_id: str
    status: Literal["OK", "BLOCKED", "ERROR"]
    request_summary: Dict[str, Any]          # ← MISSING
    feasibility: Dict[str, Any]
    decision: RunDecision                     # ← MISSING
    hashes: Hashes
    outputs: RunOutputs                       # ← MISSING
    advisory_inputs: List[AdvisoryInputRef]   # ← MISSING
    explanation_status: Literal[...]          # ← MISSING
    explanation_summary: Optional[str]        # ← MISSING
    meta: Dict[str, Any]                      # ← MISSING
```

#### Existing Has (Dataclass)
```python
@dataclass
class RunArtifact:
    run_id: str
    created_at_utc: str
    workflow_session_id: Optional[str]        # ← EXTRA
    tool_id: Optional[str]
    material_id: Optional[str]                # ← EXTRA
    machine_id: Optional[str]                 # ← EXTRA
    workflow_mode: Optional[str]              # ← EXTRA
    toolchain_id: Optional[str]               # ← EXTRA
    post_processor_id: Optional[str]          # ← EXTRA
    geometry_ref: Optional[str]               # ← EXTRA
    geometry_hash: Optional[str]              # ← EXTRA
    event_type: str
    status: RunStatus
    feasibility: Optional[Dict[str, Any]]
    request_hash: Optional[str]
    toolpaths_hash: Optional[str]
    gcode_hash: Optional[str]
    attachments: Optional[List[RunAttachment]]  # ← EXTRA
    parent_run_id: Optional[str]              # ← EXTRA
    drift_detected: Optional[bool]            # ← EXTRA
    drift_summary: Optional[Dict[str, Any]]   # ← EXTRA
    gate_policy_id: Optional[str]             # ← EXTRA
    gate_decision: Optional[str]              # ← EXTRA
    engine_version: Optional[str]             # ← EXTRA
    toolchain_version: Optional[str]          # ← EXTRA
    config_fingerprint: Optional[str]         # ← EXTRA
    notes: Optional[str]
    errors: Optional[List[str]]
```

### 2. Feature Matrix

| Feature | Patch | Existing | Winner |
|---------|:-----:|:--------:|:------:|
| **Schemas** |
| Basic run fields | ✅ | ✅ | Tie |
| Workflow linkage | ❌ | ✅ | Existing |
| Provenance/lineage | ❌ | ✅ | Existing |
| Gate policies | ❌ | ✅ | Existing |
| Drift detection | ❌ | ✅ | Existing |
| Advisory inputs | ✅ | ❌ | Patch |
| Explanation status | ✅ | ❌ | Patch |
| Request summary | ✅ | ❌ | Patch |
| Meta field | ✅ | ❌ | Patch |
| Decision model | ✅ | ❌ | Patch |
| Outputs model | ✅ | ❌ | Patch |
| **Hashing** |
| SHA256 of object | ✅ | ✅ | Tie |
| SHA256 of text | ✅ | ✅ | Tie |
| SHA256 of bytes | ❌ | ✅ | Existing |
| SHA256 of file | ❌ | ✅ | Existing |
| Null handling | ✅ | ❌ | Patch |
| Request summarization | ✅ | ❌ | Patch |
| **Store** |
| Thread safety | ❌ | ✅ | Existing |
| Atomic writes | ✅ | ❌ | Patch |
| Filtering | ❌ | ✅ | Existing |
| Patch operations | ✅ | ❌ | Patch |
| **Router** |
| Create run | ✅ | ❌ | Patch |
| Get run | ✅ | ✅ | Tie |
| List runs | ❌ | ✅ | Existing |
| Patch meta | ✅ | ❌ | Patch |
| Diff runs | ❌ | ✅ | Existing |
| Attachments | ❌ | ✅ | Existing |
| Verification | ❌ | ✅ | Existing |

---

## Missing Features to Add

### Priority 1: Schema Extensions

Add to `services/api/app/rmos/runs/schemas.py`:

```python
from typing import List, Dict, Any, Optional, Literal
from dataclasses import dataclass, field

# NEW: Decision model
@dataclass
class RunDecision:
    """Structured decision data from feasibility evaluation."""
    risk_level: Optional[str] = None  # GREEN/YELLOW/RED/ERROR
    score: Optional[float] = None
    block_reason: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

# NEW: Advisory input reference
@dataclass
class AdvisoryInputRef:
    """Reference to an attached advisory/explanation."""
    advisory_id: str
    kind: str = "unknown"  # "explanation", "advisory", "note"
    created_at_utc: str = ""
    request_id: Optional[str] = None
    engine_id: Optional[str] = None
    engine_version: Optional[str] = None

# ADD to RunArtifact:
@dataclass
class RunArtifact:
    # ... existing fields ...

    # NEW fields from patch
    mode: Optional[str] = None                              # Operation mode
    request_summary: Optional[Dict[str, Any]] = None        # Redacted request
    decision: Optional[RunDecision] = None                  # Structured decision
    advisory_inputs: Optional[List[AdvisoryInputRef]] = None  # Explanations
    explanation_status: str = "NONE"                        # NONE/PENDING/READY/ERROR
    explanation_summary: Optional[str] = None               # Brief explanation
    meta: Optional[Dict[str, Any]] = None                   # Free-form metadata
```

### Priority 2: Hashing Extensions

Add to `services/api/app/rmos/runs/hashing.py`:

```python
from typing import Any, Dict, Optional

def sha256_of_text_safe(text: Optional[str]) -> Optional[str]:
    """SHA256 with null handling - returns None if input is None."""
    if text is None:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def summarize_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produce redaction-friendly request summary for audit logging.

    Limits key exposure and extracts key identifiers.
    """
    if not isinstance(request, dict):
        return {"type": str(type(request)), "note": "non-dict request"}

    keys = list(request.keys())
    summary: Dict[str, Any] = {"keys": keys[:50]}

    design = request.get("design")
    ctx = request.get("context") or request.get("ctx")

    if isinstance(design, dict):
        summary["design_keys"] = list(design.keys())[:50]
    if isinstance(ctx, dict):
        summary["context_keys"] = list(ctx.keys())[:50]
        if "model_id" in ctx:
            summary["model_id"] = ctx.get("model_id")
        if "feasibility_engine_id" in ctx:
            summary["feasibility_engine_id"] = ctx.get("feasibility_engine_id")

    return summary
```

### Priority 3: Store Extensions

Add to `services/api/app/rmos/runs/store.py`:

```python
def patch_run_meta(run_id: str, meta_updates: Dict[str, Any]) -> RunArtifact:
    """
    Update the meta field of a run artifact.

    Thread-safe patch operation.
    """
    with _LOCK:
        data = _read_all()
        if run_id not in data:
            raise KeyError(f"Run {run_id} not found")

        raw = data[run_id]
        if raw.get("meta") is None:
            raw["meta"] = {}
        raw["meta"].update(meta_updates)

        _write_all(data)

    return _deserialize_artifact(raw)
```

### Priority 4: Router Extensions

Add to `services/api/app/rmos/runs/api_runs.py`:

```python
from pydantic import BaseModel, Field
from .store import persist_run, create_run_id, patch_run_meta

class RunCreateRequest(BaseModel):
    """Request body for creating a new run."""
    mode: str = "unknown"
    tool_id: str = "unknown"
    status: str = "OK"
    event_type: str = "unknown"
    request_summary: Dict[str, Any] = Field(default_factory=dict)
    feasibility: Dict[str, Any] = Field(default_factory=dict)
    meta: Dict[str, Any] = Field(default_factory=dict)


class PatchMetaRequest(BaseModel):
    """Request body for patching run metadata."""
    meta_updates: Dict[str, Any] = Field(default_factory=dict)


@router.post("", response_model=Dict[str, Any], summary="Create a new run artifact.")
def create_run_endpoint(req: RunCreateRequest, request: Request):
    """Create a new run artifact."""
    from datetime import datetime, timezone

    run_id = create_run_id()
    req_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id")

    artifact = RunArtifact(
        run_id=run_id,
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        event_type=req.event_type,
        status=req.status,
        tool_id=req.tool_id,
        mode=req.mode,
        request_summary=req.request_summary,
        feasibility=req.feasibility,
        meta={**req.meta, **({"request_id": req_id} if req_id else {})},
    )

    persist_run(artifact)
    return {"run_id": run_id, "status": "created"}


@router.patch("/{run_id}/meta", response_model=Dict[str, Any], summary="Patch run metadata.")
def patch_meta_endpoint(run_id: str, req: PatchMetaRequest):
    """Update the meta field of a run artifact."""
    try:
        artifact = patch_run_meta(run_id, req.meta_updates)
        return {"run_id": run_id, "meta": artifact.meta, "status": "updated"}
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
```

---

## Implementation Plan

### Phase 1: Schema Extensions (Low Risk)
1. Add `RunDecision` dataclass
2. Add `AdvisoryInputRef` dataclass
3. Extend `RunArtifact` with new optional fields
4. Update serialization/deserialization to handle new fields

### Phase 2: Hashing Extensions (Low Risk)
1. Add `sha256_of_text_safe()` with null handling
2. Add `summarize_request()` function
3. Update `__init__.py` exports

### Phase 3: Store Extensions (Medium Risk)
1. Add `patch_run_meta()` function
2. Ensure thread safety
3. Add backward compatibility for missing fields

### Phase 4: Router Extensions (Medium Risk)
1. Add `POST /runs` endpoint for run creation
2. Add `PATCH /runs/{id}/meta` endpoint
3. Update response models
4. Test with existing data

---

## Conclusion

**Do NOT replace** the existing implementation. Instead, **extend** it with the valuable features from the patch:

| Add From Patch | Keep From Existing |
|----------------|-------------------|
| Advisory inputs | Thread safety |
| Explanation status | Attachment system |
| Request summary | Diff capability |
| Meta field | Filter queries |
| Decision model | Verification |
| Create endpoint | Provenance tracking |
| Patch meta endpoint | Gate policies |

This approach preserves the battle-tested existing code while adding the new advisory/explanation capabilities needed for the next phase.
