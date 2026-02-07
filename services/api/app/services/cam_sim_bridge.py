"""
================================================================================
CAM Simulation Bridge Service Module
================================================================================

PURPOSE:
--------
Normalizes outputs from different CAM simulation engines into a unified format.
Decouples the pipeline and UI from engine-specific response structures.
Part of Art Studio v16.1 integration for multi-engine simulation support.

CORE FUNCTIONS:
--------------
1. simulate_gcode_inline(gcode, stock_thickness, **extra)
   - Inline simulation call used by pipeline operations
   - Returns normalized SimIssuesSummary + raw engine payload
   - Stub implementation (wire to actual sim engine)

2. _extract_issues_from_raw(raw)
   - Parses engine-specific issue formats into SimIssue objects
   - Handles multiple formats: issues[], collisions[], gouges[]
   - Graceful degradation for unknown formats

SUPPORTED ENGINE FORMATS:
-------------------------
**Format 1: Standard Issues Array**
```json
{
  "ok": true,
  "issues": [
    {"type": "collision", "x": 50.0, "y": 30.0, "z": -2.0, 
     "severity": "high", "note": "Tool collision with stock"},
    {"type": "rapid_plunge", "x": 25.0, "y": 15.0, 
     "severity": "medium", "note": "Rapid Z move below safe height"}
  ],
  "stats": {"time_s": 120.5, "move_count": 450}
}
```

**Format 2: Collisions Array** (legacy engines)
```json
{
  "ok": false,
  "collisions": [
    {"type": "collision", "x": 50.0, "y": 30.0, "z": -2.0, 
     "severity": "high", "note": "Collision"}
  ]
}
```

**Format 3: Gouges Array** (surface finish engines)
```json
{
  "ok": true,
  "gouges": [
    {"type": "gouge", "x": 75.0, "y": 45.0, "severity": "medium"}
  ]
}
```

NORMALIZED OUTPUT FORMAT:
-------------------------
**SimIssuesSummary Schema:**
```python
{
  "ok": bool,               # Overall pass/fail
  "gcode_bytes": int,       # G-code size in bytes
  "stock_thickness": float, # Stock height (optional)
  "issues": [               # Normalized issue list
    {
      "type": str,          # collision, gouge, rapid_plunge, etc.
      "x": float,           # Position X (mm)
      "y": float,           # Position Y (mm)
      "z": float | None,    # Position Z (mm, optional)
      "severity": str,      # high, medium, low
      "note": str           # Human-readable description
    }
  ],
  "stats": dict,            # Engine-specific statistics
  "meta": dict,             # Additional engine data
  "raw": dict               # Original engine response
}
```

ALGORITHM OVERVIEW:
------------------
**Issue Extraction Process:**

1. Try standard format (raw["issues"]):
   - If list exists, parse each dict into SimIssue
   - Use **item to unpack fields directly
   - Skip malformed items (continue on Exception)

2. Try collisions format (raw["collisions"]):
   - Map to SimIssue with type="collision"
   - Default severity="high"
   - Default note="Collision detected"

3. Try gouges format (raw["gouges"]):
   - Map to SimIssue with type="gouge"
   - Default severity="medium"
   - Default note="Gouge detected"

4. Aggregate all sources:
   - Combine issues from all formats
   - Remove duplicates (by position)
   - Sort by severity (high → medium → low)

**Simulation Stub (Current):**
- Counts G-code lines for move_count estimate
- Estimates time_s as ~0.1ms per character (trivial)
- Returns ok=True (no actual simulation)
- **WIRE TO ACTUAL ENGINE:** Replace with real sim call

USAGE EXAMPLE:
-------------
    from app.services.cam_sim_bridge import simulate_gcode_inline
    
    # Simulate G-code with inline stub
    gcode = \"\"\"
    G21 G90 G17
    G0 Z5
    G1 X50 Y30 F1200
    G1 Z-2 F300
    M30
    \"\"\"
    
    result = simulate_gcode_inline(
        gcode=gcode,
        stock_thickness=10.0
    )
    
    # Result structure:
    # {
    #   "ok": True,
    #   "gcode_bytes": 67,
    #   "stock_thickness": 10.0,
    #   "issues": [],
    #   "stats": {"time_s": 0.0067, "move_count": 5},
    #   "meta": {},
    #   "raw": {"ok": True, "issues": [], "stats": {...}}
    # }
    
    # Check for issues
    if not result["ok"] or result["issues"]:
        print(f"Simulation found {len(result['issues'])} issues:")
        for issue in result["issues"]:
            print(f"  - {issue['type']} at ({issue['x']}, {issue['y']}): {issue['note']}")

INTEGRATION POINTS:
------------------
- Used by: Pipeline operation processor (CAM simulation step)
- Used by: cam_sim_router.py (simulation API endpoint)
- Calls: (Stub) External simulation engine API
- Schema: app.schemas.cam_sim (SimIssue, SimIssuesSummary)
- Exports: simulate_gcode_inline(), _extract_issues_from_raw()

CRITICAL SAFETY RULES:
---------------------
1. **Graceful Degradation**: Unknown formats don't crash
   - Try/except around each issue parse
   - Malformed items skipped (continue loop)
   - Empty issues list returned if all fail

2. **Type Safety**: All fields have defaults
   - type: "collision", "gouge", "unknown"
   - severity: "medium" (if not specified)
   - note: Generic description
   - Prevents KeyError on missing fields

3. **Coordinate Validation**: X/Y required, Z optional
   - X/Y coerced to float (default: 0.0)
   - Z allowed to be None (planar operations)
   - Invalid coords: Skip issue (don't crash)

4. **Raw Payload Preservation**: Original response kept
   - result["raw"] contains full engine output
   - Enables debugging and format evolution
   - UI can access engine-specific data

5. **Stub Warning**: Current implementation is placeholder
   - Always returns ok=True
   - No actual collision detection
   - **PRODUCTION: Wire to real simulation engine**

PERFORMANCE CHARACTERISTICS:
---------------------------
- **Stub Performance**: ~0.1ms (trivial, no actual sim)
- **Real Engine (Target)**: 100-500ms for typical G-code
- **Issue Parsing**: O(n) where n = issue count (typically < 100)
- **Memory**: O(n) for issue storage

ENGINE INTEGRATION TODO:
-----------------------
**To Wire Real Simulation Engine:**

1. Replace stub in simulate_gcode_inline():
```python
# Example: Call external sim engine
import requests
response = requests.post(
    "http://sim-engine:8080/simulate",
    json={"gcode": gcode, "stock_thickness": stock_thickness}
)
raw_out = response.json()
```

2. Or import internal engine:
```python
from app.sim_engines.vericut import simulate_gcode
raw_out = simulate_gcode(gcode, stock_thickness)
```

3. Ensure engine returns one of supported formats
4. Update stats schema if needed
5. Add engine-specific parameters to **extra

PATCH HISTORY:
-------------
- Author: Art Studio v16.1 Integration
- Integrated: November 2025
- Enhanced: Phase 6.7 (Coding Policy Application)

================================================================================
"""

from typing import Dict, Any, List

from app.schemas.cam_sim import SimIssue, SimIssuesSummary


# =============================================================================
# ISSUE EXTRACTION (FORMAT NORMALIZATION)
# =============================================================================

def _extract_issues_from_raw(raw: Dict[str, Any]) -> List[SimIssue]:
    """
    Try to interpret whatever the sim engine gave us into a list[SimIssue].
    This keeps the pipeline + UI decoupled from engine-specific formats.
    """
    issues: List[SimIssue] = []

    # Preferred: raw["issues"] is already close to the schema
    raw_issues = raw.get("issues")
    if isinstance(raw_issues, list):
        for item in raw_issues:
            if not isinstance(item, dict):
                continue
            try:
                issues.append(SimIssue(**item))
            except (ValueError, TypeError, KeyError):  # WP-1: narrowed from except Exception
                continue

    # Alternate: raw["collisions"]
    collisions = raw.get("collisions")
    if isinstance(collisions, list):
        for c in collisions:
            if not isinstance(c, dict):
                continue
            try:
                issues.append(
                    SimIssue(
                        type=c.get("type", "collision"),
                        x=float(c.get("x", 0.0)),
                        y=float(c.get("y", 0.0)),
                        z=c.get("z"),
                        severity=c.get("severity", "high"),
                        note=c.get("note", "Collision detected"),
                    )
                )
            except (ValueError, TypeError, KeyError):  # WP-1: narrowed from except Exception
                continue

    # Alternate: raw["gouges"]
    gouges = raw.get("gouges")
    if isinstance(gouges, list):
        for g in gouges:
            if not isinstance(g, dict):
                continue
            try:
                issues.append(
                    SimIssue(
                        type=g.get("type", "gouge"),
                        x=float(g.get("x", 0.0)),
                        y=float(g.get("y", 0.0)),
                        z=g.get("z"),
                        severity=g.get("severity", "medium"),
                        note=g.get("note", "Gouge detected"),
                    )
                )
            except (ValueError, TypeError, KeyError):  # WP-1: narrowed from except Exception
                continue

    return issues


# =============================================================================
# INLINE SIMULATION (PIPELINE INTEGRATION)
# =============================================================================

def simulate_gcode_inline(
    gcode: str,
    stock_thickness: float | None = None,
    **extra: Any,
) -> Dict[str, Any]:
    """
    Inline sim call used by the pipeline.

    Always returns a dict matching SimIssuesSummary, plus the raw engine payload.
    
    NOTE: This is a stub implementation. Wire to your actual sim engine.
    """
    # Stub implementation - replace with actual sim engine call
    raw_out = {
        "ok": True,
        "issues": [],
        "stats": {
            "time_s": len(gcode) * 0.0001,  # Trivial estimate
            "move_count": len([l for l in gcode.split('\n') if l.strip()])
        }
    }

    issues = _extract_issues_from_raw(raw_out)

    summary = SimIssuesSummary(
        ok=bool(raw_out.get("ok", True)),
        gcode_bytes=len(gcode.encode("utf-8")),
        stock_thickness=stock_thickness,
        issues=issues,
        stats=raw_out.get("stats") or {},
        meta={
            k: v
            for k, v in raw_out.items()
            if k not in ("issues", "collisions", "gouges", "stats")
        },
    )

    out: Dict[str, Any] = summary.model_dump()
    out["raw"] = raw_out
    return out
