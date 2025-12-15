# services/api/app/rmos/api_constraint_profiles.py
"""
RMOS Constraint Profile API Routes
FastAPI router for profile CRUD operations.

Endpoints:
    GET  /api/rmos/profiles           - List all profiles
    GET  /api/rmos/profiles/{id}      - Get profile by ID
    POST /api/rmos/profiles           - Create new profile
    PUT  /api/rmos/profiles/{id}      - Update profile
    DELETE /api/rmos/profiles/{id}    - Delete profile
    GET  /api/rmos/profiles/tags/{tag} - List profiles by tag
"""
from __future__ import annotations

import os
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from .constraint_profiles import (
    ConstraintProfile,
    RosetteGeneratorConstraints,
    ProfileMetadata,
    ProfileStore,
    get_profile_store,
)
from .profile_history import (
    ChangeType,
    record_profile_change,
    get_profile_history,
    ProfileHistoryEntry,
)

# Environment variable for admin guard
ENABLE_PROFILE_ADMIN = os.environ.get("ENABLE_RMOS_PROFILE_ADMIN", "true").lower() == "true"


# ======================
# Pydantic Schemas
# ======================

class ConstraintsSchema(BaseModel):
    """Schema for constraint fields."""
    min_rings: int = Field(1, ge=1, le=12)
    max_rings: int = Field(8, ge=1, le=12)
    min_ring_width_mm: float = Field(0.5, ge=0.1, le=10.0)
    max_ring_width_mm: float = Field(4.0, ge=0.1, le=10.0)
    min_total_width_mm: float = Field(3.0, ge=1.0, le=20.0)
    max_total_width_mm: float = Field(10.0, ge=1.0, le=20.0)
    allow_mosaic: bool = True
    allow_segmented: bool = True
    palette_key: Optional[str] = None
    bias_simple: float = Field(0.5, ge=0.0, le=1.0)


class MetadataSchema(BaseModel):
    """Schema for profile metadata."""
    tags: List[str] = Field(default_factory=list)
    author: str = "user"
    machine_profile_id: Optional[str] = None


class ProfileCreateRequest(BaseModel):
    """Request body for creating a profile."""
    profile_id: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-z0-9_-]+$")
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field("", max_length=500)
    constraints: ConstraintsSchema
    metadata: Optional[MetadataSchema] = None


class ProfileUpdateRequest(BaseModel):
    """Request body for updating a profile."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    constraints: Optional[ConstraintsSchema] = None
    metadata: Optional[MetadataSchema] = None


class ProfileResponse(BaseModel):
    """Response schema for a profile."""
    profile_id: str
    name: str
    description: str
    constraints: ConstraintsSchema
    metadata: Dict[str, Any]
    is_system: bool


class ProfileListResponse(BaseModel):
    """Response schema for profile list."""
    profiles: List[ProfileResponse]
    count: int


class ProfileSummary(BaseModel):
    """Lightweight profile summary for lists."""
    profile_id: str
    name: str
    description: str
    tags: List[str]
    is_system: bool


class ProfileSummaryListResponse(BaseModel):
    """Response schema for profile summary list."""
    profiles: List[ProfileSummary]
    count: int


# ======================
# Router
# ======================

router = APIRouter(
    prefix="/profiles",
    tags=["rmos-profiles"],
)


def _profile_to_response(profile: ConstraintProfile) -> ProfileResponse:
    """Convert internal profile to response schema."""
    return ProfileResponse(
        profile_id=profile.profile_id,
        name=profile.name,
        description=profile.description,
        constraints=ConstraintsSchema(**profile.constraints.to_dict()),
        metadata=profile.metadata.to_dict(),
        is_system=profile.metadata.is_system,
    )


def _profile_to_summary(profile: ConstraintProfile) -> ProfileSummary:
    """Convert internal profile to summary schema."""
    return ProfileSummary(
        profile_id=profile.profile_id,
        name=profile.name,
        description=profile.description,
        tags=profile.metadata.tags,
        is_system=profile.metadata.is_system,
    )


def _check_admin_enabled():
    """Check if admin operations are enabled."""
    if not ENABLE_PROFILE_ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Profile administration is disabled. Set ENABLE_RMOS_PROFILE_ADMIN=true to enable.",
        )


# ======================
# Endpoints
# ======================

@router.get(
    "",
    response_model=ProfileSummaryListResponse,
    summary="List all profiles",
    description="Get a summary list of all available constraint profiles.",
)
async def list_profiles(
    include_system: bool = Query(True, description="Include system profiles"),
) -> ProfileSummaryListResponse:
    """
    GET /api/rmos/profiles
    
    List all available constraint profiles.
    """
    store = get_profile_store()
    profiles = store.list_all()
    
    if not include_system:
        profiles = [p for p in profiles if not p.metadata.is_system]
    
    summaries = [_profile_to_summary(p) for p in profiles]
    
    return ProfileSummaryListResponse(
        profiles=summaries,
        count=len(summaries),
    )


@router.get(
    "/ids",
    summary="List all profile IDs",
    description="Get just the IDs of all available profiles.",
)
async def list_profile_ids() -> Dict[str, List[str]]:
    """
    GET /api/rmos/profiles/ids
    
    List all profile IDs.
    """
    store = get_profile_store()
    return {"profile_ids": store.list_ids()}


@router.get(
    "/tags/{tag}",
    response_model=ProfileSummaryListResponse,
    summary="List profiles by tag",
    description="Get profiles that have a specific tag.",
)
async def list_profiles_by_tag(tag: str) -> ProfileSummaryListResponse:
    """
    GET /api/rmos/profiles/tags/{tag}
    
    List profiles matching a tag.
    """
    store = get_profile_store()
    profiles = store.list_by_tag(tag)
    summaries = [_profile_to_summary(p) for p in profiles]
    
    return ProfileSummaryListResponse(
        profiles=summaries,
        count=len(summaries),
    )


@router.get(
    "/{profile_id}",
    response_model=ProfileResponse,
    summary="Get profile by ID",
    description="Get full details of a specific constraint profile.",
)
async def get_profile(profile_id: str) -> ProfileResponse:
    """
    GET /api/rmos/profiles/{profile_id}
    
    Get a specific profile by ID.
    """
    store = get_profile_store()
    profile = store.get(profile_id)
    
    if not profile:
        raise HTTPException(
            status_code=404,
            detail=f"Profile '{profile_id}' not found",
        )
    
    return _profile_to_response(profile)


@router.post(
    "",
    response_model=ProfileResponse,
    status_code=201,
    summary="Create new profile",
    description="Create a new constraint profile. System profiles cannot be created via API.",
)
async def create_profile(request: ProfileCreateRequest) -> ProfileResponse:
    """
    POST /api/rmos/profiles
    
    Create a new constraint profile.
    """
    _check_admin_enabled()
    
    store = get_profile_store()
    
    # Check if already exists
    if store.exists(request.profile_id):
        raise HTTPException(
            status_code=409,
            detail=f"Profile '{request.profile_id}' already exists",
        )
    
    # Build constraints
    constraints = RosetteGeneratorConstraints.from_dict(request.constraints.model_dump())
    
    # Validate constraints
    errors = constraints.validate()
    if errors:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid constraints: {'; '.join(errors)}",
        )
    
    # Build metadata
    metadata = ProfileMetadata(
        tags=request.metadata.tags if request.metadata else [],
        author=request.metadata.author if request.metadata else "user",
        is_system=False,
        machine_profile_id=request.metadata.machine_profile_id if request.metadata else None,
    )
    
    # Create profile
    profile = ConstraintProfile(
        profile_id=request.profile_id,
        name=request.name,
        description=request.description,
        constraints=constraints,
        metadata=metadata,
    )
    
    if not store.create(profile):
        raise HTTPException(
            status_code=500,
            detail="Failed to create profile",
        )
    
    # Record in history
    record_profile_change(
        change_type=ChangeType.CREATE,
        profile_id=request.profile_id,
        new_state=profile.to_dict(),
        description=f"Created profile '{request.name}'",
    )
    
    # Save to YAML
    store.save_to_yaml()
    
    return _profile_to_response(profile)


@router.put(
    "/{profile_id}",
    response_model=ProfileResponse,
    summary="Update profile",
    description="Update an existing constraint profile. System profiles cannot be modified.",
)
async def update_profile(
    profile_id: str,
    request: ProfileUpdateRequest,
) -> ProfileResponse:
    """
    PUT /api/rmos/profiles/{profile_id}
    
    Update an existing profile.
    """
    _check_admin_enabled()
    
    store = get_profile_store()
    
    # Get existing profile
    existing = store.get(profile_id)
    if not existing:
        raise HTTPException(
            status_code=404,
            detail=f"Profile '{profile_id}' not found",
        )
    
    # Check if system profile
    if existing.metadata.is_system:
        raise HTTPException(
            status_code=403,
            detail="Cannot modify system profiles",
        )
    
    # Build updates dict
    updates: Dict[str, Any] = {}
    
    if request.name is not None:
        updates["name"] = request.name
    if request.description is not None:
        updates["description"] = request.description
    if request.constraints is not None:
        constraints = RosetteGeneratorConstraints.from_dict(request.constraints.model_dump())
        errors = constraints.validate()
        if errors:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid constraints: {'; '.join(errors)}",
            )
        updates["constraints"] = request.constraints.model_dump()
    if request.metadata is not None:
        updates["metadata"] = request.metadata.model_dump()
    
    # Store previous state for history
    previous_state = existing.to_dict()
    
    # Apply updates
    updated = store.update(profile_id, updates)
    if not updated:
        raise HTTPException(
            status_code=500,
            detail="Failed to update profile",
        )
    
    # Record in history
    record_profile_change(
        change_type=ChangeType.UPDATE,
        profile_id=profile_id,
        new_state=updated.to_dict(),
        previous_state=previous_state,
        description=f"Updated profile '{profile_id}'",
    )
    
    # Save to YAML
    store.save_to_yaml()
    
    return _profile_to_response(updated)


@router.delete(
    "/{profile_id}",
    status_code=204,
    summary="Delete profile",
    description="Delete a constraint profile. System profiles cannot be deleted.",
)
async def delete_profile(profile_id: str) -> None:
    """
    DELETE /api/rmos/profiles/{profile_id}
    
    Delete a profile.
    """
    _check_admin_enabled()
    
    store = get_profile_store()
    
    # Get existing profile for history
    existing = store.get(profile_id)
    if not existing:
        raise HTTPException(
            status_code=404,
            detail=f"Profile '{profile_id}' not found",
        )
    
    # Check if system profile
    if existing.metadata.is_system:
        raise HTTPException(
            status_code=403,
            detail="Cannot delete system profiles",
        )
    
    # Store state for history
    previous_state = existing.to_dict()
    
    # Delete
    if not store.delete(profile_id):
        raise HTTPException(
            status_code=500,
            detail="Failed to delete profile",
        )
    
    # Record in history
    record_profile_change(
        change_type=ChangeType.DELETE,
        profile_id=profile_id,
        previous_state=previous_state,
        description=f"Deleted profile '{profile_id}'",
    )
    
    # Save to YAML
    store.save_to_yaml()


@router.get(
    "/{profile_id}/constraints",
    response_model=ConstraintsSchema,
    summary="Get profile constraints only",
    description="Get just the constraints object for a profile.",
)
async def get_profile_constraints(profile_id: str) -> ConstraintsSchema:
    """
    GET /api/rmos/profiles/{profile_id}/constraints
    
    Get just the constraints for a profile.
    """
    store = get_profile_store()
    constraints = store.get_constraints(profile_id)
    
    if not constraints:
        raise HTTPException(
            status_code=404,
            detail=f"Profile '{profile_id}' not found",
        )
    
    return ConstraintsSchema(**constraints.to_dict())
