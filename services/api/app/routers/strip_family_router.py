"""
RMOS Strip Family API Router (MM-0)

REST endpoints for mixed-material strip family management.
Provides template listing, instantiation, and CRUD operations.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from typing import List, Any, Dict

from ..core.strip_family_templates import load_templates, apply_template_to_store
from ..schemas.strip_family import StripFamilyTemplate, StripFamilyBase
from ..stores.rmos_stores import get_rmos_stores

router = APIRouter(prefix="/strip-families", tags=["RMOS", "Strip Families"])


@router.get("/", response_model=List[Dict[str, Any]])
def list_strip_families():
    """List all strip families from store."""
    stores = get_rmos_stores()
    return stores.strip_families.get_all(limit=500)


@router.get("/templates", response_model=List[StripFamilyTemplate])
def list_templates():
    """List available strip family templates."""
    return load_templates()


@router.post("/from-template/{template_id}", response_model=Dict[str, Any])
def create_from_template(template_id: str):
    """
    Create a new strip family from a template.
    
    Args:
        template_id: Template identifier
        
    Returns:
        Created strip family record
    """
    try:
        obj = apply_template_to_store(template_id)
        return obj
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{family_id}", response_model=Dict[str, Any])
def get_strip_family(family_id: str):
    """Get a specific strip family by ID."""
    stores = get_rmos_stores()
    family = stores.strip_families.get_by_id(family_id)
    if not family:
        raise HTTPException(status_code=404, detail=f"Strip family not found: {family_id}")
    return family
