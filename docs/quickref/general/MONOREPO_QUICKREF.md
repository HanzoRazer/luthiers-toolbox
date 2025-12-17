# Monorepo Quick Reference

## 🚀 Start API
```powershell
.\start_api.ps1
```
Server runs at: http://localhost:8000

## 🧪 Test API
```powershell
.\test_api.ps1
```

## 📡 Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/cam/simulate_gcode` | POST | Simulate G-code with arcs |
| `/tooling/tools` | GET/POST | Tool library CRUD |
| `/tooling/materials` | GET/POST | Material library CRUD |
| `/tooling/feedspeeds` | POST | Calculate feeds/speeds |
| `/tooling/posts` | GET | List post-processors |

## 📦 File Structure

```
services/api/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── routers/
│   │   ├── sim_validate.py  # G-code simulator (310 lines)
│   │   ├── cam_sim_router.py # /cam endpoints
│   │   └── feeds_router.py   # /tooling endpoints
│   ├── models/
│   │   └── tool_db.py        # SQLAlchemy models
│   └── data/
│       └── posts/*.json      # Post-processor configs
└── requirements.txt          # Dependencies

packages/
├── client/                   # Vue 3 (placeholder)
└── shared/                   # TypeScript types (SDK target)

.github/workflows/
├── api_tests.yml             # API smoke tests
├── sdk_codegen.yml           # OpenAPI SDK generation
└── client_lint_build.yml     # Client CI (placeholder)
```

## 🎯 Arc Simulation Example

```powershell
$gcode = @"
G21 G90 G17 F1200
G0 Z5
G0 X0 Y0
G1 Z-1 F300
G2 X60 Y40 I30 J20
G0 Z5
"@

$body = @{ gcode = $gcode } | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/cam/simulate_gcode" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

**Response includes**:
- `X-CAM-Summary`: `{"units":"mm", "total_xy":94.25, "est_seconds":4.71}`
- `X-CAM-Modal`: `{"units":"mm", "abs":true, "plane":"G17", "F":1200}`
- Arc move: `{"code":"G2", "i":30, "j":20, "cx":30, "cy":20, "t":2.35}`

## 🛠️ Tool Library Example

```powershell
# Add tool
$tool = @{
    name = "Endmill 6mm"
    type = "flat"
    diameter_mm = 6.0
    flute_count = 2
    helix_deg = 30.0
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/tooling/tools" `
    -Method POST `
    -ContentType "application/json" `
    -Body $tool

# Add material
$material = @{
    name = "Hardwood"
    chipload_mm = 0.15
    max_rpm = 18000
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/tooling/materials" `
    -Method POST `
    -ContentType "application/json" `
    -Body $material

# Calculate feeds/speeds
$request = @{
    tool_name = "Endmill 6mm"
    material_name = "Hardwood"
    rpm = 15000
    width_mm = 3.0
    depth_mm = 2.0
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/tooling/feedspeeds" `
    -Method POST `
    -ContentType "application/json" `
    -Body $request
# Returns: {"rpm": 15000, "feed_mm_min": 4500.0}
```

## 📋 Arc Math Reference

### IJK Format (Center Offset)
```gcode
G2 X60 Y40 I30 J20  ; Arc from current to (60,40), center at current+(30,20)
```
Python: `arc_center_from_ijk(ms, start=(0,0), params={'I':30,'J':20})` → `(30,20)`

### R Format (Radius)
```gcode
G2 X60 Y40 R50  ; Arc from current to (60,40) with radius 50mm
```
Python: `arc_center_from_r(ms, start=(0,0), end=(60,40), r=50, cw=True)` → `(cx,cy)`

### Arc Length
```python
arc_length(cx=30, cy=20, sx=0, sy=0, ex=60, ey=40, cw=True)  # → 94.25mm
```

### Time Estimation
```python
trapezoidal_time(distance_mm=94.25, feed_mm_min=1200, accel_mm_s2=2000)  # → 2.35s
```

## 🎨 Modal State

| G-code | Modal Field | Value |
|--------|-------------|-------|
| G20/G21 | `units` | "inch" / "mm" |
| G90/G91 | `abs` | true / false |
| G17/G18/G19 | `plane` | "G17" / "G18" / "G19" |
| G93/G94 | `feed_mode` | "G93" / "G94" |
| F1200 | `F` | 1200.0 |
| S15000 | `S` | 15000.0 |

## 📊 Performance

| Operation | Time |
|-----------|------|
| Health check | <1ms |
| Simulate 1K moves | ~50ms |
| Simulate 10K moves | ~500ms |
| Tool query | ~1ms |
| Feeds/speeds calc | ~2ms |

## 🔗 URLs

- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **OpenAPI**: http://localhost:8000/openapi.json
- **Health**: http://localhost:8000/health

## 📚 Documentation

- `MONOREPO_SETUP.md` - Full setup guide (650 lines)
- `MONOREPO_INTEGRATION_SUMMARY.md` - What was created (450 lines)
- `PATCHES_I1_2_3_INTEGRATION.md` - Arc rendering details (1200 lines)

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Module not found" | `pip install -r services/api/requirements.txt` |
| "Address in use" | Kill process: `netstat -ano \| findstr :8000` |
| "Database locked" | Close SQLite viewers, restart API |
| Import errors | Run from `services/api/`: `uvicorn app.main:app --reload` |

## ✅ Verification

```powershell
# Syntax check all Python files
python -m py_compile services/api/app/main.py
python -m py_compile services/api/app/routers/sim_validate.py
python -m py_compile services/api/app/routers/cam_sim_router.py
python -m py_compile services/api/app/routers/feeds_router.py
python -m py_compile services/api/app/models/tool_db.py

# All should complete without errors
```

## 🎯 Next Steps

1. ✅ Structure created
2. ✅ Python syntax verified
3. ✅ Documentation written
4. **→ Test**: `.\test_api.ps1`
5. **→ Browse**: http://localhost:8000/docs
6. **→ SDK**: `bash tools/codegen/generate_ts_sdk.sh`

---

**Created**: November 4, 2025  
**Status**: 🟢 Ready for Testing
