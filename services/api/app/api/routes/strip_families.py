from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.strip_family_store import STRIP_FAMILY_STORE
from app.schemas.strip_family import (
    StripFamilyCreate,
    StripFamilyInDB,
    StripFamilyUpdate,
)

router = APIRouter(prefix="/strip-families", tags=["strip-families"])


@router.get("/", response_model=list[StripFamilyInDB])
def list_families() -> list[StripFamilyInDB]:
    return STRIP_FAMILY_STORE.list()


@router.post("/", response_model=StripFamilyInDB, status_code=201)
def create_family(body: StripFamilyCreate) -> StripFamilyInDB:
    if STRIP_FAMILY_STORE.get(body.id):
        raise HTTPException(status_code=400, detail="Strip family already exists")
    return STRIP_FAMILY_STORE.create(body)


@router.get("/{family_id}", response_model=StripFamilyInDB)
def get_family(family_id: str) -> StripFamilyInDB:
    record = STRIP_FAMILY_STORE.get(family_id)
    if not record:
        raise HTTPException(status_code=404, detail="Strip family not found")
    return record


@router.patch("/{family_id}", response_model=StripFamilyInDB)
def update_family(family_id: str, body: StripFamilyUpdate) -> StripFamilyInDB:
    record = STRIP_FAMILY_STORE.update(family_id, body)
    if not record:
        raise HTTPException(status_code=404, detail="Strip family not found")
    return record


@router.delete("/{family_id}")
def delete_family(family_id: str) -> dict[str, bool]:
    record = STRIP_FAMILY_STORE.delete(family_id)
    if not record:
        raise HTTPException(status_code=404, detail="Strip family not found")
    return {"success": True}
