from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from ..models.tool_db import SessionLocal, Tool, Material, init_db
import json
import os

router = APIRouter(prefix="/tooling", tags=["tooling"])
init_db()


class ToolIn(BaseModel):
    name: str
    type: str
    diameter_mm: float
    flute_count: int = 2
    helix_deg: float = 0.0


class MaterialIn(BaseModel):
    name: str
    chipload_mm: float
    max_rpm: int = 24000


@router.get("/tools", response_model=List[ToolIn])
def list_tools():
    db = SessionLocal()
    try:
        return [ToolIn(name=t.name, type=t.type, diameter_mm=t.diameter_mm, flute_count=t.flute_count, helix_deg=t.helix_deg) for t in db.query(Tool).all()]
    finally:
        db.close()


@router.post("/tools")
def add_tool(t: ToolIn):
    db = SessionLocal()
    try:
        obj = Tool(name=t.name, type=t.type, diameter_mm=t.diameter_mm, flute_count=t.flute_count, helix_deg=t.helix_deg)
        db.add(obj)
        db.commit()
        return {"ok": True}
    finally:
        db.close()


@router.get("/materials", response_model=List[MaterialIn])
def list_materials():
    db = SessionLocal()
    try:
        return [MaterialIn(name=m.name, chipload_mm=m.chipload_mm, max_rpm=m.max_rpm) for m in db.query(Material).all()]
    finally:
        db.close()


@router.post("/materials")
def add_material(m: MaterialIn):
    db = SessionLocal()
    try:
        obj = Material(name=m.name, chipload_mm=m.chipload_mm, max_rpm=m.max_rpm)
        db.add(obj)
        db.commit()
        return {"ok": True}
    finally:
        db.close()


class FeedRequest(BaseModel):
    tool_name: str
    material_name: str
    rpm: Optional[int] = None
    width_mm: Optional[float] = None
    depth_mm: Optional[float] = None


@router.post("/feedspeeds")
def feedspeeds(req: FeedRequest):
    db = SessionLocal()
    try:
        t = db.query(Tool).filter(Tool.name == req.tool_name).first()
        m = db.query(Material).filter(Material.name == req.material_name).first()
        if not t or not m:
            raise HTTPException(404, "tool or material not found")
        rpm = req.rpm or min(20000, m.max_rpm)
        feed_mm_min = m.chipload_mm * max(1, t.flute_count) * rpm
        if req.width_mm and req.depth_mm:
            engagement = min(1.0, (req.width_mm / max(1e-6, t.diameter_mm)) * 0.7 + (req.depth_mm / max(1e-6, t.diameter_mm)) * 0.3)
            feed_mm_min *= max(0.2, engagement)
        return {"rpm": rpm, "feed_mm_min": round(feed_mm_min, 2)}
    finally:
        db.close()


@router.get("/posts")
def list_posts():
    dirp = os.path.join(os.path.dirname(__file__), "..", "data", "posts")
    out = {}
    if os.path.exists(dirp):
        for name in os.listdir(dirp):
            if name.endswith(".json"):
                with open(os.path.join(dirp, name), "r") as f:
                    out[name.replace(".json", "")] = json.load(f)
    return out
