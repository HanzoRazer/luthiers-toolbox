# Express Edition Feature Extraction Guide
**Phase 1 Week 1: Step-by-Step File Extraction**

---

## 🎯 Overview

You will extract **3 features** from the golden master into `ltb-express`:
1. **Rosette Designer Lite** (12-18 hours)
2. **Curve Lab Mini** (10-15 hours)
3. **Fretboard Designer** (8-12 hours)

**Total Time:** 30-45 hours Week 1

---

## 📦 Feature 1: Rosette Designer Lite (12-18 hours)

### **Backend Files to Extract**

#### **Step 1: Router** (3-4 hours)
```powershell
# Source: Golden Master
$source = "c:\Users\thepr\Downloads\Luthiers ToolBox\services\api\app\routers\art_studio_rosette_router.py"

# Destination: ltb-express
$dest = "c:\Users\thepr\Downloads\ltb-express\server\app\routers\rosette_router.py"

# Create directory if needed
New-Item -ItemType Directory -Force -Path "c:\Users\thepr\Downloads\ltb-express\server\app\routers"

# Copy file
Copy-Item $source $dest
```

**What to strip out (downgrade to Express):**
- Remove `/compare` endpoint (Pro feature)
- Remove `/compare/snapshot` endpoint (Pro feature)
- Remove risk scoring logic (Pro feature)
- Keep: `/preview`, `/save`, `/jobs`, `/presets`

#### **Step 2: Database Store** (2-3 hours)
```powershell
# Source
$source = "c:\Users\thepr\Downloads\Luthiers ToolBox\services\api\app\art_studio_rosette_store.py"

# Destination
$dest = "c:\Users\thepr\Downloads\ltb-express\server\app\stores\rosette_store.py"

New-Item -ItemType Directory -Force -Path "c:\Users\thepr\Downloads\ltb-express\server\app\stores"
Copy-Item $source $dest
```

**What to keep:**
- `init_db()` - creates rosette_jobs and rosette_presets tables
- `save_job()` - persist designs
- `list_jobs()` - query saved designs
- `list_presets()` - preset patterns

**What to strip:**
- Risk analysis tables
- Compare history tables
- Enterprise audit logging

#### **Step 3: Register Router** (30 minutes)
Edit `ltb-express/server/app/main.py`:

```python
from fastapi import FastAPI
from .routers.rosette_router import router as rosette_router

app = FastAPI(
    title="Luthier's ToolBox Express Edition",
    version="1.0.0"
)

# Register Rosette router
app.include_router(
    rosette_router,
    prefix="/api/rosette",
    tags=["Rosette"]
)

@app.get("/")
def read_root():
    return {"status": "ready", "edition": "EXPRESS"}
```

### **Frontend Files to Extract**

#### **Step 4: Main View** (4-6 hours)
```powershell
# Source
$source = "c:\Users\thepr\Downloads\Luthiers ToolBox\client\src\views\ArtStudioRosette.vue"

# Destination
$dest = "c:\Users\thepr\Downloads\ltb-express\client\src\views\RosetteDesigner.vue"

New-Item -ItemType Directory -Force -Path "c:\Users\thepr\Downloads\ltb-express\client\src\views"
Copy-Item $source $dest
```

**What to strip:**
- Compare mode button/link (Pro feature)
- Risk analysis panel (Pro feature)
- Advanced export options (Enterprise feature)

**What to keep:**
- Pattern parameter controls
- Preview canvas
- Save/load functionality
- Basic DXF/SVG export

#### **Step 5: Components** (3-4 hours)
```powershell
# Create components directory
New-Item -ItemType Directory -Force -Path "c:\Users\thepr\Downloads\ltb-express\client\src\components\rosette"

# Copy components
Copy-Item "c:\Users\thepr\Downloads\Luthiers ToolBox\client\src\components\rosette\RosetteCanvas.vue" `
          "c:\Users\thepr\Downloads\ltb-express\client\src\components\rosette\RosetteCanvas.vue"

Copy-Item "c:\Users\thepr\Downloads\Luthiers ToolBox\client\src\components\rosette\PatternTemplates.vue" `
          "c:\Users\thepr\Downloads\ltb-express\client\src\components\rosette\PatternTemplates.vue"

Copy-Item "c:\Users\thepr\Downloads\Luthiers ToolBox\client\src\components\rosette\MaterialPalette.vue" `
          "c:\Users\thepr\Downloads\ltb-express\client\src\components\rosette\MaterialPalette.vue"
```

#### **Step 6: Setup Vue Client** (2-3 hours)
```powershell
cd c:\Users\thepr\Downloads\ltb-express\client

# Initialize Vite + Vue 3
npm create vite@latest . -- --template vue-ts

# Install dependencies
npm install vue-router pinia axios

# Create router
New-Item -ItemType Directory -Force -Path "src\router"
```

Create `src/router/index.ts`:
```typescript
import { createRouter, createWebHistory } from 'vue-router'
import RosetteDesigner from '../views/RosetteDesigner.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/rosette'
    },
    {
      path: '/rosette',
      name: 'RosetteDesigner',
      component: RosetteDesigner
    }
  ]
})

export default router
```

Update `src/main.ts`:
```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
```

#### **Step 7: Test Rosette Feature** (1-2 hours)
```powershell
# Start backend
cd c:\Users\thepr\Downloads\ltb-express\server
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload

# In another terminal, start frontend
cd c:\Users\thepr\Downloads\ltb-express\client
npm run dev

# Visit http://localhost:5173/rosette
# Test:
# ✓ Create rosette pattern
# ✓ Adjust parameters
# ✓ Preview updates
# ✓ Save design
# ✓ Export DXF/SVG
```

---

## 📦 Feature 2: Curve Lab Mini (10-15 hours)

### **Files to Extract**

#### **Backend**
```powershell
# Search for curve/bezier related routers
# Look in: services/api/app/routers/
# Files likely named: curve_router.py, bezier_router.py, geometry_router.py

# Extract endpoints:
# - POST /api/curves/bezier
# - POST /api/curves/arc
# - POST /api/curves/smooth
```

**Find the files:**
```powershell
# Search for curve-related files
Get-ChildItem -Path "c:\Users\thepr\Downloads\Luthiers ToolBox\services\api\app\routers" -Recurse -Filter "*curve*.py"
Get-ChildItem -Path "c:\Users\thepr\Downloads\Luthiers ToolBox\services\api\app\routers" -Recurse -Filter "*bezier*.py"
```

#### **Frontend**
```powershell
# Search for curve views
Get-ChildItem -Path "c:\Users\thepr\Downloads\Luthiers ToolBox\client\src\views" -Recurse -Filter "*Curve*.vue"
Get-ChildItem -Path "c:\Users\thepr\Downloads\Luthiers ToolBox\packages\client\src\views" -Recurse -Filter "*Curve*.vue"
```

---

## 📦 Feature 3: Fretboard Designer (8-12 hours)

### **Files to Extract**

#### **Backend**
```powershell
# Search for fretboard/fingerboard routers
Get-ChildItem -Path "c:\Users\thepr\Downloads\Luthiers ToolBox\services\api\app\routers" -Recurse -Filter "*fret*.py"
Get-ChildItem -Path "c:\Users\thepr\Downloads\Luthiers ToolBox\services\api\app\routers" -Recurse -Filter "*fingerboard*.py"
```

#### **Frontend**
```powershell
# Search for fretboard views
Get-ChildItem -Path "c:\Users\thepr\Downloads\Luthiers ToolBox\client\src\views" -Recurse -Filter "*Fret*.vue"
Get-ChildItem -Path "c:\Users\thepr\Downloads\Luthiers ToolBox\packages\client\src\views" -Recurse -Filter "*Fingerboard*.vue"
```

---

## ✅ Extraction Checklist

### **Per Feature**
- [ ] Identify backend router file
- [ ] Copy router to ltb-express
- [ ] Strip Pro/Enterprise features
- [ ] Copy supporting modules (utils, stores)
- [ ] Register router in main.py
- [ ] Test backend endpoints (curl/Postman)
- [ ] Identify frontend view file
- [ ] Copy view to ltb-express
- [ ] Copy related components
- [ ] Strip Pro/Enterprise UI elements
- [ ] Add route to router
- [ ] Test frontend UI
- [ ] Test export functionality
- [ ] Commit to ltb-express repo

### **Week 1 Complete**
- [ ] Rosette Designer works end-to-end
- [ ] Curve Lab works end-to-end
- [ ] Fretboard Designer works end-to-end
- [ ] All 3 features export DXF/SVG
- [ ] Frontend builds without errors
- [ ] Ready for Week 2 (Polish + Parametric Guitar)

---

## 🚀 Quick Start Commands

### **Find Files to Extract**
```powershell
# Run these to identify exact files
.\scripts\Find-ExpressFeatures.ps1  # (I can create this script)
```

### **Extract Rosette (Quick)**
```powershell
# I can create an automated extraction script
.\scripts\Extract-Rosette.ps1
```

### **Test After Extraction**
```powershell
# Backend
cd ltb-express\server
uvicorn app.main:app --reload

# Frontend
cd ltb-express\client
npm run dev
```

---

## 📝 Notes

- **Don't copy everything** - Only copy files you need
- **Strip aggressively** - Remove Pro/Enterprise features
- **Test incrementally** - Test after each feature extraction
- **Commit often** - Commit after each working feature
- **Golden master unchanged** - Never modify golden master

---

**Status:** Ready for extraction  
**Next Step:** Run file searches above to identify exact files, then extract Rosette Designer first
