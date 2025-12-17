# Patch N.14 Quick Reference

**Unified CAM Settings** – Post template editor + adaptive preview

---

## 🎯 At a Glance

**What It Does:**
- Edit post-processor templates (header/footer/tokens) via web UI
- Preview adaptive toolpaths (spiral, trochoid) as SVG
- Unified `/cam/settings` route for CAM configuration

**Key Features:**
- Live JSON editor with validation
- Visual toolpath generators
- Real-time SVG rendering
- Client + server validation

---

## 📡 API Endpoints

### **GET /api/posts**
```bash
curl http://localhost:8000/api/posts
# Returns: Array of PostDef objects
```

### **PUT /api/posts**
```bash
curl -X PUT http://localhost:8000/api/posts \
  -H "Content-Type: application/json" \
  -d '[{"id":"grbl","title":"GRBL","controller":"GRBL","header":["G21"],"footer":["M30"]}]'
# Returns: {"ok": true, "count": 1}
```

### **POST /api/cam/adaptive/spiral.svg**
```bash
curl -X POST http://localhost:8000/api/cam/adaptive/spiral.svg \
  -H "Content-Type: application/json" \
  -d '{"width":60,"height":40,"step":2.0}' \
  -o spiral.svg
# Returns: SVG image
```

### **POST /api/cam/adaptive/trochoid.svg**
```bash
curl -X POST http://localhost:8000/api/cam/adaptive/trochoid.svg \
  -H "Content-Type: application/json" \
  -d '{"width":50,"height":30,"pitch":3.0,"amp":0.6,"feed_dir":"x"}' \
  -o trochoid.svg
# Returns: SVG image
```

---

## 🎨 Vue Components

### **PostTemplatesEditor.vue**
```vue
<template>
  <PostTemplatesEditor />
</template>
```

**Features:**
- Textarea JSON editor
- Load/Save buttons
- Client-side validation (syntax, schema, duplicate IDs)
- Success/error feedback

**Usage:**
1. Click "Load Templates"
2. Edit JSON in textarea
3. Click "Save Templates"
4. Verify success message

---

### **AdaptivePreview.vue**
```vue
<template>
  <AdaptivePreview />
</template>
```

**Features:**
- Two-panel layout (spiral + trochoid)
- Parameter inputs with v-model
- Plot buttons → API calls
- Inline SVG rendering

**Usage:**
1. Adjust parameters (width, height, step/pitch)
2. Click "Plot Spiral" or "Plot Trochoid"
3. View SVG preview in panel

---

## 📋 PostDef Schema

```typescript
interface LineNumbers {
  enabled: boolean;      // Enable line numbers
  start: number;         // Starting line number (default: 10)
  step: number;          // Increment (default: 10)
  prefix: string;        // Prefix (default: "N")
}

interface PostDef {
  id: string;                      // Unique identifier (lowercase, no spaces)
  title: string;                   // Display name
  controller: string;              // Controller type
  line_numbers: LineNumbers;       // Line numbering config
  header: string[];                // Header lines
  footer: string[];                // Footer lines
  percent_wrapper: boolean;        // Wrap in % signs
  program_number_from: string;     // "filename" or "manual"
  tokens: Record<string, string>;  // Custom token replacements
}
```

**Minimal Example:**
```json
{
  "id": "grbl",
  "title": "GRBL 1.1",
  "controller": "GRBL",
  "header": ["G21", "G90"],
  "footer": ["M30"]
}
```

**Full Example:**
```json
{
  "id": "mach4_mill",
  "title": "Mach4 Mill",
  "controller": "Mach4",
  "line_numbers": {
    "enabled": true,
    "start": 10,
    "step": 10,
    "prefix": "N"
  },
  "header": [
    "G21",
    "G90",
    "G17",
    "(POST=Mach4;UNITS=mm;DATE={DATE})",
    "M6 T{TOOL}",
    "M3 S{RPM}"
  ],
  "footer": [
    "M5",
    "M30",
    "(End of program)"
  ],
  "percent_wrapper": false,
  "program_number_from": "filename",
  "tokens": {
    "MACHINE_NAME": "Mach4 3-Axis Mill",
    "SAFE_Z": "10.0"
  }
}
```

---

## 🧮 Validation Rules

### **Client-Side (Before Save)**
```typescript
// 1. Valid JSON syntax
JSON.parse(rawJson)

// 2. Must be array
Array.isArray(parsed)

// 3. Required fields per post
post.id && post.title && post.controller

// 4. Arrays for header/footer
Array.isArray(post.header) && Array.isArray(post.footer)

// 5. No duplicate IDs
ids.filter((id, i) => ids.indexOf(id) !== i).length === 0
```

### **Server-Side (In PUT /posts)**
```python
# 1. Pydantic validation (types, required fields)
posts: List[PostDef]

# 2. Duplicate ID check
if ids.count(id) > 1: raise HTTPException(400)

# 3. File write validation
json.dump(data, f, ensure_ascii=False)
```

---

## 🔧 Common Tasks

### **Task 1: Edit Post Header**
1. Open `/cam/settings`
2. Click "Load Templates"
3. Find post by `"id": "grbl"`
4. Edit `"header"` array
5. Click "Save Templates"

### **Task 2: Add Custom Token**
```json
{
  "id": "mach4",
  "tokens": {
    "COOLANT_ON": "M8",
    "COOLANT_OFF": "M9"
  }
}
```
Use in header: `{COOLANT_ON}`

### **Task 3: Preview Spiral Toolpath**
1. Open `/cam/settings` → Adaptive Preview
2. Set: width=80, height=50, step=3
3. Click "Plot Spiral"
4. View purple spiral SVG

### **Task 4: Preview Trochoid Path**
1. Set: width=60, height=20, pitch=4, amp=0.8, direction=X
2. Click "Plot Trochoid"
3. View teal trochoidal SVG

---

## 🐛 Error Messages

| Error | Cause | Fix |
|-------|-------|-----|
| `JSON must be an array` | Root is object, not array | Wrap in `[...]` |
| `Duplicate post IDs: grbl` | Two posts with same ID | Change one ID to unique value |
| `header and footer must be arrays` | String instead of array | Change `"header": "G21"` to `"header": ["G21"]` |
| `Each post must have id, title, and controller` | Missing required field | Add missing field |
| `HTTP 400` (server error) | Server validation failed | Check server logs for detail |

---

## 📊 Parameter Ranges

### **Spiral Parameters**
| Parameter | Typical Range | Notes |
|-----------|---------------|-------|
| width | 20-200 mm | Pocket width |
| height | 20-200 mm | Pocket height |
| step | 1-10 mm | Stepover distance |

### **Trochoid Parameters**
| Parameter | Typical Range | Notes |
|-----------|---------------|-------|
| width | 20-200 mm | Slot length |
| height | 5-100 mm | Slot width |
| pitch | 2-10 mm | Pass spacing |
| amp | 0.3-2.0 mm | Oscillation depth |
| feed_dir | "x" or "y" | Primary feed axis |

---

## 🚀 Quick Start

### **1. Start Backend**
```powershell
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

### **2. Start Frontend**
```powershell
cd packages/client
npm run dev
```

### **3. Test Endpoints**
```powershell
# List posts
curl http://localhost:8000/api/posts

# Generate spiral
curl -X POST http://localhost:8000/api/cam/adaptive/spiral.svg \
  -H "Content-Type: application/json" \
  -d '{"width":60,"height":40,"step":2}' \
  -o test_spiral.svg

start test_spiral.svg
```

### **4. Test UI**
1. Open `http://localhost:5173/cam/settings`
2. Click "Load Templates"
3. Edit a header line
4. Click "Save Templates"
5. Switch to Adaptive Preview
6. Click "Plot Spiral"
7. View purple spiral

---

## 📁 File Locations

**Backend:**
```
services/api/app/
├── routers/
│   ├── posts_router.py              # Template CRUD API
│   └── adaptive_preview_router.py   # SVG generators
├── data/
│   └── posts.json                   # Post definitions
└── main.py                          # Router registration
```

**Frontend:**
```
packages/client/src/
├── components/
│   ├── PostTemplatesEditor.vue      # JSON editor
│   └── AdaptivePreview.vue          # Toolpath preview
└── router/
    └── index.js                     # Route: /cam/settings
```

---

## 🔗 Integration Points

**N.12 (Tool Tables):**
- Post tokens can reference tools: `{TOOL_DIA}`, `{RPM}`
- Combined workflow: tools → posts → export

**Module L (Adaptive Pocketing):**
- Preview uses same spiral algorithm as `/cam/pocket/adaptive/plan`
- Validate strategy before full G-code generation

**Module M (Machine Profiles):**
- Posts associated with machines
- Unified CAM settings: machine + tools + posts

---

## 📚 See Also

- [Full Specification](./PATCH_N14_UNIFIED_CAM_SETTINGS.md) - Complete documentation
- [Patch N.12](./PATCH_N12_MACHINE_TOOL_TABLES.md) - Tool management
- [Module L](./ADAPTIVE_POCKETING_MODULE_L.md) - Adaptive pocketing
- [Post System](./POST_CHOOSER_SYSTEM.md) - Multi-post exports

---

**Status:** ✅ Core implementation complete  
**Pending:** Route integration, comprehensive testing  
**Next:** Add `/cam/settings` route to Vue router
