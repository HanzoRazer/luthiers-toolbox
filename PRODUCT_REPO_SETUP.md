# PRODUCT REPO SETUP GUIDE
### Step-by-Step Scaffolding for Luthier's ToolBox Product Suite

**Version:** 1.0  
**Last Updated:** December 3, 2025

---

## 📋 Overview

This guide provides step-by-step instructions for creating each product repository in the Luthier's ToolBox ecosystem. All products share a common structure with edition-specific customizations.

### **Product Family:**

**Core Editions:**
1. `ltb-express` - Entry-tier design tools
2. `ltb-pro` - Full CAM workstation
3. `ltb-enterprise` - Complete shop OS

**Parametric Products:**
4. `ltb-parametric-guitar` - Body shape generator
5. `ltb-neck-designer` - Neck profile creator
6. `ltb-headstock-designer` - Headstock layout tool
7. `ltb-bridge-designer` - Bridge geometry tool
8. `ltb-fingerboard-designer` - Fingerboard calculator

**Specialized:**
9. `blueprint-reader` - Blueprint import/vectorization

---

## 🏗️ Common Repository Structure

All products follow this standard structure:

```
product-name/
├── client/                  # Vue 3 + Vite frontend
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── src/
│       ├── main.ts
│       ├── App.vue         # Copy from templates/client/App.vue
│       ├── router/
│       ├── views/
│       ├── components/
│       ├── store/
│       └── styles/
│
├── server/                  # FastAPI backend
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py         # Copy from templates/server/main.py
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── db.py
│   └── .env                # Copy from templates/env/.env.<edition>
│
├── docs/
│   └── README.md
│
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start (Any Product)

### **1. Create Repository**

```powershell
# Create repo directory
mkdir ltb-<product-name>
cd ltb-<product-name>

# Initialize git
git init

# Create directory structure
mkdir client, server, docs, tests
```

### **2. Setup Client (Vue 3 + Vite)**

```powershell
cd client
npm create vite@latest . -- --template vue-ts

# Install dependencies
npm install
npm install vue-router pinia

# Copy canonical App.vue
Copy-Item ..\..\..\templates\client\App.vue .\src\App.vue

# Configure Vite proxy (vite.config.ts)
# See template below
```

**vite.config.ts template:**

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/config': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

### **3. Setup Server (FastAPI)**

```powershell
cd ..\server

# Create pyproject.toml or requirements.txt
# See template below

# Copy canonical main.py
Copy-Item ..\..\templates\server\main.py .\app\main.py

# Copy .env template
Copy-Item ..\..\templates\env\.env.<edition> .\.env

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

**requirements.txt template:**

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-multipart==0.0.6
```

**Add per edition:**
- **Express:** `ezdxf`, `shapely`
- **Pro:** Add `pyclipper`, `numpy`, all Express deps
- **Enterprise:** Add `psycopg2-binary`, `sqlalchemy`, `alembic`, all Pro deps

### **4. Test the Stack**

```powershell
# Terminal 1: Start server
cd server
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# Terminal 2: Start client
cd client
npm run dev

# Open browser to http://localhost:5173
# Should see edition-specific header and subtitle
```

---

## 📦 Product-Specific Setup

### **1. LTB Express Edition**

```powershell
# Create repo
mkdir ltb-express
cd ltb-express
git init

# Setup client
cd client
npm create vite@latest . -- --template vue-ts
npm install vue-router pinia
Copy-Item ..\..\templates\client\App.vue .\src\App.vue

# Setup server
cd ..\server
Copy-Item ..\..\templates\server\main.py .\app\main.py
Copy-Item ..\..\templates\env\.env.express .\.env

# Create Express-specific views:
# client/src/views/DashboardExpress.vue
# client/src/views/RosetteDesignerLite.vue
# client/src/views/CurveLabMini.vue
# client/src/views/FretboardDesigner.vue

# Create Express-specific routers:
# server/app/api/routes_projects.py
# server/app/api/routes_rosettes.py
# server/app/api/routes_curves.py
# server/app/api/routes_fretboards.py
# server/app/api/routes_exports.py

# Mount routers in main.py:
```python
from .api import routes_projects, routes_rosettes, routes_curves
app.include_router(routes_projects.router, prefix="/projects", tags=["projects"])
app.include_router(routes_rosettes.router, prefix="/rosettes", tags=["design"])
# ... etc
```

---

### **2. LTB Pro Edition**

```powershell
# Follow Express setup, then add:

# Update .env
Copy-Item ..\..\templates\env\.env.pro .\server\.env

# Add Pro-specific views:
# client/src/views/CamPipelineLab.vue
# client/src/views/PostConfigurator.vue
# client/src/views/JobLog.vue

# Add Pro-specific routers:
# server/app/api/routes_cam.py
# server/app/api/routes_overrides.py
# server/app/api/routes_posts.py
# server/app/api/routes_jigs.py

# Copy CAM core from golden master:
# server/app/cam/ (adaptive_core_l*.py, feedtime*.py, etc.)

# Mount additional routers:
```python
from .api import routes_cam, routes_overrides
app.include_router(routes_cam.router, prefix="/cam", tags=["cam"])
```

---

### **3. LTB Enterprise Edition**

```powershell
# Follow Pro setup, then add:

# Update .env
Copy-Item ..\..\templates\env\.env.enterprise .\server\.env

# Change database to PostgreSQL in .env:
# DATABASE_URL="postgresql://user:password@localhost:5432/ltb_enterprise"

# Add Enterprise-specific views:
# client/src/views/Orders.vue
# client/src/views/Customers.vue
# client/src/views/InventoryBOM.vue
# client/src/views/ProductionSchedule.vue
# client/src/views/Financials.vue

# Add Enterprise-specific routers:
# server/app/api/routes_orders.py
# server/app/api/routes_customers.py
# server/app/api/routes_inventory.py
# server/app/api/routes_financials.py

# Mount additional routers:
```python
from .api import routes_orders, routes_customers
app.include_router(routes_orders.router, prefix="/orders", tags=["business"])
```

---

### **4. LTB Neck Designer (Parametric Product)**

```powershell
# Create repo
mkdir ltb-neck-designer
cd ltb-neck-designer
git init

# Setup client
cd client
npm create vite@latest . -- --template vue-ts
npm install vue-router pinia
Copy-Item ..\..\templates\client\App.vue .\src\App.vue

# Setup server
cd ..\server
Copy-Item ..\..\templates\server\main.py .\app\main.py
Copy-Item ..\..\templates\env\.env.neck .\.env

# Create Neck Designer views:
# client/src/views/NeckDesigner.vue
# client/src/components/NeckParamControls.vue
# client/src/components/NeckSectionPreview.vue

# Create data files:
# server/data/NeckProfileLibrary.json
# server/data/NeckProfilePresets.json

# Create routers:
# server/app/api/routes_neck_presets.py
# server/app/api/routes_neck_exports.py

# Mount routers:
```python
from .api import routes_neck_presets, routes_neck_exports
app.include_router(routes_neck_presets.router, prefix="/presets", tags=["neck"])
app.include_router(routes_neck_exports.router, prefix="/exports", tags=["io"])
```

---

## 🔧 Configuration Checklist

### **Client Configuration**

- [ ] `package.json` - Set name, version, description
- [ ] `vite.config.ts` - Configure proxy to backend
- [ ] `tsconfig.json` - Enable strict mode, Vite types
- [ ] `src/main.ts` - Initialize Vue app, router, pinia
- [ ] `src/App.vue` - Copy from templates (auto-detects edition)
- [ ] `src/router/index.ts` - Define routes for product views

### **Server Configuration**

- [ ] `app/main.py` - Copy from templates (feature flags work automatically)
- [ ] `.env` - Copy correct edition template, customize settings
- [ ] `requirements.txt` - Add edition-specific dependencies
- [ ] `app/api/` - Create product-specific routers
- [ ] `app/models/` - Define database models
- [ ] `app/schemas/` - Define Pydantic schemas
- [ ] Mount routers in `main.py`

### **Documentation**

- [ ] `README.md` - Product overview, setup instructions
- [ ] `docs/API.md` - API endpoint documentation
- [ ] `docs/FEATURES.md` - Feature list and roadmap

---

## 🧪 Testing Strategy

### **Local Testing**

```powershell
# Server tests
cd server
pytest tests/

# Client tests (optional)
cd client
npm run test

# Smoke test
.\scripts\smoke_test.ps1
```

### **CI/CD Integration**

Create `.github/workflows/<product>.yml`:

```yaml
name: Product Name CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install server dependencies
        run: |
          cd server
          pip install -r requirements.txt
      
      - name: Run server tests
        run: |
          cd server
          pytest
      
      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install client dependencies
        run: |
          cd client
          npm install
      
      - name: Build client
        run: |
          cd client
          npm run build
```

---

## 📊 Feature Matrix

| Feature | Express | Pro | Enterprise | Parametric |
|---------|---------|-----|------------|------------|
| Rosette Designer | ✅ | ✅ | ✅ | ❌ |
| Curve Lab | ✅ | ✅ | ✅ | ❌ |
| Fretboard Designer | ✅ | ✅ | ✅ | ❌ |
| CAM Pipeline | ❌ | ✅ | ✅ | ❌ |
| Adaptive Pocketing | ❌ | ✅ | ✅ | ❌ |
| Overrides Learning | ❌ | ✅ | ✅ | ❌ |
| Risk Modeling | ❌ | ✅ | ✅ | ❌ |
| Orders & Customers | ❌ | ❌ | ✅ | ❌ |
| Inventory & BOM | ❌ | ❌ | ✅ | ❌ |
| COGS & Financials | ❌ | ❌ | ✅ | ❌ |
| E-Commerce | ❌ | ❌ | ✅ | ❌ |
| Parametric Design | ❌ | ❌ | ❌ | ✅ |

---

## 🔐 IP Protection Strategy

### **Express Edition (Public)**
- Contains no proprietary algorithms
- Safe to open-source or distribute widely
- Acts as marketing funnel

### **Pro Edition (Protected)**
- Obfuscate CAM core (`cam/` module)
- License key validation (future)
- Watermark exports with Pro license

### **Enterprise Edition (Protected)**
- Server-side license validation
- Role-based access control
- Audit logging for compliance

### **Parametric Products (Hybrid)**
- Core geometry algorithms can be public
- Premium presets behind paywall
- Etsy/Gumroad handles licensing

---

## 📈 Deployment Strategy

### **Desktop Apps (Electron)**
```powershell
# Install Electron builder
npm install -g electron-builder

# Package for Windows
electron-builder --windows

# Package for macOS
electron-builder --mac

# Package for Linux
electron-builder --linux
```

### **Web Apps (Docker)**
```dockerfile
# Dockerfile example
FROM node:18 AS client-build
WORKDIR /app/client
COPY client/package*.json ./
RUN npm install
COPY client/ ./
RUN npm run build

FROM python:3.11
WORKDIR /app
COPY server/requirements.txt ./
RUN pip install -r requirements.txt
COPY server/ ./server/
COPY --from=client-build /app/client/dist ./server/static
CMD ["uvicorn", "server.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🎯 Launch Checklist

### **Pre-Launch**
- [ ] All tests passing
- [ ] Documentation complete
- [ ] License terms finalized
- [ ] Pricing confirmed
- [ ] Marketing materials ready

### **Launch Day**
- [ ] Deploy to production
- [ ] Announce on social media
- [ ] Email existing users
- [ ] Submit to Etsy/Gumroad

### **Post-Launch**
- [ ] Monitor telemetry
- [ ] Collect user feedback
- [ ] Fix critical bugs
- [ ] Plan next iteration

---

## 📚 Related Documents

- [Master Segmentation Strategy](./docs/products/MASTER_SEGMENTATION_STRATEGY.md) - Overall product ecosystem
- [Marketing & Positioning](./docs/products/MARKETING_POSITIONING_ADDENDUM.md) - Go-to-market strategy
- [Founder's Preface](./docs/products/FOUNDERS_PREFACE.md) - Vision and motivation
- [Unresolved Tasks Inventory](./UNRESOLVED_TASKS_INVENTORY.md) - Current project status

---

## 🆘 Troubleshooting

### **Issue: /config endpoint returns 404**
**Solution:** Check that `main.py` includes the `/config` route (should be in template)

### **Issue: Frontend shows "DEV" edition**
**Solution:** Verify `.env` file exists and `APP_EDITION` is set correctly

### **Issue: CORS errors in browser**
**Solution:** Check `CORS_ORIGINS` in `.env` and restart server

### **Issue: Database locked (SQLite)**
**Solution:** Close all connections, delete `.db` file, restart

---

**Status:** ✅ Setup Guide Complete  
**Version:** 1.0  
**Last Updated:** December 3, 2025  
**Next Steps:** Begin Phase 1 implementation (Express + Parametric Guitar)
