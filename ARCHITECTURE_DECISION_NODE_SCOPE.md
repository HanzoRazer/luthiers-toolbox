# Architecture Decision: Node.js Scope Limitation

**Date:** November 10, 2025  
**Status:** ✅ Approved  
**Decision Type:** Technology Stack Boundaries

---

## Decision

**Node.js will ONLY be used for frontend build tooling and development. It will NOT be used for backend runtime services.**

---

## Context

We are deep in "ship-it mode" with:
- ✅ **FastAPI backend** (Python 3.11+) handling all business logic
- ✅ **Vue 3 + Vite** frontend with TypeScript
- ✅ **Production-grade CAM algorithms** (adaptive pocketing L.2, multi-post export)
- ✅ **Stable deployment pipeline** (Docker Compose, health checks, CI/CD)

Current working endpoints:
- `/cam/pipeline/run` - CAM pipeline orchestration
- `/cam/pipeline/presets` - Pipeline templates
- `/cam/pocket/adaptive/plan` - Adaptive pocket toolpaths (L.2 continuous spiral ✅)
- `/cam_vcarve/preview_infill` - V-Carve engraving (v13)
- `/cam_gcode/posts_v155` - Post-processor presets (v15.5)
- `/api/art/svg/*` - SVG editor (v16.0)
- `/api/art/relief/*` - Relief mapper (v16.0)
- `/cam/toolpath/helical_entry` - Helical ramping (v16.1)

---

## Node.js Role: Frontend Build & Development ONLY

### ✅ Approved Uses

**1. Vite Dev Server**
```bash
npm run dev  # Hot-reload development at localhost:5173
```

**2. Production Builds**
```bash
npm run build  # Compiles Vue → static assets in dist/
```

**3. Frontend Tooling**
- **TypeScript compiler** (type checking)
- **ESLint** (code quality)
- **Prettier** (formatting)
- **Vue SFC compiler** (`.vue` files → JS)

**4. Development Plugins**
- Vite plugins (vue, typescript, autoprefixer)
- Dev-only tools (vue-devtools, hot module replacement)

---

## What Node.js Will NOT Do

### ❌ No Backend Services

**Explicitly EXCLUDED:**
- ❌ Express/Koa/Fastify servers
- ❌ Real-time WebSocket servers
- ❌ Backend API routes (e.g., no `/api/*` in Node)
- ❌ Database connections (Postgres, MongoDB, Redis)
- ❌ Background job processing
- ❌ Server-side rendering (SSR/SSG)

**Rationale:**
- FastAPI already handles ALL business logic
- Python ecosystem has proven CAM libraries (ezdxf, pyclipper, shapely, OpenCV)
- Adding Node backend = dual-stack complexity with zero benefit
- Current architecture is **stable, tested, production-ready**

---

## Current Architecture (Approved)

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Node.js (Dev/Build ONLY)                          │    │
│  │  • Vite dev server (localhost:5173)                │    │
│  │  • npm run build → dist/ (static assets)           │    │
│  │  • TypeScript, ESLint, Prettier                    │    │
│  └────────────────────────────────────────────────────┘    │
│                          ↓ compiles to                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Vue 3 + TypeScript (Static Assets)                │    │
│  │  • AdaptiveLab.vue                                 │    │
│  │  • PipelineLab.vue                                 │    │
│  │  • ArtStudio.vue (v13, v15.5, v16.0, v16.1)        │    │
│  │  • CamIssuesList.vue (Phase 17)                    │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                          ↓ HTTP/JSON API
┌─────────────────────────────────────────────────────────────┐
│                        BACKEND                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  FastAPI (Python 3.11+)                            │    │
│  │  • /cam/pocket/adaptive/* (L.2 spiralizer)         │    │
│  │  • /cam/pipeline/* (orchestration)                 │    │
│  │  • /cam_vcarve/* (v13 engraving)                   │    │
│  │  • /cam_gcode/* (v15.5 post-processors)            │    │
│  │  • /api/art/* (v16.0 SVG + relief)                 │    │
│  │  • /cam/toolpath/* (v16.1 helical)                 │    │
│  └────────────────────────────────────────────────────┘    │
│                          ↓                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │  CAM Libraries (Python)                            │    │
│  │  • ezdxf (DXF R12 export)                          │    │
│  │  • pyclipper (polygon offsetting)                  │    │
│  │  • shapely (computational geometry)                │    │
│  │  • numpy (numerical operations)                    │    │
│  │  • OpenCV (blueprint vectorization)                │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## Future Scenarios (When to Revisit)

### Scenario 1: Real-Time Machine Streaming
**Need:** WebSocket connection to CNC controller for live position updates

**Solution Options:**
- **Option A:** FastAPI WebSockets (Python) - **PREFERRED** (keep single backend)
- **Option B:** Node.js streaming proxy (if FastAPI websockets inadequate)

**Decision:** Cross that bridge IF/WHEN needed. FastAPI supports websockets natively.

---

### Scenario 2: TypeScript Core Library
**Need:** Shared TS library for both frontend and backend (e.g., geometry validation)

**Solution Options:**
- **Option A:** Keep in frontend, call via API - **CURRENT** (works fine)
- **Option B:** Dual-language bindings (Python ↔ TS via WASM or IPC)
- **Option C:** Node.js microservice for TS-only logic

**Decision:** Current API boundary is clean. No need for shared TS library yet.

---

### Scenario 3: Per-User Dashboards
**Need:** Real-time multi-user collaboration, live cursors, presence indicators

**Solution Options:**
- **Option A:** FastAPI + Server-Sent Events (SSE) - **PREFERRED**
- **Option B:** Node.js + Socket.io (if SSE insufficient)

**Decision:** Not needed for single-user CNC workflows. Revisit if adding collaboration.

---

## Implementation Plan

### Step 1: Install Node.js (Frontend Dev ONLY)
```bash
# Download LTS from https://nodejs.org
# Install to default location (adds to PATH)
node --version  # Should show v20.x or v22.x
npm --version   # Should show v10.x
```

### Step 2: Install Frontend Dependencies
```bash
cd "c:\Users\thepr\Downloads\Luthiers ToolBox\client"
npm install  # Installs Vue, Vite, TypeScript, vue-router, etc.
```

### Step 3: Start Development Server
```bash
npm run dev  # Starts Vite at http://localhost:5173
```

### Step 4: Verify Frontend Routes
- Navigate to http://localhost:5173/lab/adaptive
- Navigate to http://localhost:5173/art-studio
- Navigate to http://localhost:5173/art-studio-v16
- Navigate to http://localhost:5173/helical-ramp

### Step 5: Production Build (When Ready)
```bash
npm run build  # Outputs to client/dist/
# Nginx serves static files from dist/
# All API calls proxy to FastAPI backend (port 8000)
```

---

## Benefits of This Approach

### ✅ Clear Separation of Concerns
- **Node:** Frontend build pipeline (npm, Vite, TypeScript)
- **Python:** All business logic, CAM algorithms, API endpoints

### ✅ Single Source of Truth
- All state management in FastAPI backend
- Vue frontend is stateless (fetches data via API)
- No dual-database syncing, no cross-language data models

### ✅ Predictable Deployment
- **Docker Compose:**
  - `api` container: FastAPI (Python)
  - `client` container: Nginx serving static assets (no Node.js runtime)
  - `proxy` container: Routes `/api/*` → FastAPI, `/*` → Nginx

### ✅ Stability Focus
- Python CAM libraries are mature, battle-tested
- FastAPI is production-grade (used by Netflix, Uber, Microsoft)
- No experimental Node.js CAM libraries (most are academic projects)

### ✅ Team Expertise
- Luthier community knows Python (CNC/CAM workflows)
- Adding Node.js backend = new language for contributors
- Current stack: Python devs can contribute immediately

---

## When to Violate This Decision

**ONLY IF:**
1. **Performance bottleneck** in Python backend (profiled, measured, confirmed)
2. **Library limitation** (no Python equivalent exists for critical feature)
3. **Real-time requirements** FastAPI cannot meet (after testing websockets/SSE)
4. **Community contribution** requires Node.js (e.g., external integration)

**Process:**
1. Document the limitation in GitHub issue
2. Benchmark FastAPI solution first
3. Propose Node.js addition with clear scope
4. Get team approval before implementing

---

## Current Status

### ✅ Backend (100% Complete)
- FastAPI server running on port 8000
- All 6 backend endpoints tested and working:
  * Phase 1 adaptive pocketing (L.2 spiral ✅)
  * Art Studio v13, v15.5, v16.0, v16.1 (all ✅)

### ⏸️ Frontend (Blocked - Need Node.js Install)
- Vue 3 components: ✅ Integrated (8 routes, 14 components)
- Router config: ✅ Complete
- Navigation: ✅ App.vue updated
- **Blocking:** Node.js not installed, cannot run `npm install`

### 📋 Next Action
**Install Node.js LTS** → Unblocks frontend testing → Complete integration validation

---

## References

- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Vite Production Build](https://vitejs.dev/guide/build.html)
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [Docker Multi-Stage Builds](https://docs.docker.com/build/building/multi-stage/)

---

**Decision Approved By:** User (ship-it mode focus on stability)  
**Effective Date:** November 10, 2025  
**Review Date:** When real-time streaming or TS core library becomes necessary
