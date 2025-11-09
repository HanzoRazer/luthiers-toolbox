# Adaptive Feed Override + NC Preview System

**Status:** ✅ Implemented  
**Date:** November 5, 2025  
**Module:** Adaptive Pocketing Engine Extension

---

## 🎯 Overview

This system provides **runtime control** over adaptive feed translation modes without editing post-processor configuration files. Users can override the adaptive feed mode (comment/inline_f/mcode) on a per-export basis and preview the resulting G-code with visual highlighting of FEED_HINT zones.

**Key Features:**
- ✅ **Per-export override** - Select adaptive feed mode at export time
- ✅ **Post profile inheritance** - Default to post-processor profile settings
- ✅ **NC preview drawer** - Line-by-line G-code display with FEED_HINT highlighting
- ✅ **localStorage persistence** - Remember user preferences across sessions
- ✅ **Visual feedback** - Yellow highlighting for slowdown zones, purple for trochoids

---

## 📦 Components

### **Backend API** (`services/api/app/routers/adaptive_router.py`)

#### **1. AdaptiveFeedOverride Model**
```python
class AdaptiveFeedOverride(BaseModel):
    mode: Literal["comment", "inline_f", "mcode", "inherit"] = "inherit"
    slowdown_threshold: Optional[float] = None
    inline_min_f: Optional[float] = None
    mcode_start: Optional[str] = None
    mcode_end: Optional[str] = None
```

**Fields:**
- `mode` - Override mode ("inherit" uses post profile defaults)
- `slowdown_threshold` - Optional custom threshold for slowdown detection
- `inline_min_f` - Minimum feed rate for inline_f mode (mm/min)
- `mcode_start` - M-code for zone start (e.g., "M52 P")
- `mcode_end` - M-code for zone end (e.g., "M52 P100")

#### **2. _merge_adaptive_override() Function**
```python
def _merge_adaptive_override(post: Dict, override: Optional[Dict]) -> Dict:
    """Merge user override with post profile defaults."""
    if not override or override.get("mode") in (None, "inherit"):
        return post
    
    post = post.copy()
    af = (post.get("adaptive_feed") or {}).copy()
    af["mode"] = override.get("mode", af.get("mode", "comment"))
    
    for k in ("slowdown_threshold", "inline_min_f", "mcode_start", "mcode_end"):
        if override.get(k) is not None:
            af[k] = override[k]
    
    post["adaptive_feed"] = af
    return post
```

**Logic:**
1. Return post unchanged if mode is "inherit" or None
2. Copy post and adaptive_feed config (immutable merge)
3. Override mode field
4. Merge optional parameters if provided
5. Return modified post

#### **3. GcodeIn Model Extension**
```python
class GcodeIn(PlanIn):
    post_id: Optional[str] = None
    adaptive_feed_override: Optional[AdaptiveFeedOverride] = None  # NEW
```

#### **4. gcode() Endpoint Integration**
```python
@router.post("/gcode")
def gcode(body: GcodeIn):
    # Load post profile
    post_profiles = _load_post_profiles()
    post = post_profiles.get(body.post_id or "GRBL")
    
    # Apply user override if provided
    post = _merge_adaptive_override(
        post, 
        body.adaptive_feed_override.dict() if body.adaptive_feed_override else None
    )
    
    # Continue with adaptive feed translation using merged config
    body_lines = _apply_adaptive_feed(moves=plan_out.moves, post=post, ...)
```

---

### **Frontend UI** (`packages/client/src/components/`)

#### **1. PreviewNcDrawer.vue** (NEW)

**Purpose:** Display G-code with line-by-line FEED_HINT zone highlighting

**Props:**
```typescript
interface Props {
  open: boolean       // Drawer visibility
  gcodeText: string   // NC program text
}
```

**Emits:**
- `close` - User closes drawer

**Features:**
- Fixed overlay drawer (right side, 42rem width)
- Line numbers (gray, non-selectable)
- Dark theme (VS Code-style)
- **Yellow background** for lines within FEED_HINT zones
- **Purple text** for trochoid-related comments
- Legend with color-coded chips
- State machine for zone tracking (START → END markers)

**Zone Detection:**
```typescript
// Markers detected:
- "FEED_HINT START" / "FEED_HINT END" (comment mode)
- "M52 P" (start) / "M52 P100" (end) (mcode mode)
- "(TROCHOID" or "trochoid" keywords (trochoid highlighting)
```

**Styling:**
```css
.line.feed-hint-zone {
  background: rgba(253, 224, 71, 0.15);  /* Yellow glow */
}

.line.trochoid-line .line-content {
  color: #c084fc;  /* Purple text */
  font-weight: 500;
}
```

#### **2. AdaptivePocketLab.vue** (UPDATED)

**New UI Controls:**
```vue
<label class="block text-sm font-medium mt-2">
  Adaptive Feed Mode <span class="text-xs text-gray-500">Override</span>
</label>
<select v-model="afMode" class="border px-2 py-1 rounded w-full">
  <option value="inherit">Inherit from post</option>
  <option value="comment">Comment mode</option>
  <option value="inline_f">Inline F</option>
  <option value="mcode">M-code</option>
</select>

<!-- Conditional inputs based on mode -->
<div v-if="afMode === 'inline_f'" class="pl-4">
  <label class="block text-xs">Min feed (mm/min)</label>
  <input v-model.number="afInlineMinF" type="number" step="50" />
</div>

<div v-if="afMode === 'mcode'" class="pl-4 grid grid-cols-2 gap-2">
  <div>
    <label class="block text-xs">M-code start</label>
    <input v-model="afMStart" type="text" placeholder="M52 P" />
  </div>
  <div>
    <label class="block text-xs">M-code end</label>
    <input v-model="afMEnd" type="text" placeholder="M52 P100" />
  </div>
</div>
```

**New State Variables:**
```typescript
const afMode = ref<'inherit'|'comment'|'inline_f'|'mcode'>('inherit')
const afInlineMinF = ref(600)
const afMStart = ref('M52 P')
const afMEnd = ref('M52 P100')

const ncOpen = ref(false)    // Drawer visibility
const ncText = ref('')       // NC program text
```

**New Functions:**

**buildAdaptiveOverride()** - Construct override object
```typescript
function buildAdaptiveOverride() {
  if (afMode.value === 'inherit') {
    return null  // Use post profile defaults
  }
  
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

**previewNc()** - Fetch G-code and open drawer
```typescript
async function previewNc() {
  const body = {
    // ... all existing plan parameters
    adaptive_feed_override: buildAdaptiveOverride()
  }
  
  const r = await fetch('/api/cam/pocket/adaptive/gcode', { 
    method:'POST', 
    headers:{'Content-Type':'application/json'}, 
    body: JSON.stringify(body) 
  })
  
  ncText.value = await r.text()
  ncOpen.value = true
}
```

**localStorage Persistence:**
```typescript
function loadAfPrefs() {
  const saved = localStorage.getItem('toolbox.adaptiveFeed')
  if (saved) {
    const prefs = JSON.parse(saved)
    afMode.value = prefs.mode || 'inherit'
    afInlineMinF.value = prefs.inline_min_f || 600
    afMStart.value = prefs.mcode_start || 'M52 P'
    afMEnd.value = prefs.mcode_end || 'M52 P100'
  }
}

function saveAfPrefs() {
  localStorage.setItem('toolbox.adaptiveFeed', JSON.stringify({
    mode: afMode.value,
    inline_min_f: afInlineMinF.value,
    mcode_start: afMStart.value,
    mcode_end: afMEnd.value
  }))
}

watch([afMode, afInlineMinF, afMStart, afMEnd], saveAfPrefs)
onMounted(() => { loadAfPrefs(); setTimeout(draw, 100) })
```

---

## 🔄 User Workflow

### **Scenario 1: Override to Comment Mode**
1. User selects **GRBL** post-processor (default: inline_f mode)
2. User changes **Adaptive Feed Mode** to "Comment mode"
3. User clicks **Preview NC**
4. Drawer opens showing G-code with:
   - `(FEED_HINT START slowdown=0.75)` comments
   - Yellow highlighting on lines within zones
5. User clicks **Export G-code**
6. Downloaded file has comment-based FEED_HINT markers

### **Scenario 2: Custom M-code for Mach4**
1. User selects **Mach4** post-processor
2. User changes **Adaptive Feed Mode** to "M-code"
3. User customizes:
   - M-code start: `M100 P`
   - M-code end: `M100 P0`
4. User clicks **Preview NC**
5. Drawer shows G-code with:
   - `M100 P75` (start of slowdown zone)
   - `M100 P0` (end of zone)
   - Yellow highlighting on lines between M-codes
6. Settings persist to localStorage for next session

### **Scenario 3: Inherit from Post Profile**
1. User selects **LinuxCNC** post-processor (default: mcode with M68)
2. User leaves **Adaptive Feed Mode** at "Inherit from post"
3. User clicks **Preview NC**
4. Drawer shows G-code with default M68 E0 Q... M-codes
5. No override sent in API request (uses post profile as-is)

---

## 🧪 Testing

### **Manual Testing Steps**

**1. Test Override Model (Backend)**
```powershell
# Start API
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# Test override (in another terminal)
curl -X POST http://localhost:8000/api/cam/pocket/adaptive/gcode `
  -H 'Content-Type: application/json' `
  -d '{
    "loops": [{"pts": [[0,0],[50,0],[50,30],[0,30]]}],
    "units": "mm",
    "tool_d": 6.0,
    "stepover": 0.45,
    "stepdown": 1.5,
    "post_id": "GRBL",
    "adaptive_feed_override": {
      "mode": "comment"
    }
  }' -o test_override.nc

# Verify: Should contain "(FEED_HINT START" comments
grep "FEED_HINT" test_override.nc
```

**2. Test UI (Frontend)**
```powershell
# Start client
cd packages/client
npm run dev

# Open http://localhost:5173
# 1. Change Adaptive Feed Mode to "Comment mode"
# 2. Click "Preview NC" button
# 3. Verify drawer opens with yellow highlighted zones
# 4. Close and reopen - verify settings persist
```

**3. Test PreviewNcDrawer Highlighting**
```typescript
// Test cases for zone detection:
1. Comment mode markers:
   - "(FEED_HINT START slowdown=0.75)" → zone starts
   - "(FEED_HINT END)" → zone ends

2. M-code markers:
   - "M52 P75" → zone starts
   - "M52 P100" → zone ends

3. Trochoid comments:
   - "(TROCHOID arc R=1.5 P=3.0)" → purple text
   - "(trochoid entry)" → purple text

4. Combined:
   - Trochoid inside FEED_HINT zone → yellow background + purple text
```

### **CI Validation (Optional)**

Add smoke test to `.github/workflows/adaptive_pocket.yml`:
```yaml
- name: Test adaptive feed override modes
  run: |
    python - <<'PY'
    import urllib.request, json
    
    body = {
      "loops": [{"pts": [[0,0],[60,0],[60,40],[0,40]]}],
      "units": "mm", "tool_d": 6.0, "stepover": 0.45,
      "stepdown": 1.5, "post_id": "GRBL",
      "adaptive_feed_override": {"mode": "comment"}
    }
    
    req = urllib.request.Request(
      "http://localhost:8000/api/cam/pocket/adaptive/gcode",
      data=json.dumps(body).encode(), headers={"Content-Type":"application/json"}
    )
    res = urllib.request.urlopen(req).read().decode()
    
    assert "(FEED_HINT START" in res, "Comment override failed"
    print("✓ Comment mode override validated")
    
    # Test inline_f override
    body["adaptive_feed_override"] = {"mode": "inline_f", "inline_min_f": 500}
    req = urllib.request.Request(
      "http://localhost:8000/api/cam/pocket/adaptive/gcode",
      data=json.dumps(body).encode(), headers={"Content-Type":"application/json"}
    )
    res = urllib.request.urlopen(req).read().decode()
    
    assert " F5" in res or " F6" in res, "Inline_f override failed"
    print("✓ Inline_f mode override validated")
    
    # Test mcode override
    body["adaptive_feed_override"] = {
      "mode": "mcode", 
      "mcode_start": "M100 P", 
      "mcode_end": "M100 P0"
    }
    req = urllib.request.Request(
      "http://localhost:8000/api/cam/pocket/adaptive/gcode",
      data=json.dumps(body).encode(), headers={"Content-Type":"application/json"}
    )
    res = urllib.request.urlopen(req).read().decode()
    
    assert "M100 P" in res, "M-code override failed"
    print("✓ M-code mode override validated")
    PY
```

---

## 📊 Override Mode Comparison

| Mode | FEED_HINT Output | Use Case | Override Required Fields |
|------|------------------|----------|--------------------------|
| **inherit** | Uses post profile defaults | User trusts config | None (sends null) |
| **comment** | `(FEED_HINT START slowdown=0.75)`<br/>`(FEED_HINT END)` | Documentation, simulator | mode |
| **inline_f** | `G1 X10 Y20 F600`<br/>(scaled F values) | Direct machine control | mode, inline_min_f |
| **mcode** | `M52 P75`<br/>`M52 P100` | CNC with feed override registers | mode, mcode_start, mcode_end |

---

## 🎨 UI Preview

### **Adaptive Feed Selector**
```
Post-Processor: [GRBL ▼]

Adaptive Feed Mode [Override]
[Inherit from post ▼]  ← Default

Options when changed:
├─ Comment mode
├─ Inline F
│  └─ Min feed (mm/min): [600]
└─ M-code
   ├─ M-code start: [M52 P]
   └─ M-code end: [M52 P100]

[Plan] [Preview NC] [Export G-code]
```

### **NC Preview Drawer**
```
╔════════════════════════════════════════════════╗
║  NC Preview                               [✕] ║
╟────────────────────────────────────────────────╢
║  [▢ FEED_HINT zones]  [▢ Trochoid arcs]      ║
╟────────────────────────────────────────────────╢
║   1  G21                                       ║
║   2  G90                                       ║
║   3  G17                                       ║
║   4  (POST=GRBL;UNITS=mm;DATE=2025-11-05...)  ║
║   5  G0 Z5.0000                                ║
║   6  G0 X3.0000 Y3.0000                        ║
║   7  (FEED_HINT START slowdown=0.75)          ║ ← Yellow
║   8  G1 Z-1.5000 F1200.0                      ║ ← Yellow
║   9  G1 X3.5000 Y3.2000 F900.0                ║ ← Yellow
║  10  (TROCHOID arc R=1.5 P=3.0)               ║ ← Purple
║  11  G2 X4.5000 Y3.8000 I0.5 J0.6 F900.0      ║ ← Yellow
║  12  (FEED_HINT END)                          ║ ← Yellow
║  13  G1 X97.0000 Y3.0000 F1200.0              ║
║ ...                                            ║
╚════════════════════════════════════════════════╝
```

---

## 🚀 Integration Checklist

- [x] Add `Literal` to imports in adaptive_router.py
- [x] Create `AdaptiveFeedOverride` model class
- [x] Implement `_merge_adaptive_override()` function
- [x] Extend `GcodeIn` model with `adaptive_feed_override` field
- [x] Update `gcode()` endpoint to apply override
- [x] Create `PreviewNcDrawer.vue` component
- [x] Add adaptive feed selector UI to AdaptivePocketLab.vue
- [x] Add `buildAdaptiveOverride()` helper function
- [x] Add `previewNc()` async function
- [x] Add Preview NC button
- [x] Import and wire PreviewNcDrawer component
- [x] Add localStorage persistence (loadAfPrefs, saveAfPrefs)
- [x] Add watch for auto-save on changes
- [ ] Add CI smoke test for override modes (optional)
- [ ] User acceptance testing with real CNC machines (user task)

---

## 📚 See Also

- [Adaptive Pocketing Module L](./ADAPTIVE_POCKETING_MODULE_L.md) - Core CAM system
- [Patch L.3 Summary](./PATCH_L3_SUMMARY.md) - Trochoidal insertion + jerk-aware time
- [Post Profiles](./services/api/app/assets/post_profiles.json) - Default adaptive feed configs
- [Multi-Post Export System](./PATCH_K_EXPORT_COMPLETE.md) - G-code export infrastructure

---

**Status:** ✅ Feature Complete  
**Next Steps:** Optional CI validation, user testing with production CNC machines  
**User Feedback:** Monitor localStorage usage patterns to optimize defaults
