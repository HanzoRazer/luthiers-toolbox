"""BOM (Bill of Materials) Router — Endpoints for material management and BOM templates.

Provides:
- GET /materials - List materials library
- GET /materials/{material_id} - Get material by ID
- POST /materials - Add new material
- POST /from-template - Create BOM from template
- GET /templates - List BOM templates

LANE: UTILITY (business planning operations)
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from .schemas import (
    Material,
    MaterialCategory,
    BillOfMaterials,
    InstrumentType,
)
from .bom_service import BOMService

router = APIRouter(tags=["BOM", "Business"])

# Service (singleton instance)
bom_service = BOMService()


@router.get("/materials", response_model=List[Material], summary="List materials library")
async def list_materials(
    category: Optional[MaterialCategory] = None,
) -> List[Material]:
    """List all materials in the library, optionally filtered by category."""
    return bom_service.list_materials(category)


@router.get("/materials/{material_id}", response_model=Material, summary="Get material by ID")
async def get_material(material_id: str) -> Material:
    """Get a specific material by ID."""
    material = bom_service.get_material(material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return material


@router.post("/materials", response_model=Material, summary="Add new material")
async def add_material(material: Material) -> Material:
    """Add a new material to the library."""
    bom_service.add_material(material)
    return material


@router.post("/from-template", response_model=BillOfMaterials, summary="Create BOM from template")
async def create_bom_from_template(
    instrument_type: InstrumentType,
    instrument_name: str = Query(..., min_length=1),
) -> BillOfMaterials:
    """
    Create a Bill of Materials from a template.

    Templates available for:
    - acoustic_dreadnought
    - classical
    - electric_solid (coming soon)
    """
    return bom_service.create_bom_from_template(
        instrument_type=instrument_type,
        instrument_name=instrument_name,
    )


@router.get("/templates", summary="List BOM templates")
async def list_bom_templates():
    """List available BOM templates."""
    return {
        "templates": [
            {
                "type": t.value,
                "name": t.value.replace("_", " ").title(),
                "available": t in bom_service.BOM_TEMPLATES,
            }
            for t in InstrumentType
        ]
    }


__all__ = ["router", "bom_service"]
