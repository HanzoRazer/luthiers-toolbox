# Patches I, I1, J - Quick Reference

## 🚀 Quick Start

### Start Server
```powershell
cd server
.\.venv\Scripts\Activate.ps1
uvicorn app:app --reload --port 8000
```

### API Base URL
```
http://localhost:8000
```

---

## 📡 API Endpoints

### 1. Simulate G-code
```bash
# Endpoint
POST /cam/simulate_gcode

# Example: Safe toolpath
curl -X POST http://localhost:8000/cam/simulate_gcode \
  -H "Content-Type: application/json" \
  -d '{
    "gcode": "G0 Z10\nG0 X50 Y50\nG1 Z-3 F1200\nG1 X100 Y100",
    "safe_z": 5.0,
    "units": "mm",
    "feed_xy": 1200,
    "feed_z": 600
  }'

# Example: Export CSV
curl -X POST http://localhost:8000/cam/simulate_gcode \
  -H "Content-Type: application/json" \
  -d '{"gcode": "...", "safe_z": 5.0, "as_csv": true}' \
  --output trace.csv
```

**Response Headers**:
- `X-CAM-Summary`: JSON summary string
- `X-CAM-Safe`: `"true"` or `"false"`
- `X-CAM-Issues`: Issue count

### 2. Get Tool Library
```bash
# Endpoint
GET /cam/tools

# Example
curl http://localhost:8000/cam/tools | jq '.tools[] | {id, type, diameter_mm, default_rpm}'
```

**Response**: 12 tools with 7 materials

### 3. Get Post-Processors
```bash
# Endpoint
GET /cam/posts

# Example
curl http://localhost:8000/cam/posts | jq 'keys'
```

**Response**: 10 CNC controller profiles

### 4. Calculate Optimized Feeds
```bash
# Endpoint
POST /cam/tools/{tool_id}/calculate_feeds?material={material}&doc={depth}&woc={width}

# Example
curl -X POST "http://localhost:8000/cam/tools/flat_6.0/calculate_feeds?material=Hard%20Maple&doc=3.0&woc=4.0"
```

**Response**:
```json
{
  "optimized": {
    "rpm": 16000,
    "feed_xy": 1620.0,
    "feed_z": 360.0,
    "chip_load_mm": 0.0506
  }
}
```

---

## 🛠️ Tool Database

### Available Tools (12)
| ID | Type | Diameter | Flutes | Default RPM | Default Feed XY | Notes |
|----|------|----------|--------|-------------|-----------------|-------|
| `flat_3.175` | Flat | 3.175mm | 2 | 18000 | 1500 mm/min | 1/8" detail work |
| `flat_6.0` | Flat | 6.0mm | 2 | 16000 | 1800 mm/min | General-purpose |
| `flat_6.35` | Flat | 6.35mm | 2 | 16000 | 2000 mm/min | 1/4" standard |
| `flat_12.7` | Flat | 12.7mm | 3 | 14000 | 2500 mm/min | 1/2" heavy cuts |
| `ball_3.0` | Ball | 3.0mm | 2 | 18000 | 1200 mm/min | Small radius |
| `ball_6.0` | Ball | 6.0mm | 2 | 16000 | 1500 mm/min | Large radius |
| `vbit_60` | V-bit | 6.35mm | 2 | 16000 | 1200 mm/min | 60° chamfers |
| `vbit_90` | V-bit | 6.35mm | 2 | 16000 | 1000 mm/min | 90° V-carve |
| `drill_3.0` | Drill | 3.0mm | 2 | 4000 | 200 mm/min | Small holes |
| `drill_6.35` | Drill | 6.35mm | 2 | 3000 | 150 mm/min | 1/4" holes |
| `drill_10.0` | Drill | 10.0mm | 2 | 2500 | 120 mm/min | Large holes |
| `compression_6.35` | Compression | 6.35mm | 2 | 16000 | 1800 mm/min | Thin stock |

### Material Coefficients (k)
| Material | k | Hardness | Use Case |
|----------|---|----------|----------|
| **Birch Ply** | 1.0 | Medium | Reference material |
| **Hard Maple** | 0.9 | Hard | Back/sides, necks |
| **Mahogany** | 0.85 | Medium-Soft | Bodies, necks |
| **Spruce** | 1.1 | Soft | Soundboards |
| **Rosewood** | 0.75 | Hard | Fretboards, bridges |
| **Ebony** | 0.7 | Very Hard | Fretboards |
| **MDF** | 1.2 | Medium | Templates |

**Feed Adjustment**: `adjusted_feed = default_feed × k`

---

## 🎛️ Post-Processors

### Available Controllers (10)
| ID | Name | Description | Arc Support | Tool Changer |
|----|------|-------------|-------------|--------------|
| `grbl` | GRBL | Arduino-based (hobby) | ✅ | ❌ |
| `mach4` | Mach4 | Industrial PC-based | ✅ | ✅ |
| `linuxcnc` | LinuxCNC | Open-source CNC | ✅ | ✅ |
| `pathpilot` | PathPilot | Tormach controller | ✅ | ✅ |
| `masso` | MASSO | G3 touch controller | ✅ | ✅ |
| `fusion360` | Fusion 360 | Autodesk CAM | ✅ | ✅ |
| `vcarve` | VCarve | Vectric CAM | ✅ | ❌ |
| `shopbot` | ShopBot | ShopBot Control | ✅ | ❌ |
| `haas` | HAAS | Industrial VMC | ✅ | ✅ |
| `fanuc` | FANUC | Industrial CNC | ✅ | ✅ |

---

## ⚠️ Safety Rules

### Error: Unsafe Rapid
**Rule**: G0 (rapid) moves must be at or above `safe_z`

**Example**:
```gcode
G0 X50 Y50  ; OK
G0 Z2       ; ❌ ERROR if safe_z=5
```

### Warning: Cut Below Safe After Rapid
**Rule**: G1/G2/G3 (cutting) shouldn't start below `safe_z` after G0

**Example**:
```gcode
G0 Z10      ; Above safe Z
G0 X50      ; Still OK
G1 Z2       ; ⚠️ WARNING: cutting started below safe Z
```

---

## 📊 Simulation Output

### JSON Structure
```json
{
  "moves": [
    {"i": 0, "code": "G0", "x": 0, "y": 0, "z": 10, "dx": 0, "dy": 0, "dz": 10, "dxy": 0}
  ],
  "issues": [
    {"index": 1, "line": 2, "type": "unsafe_rapid", "severity": "error", "msg": "..."}
  ],
  "summary": {
    "units": "mm",
    "safe_z": 5.0,
    "total_xy_mm": 141.42,
    "total_z_mm": 15.0,
    "est_minutes": 2.62,
    "move_count": 4,
    "issue_count": 0
  },
  "safety": {
    "safe": true,
    "error_count": 0,
    "warning_count": 0,
    "errors": [],
    "warnings": [],
    "total_issues": 0
  }
}
```

### CSV Format
```csv
i,code,x,y,z,dx,dy,dz,dxy
0,G0,0.0000,0.0000,10.0000,0.0000,0.0000,10.0000,0.0000
1,G1,50.0000,50.0000,-3.0000,50.0000,50.0000,-13.0000,70.7107
```

---

## 🧪 Testing Checklist

### Manual Tests
```bash
# 1. Safe simulation (expect: safe=true)
curl -X POST http://localhost:8000/cam/simulate_gcode \
  -H "Content-Type: application/json" \
  -d '{"gcode": "G0 Z10\nG1 Z-3 F1200", "safe_z": 5.0}' | jq '.safety.safe'

# 2. Unsafe rapid (expect: error)
curl -X POST http://localhost:8000/cam/simulate_gcode \
  -H "Content-Type: application/json" \
  -d '{"gcode": "G0 Z2\nG1 X50", "safe_z": 5.0}' | jq '.issues[0].type'

# 3. CSV export (expect: CSV file)
curl -X POST http://localhost:8000/cam/simulate_gcode \
  -H "Content-Type: application/json" \
  -d '{"gcode": "G0 Z10\nG1 X100", "as_csv": true}' --output test.csv

# 4. Tool count (expect: 12)
curl http://localhost:8000/cam/tools | jq '.tools | length'

# 5. Post count (expect: 10)
curl http://localhost:8000/cam/posts | jq 'keys | length'

# 6. Feed calculator (expect: adjusted feeds)
curl -X POST "http://localhost:8000/cam/tools/flat_6.0/calculate_feeds?material=Hard%20Maple&doc=3&woc=4" | jq '.optimized.feed_xy'
```

### Expected Results
| Test | Expected Output |
|------|----------------|
| Safe simulation | `true` |
| Unsafe rapid | `"unsafe_rapid"` |
| CSV export | File created with header |
| Tool count | `12` |
| Post count | `10` |
| Feed calculator | `1620.0` (1800 × 0.9) |

---

## 🔧 Configuration

### Environment Variables
```bash
# Custom tool library path
export TOOLBOX_TOOL_LIBRARY=/path/to/custom_tools.json

# Custom post-processor profiles
export TOOLBOX_POST_PROFILES=/path/to/custom_posts.json
```

### Default Paths
- Tool Library: `server/assets/tool_library.json`
- Post Profiles: `server/assets/post_profiles.json`

---

## 📁 File Locations

### Server Files
```
server/
├── sim_validate.py              # G-code parser/simulator
├── cam_sim_router.py            # Simulation endpoint
├── tool_router.py               # Tool/post endpoints
└── assets/
    ├── tool_library.json        # 12 tools, 7 materials
    └── post_profiles.json       # 10 controllers
```

### Client Files (Documented, not yet integrated)
```
client/src/components/toolbox/
└── SimLab.vue                   # Animated playback UI
```

---

## 🐛 Common Issues

### Issue: "Tool not found"
**Solution**: Check tool ID matches one of the 12 tools in `tool_library.json`

### Issue: "Material not found"
**Solution**: Use exact material name (case-sensitive): "Hard Maple", "Rosewood", etc.

### Issue: "Simulation returns empty moves"
**Solution**: Ensure G-code contains at least one G0/G1/G2/G3 move

### Issue: "CSV export shows JSON"
**Solution**: Set `as_csv: true` in request body

---

## 🚦 Integration Status

| Component | Status | Notes |
|-----------|--------|-------|
| **Server-Side** | ✅ Complete | All endpoints functional |
| **Client-Side** | 📝 Documented | SimLab.vue ready for integration |
| **Documentation** | ✅ Complete | Full guide in PATCHES_I-I1-J_INTEGRATION.md |
| **Testing** | ⏳ Pending | Awaiting manual validation |

---

## 📚 Full Documentation
See: `PATCHES_I-I1-J_INTEGRATION.md`

---

**Last Updated**: 2025-11-04  
**Version**: 1.0.0
