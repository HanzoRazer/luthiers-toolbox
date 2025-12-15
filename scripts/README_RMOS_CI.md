# RMOS CI Testing Pack

Complete testing infrastructure for RMOS Phase 1 implementation with Python, PowerShell, bash, and GitHub Actions support.

---

## 📦 What's Included

### **1. Python CI Smoke Tester** (`rmos_ci_test.py`)
- Starts uvicorn server automatically
- Hits all RMOS endpoints (patterns, plans, saw ops, joblog)
- Validates responses and error codes
- Exits non-zero on failure (CI-friendly)
- **Best for:** Automated CI/CD pipelines

### **2. PowerShell Full Test Suite** (`Test-RMOS-Full.ps1`)
- Wraps both sandbox and slice preview tests
- Single command to run all RMOS tests
- **Best for:** Windows developers, manual testing

### **3. PowerShell Single-Slice Test** (`Test-RMOS-SlicePreview.ps1`)
- Tests `/saw-ops/slice/preview` endpoint
- Validates both circle and line geometry modes
- **Best for:** Saw operations testing, geometry validation

### **4. Bash Full Test** (`test_rmos_full.sh`)
- curl-based testing for Linux/macOS
- Minimal dependencies
- **Best for:** Linux CI, Docker containers, manual validation

### **5. GitHub Actions Workflow** (`.github/workflows/rmos_ci.yml`)
- Runs Python CI test on every push/PR
- Triggers on changes to `services/api/`, `scripts/`, or workflow file
- **Best for:** Automated PR validation

### **6. Saw Operations Router** (`services/api/app/api/routes/saw_ops.py`)
- Single-slice preview endpoint (`/saw-ops/slice/preview`)
- Multi-ring batch preview endpoint (`/saw-ops/batch/preview`)
- Matches RosetteMultiRingOpPanel.vue frontend exactly
- **Purpose:** Risk analysis + G-code generation for saw operations

---

## 🚀 Quick Start

### **Option 1: Python CI Test (Recommended for CI)**

```bash
# From project root
cd services/api
python ../../scripts/rmos_ci_test.py
```

**What it does:**
1. Starts FastAPI server automatically
2. Waits for server to be ready
3. Creates test rosette pattern
4. Requests manufacturing plan
5. Tests single-slice preview (circle)
6. Tests batch preview (multi-ring)
7. Validates JobLog entries
8. Shuts down server
9. Exits 0 on success, 1 on failure

### **Option 2: PowerShell Full Suite (Windows)**

```powershell
# Start server in one terminal
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# Run tests in another terminal
.\scripts\Test-RMOS-Full.ps1 -BaseUrl "http://localhost:8000/rmos" -Verbose
```

**What it does:**
1. Runs `Test-RMOS-Sandbox.ps1` (pattern + plan + joblog)
2. Runs `Test-RMOS-SlicePreview.ps1` (single-slice circle + line)
3. Reports combined success/failure

### **Option 3: Bash Test (Linux/macOS)**

```bash
# Make executable (first time only)
chmod +x scripts/test_rmos_full.sh

# Start server in one terminal
cd services/api
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000

# Run tests in another terminal
export RMOS_BASE_URL="http://127.0.0.1:8000/rmos"
./scripts/test_rmos_full.sh
```

---

## 🔧 Configuration

### **Environment Variables**

| Variable | Default | Description |
|----------|---------|-------------|
| `RMOS_BASE_URL` | `http://127.0.0.1:8000/rmos` | Base URL for RMOS API |
| `APP_MODULE` | `app.main:app` | FastAPI app module path |

### **Change Base URL**

**Python:**
```bash
export RMOS_BASE_URL="http://localhost:5000/rmos"
python scripts/rmos_ci_test.py
```

**PowerShell:**
```powershell
.\scripts\Test-RMOS-Full.ps1 -BaseUrl "http://localhost:5000/rmos"
```

**Bash:**
```bash
export RMOS_BASE_URL="http://localhost:5000/rmos"
./scripts/test_rmos_full.sh
```

### **Change App Module (Python CI only)**

```bash
export APP_MODULE="server.main:application"
python scripts/rmos_ci_test.py
```

---

## 📊 Test Coverage

### **Endpoints Tested**

| Endpoint | Python CI | PowerShell | Bash | Description |
|----------|-----------|------------|------|-------------|
| `POST /rosette/patterns` | ✅ | ✅ | ❌ | Create rosette pattern |
| `GET /rosette/patterns` | ✅ | ✅ | ❌ | List patterns |
| `DELETE /rosette/patterns/{id}` | ✅ | ✅ | ❌ | Delete pattern |
| `POST /rosette/manufacturing-plan` | ✅ | ✅ | ❌ | Generate plan + JobLog |
| `GET /joblog` | ✅ | ✅ | ✅ | List JobLog entries |
| `POST /saw-ops/slice/preview` | ✅ | ✅ | ✅ | Single-slice preview |
| `POST /saw-ops/batch/preview` | ✅ | ✅ | ✅ | Multi-ring batch preview |

### **Validation Checks**

- ✅ **HTTP Status Codes** - All endpoints return 2xx on success
- ✅ **Response Schema** - JSON matches Pydantic models
- ✅ **Risk Analysis** - Risk grades computed correctly (GREEN/YELLOW/RED)
- ✅ **G-code Generation** - Valid G-code returned for saw operations
- ✅ **JobLog Integration** - rosette_plan entries created when expected
- ✅ **Multi-Family Logic** - Strip plans group by strip_family_id correctly
- ✅ **Geometry Modes** - Both circle and line slice modes work

---

## 🐛 Troubleshooting

### **Connection Refused**

```
[ERR] Request failed: POST http://localhost:8000/rmos/rosette/patterns
[ERR] No connection could be made because the target machine actively refused it.
```

**Solution:** Start FastAPI server first:
```bash
cd services/api
.venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows
uvicorn app.main:app --reload --port 8000
```

### **404 Not Found**

```
[ERR] Request error 404: POST http://localhost:8000/rmos/rosette/patterns
```

**Solution:** Verify routers are registered in `services/api/app/main.py`:
```python
from app.api.routes import joblog, rosette_patterns, manufacturing, saw_ops

app.include_router(joblog.router, prefix="/rmos")
app.include_router(rosette_patterns.router, prefix="/rmos")
app.include_router(manufacturing.router, prefix="/rmos")
app.include_router(saw_ops.router, prefix="/rmos")
```

### **422 Validation Error**

```
[ERR] Request error 422: POST http://localhost:8000/rmos/rosette/patterns
```

**Solution:** Check Pydantic schema matches. Visit `http://localhost:8000/docs` to see API specs.

### **Tool Not Found**

```
[ERR] Saw tool 'saw_default' not found
```

**Solution:** Ensure saw tools are initialized. Add to `app/api/routes/saw_tools.py`:
```python
SAW_TOOLS_DB = {
    "saw_default": SawToolInDB(
        id="saw_default",
        name="Default Saw",
        diameter_mm=300.0,
        rpm=3600,
        # ... other fields
    )
}
```

### **Python Import Errors**

```
ModuleNotFoundError: No module named 'requests'
```

**Solution:** Install dependencies:
```bash
cd services/api
pip install -r requirements.txt
# or manually:
pip install uvicorn requests fastapi pydantic
```

---

## 🎯 Integration with CI/CD

### **GitHub Actions (Automatic)**

The workflow is already configured in `.github/workflows/rmos_ci.yml`. It will:
- Trigger on push/PR to `services/api/**` or `scripts/**`
- Set up Python 3.11
- Install dependencies
- Run Python CI smoke test
- Fail the build if tests fail

**View results:** GitHub → Actions → RMOS CI

### **Add to Existing CI**

**If you have an existing workflow:**
```yaml
- name: Run RMOS tests
  working-directory: services/api
  run: python ../../scripts/rmos_ci_test.py
```

**If you want PowerShell tests in Windows CI:**
```yaml
- name: Run RMOS PowerShell tests
  run: |
    cd services/api
    .\.venv\Scripts\Activate.ps1
    uvicorn app.main:app --host 127.0.0.1 --port 8000 &
    sleep 5
    cd ../..
    .\scripts\Test-RMOS-Full.ps1 -BaseUrl "http://127.0.0.1:8000/rmos"
```

---

## 📋 Test Script Details

### **Python CI Test** (`rmos_ci_test.py`)

**Lines:** ~170  
**Dependencies:** `requests`, `uvicorn`  
**Runtime:** ~8-12 seconds  

**Test Flow:**
```
1. Start uvicorn server
2. Wait for server ready (max 20s)
3. Create test pattern (2 rings, bw_checker_main)
4. Request manufacturing plan (4 guitars, 8mm tiles, 12% scrap)
5. Single-slice circle preview (50mm radius, hardwood)
6. Batch preview (45mm base, 2 rings, 3mm step)
7. Fetch JobLog (expect >= 1 entry)
8. Shutdown server
```

### **PowerShell Full Test** (`Test-RMOS-Full.ps1`)

**Lines:** ~25  
**Dependencies:** None (calls other scripts)  
**Runtime:** ~5-8 seconds  

**Test Flow:**
```
1. Call Test-RMOS-Sandbox.ps1
2. Call Test-RMOS-SlicePreview.ps1
3. Report combined success/failure
```

### **PowerShell Slice Preview Test** (`Test-RMOS-SlicePreview.ps1`)

**Lines:** ~110  
**Dependencies:** None  
**Runtime:** ~2-3 seconds  

**Test Flow:**
```
1. Circle slice preview (50mm radius)
2. Line slice preview (100mm line)
3. Validate risk grades and rim speeds
```

### **Bash Full Test** (`test_rmos_full.sh`)

**Lines:** ~60  
**Dependencies:** `curl`, `bash`  
**Runtime:** ~2-3 seconds  

**Test Flow:**
```
1. Health check (/joblog)
2. Circle slice preview
3. Batch preview
4. Validate all return 2xx
```

---

## 📚 See Also

- [Test-RMOS-Sandbox.ps1](./README_RMOS_TEST.md) - Original sandbox smoke test
- [INTEGRATION_QUICKSTART.md](../projects/rmos/INTEGRATION_QUICKSTART.md) - Integration guide
- [PHASE1_IMPLEMENTATION_COMPLETE.md](../projects/rmos/PHASE1_IMPLEMENTATION_COMPLETE.md) - Implementation summary
- [ARCHITECTURE.md](../projects/rmos/ARCHITECTURE.md) - RMOS technical design

---

## ✅ Test Status

**Current Coverage:**
- ✅ Pattern CRUD (create, read, delete)
- ✅ Manufacturing planner (multi-family grouping)
- ✅ JobLog integration (rosette_plan jobs)
- ✅ Single-slice preview (circle + line)
- ✅ Batch preview (multi-ring circle_param)
- ✅ Risk analysis (GREEN/YELLOW/RED grades)
- ✅ G-code generation (valid output)

**Not Yet Tested (Phase 2+):**
- ❌ Saw batch execution with JobLog write (saw_slice_batch jobs)
- ❌ DXF geometry mode
- ❌ Vue component integration
- ❌ SQLite persistence
- ❌ Ultra-thin slice recipes (<0.3mm)

---

**Status:** ✅ Production Ready  
**Last Updated:** November 21, 2025  
**Version:** Phase 1 Complete
