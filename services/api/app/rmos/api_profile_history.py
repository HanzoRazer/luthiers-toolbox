# services/api/app/rmos/api_profile_history.py
"""
RMOS Profile History API Routes
FastAPI router for profile change history and rollback operations.

Endpoints:
    GET  /api/rmos/profiles/history              - Get all history
    GET  /api/rmos/profiles/{id}/history         - Get history for profile
    GET  /api/rmos/profiles/history/{entry_id}   - Get specific entry
    POST /api/rmos/profiles/{id}/rollback        - Rollback to entry
"""
from __future__ import annotations

import os
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from .profile_history import (
    ChangeType,
    ProfileHistoryEntry,
    ProfileHistoryStore,
    get_profile_history_store,
    record_profile_change,
)
from .constraint_profiles import (
    ConstraintProfile,
    RosetteGeneratorConstraints,
    ProfileMetadata,
    get_profile_store,
)

# Environment variable for admin guard
ENABLE_PROFILE_ADMIN = os.environ.get("ENABLE_RMOS_PROFILE_ADMIN", "true").lower() == "true"


# ======================
# Pydantic Schemas
# ======================

class HistoryEntryResponse(BaseModel):
    """Response schema for a history entry."""
    entry_id: str
    timestamp: str
    change_type: str
    profile_id: str
    user_id: Optional[str]
    description: Optional[str]
    has_new_state: bool
    has_previous_state: bool
    rollback_target_entry_id: Optional[str] = None


class HistoryEntryDetailResponse(HistoryEntryResponse):
    """Detailed response including state data."""
    new_state: Optional[Dict[str, Any]] = None
    previous_state: Optional[Dict[str, Any]] = None


class HistoryListResponse(BaseModel):
    """Response schema for history list."""
    entries: List[HistoryEntryResponse]
    count: int
    profile_id: Optional[str] = None


class RollbackRequest(BaseModel):
    """Request body for rollback operation."""
    target_entry_id: str = Field(..., description="Entry ID to rollback to")
    description: Optional[str] = Field(None, description="Optional description")


class RollbackResponse(BaseModel):
    """Response schema for rollback operation."""
    success: bool
    message: str
    profile_id: str
    rollback_entry_id: str
    target_entry_id: str
    new_state: Dict[str, Any]


# ======================
# Router
# ======================

router = APIRouter(
    prefix="/profiles",
    tags=["rmos-profile-history"],
)


def _entry_to_response(entry: ProfileHistoryEntry) -> HistoryEntryResponse:
    """Convert internal entry to response schema."""
    return HistoryEntryResponse(
        entry_id=entry.entry_id,
        timestamp=entry.timestamp,
        change_type=entry.change_type.value if isinstance(entry.change_type, ChangeType) else entry.change_type,
        profile_id=entry.profile_id,
        user_id=entry.user_id,
        description=entry.description,
        has_new_state=entry.new_state is not None,
        has_previous_state=entry.previous_state is not None,
        rollback_target_entry_id=entry.rollback_target_entry_id,
    )


def _entry_to_detail_response(entry: ProfileHistoryEntry) -> HistoryEntryDetailResponse:
    """Convert internal entry to detailed response schema."""
    return HistoryEntryDetailResponse(
        entry_id=entry.entry_id,
        timestamp=entry.timestamp,
        change_type=entry.change_type.value if isinstance(entry.change_type, ChangeType) else entry.change_type,
        profile_id=entry.profile_id,
        user_id=entry.user_id,
        description=entry.description,
        has_new_state=entry.new_state is not None,
        has_previous_state=entry.previous_state is not None,
        rollback_target_entry_id=entry.rollback_target_entry_id,
        new_state=entry.new_state,
        previous_state=entry.previous_state,
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
    "/history",
    response_model=HistoryListResponse,
    summary="Get all profile history",
    description="Get the change history for all profiles.",
)
async def get_all_history(
    limit: int = Query(100, ge=1, le=500, description="Maximum entries to return"),
    change_type: Optional[str] = Query(None, description="Filter by change type"),
) -> HistoryListResponse:
    """
    GET /api/rmos/profiles/history
    
    Get change history for all profiles.
    """
    store = get_profile_history_store()
    
    # Parse change type filter
    type_filter = None
    if change_type:
        try:
            type_filter = ChangeType(change_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid change_type: {change_type}. Valid: {[t.value for t in ChangeType]}",
            )
    
    entries = store.get_all_history(limit=limit, change_type=type_filter)
    
    return HistoryListResponse(
        entries=[_entry_to_response(e) for e in entries],
        count=len(entries),
        profile_id=None,
    )


@router.get(
    "/history/{entry_id}",
    response_model=HistoryEntryDetailResponse,
    summary="Get history entry by ID",
    description="Get full details of a specific history entry including state data.",
)
async def get_history_entry(entry_id: str) -> HistoryEntryDetailResponse:
    """
    GET /api/rmos/profiles/history/{entry_id}
    
    Get a specific history entry with full state data.
    """
    store = get_profile_history_store()
    entry = store.get_entry_by_id(entry_id)
    
    if not entry:
        raise HTTPException(
            status_code=404,
            detail=f"History entry '{entry_id}' not found",
        )
    
    return _entry_to_detail_response(entry)


@router.get(
    "/{profile_id}/history",
    response_model=HistoryListResponse,
    summary="Get profile history",
    description="Get the change history for a specific profile.",
)
async def get_profile_history_endpoint(
    profile_id: str,
    limit: int = Query(50, ge=1, le=200, description="Maximum entries to return"),
) -> HistoryListResponse:
    """
    GET /api/rmos/profiles/{profile_id}/history
    
    Get change history for a specific profile.
    """
    store = get_profile_history_store()
    entries = store.get_history_for_profile(profile_id, limit=limit)
    
    return HistoryListResponse(
        entries=[_entry_to_response(e) for e in entries],
        count=len(entries),
        profile_id=profile_id,
    )


@router.post(
    "/{profile_id}/rollback",
    response_model=RollbackResponse,
    summary="Rollback profile to previous state",
    description="""
    Rollback a profile to the state it was in at a specific history entry.
    
    This creates a new profile if the profile was deleted, or updates
    the existing profile to match the historical state.
    
    System profiles cannot be rolled back.
    """,
)
async def rollback_profile(
    profile_id: str,
    request: RollbackRequest,
) -> RollbackResponse:
    """
    POST /api/rmos/profiles/{profile_id}/rollback
    
    Rollback a profile to a previous state.
    """
    _check_admin_enabled()
    
    history_store = get_profile_history_store()
    profile_store = get_profile_store()
    
    # Get the target entry
    target_entry = history_store.get_entry_by_id(request.target_entry_id)
    if not target_entry:
        raise HTTPException(
            status_code=404,
            detail=f"History entry '{request.target_entry_id}' not found",
        )
    
    # Verify the entry is for the correct profile
    if target_entry.profile_id != profile_id:
        raise HTTPException(
            status_code=400,
            detail=f"Entry '{request.target_entry_id}' is for profile '{target_entry.profile_id}', not '{profile_id}'",
        )
    
    # Get the state to rollback to
    target_state = history_store.get_state_at_entry(request.target_entry_id)
    if not target_state:
        raise HTTPException(
            status_code=400,
            detail="Cannot rollback to a DELETE entry (no state to restore)",
        )
    
    # Get current profile state (may not exist if deleted)
    current_profile = profile_store.get(profile_id)
    current_state = current_profile.to_dict() if current_profile else None
    
    # Check if system profile
    if current_profile and current_profile.metadata.is_system:
        raise HTTPException(
            status_code=403,
            detail="Cannot rollback system profiles",
        )
    
    # Rebuild the profile from target state
    try:
        constraints = RosetteGeneratorConstraints.from_dict(
            target_state.get("constraints", {})
        )
        metadata = ProfileMetadata.from_dict(
            target_state.get("metadata", {})
        )
        # Ensure it's not marked as system
        metadata.is_system = False
        
        restored_profile = ConstraintProfile(
            profile_id=profile_id,
            name=target_state.get("name", profile_id),
            description=target_state.get("description", ""),
            constraints=constraints,
            metadata=metadata,
        )
    except (ValueError, TypeError, KeyError) as e:  # WP-1: narrowed from except Exception
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse target state: {str(e)}",
        )
    
    # Apply the rollback
    if current_profile:
        # Update existing profile
        profile_store._profiles[profile_id] = restored_profile
    else:
        # Re-create deleted profile
        profile_store.create(restored_profile)
    
    # Record the rollback in history
    rollback_entry = history_store.record_rollback(
        profile_id=profile_id,
        new_state=restored_profile.to_dict(),
        previous_state=current_state,
        target_entry_id=request.target_entry_id,
        description=request.description or f"Rolled back to entry {request.target_entry_id}",
    )
    
    # Save to YAML
    profile_store.save_to_yaml()
    
    return RollbackResponse(
        success=True,
        message=f"Profile '{profile_id}' rolled back to entry {request.target_entry_id}",
        profile_id=profile_id,
        rollback_entry_id=rollback_entry.entry_id if rollback_entry else "",
        target_entry_id=request.target_entry_id,
        new_state=restored_profile.to_dict(),
    )


@router.get(
    "/history/types",
    summary="List change types",
    description="Get list of valid change types for filtering.",
)
async def list_change_types() -> Dict[str, List[str]]:
    """
    GET /api/rmos/profiles/history/types
    
    List valid change types.
    """
    return {
        "change_types": [t.value for t in ChangeType],
        "descriptions": {
            "create": "Profile was created",
            "update": "Profile was modified",
            "delete": "Profile was deleted",
            "rollback": "Profile was rolled back to a previous state",
        },
    }
