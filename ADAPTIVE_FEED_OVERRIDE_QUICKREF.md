# Adaptive Feed Override Quick Reference

**TL;DR:** Override adaptive feed mode at export time without editing JSON configs. Preview NC with highlighted FEED_HINT zones.

---

## 🚀 Quick Start

### **User Workflow**
1. Select post-processor (GRBL/Mach4/LinuxCNC/PathPilot/MASSO)
2. Choose **Adaptive Feed Mode**:
   - `Inherit from post` - Use config defaults ✅
   - `Comment mode` - FEED_HINT comments
   - `Inline F` - Scaled feed rates (specify min_f)
   - `M-code` - Machine registers (specify M-codes)
3. Click **Preview NC** to see highlighted zones
4. Click **Export G-code** to download

### **Storage**
Settings persist to `localStorage('toolbox.adaptiveFeed')` automatically.

---

## 📦 API Integration

### **Request Body** (`/api/cam/pocket/adaptive/gcode`)
```json
{
  "post_id": "GRBL",
  "adaptive_feed_override": {
    "mode": "comment",              // or "inline_f" | "mcode" | "inherit"
    "inline_min_f": 600,            // optional (inline_f mode)
    "mcode_start": "M52 P",         // optional (mcode mode)
    "mcode_end": "M52 P100"         // optional (mcode mode)
  }
}
```

### **Override Logic**
- `mode: "inherit"` or `null` → Uses post profile defaults
- `mode: "comment"` → `(FEED_HINT START slowdown=0.75)` comments
- `mode: "inline_f"` → Scaled F values (e.g., `F900` at 75% slowdown)
- `mode: "mcode"` → M-code wrappers (e.g., `M52 P75`)

---

## 🎨 UI Controls

### **Adaptive Feed Selector** (AdaptivePocketLab.vue)
```vue
Adaptive Feed Mode [Override]
├─ [Inherit from post ▼]       ← Default (no override)
├─ Comment mode                 ← FEED_HINT comments
├─ Inline F                     ← Shows: Min feed (mm/min) [600]
└─ M-code                       ← Shows: M-code start [M52 P], M-code end [M52 P100]
```

### **Preview NC Button**
- Purple button between "Plan" and "Export G-code"
- Opens drawer with line-by-line G-code
- **Yellow background** for FEED_HINT zones
- **Purple text** for trochoid arcs

---

## 🧩 Code Examples

### **Backend: Merge Override**
```python
# In gcode() endpoint:
post = _merge_adaptive_override(
    post, 
    body.adaptive_feed_override.dict() if body.adaptive_feed_override else None
)
```

### **Frontend: Build Override Object**
```typescript
function buildAdaptiveOverride() {
  if (afMode.value === 'inherit') return null
  
  const override: any = { mode: afMode.value }
  
  if (afMode.value === 'inline_f') {
    override.inline_min_f = afInlineMinF.value
  }
  
  if (afMode.value === 'mcode') {
    override.mcode_start = afMStart.value
    override.mcode_end = afMEnd.value
  }
  
  return override
}
```

### **Frontend: Preview NC**
```typescript
async function previewNc() {
  const body = {
    // ... plan parameters
    adaptive_feed_override: buildAdaptiveOverride()
  }
  
  const r = await fetch('/api/cam/pocket/adaptive/gcode', { 
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  })
  
  ncText.value = await r.text()
  ncOpen.value = true
}
```

---

## 🧪 Testing Commands

### **Test Override API**
```powershell
curl -X POST http://localhost:8000/api/cam/pocket/adaptive/gcode `
  -H 'Content-Type: application/json' `
  -d '{
    "loops": [{"pts": [[0,0],[50,0],[50,30],[0,30]]}],
    "units": "mm", "tool_d": 6.0, "stepover": 0.45,
    "stepdown": 1.5, "post_id": "GRBL",
    "adaptive_feed_override": {"mode": "comment"}
  }' -o test.nc

# Verify comment mode
grep "FEED_HINT" test.nc
```

### **Test UI**
```powershell
cd packages/client
npm run dev
# Open http://localhost:5173
# 1. Change mode to "Comment mode"
# 2. Click "Preview NC"
# 3. Verify yellow zones in drawer
```

---

## 📂 File Locations

| Component | Path | Purpose |
|-----------|------|---------|
| API Router | `services/api/app/routers/adaptive_router.py` | Override model + merge logic |
| Post Profiles | `services/api/app/assets/post_profiles.json` | Default adaptive_feed configs |
| NC Drawer | `packages/client/src/components/PreviewNcDrawer.vue` | FEED_HINT highlighting |
| Pocket UI | `packages/client/src/components/AdaptivePocketLab.vue` | Override selector + preview |

---

## 🔍 Troubleshooting

### **Issue:** Override not applied
- Check `adaptive_feed_override` is in request body
- Verify mode is not "inherit" (use null instead)
- Check browser console for API errors

### **Issue:** Preview drawer empty
- Verify `/gcode` endpoint returns text (not blob)
- Check `ncText` state is populated
- Verify `ncOpen` is true

### **Issue:** Settings don't persist
- Check browser localStorage is enabled
- Verify `watch` is firing on state changes
- Check console for localStorage errors

### **Issue:** Yellow highlighting not showing
- Verify FEED_HINT markers in G-code
- Check state machine in `processedLines` computed
- Inspect zone tracking logic (START/END detection)

---

## 📚 Related Docs

- **[ADAPTIVE_FEED_OVERRIDE_COMPLETE.md](./ADAPTIVE_FEED_OVERRIDE_COMPLETE.md)** - Full documentation
- **[PATCH_L3_SUMMARY.md](./PATCH_L3_SUMMARY.md)** - Trochoidal insertion
- **[ADAPTIVE_POCKETING_MODULE_L.md](./ADAPTIVE_POCKETING_MODULE_L.md)** - Core CAM system

---

**Last Updated:** November 5, 2025  
**Status:** ✅ Production Ready
