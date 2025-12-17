# Art Studio v16.0 + Community Patch — Quick Reference 🚀

**Integration Date:** November 7, 2025  
**Status:** ✅ Backend Complete | ⏳ Frontend Pending Route

---

## 📁 Files Integrated

### **Backend (5 files)**
```
services/api/app/
├── main.py                              ✅ MODIFIED
└── routers/
    ├── cam_svg_v160_router.py           ✅ NEW
    └── cam_relief_v160_router.py        ✅ NEW
```

### **Frontend (4 files)**
```
packages/client/src/
├── api/v16.ts                           ✅ NEW
├── components/
│   ├── SvgCanvas.vue                    ✅ NEW
│   └── ReliefGrid.vue                   ✅ NEW
└── views/
    └── ArtStudioV16.vue                 ✅ NEW
```

### **Community (4 files)**
```
.
├── CONTRIBUTORS.md                      ✅ NEW
├── docs/PR_GUIDE.md                     ✅ NEW
└── .github/ISSUE_TEMPLATE/
    ├── bug_report.yml                   ✅ NEW
    └── feature_request.yml              ✅ NEW
```

### **Tests (1 file)**
```
smoke_v16_art_studio.ps1                 ✅ NEW (7 tests)
```

---

## ⚡ Quick Start

### **1. Test Backend (5 minutes)**
```powershell
# Start API server
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# Run smoke tests (new terminal)
cd ..\..
.\smoke_v16_art_studio.ps1
```

**Expected:** ✅ All 7 tests pass

---

### **2. Wire Up Frontend (2 minutes)**

**Add route to `packages/client/src/router/index.ts`:**
```typescript
{
  path: '/art-studio-v16',
  name: 'ArtStudioV16',
  component: () => import('@/views/ArtStudioV16.vue')
}
```

**Start dev server:**
```powershell
cd packages/client
npm run dev
```

**Visit:** `http://localhost:5173/art-studio-v16`

---

### **3. Apply Community Patch (1 minute)**

**Option A - Git:**
```powershell
git apply --reject README_Community_Patch\README_Community_Patch\patches\readme_community.diff
```

**Option B - PowerShell:**
```powershell
powershell -ExecutionPolicy Bypass -File README_Community_Patch\README_Community_Patch\patches\Append-Community.ps1 -ReadmePath README.md
```

---

## 🎯 API Endpoints

### **SVG Editor**
```
GET  /api/art/svg/health           # Service status
POST /api/art/svg/normalize        # Minify whitespace
POST /api/art/svg/outline          # Stroke → polylines
POST /api/art/svg/save             # Export base64
```

### **Relief Mapper**
```
GET  /api/art/relief/health        # Service status
POST /api/art/relief/heightmap_preview  # Grayscale → 3D mesh
```

---

## 💻 Code Examples

### **SVG Normalization**
```typescript
import { svgNormalize } from '@/api/v16'

const svg = '<svg xmlns="..."> ... </svg>'
const res = await svgNormalize(svg)
console.log(res.svg_text)  // Minified
```

### **Relief Heightmap**
```typescript
import { reliefPreview } from '@/api/v16'

const grayscale = [
  [0.0, 0.5, 1.0],
  [0.2, 0.4, 0.8]
]
const res = await reliefPreview(grayscale, 0, 1.2, 1.0)
console.log(res.verts)  // 3D coordinates
```

---

## 🧪 Smoke Test Coverage

1. ✅ SVG health (`/api/art/svg/health`)
2. ✅ Relief health (`/api/art/relief/health`)
3. ✅ SVG normalize (whitespace minification)
4. ✅ SVG outline (stroke → polylines)
5. ✅ SVG save (base64 export)
6. ✅ Relief heightmap (grayscale → mesh)
7. ✅ Z calculation validation (math accuracy)

**Run:** `.\smoke_v16_art_studio.ps1`

---

## 📋 Manual Steps Checklist

- [x] Copy backend routers
- [x] Register in `main.py`
- [x] Copy frontend components
- [x] Copy community templates
- [x] Create smoke tests
- [ ] **Add Vue route** (2 min)
- [ ] **Add navigation link** (1 min)
- [ ] **Apply README patch** (1 min)
- [ ] **Run smoke tests** (1 min)
- [ ] **Test UI in browser** (5 min)

---

## 🔗 Integration Points

| System | Integration | Status |
|--------|-------------|--------|
| **Art Studio v15.5** | SVG outline → post-processor | ⏳ Pending |
| **Module L** | Relief → adaptive pocket | ⏳ Pending |
| **Patch N18** | SVG outline → arc linkers | ⏳ Pending |
| **Dashboard** | Add v16 metrics | ⏳ Pending |

---

## 🐛 Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Check routers copied to `services/api/app/routers/` |
| `404 /api/art/svg/health` | Restart API server after main.py changes |
| `Cannot find module '@/api/v16'` | Verify `v16.ts` in `packages/client/src/api/` |
| Route not found | Add route to `router/index.ts` |

---

## 📚 Full Documentation

**Comprehensive Guide:**  
[ART_STUDIO_V16_0_INTEGRATION_COMPLETE.md](./ART_STUDIO_V16_0_INTEGRATION_COMPLETE.md)

**Enhancement Roadmap:**  
[ART_STUDIO_ENHANCEMENT_ROADMAP.md](./ART_STUDIO_ENHANCEMENT_ROADMAP.md)

---

## 🎸 Example Use Case

**Carved Rosette for Classical Guitar:**

1. Import grayscale image (512×512 px)
2. Generate heightmap: `z_min=0mm, z_max=2mm`
3. Preview in Relief Grid
4. Export polylines
5. Post-process with Art Studio v15.5 (GRBL)
6. Run adaptive pocket with Module L (3mm ball end mill)
7. Export G-code with N18 arc smoothing

---

**Next:** Add route to `router/index.ts` and test! 🚀
