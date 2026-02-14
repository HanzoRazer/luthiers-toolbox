"""
Project Assets Router — Stub for AI Images Feature

Provides stub endpoints for /api/projects/{project_id}/assets/ai_images
to prevent 404 errors in the AI Images UI. The actual asset storage uses
the vision CAS (Content-Addressed Storage) via RMOS attachments.

This stub returns empty lists and success responses, allowing the UI
to function without a full project asset storage implementation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, UploadFile
from pydantic import BaseModel


router = APIRouter(prefix="/projects", tags=["Projects"])


class ImageAsset(BaseModel):
    """Image asset model (stub)."""
    id: str
    filename: str
    path: str
    url: str
    status: str
    userPrompt: str
    engineeredPrompt: str
    provider: str
    category: str
    size: str
    quality: str
    style: str
    cost: float
    createdAt: str
    updatedAt: str
    rating: Optional[int] = None
    bodyShape: Optional[str] = None
    finish: Optional[str] = None
    attachedTo: Optional[str] = None


class ImageAssetManifest(BaseModel):
    """Asset manifest (stub)."""
    project_id: str
    images: List[ImageAsset] = []
    total_count: int = 0
    total_cost: float = 0.0


# --- GET /api/projects/{project_id}/assets/ai_images ---
@router.get("/{project_id}/assets/ai_images")
def list_project_ai_images(project_id: str) -> Dict[str, Any]:
    """
    List AI image assets for a project.
    
    Stub implementation: Returns empty list.
    Vision-generated images are stored in CAS and attached to RMOS runs.
    """
    return {"images": [], "project_id": project_id}


# --- GET /api/projects/{project_id}/assets/ai_images/manifest ---
@router.get("/{project_id}/assets/ai_images/manifest")
def get_asset_manifest(project_id: str) -> ImageAssetManifest:
    """
    Get asset manifest for a project.
    
    Stub implementation: Returns empty manifest.
    """
    return ImageAssetManifest(project_id=project_id)


# --- POST /api/projects/{project_id}/assets/ai_images ---
@router.post("/{project_id}/assets/ai_images")
async def upload_ai_image_asset(
    project_id: str,
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None),
) -> Dict[str, Any]:
    """
    Upload an AI image asset.
    
    Stub implementation: Returns success but doesn't persist.
    Vision-generated images should use /api/vision/generate which stores to CAS.
    """
    return {
        "ok": True,
        "message": "Stub endpoint - use /api/vision/generate for actual image storage",
        "project_id": project_id,
    }


# --- DELETE /api/projects/{project_id}/assets/ai_images/{asset_id} ---
@router.delete("/{project_id}/assets/ai_images/{asset_id}")
def delete_ai_image_asset(project_id: str, asset_id: str) -> Dict[str, Any]:
    """
    Delete an AI image asset.
    
    Stub implementation: Returns success.
    """
    return {"ok": True, "deleted": asset_id, "project_id": project_id}


# --- POST /api/projects/{project_id}/assets/ai_images/{asset_id} ---
@router.post("/{project_id}/assets/ai_images/{asset_id}")
def update_ai_image_asset(
    project_id: str,
    asset_id: str,
) -> Dict[str, Any]:
    """
    Update an AI image asset.
    
    Stub implementation: Returns success.
    """
    return {"ok": True, "updated": asset_id, "project_id": project_id}
