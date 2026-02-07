# M1 Advisory Mode — Golden Path Tests

Manual validation checklist for the M1 agentic directive system.

---

## Prerequisites

```bash
cd packages/client
VITE_AGENTIC_MODE=M1 npm run dev
```

Open browser at http://localhost:5173

---

## Path A: FIRST_SIGNAL Detection

**Steps:**
1. Navigate to **Acoustics > Viewer** (`/tools/audio-analyzer`)
2. Drop a valid viewer_pack ZIP file (e.g., one with wolf analysis data)

**Expected:**
- Coach Bubble appears in bottom-right with **"Inspect this"**
- Detail text: "Focus on one signal and make a small change."

**Verify in DevTools Console:**
```js
// Check latest decision
$pinia.state.value.agenticDirective.latestDecision
// Should show: { attention_action: "INSPECT", emit_directive: true, ... }
```

---

## Path B: HESITATION Detection

**Steps:**
1. Navigate to **Acoustics > Viewer**
2. Load a viewer pack
3. **Do nothing for 8+ seconds** (no mouse movement, no clicks)

**Expected:**
- Coach Bubble appears with **"Inspect this"**
- This is triggered by `idle_timeout` event from IdleDetector.vue

**Notes:**
- If you previously loaded a pack (Path A), dismiss the FIRST_SIGNAL bubble first
- HESITATION is suppressed if you recently changed parameters

---

## Path C: OVERLOAD Detection + UWSM Nudge

**Steps:**
1. Trigger a Coach Bubble (via Path A or B)
2. Click **"👎 Too much"** button

**Expected:**
- Coach Bubble dismisses immediately
- UWSM `cognitive_load_sensitivity` increases by one level
- Future directives will be throttled more aggressively

**Verify in DevTools Console:**
```js
// Before clicking "Too much"
$pinia.state.value.agenticDirective.uwsm.dimensions.cognitive_load_sensitivity
// Expected: { value: "medium" }

// After clicking "Too much"
$pinia.state.value.agenticDirective.uwsm.dimensions.cognitive_load_sensitivity
// Expected: { value: "high" }
```

---

## Path D: M0 Shadow Mode

**Steps:**
1. Restart dev server with M0:
   ```bash
   VITE_AGENTIC_MODE=M0 npm run dev
   ```
2. Navigate to Acoustics > Viewer
3. Load a viewer pack
4. Wait 8+ seconds

**Expected:**
- **No Coach Bubble appears** (M0 = shadow mode)
- Events are still collected (check store.events)
- Decisions are computed but `emit_directive: false`

**Verify in DevTools Console:**
```js
// Check mode
$pinia.state.value.agenticDirective.mode  // "M0"

// Check events are collected
$pinia.state.value.agenticDirective.events.length  // > 0

// Check decision was computed but not emitted
$pinia.state.value.agenticDirective.latestDecision
// Should show: { emit_directive: false, diagnostic: { would_have_emitted: {...} } }
```

---

## Path E: Event Deduplication

**Steps:**
1. In DevTools Console, rapidly emit the same event:
   ```js
   const store = $pinia.state.value.agenticDirective
   store.emitEvent('analysis_completed', { artifacts_created: ['test'] })
   store.emitEvent('analysis_completed', { artifacts_created: ['test'] })
   store.emitEvent('analysis_completed', { artifacts_created: ['test'] })
   ```

**Expected:**
- Only **1 event** is recorded (others deduplicated within 100ms window)

**Exception:**
- `user_feedback` and `user_action` events are never deduplicated

---

## Path F: Debounce Prevents Flicker

**Steps:**
1. Rapidly trigger multiple events that would cause directive changes
2. Observe Coach Bubble behavior

**Expected:**
- Coach Bubble updates smoothly (250ms debounce)
- No visual flicker or rapid appear/disappear

---

## Validation Summary

| Path | Trigger | Expected Directive | UWSM Change |
|------|---------|-------------------|-------------|
| A | Pack load | INSPECT | None |
| B | 8s idle | INSPECT | None |
| C | "Too much" | Dismiss | cognitive_load_sensitivity ↑ |
| D | M0 mode | None visible | None |
| E | Rapid events | 1 event only | None |
| F | Rapid changes | Smooth update | None |

---

## Troubleshooting

**Coach Bubble doesn't appear:**
- Check `VITE_AGENTIC_MODE` is set to `M1`
- Check console for errors
- Verify store.mode is "M1"

**Events not being emitted:**
- Check useAgenticEvents composable is imported correctly
- Verify store.isEnabled is true

**Directive appears but wrong type:**
- Check moment detection priority order
- ERROR > OVERLOAD > DECISION_REQUIRED > FINDING > HESITATION > FIRST_SIGNAL

---

**End of Golden Path Tests**
