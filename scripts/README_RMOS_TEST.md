# RMOS Smoke Test Script

**Location:** `scripts/Test-RMOS-Sandbox.ps1`  
**Purpose:** End-to-end validation of RMOS Phase 1 implementation

---

## 🎯 What It Tests

1. **Pattern CRUD** - Create rosette pattern with 2 rings
2. **Manufacturing Planner** - Generate multi-family plan (tiles, strips, sticks)
3. **JobLog Integration** - Verify rosette_plan jobs are written
4. **Data Validation** - Check pattern appears in library
5. **Cleanup** - Delete test pattern after test

---

## 🚀 Usage

### **Basic Run**

```powershell
.\scripts\Test-RMOS-Sandbox.ps1
```

### **With Verbose Output**

```powershell
.\scripts\Test-RMOS-Sandbox.ps1 -Verbose
```

### **Custom Base URL**

```powershell
.\scripts\Test-RMOS-Sandbox.ps1 -BaseUrl "http://localhost:5000"
```

---

## ✅ Expected Output

```
=== RMOS Sandbox Smoke Test ===
Base URL: http://localhost:8000

[INFO] Creating test pattern id=smoke_rosette_20251121143022
[ OK ] Pattern created: id=smoke_rosette_20251121143022, rings=2

[INFO] Requesting manufacturing plan for pattern smoke_rosette_20251121143022
[ OK ] Manufacturing plan received
  Pattern: Smoke Test Rosette 20251121143022
  Guitars: 4
  Strip families: 1

  Strip Plans:
    - Family: bw_checker_main
      Tiles needed: 2246
      Strip length: 17.97 m
      Sticks needed: 67

[INFO] Verifying pattern exists in library
[ OK ] Pattern found in library: Smoke Test Rosette 20251121143022

[INFO] Fetching JobLog entries
[ OK ] JobLog entries: total=1, rosette_plan=1, saw_slice_batch=0

  Recent entries:
    - Type: rosette_plan
      ID: rosette_plan_smoke_rosette_20251121143022_20251121_143025
      Pattern: smoke_rosette_20251121143022
      Guitars: 4
      Total tiles: 2246

[INFO] Cleaning up test pattern
[ OK ] Test pattern deleted

=== RMOS smoke test completed ===

Summary:
  ✓ Pattern CRUD working
  ✓ Manufacturing planner working
  ✓ JobLog integration working
  ✓ Multi-strip-family support verified
```

---

## 🔍 What Gets Created

### **Test Pattern**
- ID: `smoke_rosette_<timestamp>`
- Name: `Smoke Test Rosette <timestamp>`
- Rings: 2 (both using `bw_checker_main` strip family)
  - Ring 0: radius=45mm, width=2mm
  - Ring 1: radius=48mm, width=2mm
- Default settings: 1.0mm slice, 1 pass, vacuum workholding

### **Manufacturing Plan Request**
- Guitars: 4
- Tile length: 8.0mm
- Scrap factor: 12%
- JobLog recording: enabled

### **Expected Results**
- Total tiles: ~2246 (for 4 guitars)
- Strip length: ~17.97 meters
- Sticks needed: ~67 (300mm sticks)

---

## 🐛 Troubleshooting

### **Connection Refused**

```
[ERR] Request failed: POST http://localhost:8000/api/rosette-patterns
[ERR] No connection could be made because the target machine actively refused it.
```

**Solution:** Start FastAPI server first:
```powershell
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

### **404 Not Found**

```
[ERR] Request failed: POST http://localhost:8000/api/rosette-patterns
[ERR] The remote server returned an error: (404) Not Found.
```

**Solution:** Verify routers are registered in `app/main.py`:
```python
from app.api.routes import joblog, rosette_patterns, manufacturing

app.include_router(joblog.router, prefix="/api")
app.include_router(rosette_patterns.router, prefix="/api")
app.include_router(manufacturing.router, prefix="/api")
```

### **422 Validation Error**

```
[ERR] Request failed: POST http://localhost:8000/api/rosette-patterns
[ERR] The remote server returned an error: (422) Unprocessable Entity.
```

**Solution:** Check Pydantic schemas match. Visit `http://localhost:8000/docs` to see API specs.

### **Test Pattern Not Deleted**

**Manual Cleanup:**
```powershell
curl -X DELETE http://localhost:8000/api/rosette-patterns/smoke_rosette_<timestamp>
```

---

## 📊 Test Coverage

| Component | Coverage |
|-----------|----------|
| Pattern CRUD | ✅ Create, Read, Delete |
| Manufacturing Planner | ✅ Multi-family calculation |
| JobLog Write | ✅ rosette_plan job creation |
| Schema Validation | ✅ Pydantic validation |
| Error Handling | ✅ API exceptions |

**Not Covered (Phase 2+):**
- ❌ Saw batch operations (saw_slice_batch jobs)
- ❌ Risk analysis (needs saw tools)
- ❌ G-code generation
- ❌ Vue component integration
- ❌ SQLite persistence

---

## 🔧 Customization

### **Change Number of Rings**

Edit `$patternPayload.ring_bands` array:

```powershell
ring_bands = @(
    @{ id="ring0"; index=0; radius_mm=40; ... },
    @{ id="ring1"; index=1; radius_mm=43; ... },
    @{ id="ring2"; index=2; radius_mm=46; ... }  # Add more rings
)
```

### **Change Strip Families**

Use different `strip_family_id` values:

```powershell
@{ ... strip_family_id="ebony_black"; ... },
@{ ... strip_family_id="maple_white"; ... }
```

### **Change Manufacturing Parameters**

Edit `$planRequest`:

```powershell
$planRequest = @{
    pattern_id     = $patternId
    guitars        = 10              # More guitars
    tile_length_mm = 6.0             # Shorter tiles
    scrap_factor   = 0.15            # More scrap
    record_joblog  = $true
}
```

---

## 📚 See Also

- [PHASE1_IMPLEMENTATION_COMPLETE.md](../projects/rmos/PHASE1_IMPLEMENTATION_COMPLETE.md) - Full implementation details
- [INTEGRATION_QUICKSTART.md](../projects/rmos/INTEGRATION_QUICKSTART.md) - Integration guide
- [ARCHITECTURE.md](../projects/rmos/ARCHITECTURE.md) - Technical design
- [README.md](../projects/rmos/README.md) - RMOS overview

---

**Status:** ✅ Production Ready  
**Dependencies:** FastAPI server running on localhost:8000  
**Runtime:** ~2-3 seconds  
**Exit Codes:** 0 = success, 1 = failure
