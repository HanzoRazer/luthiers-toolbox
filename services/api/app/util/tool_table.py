# services/api/app/util/tool_table.py
"""
Patch N.12 - Tool Table Utilities
Helper functions for loading tool definitions and generating template context tokens
"""
from typing import Dict, Any, Optional
import json, os

MACHINES_PATH = os.environ.get("TB_MACHINES_PATH", "services/api/app/data/machines.json")


def _load_machines() -> Dict[str, Any]:
    """Load machines.json file"""
    try:
        with open(MACHINES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"machines": []}


def get_machine(mid: str) -> Optional[Dict[str, Any]]:
    """Get machine definition by ID"""
    for m in _load_machines().get("machines", []):
        if m.get("id") == mid:
            return m
    return None


def get_tool(mid: str, tnum: int) -> Optional[Dict[str, Any]]:
    """
    Get tool definition by machine ID and tool number
    
    Args:
        mid: Machine ID (e.g., "m1")
        tnum: Tool number (e.g., 1 for T1)
    
    Returns:
        Tool dict or None if not found
    """
    m = get_machine(mid)
    if not m:
        return None
    
    for t in (m.get("tools") or []):
        if int(t.get("t", -1)) == int(tnum):
            return t
    
    return None


def tool_context(mid: Optional[str], tnum: Optional[int]) -> Dict[str, Any]:
    """
    Generate template context tokens from tool table
    
    Returns context dict for template expansion with keys:
    - TOOL: Tool number (int)
    - TOOL_NAME: Tool name (str)
    - TOOL_DIA: Tool diameter in mm (float)
    - TOOL_LEN: Flute length in mm (float)
    - TOOL_HOLDER: Holder type (str)
    - TOOL_OFFS_LEN: Length offset in mm (float)
    - RPM: Spindle speed (float)
    - FEED: XY feed rate in mm/min (float)
    - PLUNGE: Z plunge rate in mm/min (float)
    
    Usage in post templates:
        T{TOOL} M06
        G43 H{TOOL} Z{TOOL_OFFS_LEN}
        S{RPM} M03
        F{FEED}
    
    Args:
        mid: Machine ID (optional)
        tnum: Tool number (optional)
    
    Returns:
        Context dict with tool parameters (empty if tool not found)
    """
    ctx: Dict[str, Any] = {}
    
    if not mid or tnum is None:
        return ctx
    
    t = get_tool(mid, int(tnum))
    if not t:
        return ctx
    
    # Build context with all tool parameters
    ctx.update({
        "TOOL": int(tnum),
        "TOOL_NAME": t.get("name"),
        "TOOL_DIA": t.get("dia_mm"),
        "TOOL_LEN": t.get("len_mm"),
        "TOOL_HOLDER": t.get("holder"),
        "TOOL_OFFS_LEN": t.get("offset_len_mm"),
        "RPM": t.get("spindle_rpm"),
        "FEED": t.get("feed_mm_min"),
        "PLUNGE": t.get("plunge_mm_min"),
    })
    
    return ctx
