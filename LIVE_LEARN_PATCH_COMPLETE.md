# Live Learn Patch: Session-Only Feed Override

**Status:** ✅ Complete  
**Date:** January 2025  
**Module:** M.4 Extension (Adaptive Pocketing)

---

## 🎯 Overview

The **Live Learn** system provides immediate feedback from actual CNC runtime without polluting the persistent learned model. When a user logs a run with measured actual time, the system computes a session-only feed scale factor and applies it to all subsequent plans/G-code until reset.

**Key Principle:** `factor = actual_time / estimated_time`
- **Slower actual** (factor > 1.0) → **increase feed** (machine can go faster)
- **Faster actual** (factor < 1.0) → **decrease feed** (machine is optimistic)

**Safety:** Factor clamped to 0.80–1.25 (±20% to +25%)

---

## 🔧 Architecture

### **Client-Side** (`packages/client/src/components/AdaptivePocketLab.vue`)

#### **State Management**
```typescript
// Session-only refs (NOT saved to localStorage or database)
const sessionOverrideFactor = ref<number | null>(null)
const liveLearnApplied = ref(false)
const measuredSeconds = ref<number | null>(null)

// Safety clamps
const LL_MIN = 0.80  // -20%
const LL_MAX = 1.25  // +25%
```

#### **Core Logic**
```typescript
// Compute inverse time relationship
function computeLiveLearnFactor(estimatedSeconds: number, actualSeconds: number): number {
  const raw = actualSeconds / estimatedSeconds
  const clamped = Math.max(LL_MIN, Math.min(LL_MAX, raw))
  return Number(clamped.toFixed(3))
}

// Apply session override + learned rules to request body
function patchBodyWithSessionOverride(body: any): any {
  if (liveLearnApplied.value && sessionOverrideFactor.value) {
    body.session_override_factor = sessionOverrideFactor.value
  }
  if (adoptOverrides.value) {
    body.adopt_overrides = true
  }
  return body
}
```

#### **Trigger Points**
1. **logCurrentRun(actualSeconds)**: Computes factor, sets refs
2. **plan()**: Applies factor to plan request
3. **previewNc()**: Applies factor to G-code preview
4. **exportProgram()**: Applies factor to G-code export

### **Server-Side** (`services/api/app/routers/adaptive_router.py`)

#### **Request Schema**
```python
class PlanIn(BaseModel):
    # ... existing fields ...
    adopt_overrides: bool = False  # Apply learned rules
    session_override_factor: Optional[float] = None  # Live Learn scale

class PlanOut(BaseModel):
    moves: List[Dict[str,Any]]
    stats: Dict[str,Any]  # Includes "session_override_factor"
    overlays: List[Dict[str,Any]]
```

#### **Application Order**
```python
# 1. Base feed + engagement angle slowdown
# 2. Learned rules (if adopt_overrides=True)
# 3. SESSION OVERRIDE (NEW)
if body.session_override_factor is not None:
    session_f = float(body.session_override_factor)
    if 0.5 <= session_f <= 1.5:  # Safety clamp
        for mv in moves:
            if mv.get("code") == "G1" and "f" in mv:
                mv["f"] = max(100.0, mv["f"] * session_f)
                mv["meta"]["session_override"] = round(session_f, 3)
# 4. Machine profile caps (feed/accel/jerk)
```

---

## 🎨 UI Components

### **Controls Section** (after "Adopt overrides" checkbox)
```vue
<div class="mt-3 pt-3 border-t border-gray-200 space-y-2">
  <!-- Enable/disable toggle with factor badge -->
  <div class="flex items-center gap-3">
    <label class="text-xs flex items-center gap-2">
      <input 
        type="checkbox" 
        v-model="liveLearnApplied" 
        :disabled="!sessionOverrideFactor"
      >
      Live learn (session only)
    </label>
    <span v-if="sessionOverrideFactor" class="text-xs px-2 py-0.5 border rounded bg-amber-50 text-amber-900 font-mono">
      ×{{ sessionOverrideFactor.toFixed(3) }}
    </span>
    <button @click="resetSessionOverride()">Reset</button>
  </div>
  
  <!-- Measured runtime input + log button -->
  <div class="flex items-center gap-2">
    <input 
      type="number" 
      step="0.1" 
      v-model.number="measuredSeconds" 
      placeholder="Actual sec"
    />
    <button 
      @click="logCurrentRun(measuredSeconds ?? undefined)"
      :disabled="!planOut?.moves || !measuredSeconds"
    >
      Log with actual time
    </button>
  </div>
</div>
```

### **Visual Feedback**
- **Badge:** Amber pill showing factor (e.g., `×1.150`)
- **Checkbox:** Disabled when no factor set
- **Reset button:** Only visible when factor exists
- **Alert:** Shows factor in log confirmation (e.g., "Logged run 42\nLive learn: ×1.150")

---

## 📊 Example Workflow

### **Scenario:** Machine running slower than predicted

1. **Initial Plan:**
   - Estimated time: 120 seconds
   - Feed: 1200 mm/min

2. **Actual Run:**
   - Measured time: 138 seconds (15% slower)

3. **Log with Actual Time:**
   ```typescript
   measuredSeconds.value = 138
   await logCurrentRun(138)
   // Computes: factor = 138/120 = 1.15 (clamped to [0.8, 1.25])
   // Sets: sessionOverrideFactor = 1.15, liveLearnApplied = true
   ```

4. **Subsequent Plans:**
   - All feeds multiplied by 1.15
   - New predicted time: ~104 seconds (closer to reality)
   - Factor visible in badge: `×1.150`

5. **Reset (Optional):**
   - User clicks "Reset" button
   - `sessionOverrideFactor = null`, `liveLearnApplied = false`
   - Next plan uses base feeds again

---

## 🧪 Testing

### **Manual Testing**

1. **Start Dev Stack:**
   ```powershell
   # API
   cd services/api
   .\.venv\Scripts\Activate.ps1
   uvicorn app.main:app --reload --port 8000
   
   # Client
   cd packages/client
   npm run dev
   ```

2. **Test Live Learn:**
   - Open http://localhost:5173
   - Click "Plan pocket"
   - Note estimated time (e.g., 32.1s)
   - Enter measured time (e.g., 38.0s) in "Actual sec" input
   - Click "Log with actual time"
   - Verify alert shows: "Logged run X\nLive learn: ×1.183"
   - Verify badge appears: `×1.183`
   - Click "Plan pocket" again
   - Verify feeds increased (F words ~18% higher)
   - Click "Reset"
   - Verify badge disappears
   - Click "Plan pocket" again
   - Verify feeds return to baseline

### **CI Tests** (Planned)

```python
# Test 1: Session factor echoes in plan response
body = {
    "loops": [{"pts": [[0,0], [100,0], [100,60], [0,60]]}],
    "tool_d": 6.0,
    "feed_xy": 1200,
    "session_override_factor": 1.15
}
r = requests.post("/api/cam/pocket/adaptive/plan", json=body)
assert r.json()["stats"]["session_override_factor"] == 1.15

# Test 2: Session factor scales F words in G-code
body_base = {...}  # No session factor
body_scaled = {**body_base, "session_override_factor": 1.2}

nc_base = requests.post("/api/cam/pocket/adaptive/gcode", json=body_base).text
nc_scaled = requests.post("/api/cam/pocket/adaptive/gcode", json=body_scaled).text

# Extract F words and compare
f_base = [float(m.group(1)) for m in re.finditer(r'F([\d.]+)', nc_base)]
f_scaled = [float(m.group(1)) for m in re.finditer(r'F([\d.]+)', nc_scaled)]

# Verify scaled feeds are ~20% higher
assert f_scaled[0] / f_base[0] > 1.15  # At least 15% increase
```

---

## 🚀 Usage Examples

### **Example 1: Simple Factor Computation**
```typescript
// Machine ran slower than predicted
const estimated = 120.0  // seconds
const actual = 138.0     // seconds
const factor = computeLiveLearnFactor(estimated, actual)
console.log(factor)  // 1.150

// Machine ran faster than predicted
const factor2 = computeLiveLearnFactor(120.0, 105.0)
console.log(factor2)  // 0.875
```

### **Example 2: Manual Factor Application**
```typescript
// Set session override manually (bypass log)
sessionOverrideFactor.value = 1.10
liveLearnApplied.value = true

// Next plan will include session_override_factor=1.10
await plan()
```

### **Example 3: Reset Override**
```typescript
// Clear session state
sessionOverrideFactor.value = null
liveLearnApplied.value = false
measuredSeconds.value = null

// Next plan uses base feeds
await plan()
```

---

## 🔍 Technical Details

### **Why Inverse Relationship?**
- **Actual > Estimated** → Machine is slower → **Need MORE feed** (factor > 1.0)
- **Actual < Estimated** → Machine is faster → **Need LESS feed** (factor < 1.0)

**Example:**
- Predicted 100s, actual 120s → machine slow → multiply feed by 1.2 → next run ~100s
- Predicted 100s, actual 80s → machine fast → multiply feed by 0.8 → next run ~100s

### **Safety Clamps Rationale**
| Min | Max | Reason |
|-----|-----|--------|
| 0.80 | 1.25 | Prevents extreme corrections from outliers |
| -20% | +25% | Typical CNC variability range (tool wear, material hardness) |

### **Session-Only Design**
- **Pros:** Immediate feedback, no model pollution, easy reset
- **Cons:** Lost on page reload (intentional - forces re-measurement)
- **Alternative:** Persist to localStorage (not implemented - keeps state ephemeral)

---

## 🐛 Troubleshooting

### **Issue:** Factor not applied to G-code
**Solution:** Check `liveLearnApplied` is true. Verify `patchBodyWithSessionOverride()` called in export functions.

### **Issue:** Badge not visible after logging
**Solution:** Verify `measuredSeconds` was entered before clicking "Log with actual time". Check console for "Live learn: session feed scale set to ×..." message.

### **Issue:** Factor too extreme (outside 0.8-1.25)
**Solution:** Check input `measuredSeconds` is correct. Factor automatically clamped to safe range.

### **Issue:** Reset doesn't clear factor
**Solution:** Verify reset button calls: `liveLearnApplied = false; sessionOverrideFactor = null; measuredSeconds = null`

---

## 📚 See Also

- [Module M.4 Complete](./MODULE_M4_COMPLETE.md) - Parent logging/learning system
- [Adaptive Pocketing Module L](./ADAPTIVE_POCKETING_MODULE_L.md) - Core CAM system
- [Machine Profiles Module M](./MACHINE_PROFILES_MODULE_M.md) - Feed cap integration

---

## ✅ Implementation Checklist

- [x] Add client-side state (sessionOverrideFactor, liveLearnApplied, measuredSeconds refs)
- [x] Implement computeLiveLearnFactor() with inverse time relationship and clamps
- [x] Implement patchBodyWithSessionOverride() for request patching
- [x] Update logCurrentRun() to compute and set session factor
- [x] Update plan() to apply patchBodyWithSessionOverride()
- [x] Update previewNc() to apply patchBodyWithSessionOverride()
- [x] Update exportProgram() to apply patchBodyWithSessionOverride()
- [x] Add UI controls (checkbox, badge, reset button, input field)
- [x] Add session_override_factor and adopt_overrides fields to PlanIn schema
- [x] Implement server-side session factor application (multiply eff_f after learned rules)
- [x] Add session_override_factor to stats output (echo in response)
- [x] Tag moves with session override in metadata for debugging
- [ ] Add CI tests (session factor echo + F word scaling validation)
- [ ] Test with real CNC runtime data

---

**Status:** ✅ Live Learn Patch Complete (Client + Server)  
**Next Steps:** Add CI tests and validate with production CNC data  
**Optional Enhancements:**
- Chipload coherence (adjust RPM when session factor changes feed)
- G-code header comments showing session factor
- Toast notifications for factor changes
- localStorage persistence (requires explicit user opt-in)
