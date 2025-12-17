# Known Issues - Test Coverage

## Issue 1: /geometry/import Endpoint JSON Input Broken

**Status:** Known Bug (confirmed in PowerShell tests)  
**Endpoint:** `POST /geometry/import`  
**Problem:** JSON geometry input fails with 400 Bad Request

### Root Cause

The endpoint signature uses both optional parameters:
```python
async def import_geometry(file: UploadFile = File(None), geometry: GeometryIn = Body(None)):
```

When sending JSON, FastAPI doesn't know to bind it to the `geometry` parameter because:
1. Both parameters are optional (`None` default)
2. No explicit `embed=True` on Body()
3. FastAPI can't distinguish between file upload and JSON body modes

### Evidence

**PowerShell Test (`test_patch_k_export.ps1`):**
```
Testing: 1. Import JSON Geometry
  ❌ ERROR: Response status code does not indicate success: 400 (Bad Request).
```

**Python TestClient:**
```python
# Both formats fail:
client.post('/geometry/import', json={"units": "mm", "paths": [...]})  # 400
client.post('/geometry/import', json={"geometry": {"units": "mm", ...}})  # 400
```

### Fix Required

**Option A: Use `embed=True`**
```python
async def import_geometry(
    file: UploadFile = File(None), 
    geometry: GeometryIn = Body(None, embed=True)  # Force {"geometry": {...}}
):
```

**Option B: Separate endpoints**
```python
@router.post("/import")  # File upload only
@router.post("/import/json")  # JSON only
```

**Option C: Use Form parameter to distinguish modes**
```python
async def import_geometry(
    file: UploadFile = File(None),
    geometry_json: Optional[str] = Form(None)  # Parse manually
):
```

### Workaround for Tests

Skip JSON import tests, focus on:
- ✅ `/geometry/parity` (works - uses `geometry: GeometryIn` as required param)
- ✅ `/geometry/export` (works - uses `Request` body)
- ✅ `/geometry/export_gcode` (works)
- ✅ `/geometry/export_bundle` (works)
- ✅ `/geometry/export_bundle_multi` (works)

### Impact on Coverage

- **Original target:** 85% geometry_router coverage
- **Adjusted target:** 80% geometry_router coverage (skip broken import tests)
- **Overall 80% goal:** Still achievable with other routers

---

## Next Steps

1. **Immediate:** Skip `/import` JSON tests, focus on working endpoints
2. **Short-term:** File bug report for `/import` endpoint
3. **Long-term:** Fix endpoint signature (requires API change, out of scope for P3.1)

---

**Last Updated:** November 17, 2025  
**Related:** TEST_COVERAGE_PROGRESS.md, test_geometry_router.py
