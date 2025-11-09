# Live Learn Quick Reference

**Status:** ✅ Complete  
**Module:** M.4 Extension

---

## 🎯 What is Live Learn?

**Session-only feed override** computed from actual runtime vs estimated runtime. Provides immediate feedback without touching the persistent learned model.

**Formula:** `factor = actual_time / estimated_time`  
**Range:** 0.80–1.25 (±20% to +25%)  
**Scope:** Current browser session only (reset on page reload)

---

## 🚀 Quick Start

### **1. Run a Pocket Operation**
```
Plan pocket → Note estimated time (e.g., 32.1s)
Run on CNC → Measure actual time (e.g., 38.0s)
```

### **2. Log with Actual Time**
```
Enter 38.0 in "Actual sec" input
Click "Log with actual time"
→ Factor computed: 38.0/32.1 = 1.183
→ Badge appears: ×1.183
→ Alert: "Logged run 42\nLive learn: ×1.183"
```

### **3. Automatic Application**
```
Click "Plan pocket" again
→ All feeds × 1.183
→ New estimate: ~27s (closer to reality)
→ Next run should match prediction better
```

### **4. Reset (Optional)**
```
Click "Reset" button
→ Badge disappears
→ Next plan uses base feeds
```

---

## 📊 Key Formulas

### **Factor Computation**
```typescript
factor = actual_time / estimated_time
clamped_factor = clamp(factor, 0.80, 1.25)
```

### **Feed Application**
```python
# Server-side (in adaptive_router.py)
if session_override_factor:
    for move in moves:
        if move.has_feed:
            move.f *= session_override_factor
```

---

## 🎨 UI Elements

| Element | Location | Purpose |
|---------|----------|---------|
| **Checkbox** | After "Adopt overrides" | Enable/disable session override |
| **Badge** | Next to checkbox | Show factor (e.g., `×1.150`) |
| **Reset** | Next to badge | Clear session state |
| **Input** | Below checkbox | Enter measured seconds |
| **Button** | Next to input | Log with actual time |

---

## 📝 Common Scenarios

### **Machine Running Slow**
```
Estimated: 100s
Actual:    120s
Factor:    1.20 (+20% feed)
Result:    Next run ~100s
```

### **Machine Running Fast**
```
Estimated: 100s
Actual:     85s
Factor:    0.85 (-15% feed)
Result:    Next run ~100s
```

### **Extreme Outlier**
```
Estimated: 100s
Actual:    200s
Factor:    2.00 → CLAMPED to 1.25 (+25% max)
Result:    Conservative correction
```

---

## 🔧 API Usage

### **Plan with Session Override**
```typescript
const body = {
  loops: [...],
  tool_d: 6.0,
  feed_xy: 1200,
  session_override_factor: 1.15  // +15% feed
}
const r = await fetch('/api/cam/pocket/adaptive/plan', {body})
const stats = r.json().stats
console.log(stats.session_override_factor)  // 1.15
```

### **G-code with Session Override**
```typescript
const body = {
  loops: [...],
  post_id: 'GRBL',
  session_override_factor: 1.10
}
const nc = await fetch('/api/cam/pocket/adaptive/gcode', {body}).text()
// All F words scaled by 1.10
```

---

## 🧪 Testing Checklist

- [ ] Plan pocket, note estimated time
- [ ] Enter measured time in "Actual sec" input
- [ ] Click "Log with actual time"
- [ ] Verify badge shows factor
- [ ] Verify alert shows factor
- [ ] Click "Plan pocket" again
- [ ] Verify feeds changed (check stats or G-code)
- [ ] Click "Reset"
- [ ] Verify badge disappears
- [ ] Click "Plan pocket" again
- [ ] Verify feeds return to baseline

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| No badge after log | Check measuredSeconds entered, verify console log |
| Factor not applied | Enable checkbox, verify patchBodyWithSessionOverride() called |
| Factor too extreme | Check input, factor clamped to 0.8-1.25 |
| Reset doesn't work | Verify refs set to null, check UI reactivity |

---

## 📚 Files Modified

### **Client** (`packages/client/src/components/AdaptivePocketLab.vue`)
- Lines ~680-685: State refs (sessionOverrideFactor, liveLearnApplied, measuredSeconds)
- Lines ~880-895: Helper functions (computeLiveLearnFactor, patchBodyWithSessionOverride)
- Lines ~1020-1035: logCurrentRun() extension (compute factor, set refs)
- Lines ~1075-1080: plan() extension (apply patchBodyWithSessionOverride)
- Lines ~1127-1165: previewNc() extension (apply patchBodyWithSessionOverride)
- Lines ~1178-1210: exportProgram() extension (apply patchBodyWithSessionOverride)
- Lines ~430-475: UI controls (checkbox, badge, reset, input, button)

### **Server** (`services/api/app/routers/adaptive_router.py`)
- Lines 207-209: PlanIn schema extension (adopt_overrides, session_override_factor)
- Lines 287-302: Session override application loop (multiply eff_f, tag metadata)
- Line 391: Stats output extension (session_override_factor echo)

---

## 🎯 Key Takeaways

1. **Inverse relationship:** Slower actual → MORE feed needed
2. **Safety clamps:** 0.80–1.25 prevents extreme corrections
3. **Session-only:** State lost on reload (intentional)
4. **Application order:** Base → slowdown → learned rules → **session override** → caps
5. **Immediate feedback:** No model training required

---

**Quick Reference:** Use Live Learn when you need immediate runtime-based feed correction without waiting for model training.
