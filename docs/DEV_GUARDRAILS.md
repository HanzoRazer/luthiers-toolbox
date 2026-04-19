# Live Path Verification — Mandatory Pre-Implementation Check

## Purpose

Ensure all changes are applied to the actual production execution path, not a parallel or inactive code path.

## Automated Tool

```bash
python scripts/trace_live_path.py
```

Output:
```
PRODUCTION DEFAULT PATH
  Frontend:    hostinger/blueprint-reader.html
  Endpoint:    /api/blueprint/vectorize/async
  Mode sent:   (none) -> defaults to 'refined'

Mode: refined
  Function:  _clean_blueprint_refined()
  File:      services/api/app/services/blueprint_clean.py
  Pipeline:  extract_blueprint_to_dxf -> clean_blueprint_dxf
  Writer:    unified_dxf_cleaner.write_selected_chains

  WARNING: If your fix is not in _clean_blueprint_refined(),
           it will NOT run in production.
```

## Rule (Non-Negotiable)

Before writing any backend code, trace the exact production call path starting from the Blueprint Reader HTML.

---

## 30-Second Workflow (Do This First Every Time)

### Step 1 — Find the frontend call (ground truth)

Open the Blueprint Reader HTML (or Vue component):

```javascript
fetch('/api/blueprint/vectorize/async', {
  method: 'POST',
  body: formData
})
```

Capture:
- endpoint
- parameters (especially `mode`)
- anything NOT sent (this matters)

### Step 2 — Identify the mode (critical)

Ask:
- Is `mode` explicitly set?
- YES → use that mode
- NO → use backend default

Example from production:
- `mode` not sent → defaults to `"refined"`

### Step 3 — Trace backend entry point

Router:
```
/api/blueprint/vectorize/async
→ blueprint_async_router.py
```

### Step 4 — Trace orchestrator branch

```python
orchestrator.process_file(mode=CleanupMode.X)
```

Confirm:
- Which `CleanupMode` is actually used?

### Step 5 — Identify the active cleaning path

| Mode | Function |
|------|----------|
| `refined` | `_clean_blueprint_refined()` |
| `baseline` | `_clean_blueprint_baseline()` |
| `restored_baseline` | `_clean_blueprint_restored_baseline()` |
| `layered_dual_pass` | orchestrator dual-pass path |

### Step 6 — Confirm execution target

**THIS is where your code must go**

Not:
- where it "should" go
- where a similar function exists
- where a previous fix was added

Only:
- the function actually executed in production

---

## One-Line Sanity Check (Must Run)

Before coding:
```bash
grep -n "_clean_blueprint_refined" blueprint_clean.py
```

Then confirm:
- Does this function contain my intended logic?

If not → you are about to write dead code.

---

## Anti-Pattern (What Causes Silent Failures)

**Wrong:**
- Added feature to: `_clean_blueprint_restored_baseline()`
- Production runs: `_clean_blueprint_refined()`

**Result:**
- feature "works" in tests
- production unchanged
- debugging becomes misleading

**Correct:**
- Add feature to: `_clean_blueprint_refined()`
- OR explicitly switch frontend mode (only if intentional)

---

## Required Dev Checklist

Before implementation, confirm:

- [ ] Frontend endpoint identified
- [ ] Mode parameter confirmed (explicit or default)
- [ ] Router path traced
- [ ] Orchestrator branch confirmed
- [ ] Active cleaner/export function identified
- [ ] Patch target = actual production function

---

## Optional Debug Logging (Recommended)

Add temporary debug logging:
```python
logger.info(f"ACTIVE_PATH: mode={mode}, cleaner=refined")
```

Or include in response debug:
```json
{
  "debug": {
    "mode": "refined",
    "cleaner": "_clean_blueprint_refined"
  }
}
```

This makes drift impossible to miss.

---

## Why This Matters

This one habit prevents:
- Inserting code into a non-live path
- Misattributing improvements to the wrong component
- Spending time debugging behavior that never executed

---

## One-Line Directive

> Before writing any code, trace the full frontend → router → orchestrator → mode → cleaner path and confirm the exact function executed in production. All fixes must be applied there unless intentionally changing the execution path.
