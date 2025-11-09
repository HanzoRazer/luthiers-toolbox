# G-code Reader Enhancement Summary

## Overview
Enhanced `gcode_reader.py` - a dependency-free G-code parser and analyzer for CNC lutherie workflows in Luthier's ToolBox.

## New Features Added

### 1. **Validation System** (`--validate` flag)
```python
def validate_gcode(summary: Summary, moves: List[Move]) -> None:
    """Run safety and sanity checks on parsed G-code"""
```
- Checks for missing motion, spindle, or feedrate
- Warns on extreme speeds (>5000 mm/min, <10 mm/min)
- Warns on high RPM (>24000)
- Warns on oversized bounding boxes (>2000mm - potential coordinate system issue)
- Estimates machining time from feed distance
- Detects programs going below Z=0

### 2. **Enhanced Summary Dataclass**
```python
@dataclass
class Summary:
    warnings: List[str] = field(default_factory=list)  # NEW
    errors: List[str] = field(default_factory=list)    # NEW
    filename: str = ""                                  # NEW
    file_size_bytes: int = 0                            # NEW
    estimated_time_minutes: Optional[float] = None      # NEW
    # ... existing fields
```

### 3. **Robust Error Handling**
- Try/except blocks for file reading with encoding error handling
- File existence validation
- File size checks (warns on >100MB files)
- Exit code 1 if errors found during validation

### 4. **Enhanced Report Formatting**
- Unicode box drawing characters and emojis
- Organized sections with visual hierarchy
- File metadata display (name, size)
- Estimated machining time
- Span calculations for bbox dimensions
- Dedicated warnings/notes/errors sections

### 5. **New Command-Line Options**
```bash
python gcode_reader.py file.nc --validate  # Run safety checks
python gcode_reader.py file.nc --quiet     # Suppress console output
python gcode_reader.py file.nc --pretty    # Enhanced motion listing
```

## Example Output

```
╔════════════════════════════════════════════════════════════╗
║         G‑code Summary - Luthier's ToolBox                ║
╚════════════════════════════════════════════════════════════╝

📄 File:           test_sample.nc
📊 Size:           525 bytes (0.5 KB)

⚙️  Program Configuration
────────────────────────────────────────────────────────────
Units:            mm (mm)
Coordinates:      absolute (G90)
Planes:           G17 (active G17)
Lines:            18

🔧 Motion Statistics
────────────────────────────────────────────────────────────
Total motions:    11
  ├─ Rapids:      6 moves
  ├─ Feeds:       5 moves
  └─ Arcs:        0 moves

Feedrate range:   300.0000 mm/min .. 1200.0000 mm/min
Spindle RPM:      12000.0000 RPM .. 12000.0000 RPM
Tools:            —
⏱️  Estimated time:  0 minutes (cut time only)

📏 Program Bounds
────────────────────────────────────────────────────────────
X: 0.0000 mm .. 50.0000 mm  (span: 50.000 mm)
Y: 0.0000 mm .. 50.0000 mm  (span: 50.000 mm)
Z: -2.0000 mm .. 5.0000 mm  (span: 7.000 mm)

📐 Total Travel
────────────────────────────────────────────────────────────
Total distance:   219.0000 mm
  ├─ Rapids:      12.0000 mm
  └─ Feeds:       207.0000 mm

📝 Notes
────────────────────────────────────────────────────────────
  • Program goes below Z=0 (min Z: -2.000mm)
  • Estimated cut time: 0.3 minutes (excluding rapids)
```

## Testing

**Test file created**: `test_sample.nc` - 50mm x 50mm square pocket
**Commands tested**:
```bash
python gcode_reader.py test_sample.nc --validate --pretty
python gcode_reader.py test_sample.nc --validate --json test_output.json --quiet
python gcode_reader.py --help
```

**Results**:
- ✅ All 11 motions detected correctly
- ✅ Bounding box calculated: 50mm x 50mm x 7mm
- ✅ Travel distance: 219mm total
- ✅ Validation notes generated
- ✅ JSON export working
- ✅ Quiet mode functional

## Integration Steps (Next)

### 1. **Move to pipeline directory**
```bash
mkdir -p server/pipelines/gcode_explainer
cp gcode_reader.py server/pipelines/gcode_explainer/
```

### 2. **Create FastAPI wrapper** (`server/pipelines/gcode_explainer/analyze_gcode.py`)
```python
from fastapi import UploadFile
from . import gcode_reader

async def analyze_gcode_file(file: UploadFile, validate: bool = True):
    # Save temp file, run gcode_reader.parse_gcode(), return JSON
    pass
```

### 3. **Add API endpoint** (`server/app.py`)
```python
@app.post("/api/gcode/analyze")
async def analyze_gcode(file: UploadFile, validate: bool = True):
    result = await analyze_gcode_file(file, validate)
    return {"summary": result}
```

### 4. **Create Vue component** (`client/src/components/toolbox/GcodeAnalyzer.vue`)
- File upload
- Display summary with formatted report
- Show warnings/errors
- Download JSON/CSV exports

## Compatibility

- **Python**: 3.11+ (uses dataclasses, pathlib)
- **Dependencies**: None (stdlib only)
- **G-code Dialect**: Fanuc-style (G0/G1/G2/G3, G17/18/19, G20/21, G90/91, M3/M5, S/F/T)
- **Format**: Plain text .nc/.gcode files
- **Encoding**: UTF-8 with fallback to ignore errors

## Files Modified

1. `gcode_reader.py` - Enhanced from 351 to 512 lines
   - Added validation system (40 lines)
   - Enhanced Summary dataclass (5 new fields)
   - Enhanced report formatting (80 lines)
   - Added error handling and file checks
   - Fixed indentation issues in parse loop

## Files Created

1. `test_sample.nc` - Test G-code file (50mm square pocket)
2. `test_output.json` - Example JSON export
3. `GCODE_READER_ENHANCED.md` - This documentation

## Known Limitations

1. **Arc length approximation**: Uses chord length (conservative estimate)
2. **Arc bounding box**: Approximates with start/end/center (may underestimate if arc sweeps past extrema)
3. **Time estimation**: Feed-based only (doesn't account for acceleration, rapids, tool changes)
4. **No toolpath simulation**: Doesn't check for collisions or coordinate system shifts

## Future Enhancements

- [ ] Integrate into FastAPI backend
- [ ] Create Vue component for web UI
- [ ] Add 3D toolpath visualization
- [ ] Support for more G-code variants (Haas, Mazak, etc.)
- [ ] Collision detection
- [ ] Work coordinate system (G54-G59) tracking
- [ ] Tool library integration for actual time estimates
- [ ] Compare multiple G-code files side-by-side

---

**Status**: ✅ Enhancement Complete - Ready for Integration  
**Next Priority**: Integrate BenchMuse StringSpacer (CRITICAL priority missing feature)
