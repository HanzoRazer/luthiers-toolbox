# MM-0: Mixed-Material Strip Families — Quick Reference

**Status:** ✅ Implemented  
**Date:** November 29, 2025  
**Module:** Rosette Manufacturing OS (RMOS)

---

## 🎯 Overview

MM-0 introduces **mixed-material strip families** for rosette manufacturing, enabling luthiers to design and instantiate strip families with multiple material types (wood, metal, shell, paper, charred, resin, etc.) from curated templates.

**Key Features:**
- ✅ **Template Library**: 3 curated examples (rosewood/abalone/copper, charred maple/paper, all-wood with burn lines)
- ✅ **Material Specs**: Per-material type, species, thickness, finish, CAM profile, and visual properties
- ✅ **Visual Properties**: Base color, reflectivity, iridescence, texture maps, burn gradients
- ✅ **Quality Lanes**: experimental, tuned_v1, tuned_v2, safe, archived
- ✅ **Template Instantiation**: One-click creation from templates into SQLite workspace

---

## 📁 Architecture

### **Backend Components**
```
data/rmos/
└── strip_family_templates.json          # 3 curated templates

services/api/app/
├── schemas/strip_family.py              # MaterialType, MaterialSpec, MaterialVisual, StripFamily
├── core/strip_family_templates.py       # load_templates(), apply_template_to_store()
└── routers/strip_family_router.py       # GET /, GET /templates, POST /from-template/{id}, GET /{id}
```

### **Frontend Components**
```
packages/client/src/
├── models/strip_family.ts                          # TypeScript interfaces
├── stores/useStripFamilyStore.ts                   # Pinia store with template support
├── components/rmos/MixedMaterialStripFamilyEditor.vue  # Editor UI
└── views/RmosStripFamilyLabView.vue                # View wrapper
```

---

## 🔌 API Endpoints

### **GET `/api/rmos/strip-families/`**
List all strip families in workspace.

**Response:**
```json
[
  {
    "id": "sf_wood_shell_copper_01_inst_1733...",
    "name": "Rosewood + Abalone + Copper",
    "default_width_mm": 3.5,
    "sequence": 0,
    "lane": "experimental",
    "materials": [
      {
        "key": "mat_rosewood",
        "type": "wood",
        "species": "Indian Rosewood",
        "thickness_mm": 1.2,
        "finish": "polished",
        "cam_profile": "hardwood_fast",
        "visual": {
          "base_color": "#4a2511",
          "reflectivity": 0.4,
          "iridescence": 0.0,
          "texture_map": null,
          "burn_gradient": null
        }
      },
      {
        "key": "mat_abalone",
        "type": "shell",
        "species": "Abalone",
        "thickness_mm": 0.8,
        "finish": "polished",
        "cam_profile": "shell_slow",
        "visual": {
          "base_color": "#00ffaa",
          "reflectivity": 0.8,
          "iridescence": 0.9,
          "texture_map": null,
          "burn_gradient": null
        }
      },
      {
        "key": "mat_copper",
        "type": "metal",
        "species": "Copper",
        "thickness_mm": 0.5,
        "finish": "polished",
        "cam_profile": "metal_slow",
        "visual": {
          "base_color": "#d2691e",
          "reflectivity": 0.9,
          "iridescence": 0.0,
          "texture_map": null,
          "burn_gradient": null
        }
      }
    ],
    "description": "High-end rosette with exotic inlay materials"
  }
]
```

---

### **GET `/api/rmos/strip-families/templates`**
List available strip family templates (does not create records).

**Response:**
```json
[
  {
    "id": "sf_wood_shell_copper_01",
    "name": "Rosewood + Abalone + Copper",
    "default_width_mm": 3.5,
    "sequence": 0,
    "lane": "experimental",
    "materials": [ /* same as above */ ],
    "description": "High-end rosette with exotic inlay materials"
  },
  {
    "id": "sf_charred_maple_paper_01",
    "name": "Charred Maple + Printed Paper",
    "default_width_mm": 3.0,
    "materials": [ /* 2 materials */ ]
  },
  {
    "id": "sf_all_wood_burnt_lines_01",
    "name": "All-Wood with Burn Lines",
    "default_width_mm": 2.5,
    "materials": [ /* 4 materials */ ]
  }
]
```

---

### **POST `/api/rmos/strip-families/from-template/{template_id}`**
Instantiate a template into the workspace (creates SQLite record).

**Request:**
```
POST /api/rmos/strip-families/from-template/sf_wood_shell_copper_01
```

**Response:**
```json
{
  "id": "sf_wood_shell_copper_01_inst_1733...",
  "name": "Rosewood + Abalone + Copper",
  "default_width_mm": 3.5,
  "lane": "experimental",
  "materials": [ /* full material specs */ ],
  "description": "High-end rosette with exotic inlay materials"
}
```

**Behavior:**
- Checks if record already exists (by template ID in name)
- Creates new record with unique ID (`_inst_<timestamp>`)
- Sets lane to "experimental" by default
- Returns full record with SQLite ID

---

### **GET `/api/rmos/strip-families/{family_id}`**
Get a specific strip family by ID.

**Response:**
```json
{
  "id": "sf_wood_shell_copper_01_inst_1733...",
  "name": "Rosewood + Abalone + Copper",
  /* full record */
}
```

---

## 🎨 UI Component Usage

### **Accessing the Lab**
Navigate to: **`http://localhost:5173/rmos/strip-family-lab`**

### **Template Library (Left Panel)**
1. Click **"Load Templates"** to fetch curated templates
2. Each template card shows:
   - Template name
   - Material count badge
   - Material preview bars (color-coded)
   - Width, sequence, and lane metadata
3. Click **"Apply Template"** to instantiate into workspace

### **Family Editor (Right Panel)**
Once a template is applied or an existing family is selected:
1. **Basic Properties**: Name, width, sequence, lane, description
2. **Materials Editor**:
   - **Add Material**: Click "+" to add new material
   - **Remove Material**: Click "×" on material card
   - **Per-Material Fields**:
     - Material Type (wood, metal, shell, paper, foil, charred, resin, composite)
     - Species/Name
     - Thickness (mm)
     - Finish (polished, matte, oxidized, etc.)
     - CAM Profile (optional)
   - **Visual Properties** (collapsible):
     - Base Color (color picker)
     - Reflectivity (0-1)
     - Iridescence (0-1)
     - Texture Map URL
     - Burn Gradient (JSON)
3. **Actions**:
   - **Save Changes**: Update existing family
   - **Cancel**: Deselect and discard changes

### **Existing Families (Bottom Panel)**
- Shows all instantiated strip families
- Click to select and edit
- Badge shows material count
- Lane badge shows quality tier

---

## 📊 Data Schema

### **MaterialSpec**
```typescript
interface MaterialSpec {
  key: string                   // Unique key (e.g., "mat_rosewood")
  type: MaterialType            // wood | metal | shell | paper | foil | charred | resin | composite
  species: string | null        // Species name (e.g., "Indian Rosewood", "Abalone")
  thickness_mm: number          // Material thickness in mm
  finish: string | null         // Surface finish (e.g., "polished", "matte")
  cam_profile: string | null    // CAM profile key (optional, for MM-2)
  visual: MaterialVisual        // Visual properties
}
```

### **MaterialVisual**
```typescript
interface MaterialVisual {
  base_color: string            // Hex color (e.g., "#4a2511")
  reflectivity: number          // 0.0 - 1.0
  iridescence: number           // 0.0 - 1.0
  texture_map: string | null    // Optional texture URL
  burn_gradient: any | null     // Optional burn gradient (JSON)
}
```

### **StripFamily**
```typescript
interface StripFamily {
  id: string
  name: string
  default_width_mm: number
  sequence: number
  lane: 'experimental' | 'tuned_v1' | 'tuned_v2' | 'safe' | 'archived'
  description: string | null
  materials: MaterialSpec[]
  
  // Legacy fields (backward compatibility)
  color_hex?: string
  default_tile_length_mm?: number
}
```

---

## 🧪 Testing

### **Start Both Servers**
```powershell
# Terminal 1: FastAPI
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# Terminal 2: Vite
cd packages/client
npm run dev
```

### **Test Flow**
1. Open browser: `http://localhost:5173/rmos/strip-family-lab`
2. Click **"Load Templates"** → should show 3 templates
3. Click **"Apply Template"** on "Rosewood + Abalone + Copper"
4. Verify template appears in **Existing Families** panel
5. Click on family in bottom panel → right panel should populate
6. Edit material (e.g., change thickness) → click **"Save Changes"**
7. Refresh page → changes should persist

### **API Smoke Test**
```powershell
# List templates
curl http://localhost:8000/api/rmos/strip-families/templates | ConvertFrom-Json | Format-List

# Instantiate template
curl -X POST http://localhost:8000/api/rmos/strip-families/from-template/sf_wood_shell_copper_01 | ConvertFrom-Json

# List families
curl http://localhost:8000/api/rmos/strip-families/ | ConvertFrom-Json | Format-Table
```

---

## 📚 Curated Templates

### **1. Rosewood + Abalone + Copper** (`sf_wood_shell_copper_01`)
- **Materials**: 3 (wood, shell, metal)
- **Width**: 3.5mm
- **Use Case**: High-end classical guitar rosettes with exotic inlay
- **Visual**: Dark wood + iridescent shell + metallic copper

### **2. Charred Maple + Printed Paper** (`sf_charred_maple_paper_01`)
- **Materials**: 2 (charred wood, paper)
- **Width**: 3.0mm
- **Use Case**: Experimental mixed-media rosettes with custom prints
- **Visual**: Charred gradient + printed pattern paper

### **3. All-Wood with Burn Lines** (`sf_all_wood_burnt_lines_01`)
- **Materials**: 4 (maple, burn line, rosewood, burn line)
- **Width**: 2.5mm
- **Use Case**: Traditional wood rosettes with pyrography accents
- **Visual**: Alternating light maple + dark burns + rosewood

---

## 🚀 Next Steps: MM-1 through MM-4

### **MM-1: Visual Shader/Preview Layer**
- Real-time 3D preview of strip families
- Metallic, iridescent, charred gradient rendering
- Texture map integration

### **MM-2: CAM Profile Manager**
- Per-material feeds/speeds/tooling
- Material-aware toolpath generation
- Adaptive strategies per material type

### **MM-3: PDF Design Sheet Generator**
- Export strip family specs to PDF
- Material callouts, dimensions, assembly notes
- Customer/shop-ready documentation

### **MM-4: Risk Model Integration**
- Per-material risk multipliers
- Failure mode analysis (brittle shell, thin metal)
- Safety margins and tolerances

---

## 🐛 Troubleshooting

### **Issue**: Templates not loading
**Solution**: Verify `data/rmos/strip_family_templates.json` exists and is valid JSON

### **Issue**: "Apply Template" does nothing
**Solution**: Check browser console for API errors; ensure backend is running on port 8000

### **Issue**: Changes not persisting
**Solution**: Verify SQLite file exists at `services/api/rmos_stores.db` with write permissions

### **Issue**: Materials editor fields not populating
**Solution**: Check that `visual` object is initialized with default values in TypeScript model

---

## ✅ Integration Checklist

**Backend:**
- [x] Create `data/rmos/strip_family_templates.json` with 3 templates
- [x] Extend `schemas/strip_family.py` with MM-0 fields
- [x] Create `core/strip_family_templates.py` loader
- [x] Create `routers/strip_family_router.py` with 4 endpoints
- [x] Register router in `main.py` at `/api/rmos/strip-families`

**Frontend:**
- [x] Create `models/strip_family.ts` with TypeScript interfaces
- [x] Extend `stores/useStripFamilyStore.ts` with template support
- [x] Create `MixedMaterialStripFamilyEditor.vue` component
- [x] Create `RmosStripFamilyLabView.vue` wrapper
- [x] Add route to `router/index.ts` at `/rmos/strip-family-lab`

**Testing:**
- [ ] Smoke test API endpoints
- [ ] Test template instantiation flow
- [ ] Verify UI rendering and editing
- [ ] Confirm persistence across page reloads

---

**Status:** ✅ MM-0 Implementation Complete  
**Next Module:** MM-1 (Visual Shader/Preview Layer)  
**Access:** `http://localhost:5173/rmos/strip-family-lab`
