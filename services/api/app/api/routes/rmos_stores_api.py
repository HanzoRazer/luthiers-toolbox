"""
RMOS Stores API Router (N8.6 + N8.7 + N10.0)

FastAPI endpoints for RMOS SQLite stores.
Provides REST API for patterns, joblogs, and strip families.
Includes migration dashboard for N8.7.
N10.0: Real-time WebSocket event broadcasting.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from pathlib import Path
import asyncio

from ...stores.rmos_stores import get_rmos_stores
from ...websocket.monitor import broadcast_job_event, broadcast_pattern_event, broadcast_material_event

router = APIRouter(prefix="/rmos/stores", tags=["RMOS Stores"])


# ========== Pydantic Models ==========

class PatternCreate(BaseModel):
    """Request body for creating a pattern."""
    name: str = Field(..., description="Pattern name")
    ring_count: int = Field(..., gt=0, description="Number of rings")
    geometry: Dict[str, Any] = Field(..., description="Pattern geometry")
    strip_family_id: Optional[str] = Field(None, description="Associated strip family ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class PatternUpdate(BaseModel):
    """Request body for updating a pattern."""
    name: Optional[str] = None
    ring_count: Optional[int] = Field(None, gt=0)
    geometry: Optional[Dict[str, Any]] = None
    strip_family_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class JobLogCreate(BaseModel):
    """Request body for creating a joblog."""
    job_type: str = Field(..., description="Job type (slice, batch, contour)")
    pattern_id: Optional[str] = Field(None, description="Associated pattern ID")
    strip_family_id: Optional[str] = Field(None, description="Associated strip family ID")
    status: str = Field("pending", description="Job status")
    start_time: Optional[str] = None
    parameters: Dict[str, Any] = Field(..., description="Job parameters")


class JobLogUpdate(BaseModel):
    """Request body for updating a joblog."""
    status: Optional[str] = None
    end_time: Optional[str] = None
    duration_seconds: Optional[float] = None
    results: Optional[Dict[str, Any]] = None


class StripFamilyCreate(BaseModel):
    """Request body for creating a strip family."""
    name: str = Field(..., description="Strip family name")
    strip_width_mm: float = Field(..., gt=0, description="Strip width in mm")
    strip_thickness_mm: float = Field(..., gt=0, description="Strip thickness in mm")
    material_type: str = Field(..., description="Material type")
    strips: List[Dict[str, Any]] = Field(..., description="Strip configurations")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class StripFamilyUpdate(BaseModel):
    """Request body for updating a strip family."""
    name: Optional[str] = None
    strip_width_mm: Optional[float] = Field(None, gt=0)
    strip_thickness_mm: Optional[float] = Field(None, gt=0)
    material_type: Optional[str] = None
    strips: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


# ========== Migration Dashboard (N8.7) ==========

@router.get("/migration/status")
def get_migration_status():
    """
    Get RMOS migration status and statistics.
    
    Returns:
        - last_migration: Timestamp of most recent migration
        - entity_counts: Current counts for all entity types
        - database_info: Size, location, schema version
        - recent_entities: Most recently created entities
        - validation_summary: Quick integrity check
    """
    stores = get_rmos_stores()
    db = stores.db
    
    # Get entity counts
    pattern_count = stores.patterns.count()
    family_count = stores.strip_families.count()
    joblog_count = stores.joblogs.count()
    
    # Get most recent entities (by created_at)
    recent_patterns = stores.patterns.get_all(limit=5, offset=0)
    recent_families = stores.strip_families.get_all(limit=5, offset=0)
    recent_joblogs = stores.joblogs.get_recent(limit=5)
    
    # Sort by created_at to find last migration timestamp
    all_timestamps = []
    for p in recent_patterns:
        if p.get('created_at'):
            all_timestamps.append(p['created_at'])
    for f in recent_families:
        if f.get('created_at'):
            all_timestamps.append(f['created_at'])
    for j in recent_joblogs:
        if j.get('created_at'):
            all_timestamps.append(j['created_at'])
    
    last_migration = max(all_timestamps) if all_timestamps else None
    
    # Get database info
    db_path = Path(__file__).parent.parent.parent.parent / "rmos.db"
    db_size_bytes = db_path.stat().st_size if db_path.exists() else 0
    db_size_mb = round(db_size_bytes / (1024 * 1024), 2)
    
    # Get schema version
    try:
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT version, applied_at FROM schema_version ORDER BY applied_at DESC LIMIT 1")
            row = cursor.fetchone()
            schema_version = row[0] if row else None
            schema_applied = row[1] if row else None
    except Exception:  # WP-1: keep broad — schema introspection may fail on missing table
        schema_version = None
        schema_applied = None
    
    # Quick validation checks
    validation_errors = []
    validation_warnings = []
    
    # Check for orphaned foreign keys
    try:
        patterns = stores.patterns.get_all(limit=100)
        for pattern in patterns:
            if pattern.get('strip_family_id'):
                family = stores.strip_families.get_by_id(pattern['strip_family_id'])
                if not family:
                    validation_errors.append(f"Pattern {pattern['id']} references missing strip_family")
        
        joblogs = stores.joblogs.get_all(limit=100)
        for joblog in joblogs:
            if joblog.get('pattern_id'):
                pattern = stores.patterns.get_by_id(joblog['pattern_id'])
                if not pattern:
                    validation_errors.append(f"JobLog {joblog['id']} references missing pattern")
    except Exception as e:  # WP-1: keep broad — non-critical validation check
        validation_warnings.append(f"Validation check failed: {str(e)}")
    
    return {
        "success": True,
        "migration_status": {
            "last_migration": last_migration,
            "database_location": str(db_path),
            "database_size_mb": db_size_mb,
            "schema_version": schema_version,
            "schema_applied_at": schema_applied
        },
        "entity_counts": {
            "patterns": pattern_count,
            "strip_families": family_count,
            "joblogs": joblog_count,
            "total": pattern_count + family_count + joblog_count
        },
        "recent_entities": {
            "patterns": [{"id": p["id"], "name": p.get("name"), "created_at": p.get("created_at")} for p in recent_patterns[:3]],
            "strip_families": [{"id": f["id"], "name": f.get("name"), "created_at": f.get("created_at")} for f in recent_families[:3]],
            "joblogs": [{"id": j["id"], "job_type": j.get("job_type"), "status": j.get("status"), "created_at": j.get("created_at")} for j in recent_joblogs[:3]]
        },
        "validation": {
            "errors": validation_errors,
            "warnings": validation_warnings,
            "status": "healthy" if len(validation_errors) == 0 else "errors_detected"
        }
    }


@router.get("/migration/history")
def get_migration_history(limit: int = Query(50, ge=1, le=500)):
    """
    Get migration history by analyzing entity creation timestamps.
    
    Groups entities by creation date to show migration batches.
    """
    stores = get_rmos_stores()
    
    # Get all entities with timestamps
    patterns = stores.patterns.get_all()
    families = stores.strip_families.get_all()
    joblogs = stores.joblogs.get_all()
    
    # Group by date
    migration_dates = {}
    
    for p in patterns:
        if p.get('created_at'):
            date = p['created_at'].split('T')[0]  # Get date part
            if date not in migration_dates:
                migration_dates[date] = {"patterns": 0, "strip_families": 0, "joblogs": 0}
            migration_dates[date]["patterns"] += 1
    
    for f in families:
        if f.get('created_at'):
            date = f['created_at'].split('T')[0]
            if date not in migration_dates:
                migration_dates[date] = {"patterns": 0, "strip_families": 0, "joblogs": 0}
            migration_dates[date]["strip_families"] += 1
    
    for j in joblogs:
        if j.get('created_at'):
            date = j['created_at'].split('T')[0]
            if date not in migration_dates:
                migration_dates[date] = {"patterns": 0, "strip_families": 0, "joblogs": 0}
            migration_dates[date]["joblogs"] += 1
    
    # Convert to sorted list
    history = [
        {
            "date": date,
            "entities": counts,
            "total": counts["patterns"] + counts["strip_families"] + counts["joblogs"]
        }
        for date, counts in migration_dates.items()
    ]
    history.sort(key=lambda x: x["date"], reverse=True)
    
    return {
        "success": True,
        "history": history[:limit],
        "total_migration_dates": len(history)
    }


# ========== Pattern Endpoints ==========

@router.post("/patterns")
async def create_pattern(body: PatternCreate):
    """Create a new pattern."""
    stores = get_rmos_stores()
    pattern = stores.patterns.create(body.dict())
    
    # N10.0: Broadcast event to WebSocket clients
    await broadcast_pattern_event("created", pattern)
    
    return {"success": True, "pattern": pattern}


@router.get("/patterns")
def list_patterns(
    limit: Optional[int] = Query(None, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List all patterns with optional pagination."""
    stores = get_rmos_stores()
    patterns = stores.patterns.get_all(limit=limit, offset=offset)
    count = stores.patterns.count()
    return {"success": True, "patterns": patterns, "total": count}


@router.get("/patterns/statistics")
def get_pattern_statistics():
    """Get pattern statistics."""
    stores = get_rmos_stores()
    stats = stores.patterns.get_statistics()
    return {"success": True, "statistics": stats}


@router.get("/patterns/search/name/{name_pattern}")
def search_patterns_by_name(name_pattern: str):
    """Search patterns by name (use % for wildcards)."""
    stores = get_rmos_stores()
    patterns = stores.patterns.search_by_name(name_pattern)
    return {"success": True, "patterns": patterns, "count": len(patterns)}


@router.get("/patterns/filter/rings/{ring_count}")
def filter_patterns_by_rings(ring_count: int):
    """Get patterns with specific ring count."""
    stores = get_rmos_stores()
    patterns = stores.patterns.get_by_ring_count(ring_count)
    return {"success": True, "patterns": patterns, "count": len(patterns)}


@router.get("/patterns/{pattern_id}")
def get_pattern(pattern_id: str):
    """Get a pattern by ID."""
    stores = get_rmos_stores()
    pattern = stores.patterns.get_by_id(pattern_id)
    if not pattern:
        raise HTTPException(status_code=404, detail=f"Pattern not found: {pattern_id}")
    return {"success": True, "pattern": pattern}


@router.put("/patterns/{pattern_id}")
async def update_pattern(pattern_id: str, body: PatternUpdate):
    """Update a pattern."""
    stores = get_rmos_stores()
    # Filter out None values
    update_data = {k: v for k, v in body.dict().items() if v is not None}
    pattern = stores.patterns.update(pattern_id, update_data)
    if not pattern:
        raise HTTPException(status_code=404, detail=f"Pattern not found: {pattern_id}")
    
    # N10.0: Broadcast event to WebSocket clients
    await broadcast_pattern_event("updated", pattern)
    
    return {"success": True, "pattern": pattern}


@router.delete("/patterns/{pattern_id}")
def delete_pattern(pattern_id: str):
    """Delete a pattern."""
    stores = get_rmos_stores()
    if not stores.patterns.delete(pattern_id):
        raise HTTPException(status_code=404, detail=f"Pattern not found: {pattern_id}")
    return {"success": True, "message": f"Pattern deleted: {pattern_id}"}


# ========== JobLog Endpoints ==========

@router.post("/joblogs")
async def create_joblog(body: JobLogCreate):
    """Create a new joblog."""
    stores = get_rmos_stores()
    joblog = stores.joblogs.create(body.dict())
    
    # N10.0: Broadcast event to WebSocket clients
    await broadcast_job_event("created", joblog)
    
    return {"success": True, "joblog": joblog}


@router.get("/joblogs")
def list_joblogs(
    limit: Optional[int] = Query(None, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List all joblogs with optional pagination."""
    stores = get_rmos_stores()
    joblogs = stores.joblogs.get_all(limit=limit, offset=offset)
    count = stores.joblogs.count()
    return {"success": True, "joblogs": joblogs, "total": count}


@router.get("/joblogs/statistics")
def get_joblog_statistics():
    """Get joblog statistics."""
    stores = get_rmos_stores()
    stats = stores.joblogs.get_statistics()
    return {"success": True, "statistics": stats}


@router.get("/joblogs/filter/status/{status}")
def filter_joblogs_by_status(
    status: str,
    limit: Optional[int] = Query(None, ge=1, le=1000)
):
    """Get joblogs by status."""
    stores = get_rmos_stores()
    joblogs = stores.joblogs.get_by_status(status, limit=limit)
    return {"success": True, "joblogs": joblogs, "count": len(joblogs)}


@router.get("/joblogs/filter/pattern/{pattern_id}")
def filter_joblogs_by_pattern(pattern_id: str):
    """Get joblogs for a specific pattern."""
    stores = get_rmos_stores()
    joblogs = stores.joblogs.get_by_pattern(pattern_id)
    return {"success": True, "joblogs": joblogs, "count": len(joblogs)}


@router.get("/joblogs/filter/type/{job_type}")
def filter_joblogs_by_type(
    job_type: str,
    limit: Optional[int] = Query(None, ge=1, le=1000)
):
    """Get joblogs by job type."""
    stores = get_rmos_stores()
    joblogs = stores.joblogs.get_by_job_type(job_type, limit=limit)
    return {"success": True, "joblogs": joblogs, "count": len(joblogs)}


@router.get("/joblogs/{joblog_id}")
def get_joblog(joblog_id: str):
    """Get a joblog by ID."""
    stores = get_rmos_stores()
    joblog = stores.joblogs.get_by_id(joblog_id)
    if not joblog:
        raise HTTPException(status_code=404, detail=f"JobLog not found: {joblog_id}")
    return {"success": True, "joblog": joblog}


@router.put("/joblogs/{joblog_id}")
async def update_joblog(joblog_id: str, body: JobLogUpdate):
    """Update a joblog."""
    stores = get_rmos_stores()
    update_data = {k: v for k, v in body.dict().items() if v is not None}
    joblog = stores.joblogs.update(joblog_id, update_data)
    if not joblog:
        raise HTTPException(status_code=404, detail=f"JobLog not found: {joblog_id}")
    
    # N10.0: Broadcast event based on status
    if joblog.get('status') == 'completed':
        await broadcast_job_event("completed", joblog)
    elif joblog.get('status') == 'failed':
        await broadcast_job_event("failed", joblog)
    else:
        await broadcast_job_event("updated", joblog)
    
    return {"success": True, "joblog": joblog}


@router.delete("/joblogs/{joblog_id}")
def delete_joblog(joblog_id: str):
    """Delete a joblog."""
    stores = get_rmos_stores()
    if not stores.joblogs.delete(joblog_id):
        raise HTTPException(status_code=404, detail=f"JobLog not found: {joblog_id}")
    return {"success": True, "message": f"JobLog deleted: {joblog_id}"}


# ========== Strip Family Endpoints ==========

@router.post("/strip-families")
async def create_strip_family(body: StripFamilyCreate):
    """Create a new strip family."""
    stores = get_rmos_stores()
    family = stores.strip_families.create(body.dict())
    
    # N10.0: Broadcast event to WebSocket clients
    await broadcast_material_event("created", family)
    
    return {"success": True, "strip_family": family}


@router.get("/strip-families")
def list_strip_families(
    limit: Optional[int] = Query(None, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List all strip families with optional pagination."""
    stores = get_rmos_stores()
    families = stores.strip_families.get_all(limit=limit, offset=offset)
    count = stores.strip_families.count()
    return {"success": True, "strip_families": families, "total": count}


@router.get("/strip-families/statistics")
def get_strip_family_statistics():
    """Get strip family statistics."""
    stores = get_rmos_stores()
    stats = stores.strip_families.get_statistics()
    return {"success": True, "statistics": stats}


@router.get("/strip-families/search/name/{name_pattern}")
def search_strip_families_by_name(name_pattern: str):
    """Search strip families by name (use % for wildcards)."""
    stores = get_rmos_stores()
    families = stores.strip_families.search_by_name(name_pattern)
    return {"success": True, "strip_families": families, "count": len(families)}


@router.get("/strip-families/filter/material/{material_type}")
def filter_strip_families_by_material(material_type: str):
    """Get strip families by material type."""
    stores = get_rmos_stores()
    families = stores.strip_families.get_by_material_type(material_type)
    return {"success": True, "strip_families": families, "count": len(families)}


@router.get("/strip-families/{family_id}")
def get_strip_family(family_id: str):
    """Get a strip family by ID."""
    stores = get_rmos_stores()
    family = stores.strip_families.get_by_id(family_id)
    if not family:
        raise HTTPException(status_code=404, detail=f"Strip family not found: {family_id}")
    return {"success": True, "strip_family": family}


@router.put("/strip-families/{family_id}")
async def update_strip_family(family_id: str, body: StripFamilyUpdate):
    """Update a strip family."""
    stores = get_rmos_stores()
    update_data = {k: v for k, v in body.dict().items() if v is not None}
    family = stores.strip_families.update(family_id, update_data)
    if not family:
        raise HTTPException(status_code=404, detail=f"Strip family not found: {family_id}")
    
    # N10.0: Broadcast event to WebSocket clients
    await broadcast_material_event("updated", family)
    
    return {"success": True, "strip_family": family}


@router.delete("/strip-families/{family_id}")
def delete_strip_family(family_id: str):
    """Delete a strip family."""
    stores = get_rmos_stores()
    if not stores.strip_families.delete(family_id):
        raise HTTPException(status_code=404, detail=f"Strip family not found: {family_id}")
    return {"success": True, "message": f"Strip family deleted: {family_id}"}
