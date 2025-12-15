# server/app/api/routes/rosette_patterns.py
from __future__ import annotations

from typing import Dict

from fastapi import APIRouter, HTTPException

from app.schemas.rosette_pattern import (
    RosettePatternInDB,
    RosettePatternCreate,
    RosettePatternUpdate,
)

router = APIRouter(prefix="/rosette-patterns", tags=["rosette-patterns"])

# Simple in-memory store for now
ROSETTE_PATTERNS_DB: Dict[str, RosettePatternInDB] = {}


@router.get("/", response_model=list[RosettePatternInDB])
def list_patterns() -> list[RosettePatternInDB]:
    """
    List all rosette patterns.
    """
    return list(ROSETTE_PATTERNS_DB.values())


@router.get("/{pattern_id}", response_model=RosettePatternInDB)
def get_pattern(pattern_id: str) -> RosettePatternInDB:
    """
    Get a single pattern by id.
    """
    pat = ROSETTE_PATTERNS_DB.get(pattern_id)
    if not pat:
        raise HTTPException(status_code=404, detail="Pattern not found")
    return pat


@router.post("/", response_model=RosettePatternInDB, status_code=201)
def create_pattern(body: RosettePatternCreate) -> RosettePatternInDB:
    """
    Create a new rosette pattern.
    """
    if body.id in ROSETTE_PATTERNS_DB:
        raise HTTPException(status_code=400, detail="Pattern id already exists")
    
    pat = RosettePatternInDB(**body.dict())
    ROSETTE_PATTERNS_DB[pat.id] = pat
    return pat


@router.put("/{pattern_id}", response_model=RosettePatternInDB)
def update_pattern(pattern_id: str, body: RosettePatternUpdate) -> RosettePatternInDB:
    """
    Update an existing pattern (partial update).
    """
    pat = ROSETTE_PATTERNS_DB.get(pattern_id)
    if not pat:
        raise HTTPException(status_code=404, detail="Pattern not found")
    
    update_data = body.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(pat, key, value)
    
    return pat


@router.delete("/{pattern_id}", status_code=204)
def delete_pattern(pattern_id: str) -> None:
    """
    Delete a pattern.
    """
    if pattern_id not in ROSETTE_PATTERNS_DB:
        raise HTTPException(status_code=404, detail="Pattern not found")
    del ROSETTE_PATTERNS_DB[pattern_id]
