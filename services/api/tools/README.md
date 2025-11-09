# API Environment Reinstall Guide

Quick reference for recreating your Python venv with the Art Studio v13 geometry stack.

## 🪟 Windows (PowerShell)

### Quick Reinstall
```powershell
# From repo root:
cd "C:\Users\thepr\Downloads\Luthiers ToolBox"
.\services\api\tools\reinstall_api_env.ps1 -Force
```

### Custom Python Version
```powershell
# Use specific Python (e.g., 3.11)
.\services\api\tools\reinstall_api_env.ps1 -Py "py -3.11" -EnvName ".venv311" -Force

# Or use default Python
.\services\api\tools\reinstall_api_env.ps1 -Force
```

### Options
- `-Py <path>` - Python interpreter (default: `python`)
- `-EnvName <name>` - Venv directory name (default: `.venv311`)
- `-Force` - Remove existing venv before creating

### Activate
```powershell
& ".\services\api\.venv311\Scripts\Activate.ps1"
```

---

## 🐧 macOS/Linux (Make)

### Quick Reinstall
```bash
# From services/api directory:
cd services/api
make api-reinstall
```

### Step-by-Step
```bash
# 1. Create venv + install deps
make api-env

# 2. Verify imports
make api-verify

# 3. Run smoke tests
make api-test

# 4. Start dev server
make api-run
```

### Variables
```bash
# Custom Python version
make api-reinstall PY=python3.11 VENV=.venv311

# Default uses python3 and .venv311
```

### Activate
```bash
source .venv311/bin/activate
```

---

## ✅ Verification

After installation, verify the geometry stack:

### Windows
```powershell
& ".\services\api\.venv311\Scripts\python.exe" -c @"
import shapely, fastapi, ezdxf, numpy
print('✓ shapely:', shapely.__version__)
print('✓ fastapi:', fastapi.__version__)
print('✓ ezdxf:', ezdxf.__version__)
print('✓ numpy:', numpy.__version__)
try:
    import pyclipper
    print('✓ pyclipper:', pyclipper.__version__)
except:
    print('⚠ pyclipper: not available (Python 3.13 issue)')
"@
```

### Unix
```bash
.venv311/bin/python -c "
import shapely, fastapi, ezdxf, numpy
print('✓ shapely:', shapely.__version__)
print('✓ fastapi:', fastapi.__version__)
print('✓ ezdxf:', ezdxf.__version__)
print('✓ numpy:', numpy.__version__)
try:
    import pyclipper
    print('✓ pyclipper:', pyclipper.__version__)
except:
    print('⚠ pyclipper: not available')
"
```

---

## 🚀 Quick Start After Reinstall

### 1. Activate Environment
```powershell
# Windows
& ".\services\api\.venv311\Scripts\Activate.ps1"

# Unix
source services/api/.venv311/bin/activate
```

### 2. Start API Server
```powershell
cd services\api
python -m uvicorn app.main:app --reload --port 8000
```

### 3. Test Endpoint
```powershell
# Windows
curl -X POST http://localhost:8000/api/cam_vcarve/preview_infill `
  -H "Content-Type: application/json" `
  -d '{"mode":"raster","flat_stepover_mm":1.0,"raster_angle_deg":45}'

# Unix
curl -X POST http://localhost:8000/api/cam_vcarve/preview_infill \
  -H 'Content-Type: application/json' \
  -d '{"mode":"raster","flat_stepover_mm":1.0,"raster_angle_deg":45}'
```

---

## 📦 What Gets Installed

### Core Framework
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `starlette` - ASGI toolkit

### Geometry Stack (Critical for Art Studio v13)
- `shapely` - Polygon operations, raster infill
- `numpy` - Array operations
- `ezdxf` - DXF file handling
- `pyclipper` - Contour infill (optional, fails on Python 3.13)

### Database
- `sqlalchemy` - ORM
- `sqlite-utils` - SQLite helpers

### CAM/CNC
- All existing modules (M.1-M.4, L.1-L.3)

---

## ⚠️ Known Issues

### pyclipper Build Failure (Python 3.13)
**Symptom:** Build fails with C++ compiler errors  
**Impact:** Contour infill mode unavailable  
**Workaround:**
1. Use Python 3.11: `.\reinstall_api_env.ps1 -Py "py -3.11" -Force`
2. Or accept raster-only mode (shapely handles this)

### Shapely Version Conflicts
**Symptom:** Import errors or geometry inconsistencies  
**Solution:** Pin to 2.0.x in requirements.lock

---

## 🔧 Troubleshooting

### "Module not found" errors
```powershell
# Verify venv is activated
# Windows: Check for (.venv311) in prompt
# Unix: Check for (.venv311) in prompt

# Reinstall
.\services\api\tools\reinstall_api_env.ps1 -Force
```

### Import errors after upgrade
```powershell
# Use pinned versions
cd services\api
pip install -r requirements.lock --force-reinstall
```

### API won't start
```powershell
# Check for syntax errors
python -c "from app.main import app; print('✓ OK')"

# Check router registration
python -c "from app.routers.cam_vcarve_router import router; print('✓ OK')"
```

---

## 📚 File Locations

- **Reinstall Script**: `services/api/tools/reinstall_api_env.ps1`
- **Makefile**: `services/api/Makefile`
- **Requirements**: `services/api/requirements.txt`
- **Lock File**: `services/api/requirements.lock` (pinned versions)
- **Venv**: `services/api/.venv311/` (or custom name)

---

## 🧪 Health Check

### **What It Does**
Spins up FastAPI server, tests the `/api/cam_vcarve/preview_infill` endpoint, validates response, then shuts down cleanly.

### **Windows (PowerShell)**
```powershell
# From repo root
pwsh -File "services\api\tools\health_check.ps1"

# Custom port
pwsh -File "services\api\tools\health_check.ps1" -Port 9000

# Custom venv
pwsh -File "services\api\tools\health_check.ps1" -EnvName ".venv"
```

**Expected Output:**
```
==> Art Studio v13 Health Check

✓ Found Python: C:\...\services\api\.venv311\Scripts\python.exe
==> Starting FastAPI server on port 8088
   Server PID: 12345
   Waiting 3 seconds for startup...
✓ Server started successfully

==> Testing POST /api/cam_vcarve/preview_infill
✓ Endpoint responded successfully

==> Response Preview:
{"svg":"<svg>...</svg>","stats":{"mode":"raster",...}}...

==> Response Validation:
  ✓ svg field present
  ✓ stats field present
  ✓ mode = raster
  ✓ total_len = 234.5

✅ HEALTH CHECK PASSED

==> Shutting down server...
   Stopping PID 12345
✓ Cleanup complete

==> Health check complete.
```

### **Unix (Make)**
```bash
# From services/api directory
cd services/api
make api-health

# Custom port
make api-health PORT=9000
```

**Expected Output:**
```
==> Launching FastAPI server on port 8088 for health check
==> Curling /api/cam_vcarve/preview_infill
{"svg":"<svg>...</svg>","stats":{"mode":"raster",...}}
==> Health check completed.
```

### **What Gets Tested**
- ✅ FastAPI server starts on specified port
- ✅ `/api/cam_vcarve/preview_infill` endpoint is reachable
- ✅ Raster mode infill generation works
- ✅ Response contains `svg` and `stats` fields
- ✅ Shapely geometry operations functional
- ✅ Server shuts down cleanly

---

## 🎯 Quick Commands Reference

```powershell
# Windows - Full reinstall
.\services\api\tools\reinstall_api_env.ps1 -Force

# Windows - Health check
pwsh -File "services\api\tools\health_check.ps1"

# Windows - Activate
& ".\services\api\.venv311\Scripts\Activate.ps1"

# Windows - Start server
cd services\api; python -m uvicorn app.main:app --reload

# Unix - Full reinstall
cd services/api && make api-reinstall

# Unix - Health check
cd services/api && make api-health

# Unix - Activate
source services/api/.venv311/bin/activate

# Unix - Start server
cd services/api && make api-run
```

---

**Status:** Tools ready for clean venv management + health checks across Windows/macOS/Linux! 🛠️🏥
