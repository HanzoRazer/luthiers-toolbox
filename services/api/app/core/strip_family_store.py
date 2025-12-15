from __future__ import annotations

from typing import Dict, Optional

from app.schemas.strip_family import (
    StripFamilyCreate,
    StripFamilyInDB,
    StripFamilyUpdate,
)


class StripFamilyStore:
    """In-memory strip family registry used by RMOS Sandbox."""

    def __init__(self) -> None:
        self._db: Dict[str, StripFamilyInDB] = {}

    def list(self) -> list[StripFamilyInDB]:
        return list(self._db.values())

    def get(self, family_id: str) -> Optional[StripFamilyInDB]:
        return self._db.get(family_id)

    def create(self, data: StripFamilyCreate) -> StripFamilyInDB:
        if data.id in self._db:
            raise ValueError(f"Strip family '{data.id}' already exists")
        record = StripFamilyInDB(**data.model_dump())
        self._db[data.id] = record
        return record

    def update(self, family_id: str, data: StripFamilyUpdate) -> Optional[StripFamilyInDB]:
        record = self._db.get(family_id)
        if not record:
            return None
        updated = record.model_copy(update=data.model_dump(exclude_unset=True))
        self._db[family_id] = updated
        return updated

    def delete(self, family_id: str) -> Optional[StripFamilyInDB]:
        return self._db.pop(family_id, None)


STRIP_FAMILY_STORE = StripFamilyStore()
