"""
Consolidated Machines Router - Machine profiles and tool tables.

Consolidates:
- machine_router.py (machine profiles CRUD)
- machines_router.py (CAM machine list)
- machines_tools_router.py (per-machine tool tables)

Endpoints:
- GET/POST/DELETE /machines/profiles - Machine profile CRUD
- GET /machines/profiles/{pid} - Get specific profile
- POST /machines/profiles/clone/{src_id} - Clone profile
- GET /machines/{mid}/tools - List tools for machine
- PUT /machines/{mid}/tools - Upsert tools
- DELETE /machines/{mid}/tools/{tnum} - Delete tool
- GET /machines/{mid}/tools.csv - Export tools as CSV
- POST /machines/{mid}/tools/import_csv - Import tools from CSV
"""

import csv
import io
import json
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, Response, UploadFile
from pydantic import BaseModel, Field


router = APIRouter(tags=["machines"])


# ============================================================================
# Data Paths
# ============================================================================

_PROFILES_PATH = os.path.join(
    os.path.dirname(__file__), "..", "assets", "machine_profiles.json"
)
_MACHINES_PATH = os.environ.get("TB_MACHINES_PATH", "app/data/machines.json")


# ============================================================================
# Models
# ============================================================================

class MachineProfile(BaseModel):
    """Machine controller profile with kinematic limits and capabilities."""
    id: str
    title: str
    controller: str
    axes: dict
    limits: dict
    spindle: Optional[dict] = None
    feed_override: Optional[dict] = None
    post_id_default: Optional[str] = None


class MachineProfileSimple(BaseModel):
    """Simplified machine profile for CAM integration."""
    id: str
    name: str
    max_feed_xy: Optional[float] = Field(None, description="Max cutting feed in XY (units/min)")
    rapid: Optional[float] = Field(None, description="Rapid traverse feed (units/min)")
    accel: Optional[float] = Field(None, description="Acceleration (mm/s^2)")
    jerk: Optional[float] = Field(None, description="Jerk (mm/s^3)")
    safe_z_default: Optional[float] = Field(None, description="Default safe Z height")


class Tool(BaseModel):
    """Tool definition with CNC parameters."""
    t: int  # Tool number (T1, T7, etc.)
    name: str
    type: str  # EM, DRILL, BALL, CHAMFER, etc.
    dia_mm: float
    len_mm: float
    holder: Optional[str] = None
    offset_len_mm: Optional[float] = None
    spindle_rpm: Optional[float] = None
    feed_mm_min: Optional[float] = None
    plunge_mm_min: Optional[float] = None


# ============================================================================
# Profile Storage (machine_profiles.json)
# ============================================================================

def _load_profiles() -> List[Dict[str, Any]]:
    """Load machine profiles from JSON."""
    try:
        with open(_PROFILES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def _save_profiles(profiles: List[Dict[str, Any]]) -> None:
    """Save machine profiles to JSON."""
    os.makedirs(os.path.dirname(_PROFILES_PATH), exist_ok=True)
    with open(_PROFILES_PATH, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2)


# ============================================================================
# Tools Storage (machines.json)
# ============================================================================

def _load_machines() -> Dict[str, Any]:
    """Load machines.json for tool tables."""
    try:
        with open(_MACHINES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"machines": []}


def _save_machines(data: Dict[str, Any]) -> None:
    """Save machines.json."""
    os.makedirs(os.path.dirname(_MACHINES_PATH), exist_ok=True)
    with open(_MACHINES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _find_machine(data: Dict[str, Any], mid: str) -> Optional[Dict[str, Any]]:
    """Find machine by ID in machines array."""
    for m in data.get("machines", []):
        if m.get("id") == mid:
            return m
    return None


# ============================================================================
# Profile Endpoints
# ============================================================================

@router.get("/profiles", response_model=List[Dict[str, Any]])
def list_profiles() -> List[Dict[str, Any]]:
    """List all machine profiles."""
    return _load_profiles()


@router.get("/profiles/{pid}", response_model=Dict[str, Any])
def get_profile(pid: str) -> Dict[str, Any]:
    """Get a specific machine profile by ID."""
    for p in _load_profiles():
        if p["id"] == pid:
            return p
    raise HTTPException(404, "Profile not found")


@router.post("/profiles", response_model=Dict[str, str])
def upsert_profile(profile: MachineProfile) -> Dict[str, str]:
    """Create or update a machine profile."""
    profiles = _load_profiles()
    for i, p in enumerate(profiles):
        if p["id"] == profile.id:
            profiles[i] = profile.model_dump()
            _save_profiles(profiles)
            return {"status": "updated", "id": profile.id}
    profiles.append(profile.model_dump())
    _save_profiles(profiles)
    return {"status": "created", "id": profile.id}


@router.delete("/profiles/{pid}", response_model=Dict[str, str])
def delete_profile(pid: str) -> Dict[str, str]:
    """Delete a machine profile by ID."""
    profiles = _load_profiles()
    new_profiles = [p for p in profiles if p["id"] != pid]
    if len(new_profiles) == len(profiles):
        raise HTTPException(404, "Profile not found")
    _save_profiles(new_profiles)
    return {"status": "deleted", "id": pid}


@router.post("/profiles/clone/{src_id}", response_model=Dict[str, str])
def clone_profile(src_id: str, new_id: str, new_title: Optional[str] = None) -> Dict[str, str]:
    """Clone an existing machine profile with a new ID."""
    profiles = _load_profiles()
    src = next((p for p in profiles if p["id"] == src_id), None)
    if not src:
        raise HTTPException(404, "Source profile not found")
    if any(p["id"] == new_id for p in profiles):
        raise HTTPException(400, "new_id already exists")

    clone = json.loads(json.dumps(src))
    clone["id"] = new_id
    if new_title:
        clone["title"] = new_title

    profiles.append(clone)
    _save_profiles(profiles)
    return {"status": "cloned", "id": new_id}


# ============================================================================
# Tool Endpoints
# ============================================================================

@router.get("/{mid}/tools", response_model=Dict[str, Any])
def list_tools(mid: str) -> Dict[str, Any]:
    """List all tools for a specific machine."""
    data = _load_machines()
    machine = _find_machine(data, mid)
    if not machine:
        raise HTTPException(404, f"Machine '{mid}' not found")
    return {"machine": machine["id"], "tools": machine.get("tools") or []}


@router.put("/{mid}/tools", response_model=Dict[str, Any])
def upsert_tools(mid: str, tools: List[Tool]) -> Dict[str, Any]:
    """
    Upsert tools for a machine (merge by T number).
    Existing tools with same T are replaced, new tools are added.
    """
    data = _load_machines()
    machine = _find_machine(data, mid)
    if not machine:
        raise HTTPException(404, f"Machine '{mid}' not found")

    # Index existing tools by T number
    idx = {int(t.get("t")): t for t in (machine.get("tools") or [])}

    # Merge/upsert new tools
    for tool in tools:
        idx[int(tool.t)] = tool.model_dump()

    # Sort by T and save
    machine["tools"] = [idx[k] for k in sorted(idx.keys())]
    _save_machines(data)

    return {"ok": True, "tools": machine["tools"]}


@router.delete("/{mid}/tools/{tnum}", response_model=Dict[str, Any])
def delete_tool(mid: str, tnum: int) -> Dict[str, Any]:
    """Delete a specific tool by T number."""
    data = _load_machines()
    machine = _find_machine(data, mid)
    if not machine:
        raise HTTPException(404, f"Machine '{mid}' not found")

    tools = [t for t in (machine.get("tools") or []) if int(t.get("t")) != int(tnum)]
    machine["tools"] = tools
    _save_machines(data)

    return {"ok": True, "tools": tools}


@router.get("/{mid}/tools.csv")
def export_tools_csv(mid: str) -> Response:
    """Export tool table as CSV."""
    data = _load_machines()
    machine = _find_machine(data, mid)
    if not machine:
        raise HTTPException(404, f"Machine '{mid}' not found")

    buf = io.StringIO()
    writer = csv.writer(buf)

    writer.writerow([
        "t", "name", "type", "dia_mm", "len_mm", "holder",
        "offset_len_mm", "spindle_rpm", "feed_mm_min", "plunge_mm_min"
    ])

    for t in (machine.get("tools") or []):
        writer.writerow([
            t.get("t"), t.get("name"), t.get("type"), t.get("dia_mm"),
            t.get("len_mm"), t.get("holder"), t.get("offset_len_mm"),
            t.get("spindle_rpm"), t.get("feed_mm_min"), t.get("plunge_mm_min")
        ])

    return Response(
        content=buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="tools_{mid}.csv"'}
    )


@router.post("/{mid}/tools/import_csv", response_model=Dict[str, Any])
def import_tools_csv(mid: str, file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Import tool table from CSV (upsert by T number).
    Merges with existing tools, skips invalid rows.
    """
    data = _load_machines()
    machine = _find_machine(data, mid)
    if not machine:
        raise HTTPException(404, f"Machine '{mid}' not found")

    text = file.file.read().decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(text))

    tools = []
    skipped = 0

    for row in reader:
        try:
            tools.append({
                "t": int(row["t"]),
                "name": row["name"],
                "type": row.get("type", "EM"),
                "dia_mm": float(row["dia_mm"]),
                "len_mm": float(row["len_mm"]),
                "holder": row.get("holder") or None,
                "offset_len_mm": float(row["offset_len_mm"]) if row.get("offset_len_mm") else None,
                "spindle_rpm": float(row["spindle_rpm"]) if row.get("spindle_rpm") else None,
                "feed_mm_min": float(row["feed_mm_min"]) if row.get("feed_mm_min") else None,
                "plunge_mm_min": float(row["plunge_mm_min"]) if row.get("plunge_mm_min") else None
            })
        except Exception:
            skipped += 1

    # Upsert all imported tools
    idx = {int(t.get("t")): t for t in (machine.get("tools") or [])}
    for t in tools:
        idx[int(t["t"])] = t

    machine["tools"] = [idx[k] for k in sorted(idx.keys())]
    _save_machines(data)

    return {"ok": True, "count": len(tools), "skipped": skipped, "tools": machine["tools"]}
