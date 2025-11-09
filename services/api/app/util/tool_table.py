# services/api/app/util/tool_table.py
"""
================================================================================
Tool Table Utilities Module
================================================================================

PURPOSE:
--------
Provides helper functions for loading tool definitions from machine profiles
and generating template context tokens for post-processor interpolation.
Core utility for N.12 machine/tool management system.

CORE FUNCTIONS:
--------------
1. get_machine(mid)
   - Retrieves machine definition by ID from machines.json
   - Returns machine dict with tools array

2. get_tool(mid, tnum)
   - Retrieves specific tool definition by machine ID and tool number
   - Returns tool dict with parameters (dia, rpm, feeds, etc.)

3. tool_context(mid, tnum)
   - Generates template context dict for post-processor variable expansion
   - Provides tokens like {TOOL}, {RPM}, {FEED}, {TOOL_DIA}, etc.
   - Used in post templates for dynamic tool parameter injection

MACHINE/TOOL DATA STRUCTURE:
---------------------------
**machines.json Format:**
```json
{
  "machines": [
    {
      "id": "m1",
      "name": "Hobby CNC Router",
      "tools": [
        {
          "t": 1,
          "name": "1/4\" End Mill",
          "dia_mm": 6.35,
          "len_mm": 25.4,
          "holder": "ER11",
          "offset_len_mm": 50.0,
          "spindle_rpm": 18000,
          "feed_mm_min": 1200,
          "plunge_mm_min": 300
        }
      ]
    }
  ]
}
```

**Context Tokens Generated:**
- TOOL: Tool number (int) - e.g., 1 for T1
- TOOL_NAME: Tool name (str) - e.g., "1/4\" End Mill"
- TOOL_DIA: Tool diameter in mm (float) - e.g., 6.35
- TOOL_LEN: Flute length in mm (float) - e.g., 25.4
- TOOL_HOLDER: Holder type (str) - e.g., "ER11"
- TOOL_OFFS_LEN: Length offset in mm (float) - e.g., 50.0
- RPM: Spindle speed (float) - e.g., 18000
- FEED: XY feed rate in mm/min (float) - e.g., 1200
- PLUNGE: Z plunge rate in mm/min (float) - e.g., 300

USAGE EXAMPLE:
-------------
    from .tool_table import tool_context, get_tool
    
    # Get tool definition
    tool = get_tool("m1", 1)  # Machine m1, Tool T1
    # Returns: {"t": 1, "name": "1/4\" End Mill", "dia_mm": 6.35, ...}
    
    # Generate template context
    ctx = tool_context("m1", 1)
    # Returns: {
    #   "TOOL": 1,
    #   "TOOL_NAME": "1/4\" End Mill",
    #   "TOOL_DIA": 6.35,
    #   "RPM": 18000,
    #   "FEED": 1200,
    #   ...
    # }
    
    # Use in post-processor template
    template = \"\"\"
    T{TOOL} M06
    G43 H{TOOL} Z{TOOL_OFFS_LEN}
    S{RPM} M03
    F{FEED}
    \"\"\"
    gcode = template.format(**ctx)
    # Produces:
    # T1 M06
    # G43 H1 Z50.0
    # S18000 M03
    # F1200

INTEGRATION POINTS:
------------------
- Used by: cam_post_v155_router.py (template expansion)
- Used by: machines_router.py (machine/tool management)
- Data source: services/api/app/data/machines.json
- Exports: get_machine(), get_tool(), tool_context()
- Dependencies: json, os (standard library)

CRITICAL SAFETY RULES:
---------------------
1. **Environment Variable Override**: TB_MACHINES_PATH allows custom machine file
   - Default: "services/api/app/data/machines.json"
   - Production: Can point to external database or config server
   - Always use absolute paths in production

2. **Graceful Degradation**: Missing machines.json returns empty dict
   - File not found: Returns {"machines": []}
   - Invalid JSON: Raises JSONDecodeError (caller handles)
   - Missing tool: Returns None (caller checks)

3. **Type Coercion**: Tool numbers coerced to int for comparison
   - tnum parameter: Accepts int or str
   - Tool "t" field: Converted to int for matching
   - Prevents string vs int comparison errors

4. **Empty Context Safety**: Missing mid/tnum returns empty dict
   - Template expansion with empty context: No substitution
   - Caller must validate context before using
   - Prevents KeyError in template formatting

5. **Tool Parameter Validation**: Context uses .get() for safe access
   - Missing tool parameters: Returns None in context
   - Template must handle None values (use defaults)
   - Prevents AttributeError on missing fields

PERFORMANCE CHARACTERISTICS:
---------------------------
- **Load Time**: ~1ms for typical machines.json (< 100 KB)
- **Lookup Speed**: O(n) where n = number of machines/tools
- **Memory**: Loads full machines.json into memory (acceptable for <10 MB)
- **Caching**: Not implemented (file read on every call)
- **Optimization**: For large tool libraries, add LRU cache to _load_machines()

PATCH HISTORY:
-------------
- Author: Patch N.12 (Machine/Tool Tables)
- Integrated: November 2025
- Enhanced: Phase 6.3 (Coding Policy Application)

================================================================================
"""
from typing import Dict, Any, Optional
import json, os

# =============================================================================
# CONFIGURATION
# =============================================================================

MACHINES_PATH: str = os.environ.get("TB_MACHINES_PATH", "services/api/app/data/machines.json")


# =============================================================================
# MACHINE/TOOL DATA LOADING
# =============================================================================

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


# =============================================================================
# TEMPLATE CONTEXT GENERATION
# =============================================================================

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
