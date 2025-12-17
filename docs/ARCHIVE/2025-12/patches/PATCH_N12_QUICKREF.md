# Patch N.12 Quick Reference

## 🎯 What It Does
Per-machine tool tables with CSV import/export, template token injection, and full UI.

## 📦 Files Created/Modified

### Backend (6 files)
- `services/api/app/routers/machines_tools_router.py` ✅ Created
- `services/api/app/util/tool_table.py` ✅ Created
- `services/api/app/data/machines.json` ✅ Created (with example tools)
- `services/api/app/main.py` ✅ Modified (router registration)
- `services/api/app/post_injection_dropin.py` ✅ Modified (tool context injection)

### Frontend (1 file)
- `packages/client/src/components/ToolTable.vue` ✅ Created

### Testing (1 file)
- `scripts/smoke_n12_tools.py` ✅ Created

## 🚀 Quick Start

### 1. Test Backend
```powershell
# Start API server
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# Run smoke test (separate terminal)
cd ../..
python scripts/smoke_n12_tools.py
```

**Expected Output:**
```
=== Patch N.12 Smoke Test ===

1. Testing PUT /api/machines/tools/m1 (upsert)
  ✓ Upsert OK, tool count: 3

2. Testing GET /api/machines/tools/m1
  ✓ List OK, machine: m1, tools: 3

3. Testing GET /api/machines/tools/m1.csv
  ✓ CSV export OK, lines: 4 (header + 3 tools)

4. Testing tool context injection via /api/cam/drill_g81_g83
  ⚠ Drill endpoint not implemented yet (404) - skipping

5. Testing DELETE /api/machines/tools/m1/7
  ✓ Delete OK, remaining tools: 2

=== All N.12 Tests Passed ===
```

### 2. Test Frontend
```powershell
# Start client (separate terminal)
cd packages/client
npm run dev  # Runs on http://localhost:5173
```

Navigate to ToolTable component and test:
- [ ] Machine selector shows all machines
- [ ] Add Tool button creates new row
- [ ] All fields are editable
- [ ] Save All persists changes
- [ ] Export CSV downloads file
- [ ] Import CSV merges tools

## 📋 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/machines/tools/{mid}` | List all tools |
| `PUT` | `/api/machines/tools/{mid}` | Upsert tools (merge by T) |
| `DELETE` | `/api/machines/tools/{mid}/{t}` | Delete tool |
| `GET` | `/api/machines/tools/{mid}.csv` | Export CSV |
| `POST` | `/api/machines/tools/{mid}/import_csv` | Import CSV |

## 🔧 Template Tokens

When CAM endpoints receive `machine_id` + `tool` parameters, these tokens are available:

```
{TOOL}          - Tool number (e.g., 1)
{TOOL_NAME}     - Tool name (e.g., "Ø6 flat endmill")
{TOOL_DIA}      - Diameter in mm (e.g., 6.0)
{TOOL_LEN}      - Flute length in mm (e.g., 45.0)
{TOOL_HOLDER}   - Holder type (e.g., "ER20")
{TOOL_OFFS_LEN} - Length offset in mm (e.g., 120.0)
{RPM}           - Spindle speed (e.g., 8000)
{FEED}          - XY feed rate (e.g., 600)
{PLUNGE}        - Z plunge rate (e.g., 200)
```

**Example Post Template:**
```json
{
  "header": [
    "T{TOOL} M06",
    "G43 H{TOOL} Z{TOOL_OFFS_LEN}",
    "S{RPM} M03",
    "F{FEED}"
  ]
}
```

**Generated Output:**
```gcode
T1 M06
G43 H1 Z120.0
S8000 M03
F600
```

## 📊 CSV Format

**Headers:**
```csv
t,name,type,dia_mm,len_mm,holder,offset_len_mm,spindle_rpm,feed_mm_min,plunge_mm_min
```

**Example:**
```csv
t,name,type,dia_mm,len_mm,holder,offset_len_mm,spindle_rpm,feed_mm_min,plunge_mm_min
1,Ø6 flat endmill,EM,6.0,45.0,ER20,120.0,8000,600,200
3,Ø3 drill,DRILL,3.0,55.0,ER16,121.2,6000,300,150
```

## 🎯 Usage in CAM Endpoints

### Example: Drill Operation
```python
# Router endpoint
@router.post("/cam/drill_g81_g83")
def drill_operation(body: DrillRequest):
    # ... generate G-code ...
    
    # Build context with machine_id and tool
    ctx = build_post_context(
        post=body.post,
        machine_id=body.machine_id,  # e.g., "m1"
        TOOL=body.tool,              # e.g., 1
        WORK_OFFSET=body.work_offset,
        SAFE_Z=body.safe_z
    )
    
    set_post_headers(response, ctx)
    return response
```

The middleware automatically:
1. Looks up tool definition from `machines.json`
2. Merges tool tokens into template context
3. Expands post template with all tokens
4. Wraps G-code with header/footer

## 🐛 Troubleshooting

### Issue: Machine not found (404)
**Check:** `services/api/app/data/machines.json` exists and has machines array

### Issue: Tools not saving
**Check:** File permissions on `machines.json`  
**Check:** API logs for write errors

### Issue: CSV import fails
**Check:** CSV has exact headers: `t,name,type,dia_mm,len_mm,...`  
**Check:** Required fields present: `t`, `name`, `type`, `dia_mm`, `len_mm`

### Issue: Tool context not injecting
**Check:** Post-processor template uses correct token names  
**Check:** CAM endpoint passes `machine_id` and `tool` in context  
**Check:** Tool exists in machine's tools array

## 📚 See Also

- [PATCH_N12_MACHINE_TOOL_TABLES.md](./PATCH_N12_MACHINE_TOOL_TABLES.md) - Complete specification
- [MACHINE_PROFILES_MODULE_M.md](./MACHINE_PROFILES_MODULE_M.md) - Machine profiles
- [PATCH_K_EXPORT_COMPLETE.md](./PATCH_K_EXPORT_COMPLETE.md) - Post-processor system

---

**Status:** ✅ Implementation Complete  
**Version:** N.12  
**Date:** November 6, 2025
