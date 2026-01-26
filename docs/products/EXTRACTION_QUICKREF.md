# Feature Extraction Quick Reference

> How to migrate code from Golden Master to standalone repos.
>
> **Last Updated:** 2026-01-26

---

## 🚀 Automated Extraction (Recommended)

Use the PowerShell extraction script:

```powershell
# From Golden Master root
cd c:\Users\thepr\Downloads\luthiers-toolbox

# Extract a designer product
.\scripts\Extract-Designer.ps1 -Product neck -TargetPath "C:\repos\ltb-neck-designer"
.\scripts\Extract-Designer.ps1 -Product headstock -TargetPath "C:\repos\ltb-headstock-designer"
.\scripts\Extract-Designer.ps1 -Product fingerboard -TargetPath "C:\repos\ltb-fingerboard-designer"
.\scripts\Extract-Designer.ps1 -Product bridge -TargetPath "C:\repos\ltb-bridge-designer"
.\scripts\Extract-Designer.ps1 -Product blueprint -TargetPath "C:\repos\blueprint-reader"
```

The script:
1. Creates directory structure
2. Copies source files
3. Adapts imports (removes `app.rmos.*` references)
4. Creates `main.py` with health endpoint
5. Creates `requirements.txt`
6. Creates test file for edition tag verification
7. Copies and customizes copilot-instructions.md

---

## 📋 Manual Extraction Workflow

If you prefer manual extraction or need more control:

### Step 1: Clone Template Structure

```powershell
# Create directories
mkdir ltb-neck-designer
cd ltb-neck-designer

mkdir server/app/routers
mkdir server/app/geometry
mkdir server/app/calculators
mkdir server/tests
mkdir client/src/components
mkdir client/src/views
mkdir .github/workflows
```

### Step 2: Copy Source Files

Reference the [DESIGNER_SOURCE_MAP.md](docs/products/DESIGNER_SOURCE_MAP.md) for each product's file list.

```powershell
# Example: Neck Designer
$GM = "C:\Users\thepr\Downloads\luthiers-toolbox"
$Target = "C:\repos\ltb-neck-designer"

# Copy core files
Copy-Item "$GM\services\api\app\routers\neck_router.py" "$Target\server\app\routers\"
Copy-Item "$GM\services\api\app\instrument_geometry\neck\*.py" "$Target\server\app\geometry\"
Copy-Item "$GM\services\api\app\instrument_geometry\body\fretboard_geometry.py" "$Target\server\app\geometry\"
```

### Step 3: Adapt Imports

Replace Golden Master import paths with local paths:

| Golden Master Import | Standalone Import |
|---------------------|-------------------|
| `from app.instrument_geometry.neck.` | `from app.geometry.` |
| `from app.calculators.` | `from app.calculators.` |
| `from app.rmos.` | **REMOVE** (flag for review) |
| `from ..instrument_geometry.` | `from app.geometry.` |

```python
# Before (Golden Master)
from ..instrument_geometry.neck.fret_math import compute_fret_positions_mm

# After (Standalone)
from app.geometry.fret_math import compute_fret_positions_mm
```

### Step 4: Create main.py

Use the template from `templates/server/main.py` or create minimal:

```python
from fastapi import FastAPI

app = FastAPI(title="Neck Designer", version="1.0.0")

# Mount your router
from app.routers.neck_router import router
app.include_router(router, prefix="/api/neck", tags=["Neck"])

@app.get("/health")
def health():
    return {"status": "ok", "edition": "NECK_DESIGNER"}
```

### Step 5: Create requirements.txt

```
fastapi>=0.109.0
uvicorn>=0.27.0
pydantic>=2.5.0
ezdxf>=1.1.0
```

### Step 6: Test in Isolation

```powershell
cd server
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Start server
uvicorn app.main:app --reload --port 8000

# Verify edition tag
curl http://localhost:8000/health
# Expected: {"status": "ok", "edition": "NECK_DESIGNER"}
```

---

## 🔍 Common Import Issues

### Issue: RMOS Dependencies

Golden Master files may import from `app.rmos.*` for governance features. These must be removed for standalone products.

**Solution:** The extraction script marks these with `# REMOVED:` comments. Review and either:
1. Delete the import and related code
2. Implement a simplified local version

```python
# Original
from app.rmos.context import RmosContext

# Standalone - remove or simplify
# from app.rmos.context import RmosContext  # REMOVED: Not available in standalone
```

### Issue: Circular Imports

Some geometry modules have cross-references.

**Solution:** Copy all related modules or refactor imports:

```python
# Instead of relative imports
from ..neck.neck_profiles import FretboardSpec

# Use absolute from app root
from app.geometry.neck_profiles import FretboardSpec
```

### Issue: Missing ezdxf

DXF export requires the `ezdxf` library.

**Solution:** Already in requirements.txt. The code handles missing ezdxf gracefully:

```python
try:
    import ezdxf
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False
```

---

## ✅ Extraction Checklist

```markdown
## Pre-Extraction
- [ ] Target repo exists (git init or clone from GitHub)
- [ ] Golden Master is up to date (git pull)
- [ ] Read DESIGNER_SOURCE_MAP.md for file list

## Extraction
- [ ] Run Extract-Designer.ps1 OR manual copy
- [ ] All source files copied
- [ ] Imports adapted (no `app.rmos.*` references)
- [ ] `__init__.py` files created

## Post-Extraction
- [ ] Review `# REMOVED:` comments
- [ ] main.py imports routers
- [ ] requirements.txt is minimal
- [ ] .env.example created

## Verification
- [ ] `pip install -r requirements.txt` succeeds
- [ ] `pytest tests/ -v` passes
- [ ] `GET /health` returns edition tag
- [ ] API docs load at `/docs`

## Documentation
- [ ] .github/copilot-instructions.md customized
- [ ] README.md updated
- [ ] Feature scope documented
```

---

## 📁 Expected Directory Structure

After extraction, your repo should look like:

```
ltb-{product}/
├── .github/
│   ├── copilot-instructions.md    # AI agent instructions
│   └── workflows/
│       └── ci.yml                 # GitHub Actions (optional)
├── server/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI entry point
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   └── {product}_router.py
│   │   ├── geometry/
│   │   │   ├── __init__.py
│   │   │   └── *.py               # Geometry modules
│   │   └── calculators/           # (if needed)
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_health.py         # Edition tag test
│   ├── requirements.txt
│   ├── pytest.ini
│   └── .env.example
├── client/                        # (if frontend needed)
│   ├── src/
│   │   ├── components/
│   │   └── views/
│   └── package.json
├── .gitignore
└── README.md
```

---

## 🔗 Related Documentation

- [DESIGNER_SOURCE_MAP.md](docs/products/DESIGNER_SOURCE_MAP.md) – Source file mappings per product
- [MASTER_SEGMENTATION_STRATEGY.md](docs/products/MASTER_SEGMENTATION_STRATEGY.md) – Product architecture
- [templates/.github/copilot-instructions.md](templates/.github/copilot-instructions.md) – AI instructions template
- [templates/server/main.py](templates/server/main.py) – Server template with feature flags
- [EXPRESS_EXTRACTION_GUIDE.md](docs/quickref/general/EXPRESS_EXTRACTION_GUIDE.md) – Detailed Express guide
