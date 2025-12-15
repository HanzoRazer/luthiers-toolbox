# Developer Quickstart Guide

**Luthier's Toolbox** - CNC Guitar CAM Web Application  
**Repository:** HanzoRazer/luthiers-toolbox  
**Stack:** FastAPI (Python 3.11+) + Vue 3 (TypeScript) + Vite  
**Started:** September 20, 2025 → Professional-grade system in 2 months 🚀

---

## 🎯 This is the Canonical Repository

- ✅ **Single source of truth** for all Luthier's Toolbox development
- ✅ All Art Studio features integrated into unified architecture
- ✅ Old scaffold folders (e.g., `ToolBox_Art_Studio_scaffold_v6`) are **retired**
- ✅ Work exclusively from this repository

---

## 🚀 Quick Start Commands

### **Backend (FastAPI)**
```powershell
# From repository root
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

**One-liner:**
```powershell
cd services/api; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port 8000
```

**API Server:** http://localhost:8000  
**API Docs:** http://localhost:8000/docs (Swagger UI)

### **Frontend (Vue 3 + Vite)**
```powershell
# From repository root
cd client
npm install      # First time only
npm run dev
```

**Dev Server:** http://localhost:5173  
**API Proxy:** Frontend proxies `/api/*` requests to backend automatically

### **Full Stack Development (Two Terminals)**

**Terminal 1 - Backend:**
```powershell
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```powershell
cd client
npm run dev
```

---

## 📁 Repository Structure

```
luthiers-toolbox/
├── services/api/          # FastAPI Backend
│   ├── app/
│   │   ├── main.py       # Application entry point
│   │   ├── routers/      # API endpoints (55 routers, 98% typed)
│   │   ├── cam/          # CAM algorithms (adaptive, helical, etc.)
│   │   └── util/         # Utilities (units, exporters, etc.)
│   ├── .venv/            # Python virtual environment
│   └── requirements.txt  # Python dependencies
│
├── client/                # Vue 3 Frontend
│   ├── src/
│   │   ├── views/        # Page components
│   │   │   ├── ArtStudioUnified.vue  # Main Art Studio UI ⭐
│   │   │   ├── CAMDashboard.vue
│   │   │   └── ...
│   │   ├── components/   # Reusable components
│   │   ├── router/       # Vue Router (index.ts) ⭐
│   │   └── api/          # API wrapper functions
│   ├── package.json      # npm dependencies
│   └── vite.config.ts    # Vite configuration
│
├── docs/                  # Documentation
├── .github/              # CI/CD workflows
└── __ARCHIVE__/          # Historical documentation (reference only)
```

---

## 🎨 Key Files for Art Studio Development

### **Main Art Studio UI**
📁 **`client/src/views/ArtStudioUnified.vue`** ⭐
- Current unified Art Studio interface
- Tab-based wrapper (Rosette / Headstock / Relief)
- **This is where to integrate Comparison Mode**

### **Routing Configuration**
📁 **`client/src/router/index.ts`**
- Defines all application routes
- Art Studio route: `/art-studio` → `ArtStudioUnified.vue`

### **Backend Routers**
📁 **`services/api/app/routers/`**
- 55 routers with 98% type coverage
- All async endpoints properly typed
- Industry-leading code quality

---

## 🛠️ Available npm Scripts (Frontend)

```powershell
npm run dev          # Start Vite dev server (port 5173)
npm run build        # Build for production
npm run preview      # Preview production build
npm run type-check   # TypeScript type checking
npm run test         # Run tests with coverage
npm run test:watch   # Watch mode for tests
npm run lint         # ESLint code quality check
```

---

## 🧪 Testing

### **Backend API Tests**
```powershell
# From repository root
.\smoke_v161_helical.ps1    # Helical ramping tests
.\smoke_n18_arcs.ps1        # Arc linking tests
.\test_adaptive_l1.ps1      # Adaptive pocketing L.1
.\test_adaptive_l2.ps1      # Adaptive pocketing L.2
```

### **Health Check**
```powershell
cd services/api/tools
.\health_check.ps1          # Full API health validation
```

---

## 📦 Dependencies

### **Backend (Python 3.11+)**
- **FastAPI** - API framework
- **Pydantic** - Data validation
- **ezdxf** - DXF file handling
- **shapely** - Geometry operations
- **pyclipper** - Polygon offsetting
- **uvicorn** - ASGI server

**Install:**
```powershell
cd services/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### **Frontend (Node.js 18+)**
- **Vue 3** - UI framework
- **TypeScript** - Type safety
- **Vite 5** - Build tool
- **Vue Router 4** - Routing
- **Three.js** - 3D visualization
- **SVG.js** - SVG manipulation

**Install:**
```powershell
cd client
npm install
```

---

## 🎯 Development Workflow

### **Standard Development Session**
1. Open **2 terminals** (PowerShell)
2. **Terminal 1:** Start backend
   ```powershell
   cd services/api; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port 8000
   ```
3. **Terminal 2:** Start frontend
   ```powershell
   cd client; npm run dev
   ```
4. Open browser to http://localhost:5173
5. Edit code - both hot-reload automatically

### **Backend Changes**
- Edit files in `services/api/app/`
- Uvicorn auto-reloads on save
- Check http://localhost:8000/docs for API changes

### **Frontend Changes**
- Edit files in `client/src/`
- Vite hot-reloads instantly
- Changes appear in browser immediately

---

## 🔧 Configuration

### **API Configuration**
- **Port:** 8000 (hardcoded in commands)
- **Reload:** Enabled via `--reload` flag
- **CORS:** Configured in `services/api/app/main.py`

### **Frontend Proxy** (`client/vite.config.ts`)
```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
```

**This means:**
- Frontend requests to `/api/...` automatically route to backend
- No need to hardcode `http://localhost:8000` in frontend code
- Production deployment uses same `/api` prefix

---

## 🏆 Code Quality Standards

### **Type Safety: 98% Coverage** 🎉
- 55 of 57 routers fully type-hinted
- 149 functions with proper type annotations
- 32 async functions properly typed
- **Industry-leading quality** (exceeds 95% exceptional standard)

### **Code Policy Enforcement**
- ✅ **P1: Type Safety** - 98% complete
- ✅ **P2: Import Order** - 100% complete
- ✅ **P4: Configuration** - 100% complete (zero hardcoded paths)
- ⏳ **P3: Error Handling** - Phase 5 target
- ⏳ **P6: Vue Components** - Phase 6 target

---

## 🚨 Common Issues & Solutions

### **Issue: "ModuleNotFoundError" in Backend**
**Solution:** Activate virtual environment first
```powershell
cd services/api
.\.venv\Scripts\Activate.ps1
```

### **Issue: "Port 8000 already in use"**
**Solution:** Kill existing process
```powershell
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process -Force
```

### **Issue: Frontend can't reach API**
**Solution:** Ensure backend is running on port 8000
```powershell
# Check backend is running
curl http://localhost:8000/health
```

### **Issue: npm install fails**
**Solution:** Clear cache and reinstall
```powershell
cd client
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
```

---

## 📚 Key Documentation

### **Getting Started**
- `README.md` - Project overview
- `ARCHITECTURAL_EVOLUTION.md` - System history & design
- `.github/copilot-instructions.md` - AI coding guidelines

### **API Documentation**
- `CODING_POLICY.md` - Code standards & patterns
- `ADAPTIVE_POCKETING_MODULE_L.md` - Adaptive pocketing system
- `MACHINE_PROFILES_MODULE_M.md` - Machine configuration
- `ART_STUDIO_V16_1_QUICKREF.md` - Art Studio features

### **Phase Documentation**
- `PHASE_4_BATCH_6_COMPLETE.md` - Type safety completion (98%)
- `N16_N18_FRONTEND_DEVELOPER_HANDOFF.md` - Frontend implementation guide

### **Archived Documentation**
- `__ARCHIVE__/docs_historical/` - Historical reference (DO NOT USE for current dev)

---

## 🎨 Art Studio Integration Points

### **Current Main UI**
- **File:** `client/src/views/ArtStudioUnified.vue`
- **Route:** `/art-studio`
- **Architecture:** Tab-based wrapper with domain-specific tabs
  - 🌹 Rosette (implemented)
  - 🎸 Headstock (placeholder)
  - 🗿 Relief (placeholder)

### **Comparison Mode Integration**
To add comparison mode functionality:
1. Edit `ArtStudioUnified.vue` to add new tab OR toggle
2. Create comparison component in `client/src/components/`
3. Import and integrate into tab content area
4. Backend endpoints already support preset comparison (Phase 26.3)

---

## 🔗 Quick Links

- **API Docs (Swagger):** http://localhost:8000/docs
- **API Health:** http://localhost:8000/health
- **Frontend Dev:** http://localhost:5173
- **GitHub Repo:** https://github.com/HanzoRazer/luthiers-toolbox

---

## 💡 Pro Tips

### **Fast Backend Restart**
```powershell
# One-liner from anywhere
cd services/api; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port 8000
```

### **Check Import Success**
```powershell
cd services/api
python -c "from app.main import app; print('✅ API imports successfully')"
```

### **Test Single Router**
```powershell
cd services/api
python -c "from app.routers.sim_validate import *; print('✅ Router imports successfully')"
```

### **Frontend Type Check**
```powershell
cd client
npm run type-check  # Check for TypeScript errors without building
```

---

## 🎯 Next Steps After Setup

1. ✅ Verify both servers start successfully
2. ✅ Open http://localhost:5173 and explore UI
3. ✅ Check API docs at http://localhost:8000/docs
4. ✅ Review `ArtStudioUnified.vue` structure
5. ✅ Read `N16_N18_FRONTEND_DEVELOPER_HANDOFF.md` for frontend patterns
6. ✅ Check `ARCHITECTURAL_EVOLUTION.md` for system overview

---

## 🏆 Achievement Status

**Project Timeline:**
- **Started:** September 20, 2025
- **Current Status:** Professional-grade system in 2 months
- **Type Coverage:** 98% (industry-leading)
- **Architecture:** MVP → Professional → Intelligent (complete)

**From prototype to marketable product in just 2 months!** 🚀

---

**Document Version:** 1.0  
**Last Updated:** November 16, 2025  
**Status:** ✅ Production Ready  
**Questions?** Check the documentation or API swagger docs at http://localhost:8000/docs
