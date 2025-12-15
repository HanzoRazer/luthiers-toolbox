"""Machine profiles API for controller-specific limits and capabilities."""

import json
import os
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/machine", tags=["machine"])

_ASSET = os.path.join(os.path.dirname(__file__), "..", "assets", "machine_profiles.json")


class MachineProfile(BaseModel):
    """Machine controller profile with kinematic limits and capabilities."""
    id: str
    title: str
    controller: str
    axes: dict
    limits: dict
    spindle: dict | None = None
    feed_override: dict | None = None
    post_id_default: str | None = None


def _load() -> List[Dict[str, Any]]:
    """Load machine profiles from JSON asset."""
    with open(_ASSET, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(lst: List[Dict[str, Any]]) -> None:
    """Save machine profiles to JSON asset."""
    with open(_ASSET, "w", encoding="utf-8") as f:
        json.dump(lst, f, indent=2)


@router.get("/profiles")
def list_profiles() -> List[Dict[str, Any]]:
    """List all machine profiles."""
    return _load()


@router.get("/profiles/{pid}")
def get_profile(pid: str) -> Dict[str, Any]:
    """Get a specific machine profile by ID."""
    for p in _load():
        if p["id"] == pid:
            return p
    raise HTTPException(404, "profile not found")


@router.post("/profiles")
def upsert_profile(p: MachineProfile) -> Dict[str, str]:
    """Create or update a machine profile."""
    items = _load()
    for i, it in enumerate(items):
        if it["id"] == p.id:
            items[i] = p.dict()
            _save(items)
            return {"status": "updated", "id": p.id}
    items.append(p.dict())
    _save(items)
    return {"status": "created", "id": p.id}


@router.delete("/profiles/{pid}")
def delete_profile(pid: str) -> Dict[str, str]:
    """Delete a machine profile by ID."""
    items = _load()
    nxt = [x for x in items if x["id"] != pid]
    if len(nxt) == len(items):
        raise HTTPException(404, "profile not found")
    _save(nxt)
    return {"status": "deleted", "id": pid}


@router.post("/profiles/clone/{src_id}")
def clone_profile(src_id: str, new_id: str, new_title: str | None = None) -> Dict[str, str]:
    """
    Clone an existing machine profile with a new ID and optional new title.
    
    Args:
        src_id: Source profile ID to clone
        new_id: New unique ID for the cloned profile
        new_title: Optional new title (defaults to source title)
    
    Returns:
        {"status": "cloned", "id": new_id}
    """
    items = _load()
    src = next((p for p in items if p["id"] == src_id), None)
    if not src:
        raise HTTPException(404, "source profile not found")
    if any(p["id"] == new_id for p in items):
        raise HTTPException(400, "new_id already exists")
    
    # Deep copy source profile
    clone = json.loads(json.dumps(src))
    clone["id"] = new_id
    if new_title:
        clone["title"] = new_title
    
    items.append(clone)
    _save(items)
    return {"status": "cloned", "id": new_id}
