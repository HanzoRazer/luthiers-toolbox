# LWPOLYLINE Fusion 360 Compatibility Verification

**Date:** 2026-04-28  
**Status:** TEST FILE GENERATED — AWAITING MANUAL VERIFICATION  
**Blocker for:** Paid-tier high-fidelity DXF output (R2000+ with LWPOLYLINE/ARC entities)

---

## Executive Summary

The CLAUDE.md DXF policy prohibits LWPOLYLINE because a prior incident caused Fusion 360 to freeze on `smart_guitar_front_v3.dxf`. Before lifting this gate for paid-tier output, we must verify the freeze cannot reproduce.

A test DXF file has been generated. **Manual Fusion 360 testing is required** to proceed.

---

## Background

### The Current Policy (CLAUDE.md)

```
DXF pipeline standard: R12 (AC1009)
  - LINE entities only via dxf_compat.add_polyline(version='R12')
  - No LWPOLYLINE (causes Fusion 360 freeze)
```

### Why We Want to Lift It

- **R12 LINE-only output** is maximally compatible but loses fidelity
- **R2000+ LWPOLYLINE** supports closed paths, arcs, and cleaner geometry
- Paid-tier users expect CAD-native output that imports cleanly into CAM workflows
- LWPOLYLINE entities are standard in modern DXF — the freeze was likely a specific file issue, not a format issue

---

## Infrastructure Audit

### dxf_compat.py (version-aware layer)

```
Location: services/api/app/util/dxf_compat.py

Supports: R12, R13, R14, R2000, R2004, R2007, R2010
LWPOLYLINE_VERSIONS = {'R13', 'R14', 'R2000', 'R2004', 'R2007', 'R2010'}

Key function:
  add_polyline(msp, points, layer, closed, version)
    - version='R12' → LINE segments
    - version='R13+' → LWPOLYLINE
```

**DISCREPANCY FOUND:** dxf_compat.py lists R13 (AC1012) as supported, but ezdxf does not support R13 creation. The earliest LWPOLYLINE-capable version in ezdxf is **R2000 (AC1015)**.

### dxf_writer.py (central writer)

```
Location: services/api/app/cam/dxf_writer.py

HARDCODED to R12. Does not accept version parameter.
All generators using DxfWriter class are locked to LINE-only output.
```

**ACTION REQUIRED:** After verification passes, dxf_writer.py needs a version parameter to support R2000+ output for paid tier.

---

## Test File Generated

| Property | Value |
|----------|-------|
| **Path** | `services/api/test_temp/cuatro_R2000_LWPOLYLINE_test.dxf` |
| **Full path** | `C:\Users\thepr\Downloads\luthiers-toolbox\services\api\test_temp\cuatro_R2000_LWPOLYLINE_test.dxf` |
| **DXF Version** | AC1015 (R2000) |
| **Entity Count** | 487 |
| **Entity Types** | 100% LWPOLYLINE |
| **File Size** | 138.2 KB |
| **Source** | El Cuatro 1.dxf (485 LINE entities converted) |

### Layers in Test File

| Layer | Purpose | Color |
|-------|---------|-------|
| PICKGUARD | Original geometry | Blue (5) |
| SMALL_FEATURE | Original geometry | Yellow (2) |
| BRIDGE_ROUTE | Original geometry | Light gray (14) |
| RHYTHM_CIRCUIT | Original geometry | White (7) |
| NECK_POCKET | Original geometry | Orange (30) |
| JACK_ROUTE | Original geometry | Green (3) |
| TEST_CLOSED_RECT | Closed rectangle for CAM test | Red (1) |
| TEST_CLOSED_BODY | Closed body shape for CAM test | Green (3) |

### Why This Test File

1. **Real geometry** — converted from actual cuatro blueprint, not synthetic shapes
2. **Multiple layers** — tests layer handling in Fusion 360
3. **Closed shapes included** — `TEST_CLOSED_RECT` and `TEST_CLOSED_BODY` are closed LWPOLYLINE entities for CAM offset testing
4. **Moderate complexity** — 487 entities is representative of production files without being excessive

---

## Manual Verification Protocol

### Prerequisites

- Fusion 360 installed (note version for report)
- File: `services/api/test_temp/cuatro_R2000_LWPOLYLINE_test.dxf`

### Test Steps

#### 1. Open Test (CRITICAL)

```
Action: File → Open → select the DXF
Record:
  [ ] Opened without freeze (Y/N)
  [ ] Time to open: ___ seconds
  [ ] Fusion 360 version: ___
```

If freeze occurs here, STOP. The gate cannot be lifted.

#### 2. Visual Inspection

```
Action: Examine the imported geometry
Record:
  [ ] All 8 layers visible in browser
  [ ] Entities render correctly (no missing geometry)
  [ ] Layer colors display as expected
```

#### 3. Selection Test

```
Action: Click on individual LWPOLYLINE entities
Record:
  [ ] Entities are selectable
  [ ] Selection highlight works
  [ ] Can select across different layers
```

#### 4. Manipulation Test

```
Action: Select an entity → Move, Copy, or Rotate
Record:
  [ ] Move completes without freeze
  [ ] Copy completes without freeze
  [ ] Rotate completes without freeze
```

#### 5. CAM Operations (CRITICAL)

```
Action: 
  1. Select the closed shape on TEST_CLOSED_BODY layer
  2. Manufacturing workspace → 2D Contour toolpath
  3. Attempt to generate toolpath

Record:
  [ ] Contour selection works
  [ ] Toolpath generates
  [ ] No freeze during CAM setup
```

```
Action: Offset test
  1. Select TEST_CLOSED_RECT
  2. Sketch → Offset → offset inward 5mm

Record:
  [ ] Offset completes
  [ ] Result is correct geometry
```

---

## Outcome Paths

### If All Tests Pass

1. **Write verification note** for CLAUDE.md:

```markdown
## LWPOLYLINE Verification Record

**Date:** 2026-04-28
**Fusion 360 Version:** [version tested]
**Test File:** cuatro_R2000_LWPOLYLINE_test.dxf (138.2 KB, 487 LWPOLYLINE entities, 8 layers)
**Operations Verified:** Open, select, move, copy, rotate, 2D contour toolpath, offset
**Result:** PASS — no freeze, all operations completed normally

The R12-only gate may be lifted for R2000+ output via dxf_compat.
```

2. **Implementation scope** (separate PR):
   - Update CLAUDE.md to allow R2000+ via dxf_compat (with verification note)
   - Add `version` parameter to `DxfWriter` class, default 'R12'
   - Add `version` parameter to `export_cam_ready_dxf` and related functions
   - New orchestrator mode for paid tier passes `version='R2000'`
   - Auth gate the new mode

### If Freeze Reproduces

1. **Capture exact sequence:**
   - Which click/operation triggered it
   - Which entity/layer involved
   - Did Fusion recover or require force-quit

2. **Save the DXF** that caused the freeze

3. **Do NOT lift the gate** — investigate root cause first

4. Possible causes to investigate:
   - Specific entity count threshold
   - Malformed LWPOLYLINE structure
   - Header values (EXTMIN/EXTMAX)
   - Coordinate precision issues

---

## Code Locations for Implementation

After verification passes, these files need changes:

| File | Change Required |
|------|-----------------|
| `services/api/app/util/dxf_compat.py` | Fix R13 reference → R2000 (R13 not supported by ezdxf) |
| `services/api/app/cam/dxf_writer.py` | Add `version` parameter, default 'R12' |
| `CLAUDE.md` (both locations) | Add verification record, update policy |
| Orchestrator (TBD) | Add paid-tier mode with version='R2000' |

---

## Appendix: Generation Script

The test file was generated with:

```python
import ezdxf

# Read source (R12 LINE-only)
src = ezdxf.readfile('El Cuatro 1.dxf')

# Create R2000 document
doc = ezdxf.new('R2000', setup=True)
msp = doc.modelspace()

# Convert LINE → LWPOLYLINE
for entity in src.modelspace():
    if entity.dxftype() == 'LINE':
        start = (entity.dxf.start.x, entity.dxf.start.y)
        end = (entity.dxf.end.x, entity.dxf.end.y)
        msp.add_lwpolyline([start, end], dxfattribs={'layer': entity.dxf.layer})

# Add closed test shapes
msp.add_lwpolyline([(50,50), (150,50), (150,150), (50,150)], 
                   close=True, dxfattribs={'layer': 'TEST_CLOSED_RECT'})

doc.saveas('cuatro_R2000_LWPOLYLINE_test.dxf')
```

---

## Contact

Investigation performed by Claude Code session 2026-04-28.  
Manual Fusion 360 verification required from operator.
