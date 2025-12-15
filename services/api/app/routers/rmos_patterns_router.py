# services/api/app/routers/rmos_patterns_router.py

from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException

from ..rmos.models.pattern import RosettePattern
from ..stores.rmos_stores import get_rmos_stores

router = APIRouter(
    prefix="/rosette-patterns",
    tags=["RMOS", "Patterns"],
)


@router.get("/", response_model=List[RosettePattern])
async def list_patterns() -> List[RosettePattern]:
    """List all rosette patterns currently registered."""
    stores = get_rmos_stores()
    pattern_dicts = stores.patterns.get_all()
    # Convert SQLite dicts to Pydantic models
    patterns = [RosettePattern(**p) for p in pattern_dicts]
    return patterns


@router.post("/", response_model=RosettePattern)
async def create_pattern(pattern: RosettePattern) -> RosettePattern:
    """
    Create a new rosette pattern.

    NOTE: For now we trust the client to provide a unique pattern_id.
    Later we can add auto-ID generation if needed.
    """
    stores = get_rmos_stores()
    
    # Check if pattern already exists
    existing = stores.patterns.get_by_id(pattern.pattern_id)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Pattern {pattern.pattern_id} already exists",
        )
    
    # Convert Pydantic model to dict for storage
    pattern_dict = pattern.dict()
    pattern_dict['id'] = pattern_dict.pop('pattern_id')  # Map pattern_id -> id
    pattern_dict['pattern_type'] = 'rosette'  # Mark as rosette type
    pattern_dict['geometry_json'] = '{}'
    pattern_dict['metadata_json'] = pattern_dict.get('metadata', {})
    
    # Create in database
    created = stores.patterns.create(pattern_dict)
    
    # Convert back to Pydantic model
    created['pattern_id'] = created.pop('id')
    return RosettePattern(**created)


@router.get("/{pattern_id}", response_model=RosettePattern)
async def get_pattern(pattern_id: str) -> RosettePattern:
    """Get a specific rosette pattern by ID."""
    stores = get_rmos_stores()
    pattern_dict = stores.patterns.get_by_id(pattern_id)
    
    if not pattern_dict:
        raise HTTPException(status_code=404, detail=f"Pattern {pattern_id} not found")
    
    # Convert SQLite dict to Pydantic model
    pattern_dict['pattern_id'] = pattern_dict.pop('id')
    return RosettePattern(**pattern_dict)


@router.put("/{pattern_id}", response_model=RosettePattern)
async def update_pattern(pattern_id: str, pattern: RosettePattern) -> RosettePattern:
    """Replace a rosette pattern by ID."""
    stores = get_rmos_stores()
    
    # Check if pattern exists
    existing = stores.patterns.get_by_id(pattern_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Pattern {pattern_id} not found")
    
    # Convert Pydantic model to dict for storage
    pattern_dict = pattern.dict()
    pattern_dict['id'] = pattern_dict.pop('pattern_id')  # Map pattern_id -> id
    pattern_dict['updated_at'] = datetime.utcnow().isoformat()
    pattern_dict['pattern_type'] = existing.get('pattern_type', 'rosette')
    pattern_dict['geometry_json'] = existing.get('geometry_json', '{}')
    pattern_dict['metadata_json'] = pattern_dict.get('metadata', {})
    
    # Update in database
    updated = stores.patterns.update(pattern_id, pattern_dict)
    
    # Convert back to Pydantic model
    updated['pattern_id'] = updated.pop('id')
    return RosettePattern(**updated)


@router.delete("/{pattern_id}")
async def delete_pattern(pattern_id: str) -> dict:
    """Delete a rosette pattern by ID."""
    stores = get_rmos_stores()
    
    # Check if pattern exists
    existing = stores.patterns.get_by_id(pattern_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Pattern {pattern_id} not found")
    
    # Delete from database
    success = stores.patterns.delete(pattern_id)
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to delete pattern {pattern_id}")
    
    return {"message": f"Pattern {pattern_id} deleted"}
