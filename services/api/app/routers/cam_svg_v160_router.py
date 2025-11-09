
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import base64

router = APIRouter(prefix="/api/art/svg", tags=["art_svg_v160"])

class SvgDoc(BaseModel):
    svg_text: str

class OutlineReq(BaseModel):
    svg_text: str
    stroke_width_mm: float = 0.4

@router.get("/health")
def health()->Dict[str, Any]:
    return {"ok": True, "service": "svg_v160", "version": "16.0"}

@router.post("/normalize")
def normalize(doc: SvgDoc)->Dict[str, Any]:
    if not doc.svg_text.strip().startswith("<"):
        raise HTTPException(status_code=400, detail="Not an SVG (expected xml-like text)")
    svg_min = " ".join(doc.svg_text.split())
    return {"ok": True, "svg_text": svg_min}

@router.post("/outline")
def stroke_to_outline(req: OutlineReq)->Dict[str, Any]:
    if "<" not in req.svg_text:
        raise HTTPException(status_code=400, detail="Bad SVG input")
    return {"ok": True, "polylines": [ [[0,0],[40,0],[40,20],[0,20],[0,0]] ], "stroke_width_mm": req.stroke_width_mm}

class SaveSvgReq(BaseModel):
    svg_text: str
    name: str

@router.post("/save")
def save_svg(req: SaveSvgReq)->Dict[str, Any]:
    b = base64.b64encode(req.svg_text.encode("utf-8")).decode("ascii")
    return {"ok": True, "name": req.name, "bytes_b64": b, "hint": "store in /workspace/artworks/<name>.svg"}
