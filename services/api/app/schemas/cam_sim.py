# app/schemas/cam_sim.py
"""
Normalized simulation issue schema for all CAM simulation engines.

Ensures consistent interface regardless of underlying sim engine (GRBL, Mach4, etc.).
"""
from typing import Optional, Literal, List, Dict, Any
from pydantic import BaseModel, Field


class SimIssue(BaseModel):
    """
    Normalized simulation issue schema.

    Every sim engine should be mapped into this shape for consistent UI/pipeline handling.
    """
    type: str = Field(..., description="Issue type, e.g. collision/gouge/clearance/feed_overload")
    x: float = Field(..., description="X position in work coordinates (mm or inch)")
    y: float = Field(..., description="Y position in work coordinates (mm or inch)")
    z: Optional[float] = Field(
        None,
        description="Z position if available (gouges, clearance issues, etc.)",
    )
    severity: Literal["info", "low", "medium", "high", "critical"] = "medium"
    note: Optional[str] = Field(
        None,
        description="Human-readable description for operator",
    )
    move_idx: Optional[int] = Field(
        None,
        description="Move index in G-code sequence where issue occurs",
    )


class SimIssuesSummary(BaseModel):
    """
    Normalized simulation result with issues.

    Embeds into pipeline results for consistent structure.
    """
    ok: bool = True
    gcode_bytes: Optional[int] = None
    stock_thickness: Optional[float] = None

    # Core normalized issues
    issues: List[SimIssue] = Field(default_factory=list)

    # Optional extra stats / metadata from specific engines
    stats: Dict[str, Any] = Field(default_factory=dict)
    meta: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "ok": True,
                "gcode_bytes": 4589,
                "stock_thickness": 25.4,
                "issues": [
                    {
                        "type": "collision",
                        "x": 45.2,
                        "y": 30.1,
                        "z": -2.5,
                        "severity": "high",
                        "note": "Tool collision with stock boundary",
                        "move_idx": 127
                    }
                ],
                "stats": {
                    "total_moves": 450,
                    "rapid_moves": 23,
                    "feed_moves": 427
                },
                "meta": {
                    "engine": "GRBL",
                    "simulation_time_ms": 145
                }
            }
        }
