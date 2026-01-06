#!/usr/bin/env python3
"""
RMOS Router - Rosette Manufacturing Operating System API Endpoints

Hybrid Architecture:
- Producer Plane (Vision): Creates assets, writes to CAS, returns sha256
- Ledger Plane (RMOS): Attaches sha256 to runs, governs review/promote

Key Contracts:
- Identity: advisory_id always equals sha256
- State: reviewed/rejected/promoted live ONLY in RMOS run ledger
- Storage: advisory_inputs[] embedded on runs (not separate file)
"""

from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
import uuid
import json
import hashlib
import pathlib

router = APIRouter(prefix="/api", tags=["RMOS"])

# Storage paths (local JSON file storage for development)
STORAGE_DIR = pathlib.Path(__file__).parent / "storage" / "rmos"
PATTERNS_FILE = STORAGE_DIR / "patterns.json"
JOBLOG_FILE = STORAGE_DIR / "joblog.json"
RUNS_FILE = STORAGE_DIR / "runs.json"
CAS_DIR = STORAGE_DIR / "cas"  # Content-Addressed Storage

# Ensure directories exist
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
CAS_DIR.mkdir(parents=True, exist_ok=True)

# ==================== Advisory Status (Server-Normalized) ====================

AdvisoryStatus = Literal["NEW", "REVIEWED", "REJECTED", "PROMOTED"]


def _normalize_status(rejected: bool, current_status: str, has_review_fields: bool) -> str:
    """
    Server-normalize status based on review state.

    Rules:
    - If rejected=True → force status="REJECTED"
    - If rejected=False and review fields present → force status="REVIEWED" (unless PROMOTED)
    - If already PROMOTED → status remains PROMOTED
    """
    if current_status == "PROMOTED":
        return "PROMOTED"  # Never demote
    if rejected:
        return "REJECTED"
    if has_review_fields and current_status not in ("PROMOTED",):
        return "REVIEWED"
    return current_status


# ==================== CAS (Content-Addressed Storage) ====================

def _cas_path(sha256: str, ext: str = "") -> pathlib.Path:
    """Get CAS storage path using 2-level sharding."""
    s = sha256.lower()
    return CAS_DIR / s[:2] / s[2:4] / f"{s}{ext}"


def _cas_exists(sha256: str) -> bool:
    """Check if blob exists in CAS."""
    for ext in ["", ".png", ".jpg", ".json", ".txt"]:
        if _cas_path(sha256, ext).exists():
            return True
    return False


def _cas_get(sha256: str) -> Optional[bytes]:
    """Get blob from CAS."""
    for ext in ["", ".png", ".jpg", ".json", ".txt"]:
        path = _cas_path(sha256, ext)
        if path.exists():
            return path.read_bytes()
    return None


def _cas_put(data: bytes, ext: str = "") -> str:
    """Store blob in CAS, return sha256."""
    sha256 = hashlib.sha256(data).hexdigest()
    path = _cas_path(sha256, ext)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return sha256


# ==================== Models ====================

class RosetteRingBand(BaseModel):
    """Ring band configuration for rosette patterns."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    index: int = Field(..., description="Ring index (0 = outermost)")
    radius_mm: float = Field(..., gt=0)
    width_mm: float = Field(..., gt=0)
    color_hint: Optional[str] = None
    strip_family_id: str
    slice_angle_deg: float = Field(default=45.0)
    tile_length_override_mm: Optional[float] = None


class RosettePattern(BaseModel):
    """Rosette pattern configuration."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    center_x_mm: float = Field(default=0.0)
    center_y_mm: float = Field(default=0.0)
    ring_bands: List[RosetteRingBand] = Field(default_factory=list)
    default_slice_thickness_mm: float = Field(default=2.0)
    default_passes: int = Field(default=2)
    default_workholding: str = Field(default="vacuum")
    default_tool_id: Optional[str] = None


class RosettePatternCreate(BaseModel):
    """Request model for creating a rosette pattern."""
    name: str
    center_x_mm: float = 0.0
    center_y_mm: float = 0.0
    ring_bands: List[Dict[str, Any]] = Field(default_factory=list)
    default_slice_thickness_mm: float = 2.0
    default_passes: int = 2
    default_workholding: str = "vacuum"
    default_tool_id: Optional[str] = None


class RosettePatternUpdate(BaseModel):
    """Request model for updating a rosette pattern."""
    name: Optional[str] = None
    center_x_mm: Optional[float] = None
    center_y_mm: Optional[float] = None
    ring_bands: Optional[List[Dict[str, Any]]] = None
    default_slice_thickness_mm: Optional[float] = None
    default_passes: Optional[int] = None
    default_workholding: Optional[str] = None
    default_tool_id: Optional[str] = None


class JobLogEntry(BaseModel):
    """Base job log entry."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    job_type: str
    pipeline_id: Optional[str] = None
    node_id: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None


class ManufacturingPlanRequest(BaseModel):
    """Request for generating a manufacturing plan."""
    pattern_id: str
    guitars: int = Field(default=1, ge=1)
    notes: Optional[str] = None


# ==================== Storage Helpers ====================

def _load_patterns() -> List[dict]:
    """Load patterns from storage."""
    if PATTERNS_FILE.exists():
        try:
            return json.loads(PATTERNS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError):
            pass
    return []


def _save_patterns(patterns: List[dict]) -> None:
    """Save patterns to storage."""
    PATTERNS_FILE.write_text(json.dumps(patterns, indent=2), encoding="utf-8")


def _load_joblog() -> List[dict]:
    """Load job log from storage."""
    if JOBLOG_FILE.exists():
        try:
            return json.loads(JOBLOG_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError):
            pass
    return []


def _save_joblog(entries: List[dict]) -> None:
    """Save job log to storage."""
    JOBLOG_FILE.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def _load_runs() -> List[dict]:
    """Load runs from storage."""
    if RUNS_FILE.exists():
        try:
            return json.loads(RUNS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError):
            pass
    return []


def _save_runs(runs: List[dict]) -> None:
    """Save runs to storage."""
    RUNS_FILE.write_text(json.dumps(runs, indent=2), encoding="utf-8")


def _log_event(job_type: str, extra: dict) -> None:
    """Log an event to the job log."""
    entries = _load_joblog()
    entry = {
        "id": str(uuid.uuid4()),
        "created_at": datetime.utcnow().isoformat(),
        "job_type": job_type,
        "extra": extra,
    }
    entries.append(entry)
    _save_joblog(entries)


# ==================== Pattern Endpoints ====================

@router.get("/rosette-patterns", response_model=List[RosettePattern])
async def list_patterns():
    """List all rosette patterns."""
    return _load_patterns()


@router.post("/rosette-patterns", response_model=RosettePattern)
async def create_pattern(data: RosettePatternCreate):
    """Create a new rosette pattern."""
    patterns = _load_patterns()

    ring_bands = []
    for i, rb in enumerate(data.ring_bands):
        ring_bands.append({
            "id": rb.get("id", str(uuid.uuid4())),
            "index": rb.get("index", i),
            "radius_mm": rb.get("radius_mm", 50.0 + i * 5),
            "width_mm": rb.get("width_mm", 3.0),
            "color_hint": rb.get("color_hint"),
            "strip_family_id": rb.get("strip_family_id", "default"),
            "slice_angle_deg": rb.get("slice_angle_deg", 45.0),
            "tile_length_override_mm": rb.get("tile_length_override_mm"),
        })

    new_pattern = {
        "id": str(uuid.uuid4()),
        "name": data.name,
        "center_x_mm": data.center_x_mm,
        "center_y_mm": data.center_y_mm,
        "ring_bands": ring_bands,
        "default_slice_thickness_mm": data.default_slice_thickness_mm,
        "default_passes": data.default_passes,
        "default_workholding": data.default_workholding,
        "default_tool_id": data.default_tool_id,
    }

    patterns.append(new_pattern)
    _save_patterns(patterns)
    _log_event("pattern_created", {"pattern_id": new_pattern["id"], "name": new_pattern["name"]})

    return new_pattern


@router.get("/rosette-patterns/{pattern_id}", response_model=RosettePattern)
async def get_pattern(pattern_id: str):
    """Get a specific rosette pattern by ID."""
    for p in _load_patterns():
        if p.get("id") == pattern_id:
            return p
    raise HTTPException(status_code=404, detail=f"Pattern not found: {pattern_id}")


@router.put("/rosette-patterns/{pattern_id}", response_model=RosettePattern)
async def update_pattern(pattern_id: str, data: RosettePatternUpdate):
    """Update an existing rosette pattern."""
    patterns = _load_patterns()

    for i, p in enumerate(patterns):
        if p.get("id") == pattern_id:
            if data.name is not None:
                p["name"] = data.name
            if data.center_x_mm is not None:
                p["center_x_mm"] = data.center_x_mm
            if data.center_y_mm is not None:
                p["center_y_mm"] = data.center_y_mm
            if data.ring_bands is not None:
                p["ring_bands"] = data.ring_bands
            if data.default_slice_thickness_mm is not None:
                p["default_slice_thickness_mm"] = data.default_slice_thickness_mm
            if data.default_passes is not None:
                p["default_passes"] = data.default_passes
            if data.default_workholding is not None:
                p["default_workholding"] = data.default_workholding
            if data.default_tool_id is not None:
                p["default_tool_id"] = data.default_tool_id

            patterns[i] = p
            _save_patterns(patterns)
            _log_event("pattern_updated", {"pattern_id": pattern_id})
            return p

    raise HTTPException(status_code=404, detail=f"Pattern not found: {pattern_id}")


@router.delete("/rosette-patterns/{pattern_id}")
async def delete_pattern(pattern_id: str):
    """Delete a rosette pattern by ID."""
    patterns = _load_patterns()

    for i, p in enumerate(patterns):
        if p.get("id") == pattern_id:
            patterns.pop(i)
            _save_patterns(patterns)
            _log_event("pattern_deleted", {"pattern_id": pattern_id})
            return {"success": True, "deleted_id": pattern_id}

    raise HTTPException(status_code=404, detail=f"Pattern not found: {pattern_id}")


# ==================== Job Log Endpoints ====================

@router.get("/joblog", response_model=List[JobLogEntry])
async def list_joblog():
    """List all job log entries, newest first."""
    entries = _load_joblog()
    entries.sort(key=lambda e: e.get("created_at", ""), reverse=True)
    return entries


@router.post("/joblog", response_model=JobLogEntry)
async def create_joblog_entry(data: JobLogEntry):
    """Create a new job log entry."""
    entries = _load_joblog()
    entry = data.dict()
    if not entry.get("id"):
        entry["id"] = str(uuid.uuid4())
    if not entry.get("created_at"):
        entry["created_at"] = datetime.utcnow().isoformat()
    entries.append(entry)
    _save_joblog(entries)
    return entry


# ==================== Manufacturing Plan Endpoints ====================

@router.post("/rosette/manufacturing-plan")
async def generate_manufacturing_plan(data: ManufacturingPlanRequest):
    """Generate a manufacturing plan for a rosette pattern."""
    patterns = _load_patterns()
    pattern = next((p for p in patterns if p.get("id") == data.pattern_id), None)

    if not pattern:
        raise HTTPException(status_code=404, detail=f"Pattern not found: {data.pattern_id}")

    ring_requirements = []
    strip_plans = {}

    for ring in pattern.get("ring_bands", []):
        radius = ring.get("radius_mm", 50.0)
        width = ring.get("width_mm", 3.0)
        circumference = 2 * 3.14159 * radius
        tile_length = ring.get("tile_length_override_mm") or 10.0
        tiles_per_guitar = int(circumference / tile_length) + 1

        req = {
            "ring_index": ring.get("index", 0),
            "strip_family_id": ring.get("strip_family_id", "default"),
            "radius_mm": radius,
            "width_mm": width,
            "circumference_mm": round(circumference, 2),
            "tiles_per_guitar": tiles_per_guitar,
            "total_tiles": tiles_per_guitar * data.guitars,
            "tile_length_mm": tile_length,
        }
        ring_requirements.append(req)

        fam_id = req["strip_family_id"]
        if fam_id not in strip_plans:
            strip_plans[fam_id] = {
                "strip_family_id": fam_id,
                "color_hint": ring.get("color_hint"),
                "slice_angle_deg": ring.get("slice_angle_deg", 45.0),
                "tile_length_mm": tile_length,
                "total_tiles_needed": 0,
                "ring_indices": [],
            }
        strip_plans[fam_id]["total_tiles_needed"] += req["total_tiles"]
        strip_plans[fam_id]["ring_indices"].append(req["ring_index"])

    for fam_id, plan in strip_plans.items():
        tiles = plan["total_tiles_needed"]
        tile_len = plan["tile_length_mm"]
        plan["tiles_per_meter"] = int(1000 / tile_len)
        plan["total_strip_length_m"] = round(tiles * tile_len / 1000, 3)
        plan["suggested_stick_length_mm"] = 300
        plan["sticks_needed"] = max(1, int((tiles * tile_len) / 300) + 1)

    _log_event("rosette_plan", {
        "plan_pattern_id": data.pattern_id,
        "plan_guitars": data.guitars,
        "plan_total_tiles": sum(r["total_tiles"] for r in ring_requirements),
    })

    return {
        "pattern": pattern,
        "guitars": data.guitars,
        "ring_requirements": ring_requirements,
        "strip_plans": list(strip_plans.values()),
        "notes": data.notes,
    }


# ==================== Live Monitor Endpoints ====================

@router.get("/rmos/live-monitor/{job_id}/drilldown")
async def get_live_monitor_drilldown(job_id: str):
    """Get live monitoring drilldown data for a job."""
    return {
        "job_id": job_id,
        "status": "idle",
        "metrics": {"progress_pct": 0, "elapsed_s": 0, "eta_s": None},
        "events": [],
        "alerts": [],
    }


# ==============================================================================
# LEDGER PLANE: RMOS Runs (Authoritative)
# ==============================================================================

class RunCreate(BaseModel):
    """Request model for creating a run."""
    event_type: str = "rosette_manufacturing"
    workflow_session_id: Optional[str] = None
    tool_id: Optional[str] = None
    material_id: Optional[str] = None
    machine_id: Optional[str] = None
    notes: Optional[str] = None


class AdvisoryAttachRequest(BaseModel):
    """
    Request to attach an advisory (sha256) to a run.

    Identity Contract: advisory_id == sha256
    """
    advisory_id: str  # This IS the sha256
    kind: str = "advisory"
    meta: Optional[Dict[str, Any]] = None


class AdvisoryReviewRequest(BaseModel):
    """
    Unified review request - handles approve/reject/rate/note.

    Server normalizes status based on fields:
    - rejected=True → status="REJECTED"
    - rejected=False + review fields → status="REVIEWED"
    - Already PROMOTED → stays PROMOTED
    """
    rejected: Optional[bool] = None
    rejection_reason_code: Optional[str] = None
    rejection_reason_detail: Optional[str] = None
    rejection_operator_note: Optional[str] = None
    rating: Optional[int] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class BulkReviewRequest(BaseModel):
    """Bulk review multiple advisory variants."""
    advisory_ids: List[str]
    rejected: Optional[bool] = None
    rejection_reason_code: Optional[str] = None
    rating: Optional[int] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class PromoteRequest(BaseModel):
    """Request to promote an advisory variant."""
    label: Optional[str] = None
    note: Optional[str] = None


@router.get("/rmos/runs")
async def list_runs(
    limit: int = 50,
    event_type: Optional[str] = None,
    status: Optional[str] = None,
):
    """List RMOS runs with optional filtering."""
    runs = _load_runs()

    if event_type:
        runs = [r for r in runs if r.get("event_type") == event_type]
    if status:
        runs = [r for r in runs if r.get("status") == status]

    runs.sort(key=lambda r: r.get("created_at_utc", ""), reverse=True)
    return runs[:limit]


@router.post("/rmos/runs")
async def create_run(data: RunCreate):
    """Create a new RMOS run."""
    runs = _load_runs()

    run = {
        "run_id": str(uuid.uuid4()),
        "created_at_utc": datetime.utcnow().isoformat(),
        "event_type": data.event_type,
        "status": "ACTIVE",
        "workflow_session_id": data.workflow_session_id,
        "tool_id": data.tool_id,
        "material_id": data.material_id,
        "machine_id": data.machine_id,
        "notes": data.notes,
        "attachments": [],
        "advisory_inputs": [],  # Embedded advisory state
    }

    runs.append(run)
    _save_runs(runs)
    _log_event("run_created", {"run_id": run["run_id"]})

    return run


@router.get("/rmos/runs/{run_id}")
async def get_run(run_id: str):
    """Get full details of a single run."""
    for r in _load_runs():
        if r.get("run_id") == run_id:
            return r
    raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")


@router.get("/rmos/runs/{run_id}/attachments")
async def get_run_attachments(run_id: str):
    """List attachments for a run."""
    for r in _load_runs():
        if r.get("run_id") == run_id:
            attachments = r.get("attachments", [])
            return {"run_id": run_id, "count": len(attachments), "attachments": attachments}
    raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")


# ==============================================================================
# CANONICAL ATTACH ENDPOINT (replaces /attach-image)
# ==============================================================================

@router.post("/rmos/runs/{run_id}/advisory/attach")
async def attach_advisory_to_run(run_id: str, data: AdvisoryAttachRequest):
    """
    Attach an advisory (sha256) to a run.

    This is the CANONICAL attach endpoint.

    Pre-condition: CAS blob must exist for advisory_id (sha256).
    Creates an AdvisoryInputRef embedded on the run.
    """
    runs = _load_runs()
    run = None
    run_idx = -1

    for i, r in enumerate(runs):
        if r.get("run_id") == run_id:
            run = r
            run_idx = i
            break

    if not run:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    # Verify CAS blob exists
    if not _cas_exists(data.advisory_id):
        raise HTTPException(
            status_code=409,
            detail={
                "error": "CAS_MISSING_BLOB",
                "advisory_id": data.advisory_id,
                "message": "Blob not found in CAS. Generate or upload first.",
            }
        )

    # Check if already attached
    existing = next(
        (a for a in run.get("advisory_inputs", []) if a.get("advisory_id") == data.advisory_id),
        None
    )
    if existing:
        return {
            "success": True,
            "run_id": run_id,
            "advisory_id": data.advisory_id,
            "already_attached": True,
            "message": "Advisory already attached to this run.",
        }

    # Create AdvisoryInputRef (embedded on run)
    advisory_ref = {
        "advisory_id": data.advisory_id,  # sha256 is the identity
        "kind": data.kind,
        "created_at_utc": datetime.utcnow().isoformat(),
        "status": "NEW",
        "rejected": False,
        "rating": None,
        "notes": None,
        "promoted_candidate_id": None,
        "meta": data.meta or {},
    }

    if "advisory_inputs" not in run:
        run["advisory_inputs"] = []
    run["advisory_inputs"].append(advisory_ref)

    # Also add to attachments for backward compatibility
    attachment = {
        "sha256": data.advisory_id,
        "kind": data.kind,
        "mime": "image/png",
        "filename": f"{data.advisory_id[:12]}.png",
        "size_bytes": 0,
        "created_at_utc": datetime.utcnow().isoformat(),
    }
    if "attachments" not in run:
        run["attachments"] = []
    run["attachments"].append(attachment)

    runs[run_idx] = run
    _save_runs(runs)

    _log_event("advisory_attached", {"run_id": run_id, "advisory_id": data.advisory_id})

    return {
        "success": True,
        "run_id": run_id,
        "advisory_id": data.advisory_id,
        "status": "NEW",
        "message": "Advisory attached. Ready for review.",
    }


# ==============================================================================
# CANONICAL VARIANTS ENDPOINT
# ==============================================================================

@router.get("/rmos/runs/{run_id}/advisory/variants")
async def list_advisory_variants(run_id: str):
    """
    List advisory variants for a run.

    Returns advisory_inputs[] embedded on the run.
    """
    for r in _load_runs():
        if r.get("run_id") == run_id:
            variants = r.get("advisory_inputs", [])
            return {"items": variants, "count": len(variants)}

    raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")


# ==============================================================================
# CANONICAL REVIEW ENDPOINT (replaces /reject)
# ==============================================================================

@router.post("/rmos/runs/{run_id}/advisory/{advisory_id}/review")
async def review_advisory_variant(run_id: str, advisory_id: str, data: AdvisoryReviewRequest):
    """
    Review an advisory variant (approve/reject/rate/note).

    Server normalizes status:
    - rejected=True → status="REJECTED"
    - rejected=False + review → status="REVIEWED"
    - Already PROMOTED → stays PROMOTED
    """
    runs = _load_runs()
    run = None
    run_idx = -1

    for i, r in enumerate(runs):
        if r.get("run_id") == run_id:
            run = r
            run_idx = i
            break

    if not run:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    # Find advisory in run's advisory_inputs
    advisory = None
    advisory_idx = -1
    for i, a in enumerate(run.get("advisory_inputs", [])):
        if a.get("advisory_id") == advisory_id:
            advisory = a
            advisory_idx = i
            break

    if advisory is None:
        raise HTTPException(status_code=404, detail=f"Advisory not found on run: {advisory_id}")

    # Apply review fields
    has_review_fields = False

    if data.rejected is not None:
        advisory["rejected"] = data.rejected
        if data.rejected:
            advisory["rejected_at_utc"] = datetime.utcnow().isoformat()
        has_review_fields = True

    if data.rejection_reason_code is not None:
        advisory["rejection_reason_code"] = data.rejection_reason_code
        has_review_fields = True

    if data.rejection_reason_detail is not None:
        advisory["rejection_reason_detail"] = data.rejection_reason_detail
        has_review_fields = True

    if data.rejection_operator_note is not None:
        advisory["rejection_operator_note"] = data.rejection_operator_note
        has_review_fields = True

    if data.rating is not None:
        advisory["rating"] = data.rating
        has_review_fields = True

    if data.notes is not None:
        advisory["notes"] = data.notes
        has_review_fields = True

    # Server-normalize status
    current_status = advisory.get("status", "NEW")
    rejected = advisory.get("rejected", False)
    advisory["status"] = _normalize_status(rejected, current_status, has_review_fields)
    advisory["reviewed_at_utc"] = datetime.utcnow().isoformat()

    run["advisory_inputs"][advisory_idx] = advisory
    runs[run_idx] = run
    _save_runs(runs)

    request_id = str(uuid.uuid4())
    _log_event("advisory_reviewed", {
        "run_id": run_id,
        "advisory_id": advisory_id,
        "status": advisory["status"],
        "rejected": advisory.get("rejected"),
        "request_id": request_id,
    })

    return {
        "review_record": advisory,
        "request_id": request_id,
    }


# ==============================================================================
# BULK REVIEW ENDPOINT
# ==============================================================================

@router.post("/rmos/runs/{run_id}/advisory/bulk-review")
async def bulk_review_advisory_variants(run_id: str, data: BulkReviewRequest):
    """
    Bulk review multiple advisory variants.
    """
    runs = _load_runs()
    run = None
    run_idx = -1

    for i, r in enumerate(runs):
        if r.get("run_id") == run_id:
            run = r
            run_idx = i
            break

    if not run:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    updated_count = 0
    updated_ids = []

    for advisory_id in data.advisory_ids:
        for i, a in enumerate(run.get("advisory_inputs", [])):
            if a.get("advisory_id") == advisory_id:
                has_review_fields = False

                if data.rejected is not None:
                    a["rejected"] = data.rejected
                    if data.rejected:
                        a["rejected_at_utc"] = datetime.utcnow().isoformat()
                    has_review_fields = True

                if data.rejection_reason_code is not None:
                    a["rejection_reason_code"] = data.rejection_reason_code
                    has_review_fields = True

                if data.rating is not None:
                    a["rating"] = data.rating
                    has_review_fields = True

                if data.notes is not None:
                    a["notes"] = data.notes
                    has_review_fields = True

                current_status = a.get("status", "NEW")
                rejected = a.get("rejected", False)
                a["status"] = _normalize_status(rejected, current_status, has_review_fields)
                a["reviewed_at_utc"] = datetime.utcnow().isoformat()

                run["advisory_inputs"][i] = a
                updated_count += 1
                updated_ids.append(advisory_id)
                break

    runs[run_idx] = run
    _save_runs(runs)

    request_id = str(uuid.uuid4())
    _log_event("advisory_bulk_reviewed", {
        "run_id": run_id,
        "updated_count": updated_count,
        "request_id": request_id,
    })

    return {
        "updated_count": updated_count,
        "advisory_ids": updated_ids,
        "request_id": request_id,
    }


# ==============================================================================
# CANONICAL PROMOTE ENDPOINT
# ==============================================================================

@router.post("/rmos/runs/{run_id}/advisory/{advisory_id}/promote")
async def promote_advisory_variant(run_id: str, advisory_id: str, data: PromoteRequest = None):
    """
    Promote an advisory variant to manufacturing candidate.

    Pre-conditions:
    - Advisory must exist on run
    - Advisory must not be rejected
    - Advisory should be reviewed (warning if not)
    """
    runs = _load_runs()
    run = None
    run_idx = -1

    for i, r in enumerate(runs):
        if r.get("run_id") == run_id:
            run = r
            run_idx = i
            break

    if not run:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    advisory = None
    advisory_idx = -1
    for i, a in enumerate(run.get("advisory_inputs", [])):
        if a.get("advisory_id") == advisory_id:
            advisory = a
            advisory_idx = i
            break

    if advisory is None:
        raise HTTPException(status_code=404, detail=f"Advisory not found on run: {advisory_id}")

    # Check if rejected
    if advisory.get("rejected"):
        raise HTTPException(
            status_code=409,
            detail={"error": "PROMOTE_BLOCKED", "reason": "REJECTED", "message": "Cannot promote rejected advisory."}
        )

    # Check if not reviewed (warning, not blocking)
    if advisory.get("status") == "NEW":
        # Allow but log warning
        _log_event("promote_warning", {"advisory_id": advisory_id, "reason": "NOT_REVIEWED"})

    # Create manufacturing candidate
    candidate_id = str(uuid.uuid4())

    advisory["status"] = "PROMOTED"
    advisory["promoted_candidate_id"] = candidate_id
    advisory["promoted_at_utc"] = datetime.utcnow().isoformat()
    if data:
        advisory["promote_label"] = data.label
        advisory["promote_note"] = data.note

    run["advisory_inputs"][advisory_idx] = advisory
    runs[run_idx] = run
    _save_runs(runs)

    _log_event("advisory_promoted", {
        "run_id": run_id,
        "advisory_id": advisory_id,
        "candidate_id": candidate_id,
    })

    return {
        "promoted": True,
        "run_id": run_id,
        "advisory_id": advisory_id,
        "promoted_candidate_id": candidate_id,
    }


# ==============================================================================
# MANUFACTURING CANDIDATES (Projection)
# ==============================================================================

@router.get("/rmos/runs/{run_id}/manufacturing/candidates")
async def list_manufacturing_candidates(run_id: str):
    """
    List manufacturing candidates for a run.

    This is a PROJECTION of promoted advisory variants.
    """
    for r in _load_runs():
        if r.get("run_id") == run_id:
            candidates = [
                {
                    "candidate_id": a.get("promoted_candidate_id"),
                    "advisory_id": a.get("advisory_id"),
                    "created_at_utc": a.get("promoted_at_utc"),
                    "risk_level": "GREEN",
                    "decision": None,
                    "status": "PROPOSED",
                }
                for a in r.get("advisory_inputs", [])
                if a.get("status") == "PROMOTED"
            ]
            return {"items": candidates, "count": len(candidates)}

    raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")


# ==============================================================================
# BLOB ACCESS (Governed by run linkage)
# ==============================================================================

@router.get("/rmos/runs/{run_id}/advisory/blobs/{sha256}/download")
async def download_advisory_blob(run_id: str, sha256: str):
    """
    Download an advisory blob.

    Enforces run linkage - blob must be attached to this run.
    """
    for r in _load_runs():
        if r.get("run_id") == run_id:
            # Verify blob is attached to this run
            attached = any(
                a.get("advisory_id") == sha256 or a.get("sha256") == sha256
                for a in r.get("advisory_inputs", []) + r.get("attachments", [])
            )
            if not attached:
                raise HTTPException(status_code=403, detail="Blob not attached to this run")

            data = _cas_get(sha256)
            if data is None:
                raise HTTPException(status_code=404, detail="Blob not found in CAS")

            return Response(content=data, media_type="application/octet-stream")

    raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")


# ==============================================================================
# PRODUCER PLANE: Vision API (Stubs - Non-Authoritative)
# ==============================================================================

class VisionGenerateRequest(BaseModel):
    """Request model for generating AI images."""
    prompt: str
    num_images: int = 2
    quality: str = "standard"
    style: str = "product"
    provider: str = "auto"
    project_id: Optional[str] = None


@router.post("/vision/generate")
async def generate_vision_image(data: VisionGenerateRequest):
    """
    Generate AI images from a prompt.

    PRODUCER PLANE - Non-authoritative.
    Returns assets with sha256 identity (not advisory_id).

    Phase A: Stub implementation.
    Phase B: Wire to get_image_client("openai").
    """
    assets = []
    for i in range(data.num_images):
        # Generate deterministic mock sha256 for stub
        mock_content = f"{data.prompt}:{data.style}:{i}:{datetime.utcnow().isoformat()}"
        sha256 = hashlib.sha256(mock_content.encode()).hexdigest()

        # Store stub blob in CAS (so attach will work)
        stub_bytes = f"STUB_IMAGE:{sha256}".encode()
        _cas_put(stub_bytes, ".png")

        assets.append({
            "sha256": sha256,  # Identity
            "preview_url": f"/api/vision/preview/{sha256}",
            "prompt": data.prompt,
            "revised_prompt": f"Professional photograph of {data.prompt}, {data.style} lighting, high resolution",
            "provider": data.provider if data.provider != "auto" else "dall-e-3",
            "model": "dall-e-3",
            "quality": data.quality,
            "style": data.style,
            "size": "1024x1024",
            "created_at": datetime.utcnow().isoformat(),
            "cost_usd": 0.04 if data.quality == "standard" else 0.08,
        })

    _log_event("vision_generate", {
        "prompt": data.prompt,
        "num_images": data.num_images,
        "provider": data.provider,
    })

    return {
        "success": True,
        "assets": assets,
        "total_cost_usd": sum(a["cost_usd"] for a in assets),
    }


@router.post("/vision/prompt")
async def preview_vision_prompt(prompt: str = Query(...), style: str = "product"):
    """Preview the engineered prompt without generating images."""
    engineered = f"Professional photograph of {prompt}, {style} lighting, studio quality, high resolution"

    return {
        "original_prompt": prompt,
        "engineered_prompt": engineered,
        "positive_prompt": engineered,
        "negative_prompt": "blurry, low quality, distorted, amateur",
        "confidence": 0.85,
        "style": style,
    }


@router.get("/vision/providers")
async def list_vision_providers():
    """List available AI image generation providers."""
    return [
        {"id": "dall-e-3", "name": "DALL-E 3", "available": True, "cost_per_image": {"draft": 0.02, "standard": 0.04, "hd": 0.08}},
        {"id": "sdxl", "name": "Stable Diffusion XL", "available": True, "cost_per_image": {"draft": 0.002, "standard": 0.004, "hd": 0.008}},
        {"id": "guitar_lora", "name": "Guitar LoRA", "available": True, "cost_per_image": {"draft": 0.005, "standard": 0.01, "hd": 0.02}},
    ]


@router.get("/vision/preview/{sha256}")
async def get_vision_preview(sha256: str):
    """Get preview of a generated image (stub returns placeholder)."""
    data = _cas_get(sha256)
    if data is None:
        raise HTTPException(status_code=404, detail="Preview not found")
    return Response(content=data, media_type="image/png")


# ==================== Seed Data ====================

def _ensure_seed_data():
    """Ensure sample data exists for development."""
    patterns = _load_patterns()
    if not patterns:
        sample = {
            "id": str(uuid.uuid4()),
            "name": "Classic 3-Ring Rosette",
            "center_x_mm": 0.0,
            "center_y_mm": 0.0,
            "ring_bands": [
                {"id": str(uuid.uuid4()), "index": 0, "radius_mm": 52.0, "width_mm": 3.5, "color_hint": "#8B4513", "strip_family_id": "rosewood", "slice_angle_deg": 45.0},
                {"id": str(uuid.uuid4()), "index": 1, "radius_mm": 48.5, "width_mm": 2.0, "color_hint": "#F5F5DC", "strip_family_id": "maple", "slice_angle_deg": 45.0},
                {"id": str(uuid.uuid4()), "index": 2, "radius_mm": 46.5, "width_mm": 3.5, "color_hint": "#8B4513", "strip_family_id": "rosewood", "slice_angle_deg": 45.0},
            ],
            "default_slice_thickness_mm": 2.0,
            "default_passes": 2,
            "default_workholding": "vacuum",
            "default_tool_id": None,
        }
        _save_patterns([sample])


# Run seed on module load
_ensure_seed_data()
