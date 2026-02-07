# Patch N11.1 - Minimal Rosette Pattern API Scaffolding
# FastAPI endpoint for creating and managing RMOS Studio rosette patterns

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List

from ...stores.sqlite_pattern_store import SQLitePatternStore
from ...stores.sqlite_joblog_store import (
    SQLiteJobLogStore,
    JOB_TYPE_ROSETTE_PATTERN_GENERATION
)

router = APIRouter(prefix="/api/rmos/patterns", tags=["rmos-patterns"])


# ========== Request/Response Models ==========

class RosettePatternCreateRequest(BaseModel):
    """Request model for creating a rosette pattern."""
    
    pattern_id: str = Field(..., description="Unique pattern identifier")
    name: str = Field(..., description="Human-readable pattern name")
    rosette_geometry: Dict[str, Any] = Field(
        ...,
        description="Full rosette geometry (rings, columns, segmentation)"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional metadata (complexity, fragility_score, etc.)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "pattern_id": "rosette_001",
                "name": "Spanish Traditional 5-Ring",
                "rosette_geometry": {
                    "rings": [
                        {
                            "ring_id": 1,
                            "radius_mm": 40.0,
                            "width_mm": 3.0,
                            "tile_length_mm": 2.5,
                            "twist_angle_deg": 0.0,
                            "slice_angle_deg": 0.0,
                            "column": {
                                "strips": [
                                    {"width_mm": 1.0, "color": "maple", "material_id": "wood_001"}
                                ]
                            }
                        }
                    ],
                    "segmentation": {"tile_count_total": 94}
                },
                "metadata": {
                    "complexity": "medium",
                    "fragility_score": 0.42,
                    "rosette_type": "traditional_spanish"
                }
            }
        }


class RosetteGeometryUpdateRequest(BaseModel):
    """Request model for updating rosette geometry."""
    
    rosette_geometry: Dict[str, Any] = Field(
        ...,
        description="Updated rosette geometry definition"
    )


class RosettePatternResponse(BaseModel):
    """Response model for rosette pattern operations."""
    
    pattern_id: str
    name: str
    pattern_type: str
    ring_count: int
    rosette_geometry: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    created_at: str
    updated_at: str


# ========== API Endpoints ==========

@router.post("/rosette", response_model=Dict[str, Any])
def create_rosette_pattern(payload: RosettePatternCreateRequest) -> Dict[str, Any]:
    """
    Create a new RMOS Studio rosette pattern.
    
    N11.1 Scaffolding endpoint that:
    - Stores rosette_geometry as TEXT in patterns table
    - Marks pattern_type='rosette'
    - Creates initial JobLog entry for pattern generation
    
    Args:
        payload: Rosette pattern creation request
    
    Returns:
        Created pattern with all fields
    
    Raises:
        HTTPException 409: Pattern ID already exists
        HTTPException 400: Invalid rosette_geometry structure
    """
    store = SQLitePatternStore()
    joblog_store = SQLiteJobLogStore()
    
    # Check if pattern already exists
    existing = store.get_by_id(payload.pattern_id)
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Pattern with id '{payload.pattern_id}' already exists."
        )
    
    # Validate rosette_geometry has required structure
    if 'rings' not in payload.rosette_geometry:
        raise HTTPException(
            status_code=400,
            detail="rosette_geometry must contain 'rings' array"
        )
    
    # Create pattern
    try:
        pattern = store.create_rosette(
            pattern_id=payload.pattern_id,
            name=payload.name,
            rosette_geometry=payload.rosette_geometry,
            metadata=payload.metadata
        )
    except HTTPException:
        raise
    except Exception as e:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create rosette pattern: {str(e)}"
        )
    
    # Create JobLog entry for pattern creation
    try:
        joblog_store.create_rosette_job(
            job_type=JOB_TYPE_ROSETTE_PATTERN_GENERATION,
            pattern_id=payload.pattern_id,
            parameters={
                "ring_count": len(payload.rosette_geometry.get('rings', [])),
                "pattern_type": "rosette"
            },
            status="completed"
        )
    except Exception:  # WP-1: keep broad — non-critical joblog write
        pass
    
    return pattern


@router.get("/rosette", response_model=List[Dict[str, Any]])
def list_rosette_patterns() -> List[Dict[str, Any]]:
    """
    List all RMOS Studio rosette patterns.
    
    Returns:
        List of rosette patterns (pattern_type='rosette')
    """
    store = SQLitePatternStore()
    return store.list_by_type('rosette')


@router.get("/rosette/{pattern_id}", response_model=Dict[str, Any])
def get_rosette_pattern(pattern_id: str) -> Dict[str, Any]:
    """
    Get a specific rosette pattern by ID.
    
    Args:
        pattern_id: Pattern identifier
    
    Returns:
        Pattern dictionary
    
    Raises:
        HTTPException 404: Pattern not found
        HTTPException 400: Pattern exists but is not a rosette type
    """
    store = SQLitePatternStore()
    pattern = store.get_by_id(pattern_id)
    
    if pattern is None:
        raise HTTPException(
            status_code=404,
            detail=f"Pattern '{pattern_id}' not found"
        )
    
    if pattern.get('pattern_type') != 'rosette':
        raise HTTPException(
            status_code=400,
            detail=f"Pattern '{pattern_id}' is not a rosette pattern (type: {pattern.get('pattern_type')})"
        )
    
    return pattern


@router.patch("/rosette/{pattern_id}/geometry", response_model=Dict[str, Any])
def update_rosette_geometry(
    pattern_id: str,
    payload: RosetteGeometryUpdateRequest
) -> Dict[str, Any]:
    """
    Update rosette_geometry for an existing rosette pattern.
    
    Args:
        pattern_id: Pattern to update
        payload: Updated rosette geometry
    
    Returns:
        Updated pattern dictionary
    
    Raises:
        HTTPException 404: Pattern not found
    """
    store = SQLitePatternStore()
    
    updated = store.update_rosette_geometry(
        pattern_id=pattern_id,
        rosette_geometry=payload.rosette_geometry
    )
    
    if updated is None:
        raise HTTPException(
            status_code=404,
            detail=f"Pattern '{pattern_id}' not found"
        )
    
    return updated


@router.get("/rosette/{pattern_id}/geometry", response_model=Dict[str, Any])
def get_rosette_geometry(pattern_id: str) -> Dict[str, Any]:
    """
    Get just the rosette_geometry field for a pattern.
    
    Useful for clients that only need geometry without full pattern metadata.
    
    Args:
        pattern_id: Pattern identifier
    
    Returns:
        Rosette geometry dictionary
    
    Raises:
        HTTPException 404: Pattern not found or has no rosette_geometry
    """
    store = SQLitePatternStore()
    geometry = store.get_rosette_geometry(pattern_id)
    
    if geometry is None:
        raise HTTPException(
            status_code=404,
            detail=f"Rosette geometry not found for pattern '{pattern_id}'"
        )
    
    return geometry
