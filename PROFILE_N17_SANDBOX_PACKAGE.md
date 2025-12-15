# N.17 Polygon Offset - Performance Profiling Sandbox Package

**Purpose:** Standalone profiling tool for performance analysis in isolated environment  
**Date:** November 14, 2025  
**Status:** Ready for sandbox testing

---

## Quick Start (Sandbox Environment)

```powershell
# 1. Copy these files to sandbox:
scripts/profile_n17_polygon_offset.py
services/api/app/cam/polygon_offset_n17.py
services/api/app/util/gcode_emit_advanced.py
services/api/app/util/gcode_emit_basic.py

# 2. Install dependencies:
pip install pyclipper==1.3.0.post5

# 3. Run profiling:
python profile_n17_polygon_offset.py
```

**Expected Output:** Performance metrics in ~1-2 seconds

---

## What the Profiler Does

### 1. Offset Generation Profiling
Tests polygon offsetting at 3 sizes:
- **Small (30×20mm):** Baseline performance
- **Medium (50×30mm):** Typical use case
- **Large (100×60mm):** Stress test

**Metrics:**
- First offset time (single pass)
- Total pass generation time
- Number of passes created
- Average time per pass

### 2. Arc G-code Generation
Tests advanced G-code with G2/G3 arc commands:
- Offset path generation timing
- Arc emission timing
- Output size (character count)

### 3. Linear G-code Generation
Tests basic G-code with G1 linear moves:
- Offset path generation timing
- Linear emission timing
- Output size comparison vs arcs

### 4. Outward Offsetting (Profiling Mode)
Tests performance of outward direction:
- Small polygon (30×20mm)
- Medium polygon (40×30mm)
- Pass count and timing per size

### 5. Stepover Impact Analysis
Tests 5 stepover values (1-5mm):
- Shows how stepover affects pass count
- Identifies optimal stepover for performance
- Validates linear scaling relationship

---

## Expected Performance Baseline

```
=== OFFSET GENERATION ===
Small (30x20mm):
  First offset: 0.1ms
  Total passes: ~10-20 in 1.1ms
  Avg per pass: 0.05-0.1ms

Medium (50x30mm):
  First offset: 0.0ms
  Total passes: ~20-30 in 1.2ms
  Avg per pass: 0.04-0.06ms

Large (100x60mm):
  First offset: 0.0ms
  Total passes: ~40-50 in 2.0ms
  Avg per pass: 0.04-0.05ms

=== ARC GENERATION ===
Offset: ~20-30 paths in 1.0ms
Arc emit: 15,000-25,000 chars in 2.2ms

=== LINEAR GENERATION ===
Offset: ~20-30 paths in 1.2ms
Linear emit: 8,000-12,000 chars in 0.5ms

=== OUTWARD OFFSETTING ===
Small: 4-8 passes in 0.2ms
Medium: ~20-30 passes in 1.0ms

=== STEPOVER IMPACT ===
1.0mm: ~30-40 passes
2.0mm: ~20-30 passes
3.0mm: ~15-20 passes
4.0mm: ~10-15 passes
5.0mm: ~8-12 passes
```

---

## File Descriptions

### 1. `profile_n17_polygon_offset.py` (Main Script)

**Size:** 225 lines  
**Dependencies:** 
- Python 3.11+
- pyclipper (for polygon offsetting)
- Standard library: sys, time, pathlib

**Structure:**
```python
# Import modules
from app.cam.polygon_offset_n17 import toolpath_offsets, offset_polygon_mm
from app.util.gcode_emit_advanced import emit_xy_with_arcs
from app.util.gcode_emit_basic import emit_xy_polyline_nc

# Test functions (5 profiling scenarios)
def profile_offset_generation()      # Core offsetting
def profile_arc_generation()         # Arc G-code
def profile_linear_generation()      # Linear G-code
def profile_outward_offset()         # Profiling mode
def profile_stepover_impact()        # Stepover analysis

def main()                           # Orchestrator
```

**Key Features:**
- Uses `time.perf_counter()` for microsecond precision
- Tests realistic polygon sizes (not synthetic)
- Prints human-readable results with color coding
- No external file dependencies (self-contained)

### 2. `polygon_offset_n17.py` (Core Algorithm)

**Size:** 203 lines  
**Purpose:** Robust polygon offsetting with pyclipper

**Key Functions:**
```python
def offset_polygon_mm(poly, offset, join_type, arc_tolerance, miter_limit)
    # Single offset operation
    # Returns: List of offset polygons or None
    
def toolpath_offsets(poly, tool_dia, stepover, inward, join_type, arc_tolerance)
    # Generate multiple passes (pocketing/profiling)
    # Returns: List of offset paths
    
def _polygon_area(poly)
    # Calculate signed area (CCW=positive, CW=negative)
    
def _offset_fallback(poly, offset, miter_limit)
    # Simple miter offset if pyclipper unavailable
```

**Algorithm:**
1. Scale coordinates to integer space (×1000)
2. Use pyclipper.PyclipperOffset() for robust offsetting
3. Generate successive inward/outward offsets
4. Stop when area collapses below 0.5mm²
5. Scale back to mm coordinates

**Optimizations (Applied):**
- Early exit for small polygons (< 1mm²)
- Smart pass estimation (5-50 based on area/perimeter)
- Vertex count validation (< 3 = degenerate)

### 3. `gcode_emit_advanced.py` (Arc G-code)

**Size:** 161 lines  
**Purpose:** Generate G-code with G2/G3 arc commands

**Key Functions:**
```python
def emit_xy_with_arcs(paths, z, safe_z, units, feed, feed_arc, feed_floor, link_radius)
    # Main emission function
    # Returns: G-code string with arc fillets
    
def _fillet_points(a, b, c, r)
    # Calculate arc parameters at corner b
    # Returns: (p1, p2, ccw, center) or None
    
def _angle(a, b, c)
    # Calculate angle at point b
```

**Arc Generation:**
- Automatic fillet insertion at corners
- I/J offset calculation for arc centers
- CW/CCW direction detection (cross product)
- Feed rate management (arc vs linear vs tight curves)

### 4. `gcode_emit_basic.py` (Linear G-code)

**Size:** 72 lines  
**Purpose:** Generate G-code with G1 linear moves

**Key Function:**
```python
def emit_xy_polyline_nc(paths, z, safe_z, units, feed, spindle)
    # Emit G1 commands with spindle control
    # Returns: G-code string
```

**Output Structure:**
```gcode
(N17 Polygon Offset)
G21                    # Units (mm)
G90                    # Absolute positioning
G17                    # XY plane
S12000 M3              # Spindle start
G0 Z5.000              # Retract to safe Z
[G0/G1 moves...]       # Toolpath
M5                     # Spindle stop
M30                    # Program end
```

---

## Sandbox Setup Instructions

### Option A: Minimal Setup (Profiler Only)

```bash
# 1. Create sandbox directory
mkdir n17_profile_sandbox
cd n17_profile_sandbox

# 2. Create app structure
mkdir -p app/cam app/util

# 3. Copy files
cp /path/to/scripts/profile_n17_polygon_offset.py .
cp /path/to/services/api/app/cam/polygon_offset_n17.py app/cam/
cp /path/to/services/api/app/util/gcode_emit_advanced.py app/util/
cp /path/to/services/api/app/util/gcode_emit_basic.py app/util/

# 4. Create __init__.py files
touch app/__init__.py app/cam/__init__.py app/util/__init__.py

# 5. Install dependencies
pip install pyclipper==1.3.0.post5

# 6. Run profiler
python profile_n17_polygon_offset.py
```

### Option B: Docker Container (Isolated)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy files
COPY profile_n17_polygon_offset.py .
COPY app/ ./app/

# Install dependencies
RUN pip install --no-cache-dir pyclipper==1.3.0.post5

# Run profiler
CMD ["python", "profile_n17_polygon_offset.py"]
```

```bash
# Build and run
docker build -t n17-profiler .
docker run n17-profiler
```

### Option C: Virtual Environment (Recommended)

```bash
# 1. Create venv
python -m venv n17_venv
source n17_venv/bin/activate  # Linux/Mac
# OR
n17_venv\Scripts\activate.ps1  # Windows

# 2. Install dependencies
pip install pyclipper==1.3.0.post5

# 3. Copy files (see Option A structure)

# 4. Run profiler
python profile_n17_polygon_offset.py
```

---

## What to Look For in Sandbox Results

### 1. Performance Consistency
✅ **Good:** All operations < 5ms  
⚠️ **Investigate:** Any operation > 10ms  
❌ **Problem:** Timeouts or crashes

### 2. Pass Count Validation
✅ **Good:** 5-50 passes depending on size  
⚠️ **Investigate:** 100+ passes (hitting old limit)  
❌ **Problem:** 0 passes or infinite loop

### 3. Memory Usage
✅ **Good:** < 50MB RAM  
⚠️ **Investigate:** 50-200MB RAM  
❌ **Problem:** > 200MB or memory leak

### 4. Output Validation
✅ **Good:** G-code contains G21, G90, G17  
✅ **Good:** Arc mode has G2/G3 commands  
✅ **Good:** Linear mode has M3/M5 spindle control  
❌ **Problem:** Empty output or malformed G-code

### 5. Edge Cases
Test with:
- **Very small polygon:** 5×5mm (should exit early)
- **Very large polygon:** 500×300mm (should complete in < 10ms)
- **Weird shapes:** Triangle, star, irregular (should handle gracefully)

---

## Troubleshooting Sandbox Issues

### Issue: `ModuleNotFoundError: No module named 'pyclipper'`
**Fix:** `pip install pyclipper==1.3.0.post5`

### Issue: `ImportError: cannot import name 'toolpath_offsets'`
**Fix:** Ensure app/cam/__init__.py exists and directory structure matches

### Issue: Performance much slower than baseline
**Possible Causes:**
1. pyclipper not installed (using fallback miter mode)
2. Python interpreter not optimized (try PyPy)
3. Antivirus scanning (exclude sandbox directory)

### Issue: Different pass counts than expected
**Investigation:**
- Check stepover value (default 2.0mm)
- Check polygon size (coordinates in mm)
- Verify smart pass estimation is active (not old max_passes=100)

### Issue: No output or hangs
**Debug:**
```python
# Add print statements to profile_n17_polygon_offset.py
print("Starting offset generation...")
paths = toolpath_offsets(...)
print(f"Generated {len(paths)} paths")
```

---

## Interpreting Results

### Offset Generation Times
- **< 1ms:** Excellent (typical for small-medium polygons)
- **1-3ms:** Good (typical for large polygons)
- **3-10ms:** Acceptable (complex polygons or many passes)
- **> 10ms:** Investigate (may indicate issue)

### Pass Counts
- **Formula:** `passes ≈ (perimeter / 2) / stepover`
- **Example:** 50×30mm rect, 2mm stepover → ~20 passes
- **Validation:** Should match estimated_passes calculation

### Arc vs Linear Timing
- **Arc G-code:** 2-5× longer to generate (more math)
- **Arc output:** 1.5-3× larger file size (I/J parameters)
- **Trade-off:** Slower generation but smoother motion

---

## Files to Package for Sandbox

### Minimum Required (4 files)
```
profile_n17_polygon_offset.py        # Main profiler script
app/cam/polygon_offset_n17.py        # Core algorithm
app/util/gcode_emit_advanced.py      # Arc G-code generator
app/util/gcode_emit_basic.py         # Linear G-code generator
```

### Supporting Files (3 files)
```
app/__init__.py                      # Empty (Python package marker)
app/cam/__init__.py                  # Empty
app/util/__init__.py                 # Empty
```

### Documentation (2 files)
```
PROFILE_N17_SANDBOX_PACKAGE.md       # This file
N17_PERFORMANCE_INVESTIGATION_SUMMARY.md  # Full investigation report
```

**Total Package Size:** ~50KB (all files combined)

---

## Expected Sandbox Results (Reference)

```
============================================================
N.17 POLYGON OFFSET PERFORMANCE PROFILING
============================================================

=== PROFILING OFFSET GENERATION ===

Small (30x20mm):
  First offset: 0.1ms
  Total passes: 8 in 0.9ms
  Avg per pass: 0.1ms

Medium (50x30mm):
  First offset: 0.0ms
  Total passes: 15 in 1.1ms
  Avg per pass: 0.1ms

Large (100x60mm):
  First offset: 0.0ms
  Total passes: 30 in 1.8ms
  Avg per pass: 0.1ms


=== PROFILING ARC GENERATION ===

Offset generation: 15 paths in 1.0ms
Arc G-code emit: 18,245 chars in 2.0ms


=== PROFILING LINEAR GENERATION ===

Offset generation: 15 paths in 1.1ms
Linear G-code emit: 9,876 chars in 0.4ms


=== PROFILING OUTWARD OFFSETTING ===

Small (30x20mm) outward:
  Passes: 5 in 0.2ms
  Avg: 0.0ms per pass

Medium (40x30mm) outward:
  Passes: 12 in 0.8ms
  Avg: 0.1ms per pass


=== PROFILING STEPOVER IMPACT ===

Stepover 1.0mm: 30 passes in 1.5ms
Stepover 2.0mm: 15 passes in 1.0ms
Stepover 3.0mm: 10 passes in 0.8ms
Stepover 4.0mm: 8 passes in 0.7ms
Stepover 5.0mm: 6 passes in 0.6ms

============================================================
PROFILING COMPLETE
============================================================
```

---

## Post-Sandbox Actions

### If Results Match Baseline (Expected)
✅ Algorithm optimizations confirmed working  
✅ Performance acceptable for production  
✅ Ready to proceed with N.18 validation

### If Results Differ
1. **Document differences** (timing, pass counts, output)
2. **Check environment** (Python version, pyclipper version, OS)
3. **Compare G-code output** (diff against reference files)
4. **Report findings** for further investigation

---

## Quick Reference Commands

```bash
# Profile performance
python profile_n17_polygon_offset.py

# Check pyclipper version
pip show pyclipper

# Validate G-code output manually
python -c "from app.cam.polygon_offset_n17 import toolpath_offsets; \
           paths = toolpath_offsets([(0,0),(50,0),(50,30),(0,30)], 6, 2, True); \
           print(f'Generated {len(paths)} paths')"

# Time a specific operation
python -c "import time; \
           from app.cam.polygon_offset_n17 import offset_polygon_mm; \
           t=time.perf_counter(); \
           r=offset_polygon_mm([(0,0),(50,0),(50,30),(0,30)], -2, 'round', 0.25); \
           print(f'{(time.perf_counter()-t)*1000:.2f}ms')"
```

---

## Contact/Support

**Issue:** Sandbox results don't match baseline  
**Action:** Document actual values and compare against "Expected Performance Baseline" section

**Issue:** Profiler crashes or hangs  
**Action:** Check Python version (3.11+), pyclipper installation, file structure

**Issue:** Want to test different polygon shapes  
**Action:** Modify test_cases list in profile_n17_polygon_offset.py

---

**Package Status:** ✅ Ready for sandbox deployment  
**Last Updated:** November 14, 2025  
**Tested On:** Windows 11, Python 3.11, pyclipper 1.3.0.post5
