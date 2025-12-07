"""
Saw Blade Registry API - CRUD endpoints for blade specifications.

Endpoints:
- POST   /api/saw/blades             - Create blade
- GET    /api/saw/blades             - List all blades
- GET    /api/saw/blades/{blade_id}  - Get blade by ID
- PUT    /api/saw/blades/{blade_id}  - Update blade
- DELETE /api/saw/blades/{blade_id}  - Delete blade
- POST   /api/saw/blades/search      - Search with filters
- GET    /api/saw/blades/stats       - Registry statistics
"""

from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from ..cam_core.saw_lab.saw_blade_registry import (
    SawBladeSpec,
    SawBladeSearchFilter,
    get_registry
)


router = APIRouter(prefix="/saw/blades", tags=["Saw Lab"])


# ============================================================================
# Request/Response Models
# ============================================================================

class CreateBladeRequest(BaseModel):
    """Request to create new blade."""
    vendor: str
    model_code: str
    diameter_mm: float
    kerf_mm: float
    plate_thickness_mm: float
    bore_mm: float
    teeth: int
    hook_angle_deg: Optional[float] = None
    top_bevel_angle_deg: Optional[float] = None
    clearance_angle_deg: Optional[float] = None
    expansion_slots: Optional[int] = None
    cooling_slots: Optional[int] = None
    application: Optional[str] = None
    material_family: Optional[str] = None
    notes: Optional[str] = None


class UpdateBladeRequest(BaseModel):
    """Request to update blade fields."""
    vendor: Optional[str] = None
    model_code: Optional[str] = None
    diameter_mm: Optional[float] = None
    kerf_mm: Optional[float] = None
    plate_thickness_mm: Optional[float] = None
    bore_mm: Optional[float] = None
    teeth: Optional[int] = None
    hook_angle_deg: Optional[float] = None
    top_bevel_angle_deg: Optional[float] = None
    clearance_angle_deg: Optional[float] = None
    expansion_slots: Optional[int] = None
    cooling_slots: Optional[int] = None
    application: Optional[str] = None
    material_family: Optional[str] = None
    notes: Optional[str] = None


# ============================================================================
# Endpoints
# ============================================================================

@router.post("", response_model=SawBladeSpec, status_code=status.HTTP_201_CREATED)
def create_blade(req: CreateBladeRequest):
    """
    Create new blade in registry.
    
    Returns:
        Created blade with generated ID
        
    Raises:
        400: If blade with same vendor+model already exists
    """
    registry = get_registry()
    
    # Build blade spec
    blade = SawBladeSpec(
        id="",  # Will be auto-generated
        vendor=req.vendor,
        model_code=req.model_code,
        diameter_mm=req.diameter_mm,
        kerf_mm=req.kerf_mm,
        plate_thickness_mm=req.plate_thickness_mm,
        bore_mm=req.bore_mm,
        teeth=req.teeth,
        hook_angle_deg=req.hook_angle_deg,
        top_bevel_angle_deg=req.top_bevel_angle_deg,
        clearance_angle_deg=req.clearance_angle_deg,
        expansion_slots=req.expansion_slots,
        cooling_slots=req.cooling_slots,
        application=req.application,
        material_family=req.material_family,
        notes=req.notes
    )
    
    try:
        created = registry.create(blade)
        return created
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=List[SawBladeSpec])
def list_blades():
    """
    Get all blades in registry.
    
    Returns:
        List of blade specifications
    """
    registry = get_registry()
    return registry.list_all()


@router.get("/{blade_id}", response_model=SawBladeSpec)
def get_blade(blade_id: str):
    """
    Get blade by ID.
    
    Args:
        blade_id: Unique blade identifier
        
    Returns:
        Blade specification
        
    Raises:
        404: If blade not found
    """
    registry = get_registry()
    blade = registry.read(blade_id)
    
    if blade is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blade not found: {blade_id}"
        )
    
    return blade


@router.put("/{blade_id}", response_model=SawBladeSpec)
def update_blade(blade_id: str, req: UpdateBladeRequest):
    """
    Update blade specification.
    
    Args:
        blade_id: Unique blade identifier
        req: Fields to update (only provided fields are changed)
        
    Returns:
        Updated blade specification
        
    Raises:
        404: If blade not found
    """
    registry = get_registry()
    
    # Build updates dict (only include non-None fields)
    updates = {k: v for k, v in req.dict().items() if v is not None}
    
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    updated = registry.update(blade_id, updates)
    
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blade not found: {blade_id}"
        )
    
    return updated


@router.delete("/{blade_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_blade(blade_id: str):
    """
    Delete blade from registry.
    
    Args:
        blade_id: Unique blade identifier
        
    Raises:
        404: If blade not found
    """
    registry = get_registry()
    
    if not registry.delete(blade_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blade not found: {blade_id}"
        )
    
    return None


@router.post("/search", response_model=List[SawBladeSpec])
def search_blades(filters: SawBladeSearchFilter):
    """
    Search blades by filters.
    
    Args:
        filters: Search criteria (vendor, diameter range, teeth range, etc.)
        
    Returns:
        List of matching blades
    """
    registry = get_registry()
    return registry.search(filters)


@router.get("/stats", response_model=Dict[str, Any])
def get_registry_stats():
    """
    Get registry statistics.
    
    Returns:
        Statistics dictionary:
        - total_blades: Total blade count
        - vendors: List of vendors
        - vendor_count: Number of unique vendors
        - diameter_range_mm: Min/max blade diameters
        - applications: List of applications
        - material_families: List of material families
    """
    registry = get_registry()
    return registry.get_stats()
