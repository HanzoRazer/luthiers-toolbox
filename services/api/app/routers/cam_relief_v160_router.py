
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/art/relief", tags=["art_relief_v160"])

class HeightmapReq(BaseModel):
    grayscale: List[List[float]]  # 0..1
    z_min_mm: float = 0.0
    z_max_mm: float = 1.2
    scale_xy_mm: float = 1.0

@router.get("/health")
def health()->Dict[str, Any]:
    return {"ok": True, "service": "relief_v160", "version": "16.0"}

@router.post("/heightmap_preview")
def heightmap_preview(req: HeightmapReq)->Dict[str, Any]:
    rows = len(req.grayscale)
    cols = len(req.grayscale[0]) if rows>0 else 0
    if rows==0 or cols==0:
        raise HTTPException(status_code=400, detail="Empty grayscale array")
    verts = []
    for j in range(rows):
        row = []
        for i in range(cols):
            g = min(1.0, max(0.0, float(req.grayscale[j][i])))
            z = req.z_min_mm + g * (req.z_max_mm - req.z_min_mm)
            row.append([i*req.scale_xy_mm, j*req.scale_xy_mm, z])
        verts.append(row)
    return {"ok": True, "rows": rows, "cols": cols, "verts": verts}
