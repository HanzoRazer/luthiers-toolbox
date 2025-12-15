# services/api/app/routers/machines_tools_router.py
"""
Patch N.12 - Per-Machine Tool Tables
API endpoints for CRUD operations on tool tables with CSV import/export
"""
import csv
import io
import json
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, Response, UploadFile
from pydantic import BaseModel

MACHINES_PATH = os.environ.get("TB_MACHINES_PATH", "app/data/machines.json")
router = APIRouter(prefix="/machines/tools", tags=["machines", "tools"])


class Tool(BaseModel):
    """Tool definition model with all CNC tool parameters"""
    t: int  # Tool number (e.g., T1, T7)
    name: str  # Human-readable name
    type: str  # Tool type: EM, DRILL, BALL, CHAMFER, etc.
    dia_mm: float  # Cutting diameter in mm
    len_mm: float  # Flute length in mm
    holder: Optional[str] = None  # Holder type (ER20, ER16, Collet, etc.)
    offset_len_mm: Optional[float] = None  # Tool length offset from gauge line
    spindle_rpm: Optional[float] = None  # Default spindle speed
    feed_mm_min: Optional[float] = None  # Default XY feed rate
    plunge_mm_min: Optional[float] = None  # Default Z plunge rate


def _load() -> Dict[str, Any]:
    """Load machines.json file"""
    try:
        with open(MACHINES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"machines": []}


def _save(obj: Dict[str, Any]) -> None:
    """Save machines.json file"""
    os.makedirs(os.path.dirname(MACHINES_PATH), exist_ok=True)
    with open(MACHINES_PATH, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def _find_machine(data, mid: str) -> Optional[Dict[str, Any]]:
    """Find machine by ID in machines array"""
    for m in data.get("machines", []):
        if m.get("id") == mid:
            return m
    return None


@router.get("/{mid}", response_model=dict)
def list_tools(mid: str) -> Dict[str, Any]:
    """List all tools for a specific machine"""
    d = _load()
    m = _find_machine(d, mid)
    if not m:
        raise HTTPException(404, f"Machine '{mid}' not found")
    return {"machine": m["id"], "tools": m.get("tools") or []}


@router.put("/{mid}", response_model=dict)
def upsert_tools(mid: str, tools: List[Tool]) -> Dict[str, Any]:
    """
    Upsert tools for a machine (merge by T number)
    - Existing tools with same T are replaced
    - New tools are added
    - Result is sorted by T ascending
    """
    d = _load()
    m = _find_machine(d, mid)
    if not m:
        raise HTTPException(404, f"Machine '{mid}' not found")
    
    # Index existing tools by T number
    idx = {int(t.get("t")): t for t in (m.get("tools") or [])}
    
    # Merge/upsert new tools
    for tool in tools:
        idx[int(tool.t)] = tool.dict()
    
    # Sort by T and save
    m["tools"] = [idx[k] for k in sorted(idx.keys())]
    _save(d)
    
    return {"ok": True, "tools": m["tools"]}


@router.delete("/{mid}/{tnum}", response_model=dict)
def delete_tool(mid: str, tnum: int) -> Dict[str, Any]:
    """Delete a specific tool by T number"""
    d = _load()
    m = _find_machine(d, mid)
    if not m:
        raise HTTPException(404, f"Machine '{mid}' not found")
    
    # Filter out tool with matching T
    tools = [t for t in (m.get("tools") or []) if int(t.get("t")) != int(tnum)]
    m["tools"] = tools
    _save(d)
    
    return {"ok": True, "tools": tools}


@router.get("/{mid}.csv")
def export_csv(mid: str) -> str:
    """Export tool table as CSV"""
    d = _load()
    m = _find_machine(d, mid)
    if not m:
        raise HTTPException(404, f"Machine '{mid}' not found")
    
    buf = io.StringIO()
    w = csv.writer(buf)
    
    # Write header
    w.writerow([
        "t", "name", "type", "dia_mm", "len_mm", "holder",
        "offset_len_mm", "spindle_rpm", "feed_mm_min", "plunge_mm_min"
    ])
    
    # Write tool rows
    for t in (m.get("tools") or []):
        w.writerow([
            t.get("t"),
            t.get("name"),
            t.get("type"),
            t.get("dia_mm"),
            t.get("len_mm"),
            t.get("holder"),
            t.get("offset_len_mm"),
            t.get("spindle_rpm"),
            t.get("feed_mm_min"),
            t.get("plunge_mm_min")
        ])
    
    return Response(
        content=buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="tools_{mid}.csv"'}
    )


@router.post("/{mid}/import_csv")
def import_csv(mid: str, file: UploadFile = File(...)):
    """
    Import tool table from CSV (upsert by T number)
    - Merges with existing tools
    - Skips rows with missing/invalid required fields
    - Returns count of successfully imported tools
    """
    d = _load()
    m = _find_machine(d, mid)
    if not m:
        raise HTTPException(404, f"Machine '{mid}' not found")
    
    # Read and parse CSV
    text = file.file.read().decode("utf-8", errors="ignore")
    rdr = csv.DictReader(io.StringIO(text))
    
    tools = []
    skipped = 0
    
    for row in rdr:
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
        except Exception as e:
            skipped += 1
            continue
    
    # Upsert all imported tools
    idx = {int(t.get("t")): t for t in (m.get("tools") or [])}
    for t in tools:
        idx[int(t["t"])] = t
    
    m["tools"] = [idx[k] for k in sorted(idx.keys())]
    _save(d)
    
    return {
        "ok": True,
        "count": len(tools),
        "skipped": skipped,
        "tools": m["tools"]
    }
