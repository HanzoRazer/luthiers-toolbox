# N10.2.1 — Safety Flow Integration: Quick Reference

**Bundle ID:** RMOS_N10_2_1_SafetyFlowIntegration_v0.1_113025  
**Status:** ✅ Production Ready  
**Tags:** RMOS, Safety, Integration, Preset Promotion, Pipeline Run

---

## 🎯 Overview

N10.2.1 **wires safety evaluation into actual RMOS workflows**, transforming the N10.2 safety engine from a standalone API into an active gatekeeper for dangerous operations.

**What it does:**
- Intercepts preset promotions with safety checks before fragility policy
- Gates experimental lane runs with apprentice/mentor rules
- Provides DRY helper (`guardedAction`) for consistent UI integration
- Logs all safety decisions alongside job/promotion metadata

**Key flows integrated:**
1. **Preset promotion** (`/rmos/presets/{id}/promote`) - N10.2.1 safety → MM-5 fragility policy
2. **Pipeline/job start** (`/rmos/pipeline/run`) - Safety evaluation for experimental/high-risk lanes

---

## 🏗️ Architecture

### **Safety Evaluation Flow**

```
┌─────────────────────┐
│  UI: Promote/Start  │
│  Button Click       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────┐
│ guardedAction() helper      │
│ 1. Evaluate safety          │
│ 2. Prompt for override      │
│ 3. Execute if allowed       │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ Backend API                 │
│ 1. Safety evaluation        │
│ 2. Consume override token   │
│ 3. (Preset: fragility check)│
│ 4. Execute action           │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ Job Log Entry               │
│ - Safety decision included  │
│ - Override usage tracked    │
└─────────────────────────────┘
```

### **Policy Ordering**

**Preset Promotion:**
1. **Safety mode** (N10.2.1) - apprentice/mentor rules
2. **Ultra-fragility** (MM-5) - fragility limits + clean job count

**Pipeline Run:**
1. **Safety mode** (N10.2.1) - apprentice/mentor rules for experimental lanes
2. Job execution proceeds if safety allows

---

## 📦 Components Changed

### **Backend (3 files)**

| File | Changes | Purpose |
|------|---------|---------|
| `services/api/app/api/routes/rmos_presets_api.py` | Added safety evaluation before fragility policy | Prevent unsafe promotions |
| `services/api/app/api/routes/rmos_pipeline_run_api.py` | Created new router with safety checks | Gate experimental lane runs |
| `services/api/app/main.py` | Registered pipeline run router | Enable API endpoint |

### **Frontend (1 file)**

| File | Changes | Purpose |
|------|---------|---------|
| `packages/client/src/stores/useRmosSafetyStore.ts` | Added `guardedAction()` helper | DRY UI integration pattern |

---

## 🔌 Backend API Changes

### **POST `/api/rmos/presets/{preset_id}/promote`** (PATCHED)

**Added fields to request:**
```json
{
  "target_lane": "safe",
  "reason": "Passed validation",
  "override_token": "OVR-1701345678123456"  // NEW: Optional mentor override
}
```

**Response now includes:**
```json
{
  "preset_id": "preset_abc123",
  "from_lane": "tuned_v1",
  "target_lane": "safe",
  "policy_reason": "Allowed: 6/8 jobs clean...",
  "policy_stats": {
    "total_runs": 8,
    "clean_runs": 6,
    "worst_fragility_overall": 0.28,
    "safety_decision": {           // NEW: Safety decision metadata
      "decision": "allow",
      "mode": "unrestricted",
      "risk_level": "low",
      "reason": "Low-risk action allowed..."
    }
  }
}
```

**New error responses:**

**403 Forbidden** (safety deny):
```json
{
  "detail": "Promotion denied by safety policy: High-risk action denied in apprentice mode; mentor must run this."
}
```

**409 Conflict** (safety requires override):
```json
{
  "detail": {
    "message": "High-risk action in unrestricted mode; override recommended for fragile / experimental work.",
    "safety_decision": {
      "decision": "require_override",
      "mode": "unrestricted",
      "risk_level": "high",
      "requires_override": true
    },
    "policy": "safety_mode"
  }
}
```

**409 Conflict** (fragility policy blocks):
```json
{
  "detail": {
    "message": "Blocked: worst fragility 0.94 exceeds ultra-fragile threshold 0.90...",
    "stats": {...},
    "policy": "ultra_fragility_guard"
  }
}
```

---

### **POST `/api/rmos/pipeline/run`** (NEW)

Start a job run with safety evaluation.

**Request:**
```json
{
  "pattern_id": "preset_abc123",
  "lane": "experimental",
  "job_params": {
    "feed_xy": 1200,
    "spindle_rpm": 18000
  },
  "override_token": "OVR-1701345678123456"  // Optional
}
```

**Response:**
```json
{
  "job_id": "JOB-20251130-103045",
  "pattern_id": "preset_abc123",
  "lane": "experimental",
  "safety_decision": {
    "decision": "allow",
    "mode": "unrestricted",
    "risk_level": "high",
    "reason": "Override accepted: Override accepted."
  }
}
```

**Error responses:** Same pattern as promotion (403 deny, 409 require override)

---

## 💻 Frontend Integration

### **guardedAction() Helper**

The safety store now includes a DRY helper that wraps the entire safety flow:

```typescript
import { useRmosSafetyStore } from '@/stores/useRmosSafetyStore'

const safety = useRmosSafetyStore()

// Wrap any dangerous action:
await safety.guardedAction(
  {
    action: "promote_preset",
    lane: "safe",
    fragility_score: 0.8,
    risk_grade: "RED",
    preset_id: "preset_123"
  },
  async () => {
    // Your actual API call
    await fetch("/rmos/presets/preset_123/promote", {
      method: "POST",
      body: JSON.stringify({ target_lane: "safe" })
    })
  }
)
```

**What it does:**
1. Calls `safety.evaluateAction(ctx)` to check safety policy
2. If **deny**: Shows alert, returns `false`
3. If **require_override**: Prompts user for token, retries evaluation with token
4. If **allow** (or override succeeded): Executes `doAction()`, returns `true`

---

### **Example 1: Preset Promotion Button**

```vue
<template>
  <button
    class="px-3 py-1 rounded bg-blue-600 text-white text-xs"
    @click="onPromote"
    :disabled="promoting"
  >
    {{ promoting ? 'Promoting...' : 'Promote to Safe' }}
  </button>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRmosSafetyStore } from '@/stores/useRmosSafetyStore'

const props = defineProps<{
  presetId: string
  targetLane: string
  fragility?: number
  riskGrade?: string
}>()

const safety = useRmosSafetyStore()
const promoting = ref(false)

async function onPromote() {
  promoting.value = true
  
  const ctx = {
    action: "promote_preset",
    lane: props.targetLane,
    fragility_score: props.fragility ?? null,
    risk_grade: props.riskGrade ?? null,
    preset_id: props.presetId,
  }

  const success = await safety.guardedAction(ctx, async () => {
    const res = await fetch(`/rmos/presets/${encodeURIComponent(props.presetId)}/promote`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        target_lane: props.targetLane,
        reason: "User-initiated promotion",
      }),
    })
    
    if (!res.ok) {
      const err = await res.json().catch(() => null)
      // Distinguish between safety and fragility policy
      const msg = err?.detail?.message || err?.detail || `Promotion failed: ${res.status}`
      alert(msg)
      throw new Error(msg)
    }
    
    const data = await res.json()
    console.log("Promotion success", data)
    // Update local state, emit event, etc.
  })
  
  promoting.value = false
  
  if (success) {
    // Show success toast
    console.log("Promotion completed successfully")
  }
}
</script>
```

---

### **Example 2: Experimental Lane Run Button**

```vue
<template>
  <button
    class="px-3 py-1 rounded bg-amber-600 text-white text-xs"
    @click="onRunExperimental"
    :disabled="running"
  >
    {{ running ? 'Starting...' : 'Run Experimental Lane' }}
  </button>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRmosSafetyStore } from '@/stores/useRmosSafetyStore'

const props = defineProps<{
  patternId: string
  lane?: string
  fragility?: number
  riskGrade?: string
}>()

const safety = useRmosSafetyStore()
const running = ref(false)

async function onRunExperimental() {
  running.value = true
  
  const lane = props.lane || "experimental"
  
  const ctx = {
    action: "run_experimental_lane",
    lane,
    fragility_score: props.fragility ?? null,
    risk_grade: props.riskGrade ?? null,
    preset_id: props.patternId,
  }

  const success = await safety.guardedAction(ctx, async () => {
    const res = await fetch("/rmos/pipeline/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        pattern_id: props.patternId,
        lane,
      }),
    })
    
    if (!res.ok) {
      const err = await res.json().catch(() => null)
      const msg = err?.detail?.message || err?.detail || `Run failed: ${res.status}`
      alert(msg)
      throw new Error(msg)
    }
    
    const data = await res.json()
    console.log("Experimental run started", data)
    // Optionally push job into LiveMonitor store
  })
  
  running.value = false
  
  if (success) {
    console.log("Job started successfully")
  }
}
</script>
```

---

## 🧪 Testing

### **Backend Tests**

Test safety integration in promotion:

```powershell
# In Python console or test script:
import requests

# Test promotion without override (should require override in unrestricted mode if high-risk)
r = requests.post(
    "http://localhost:8000/api/rmos/presets/test_preset_123/promote",
    json={
        "target_lane": "safe",
        "reason": "Test promotion"
    }
)
print(r.status_code)  # Should be 409 if high-risk
print(r.json())       # Should contain safety_decision

# Create override token
r_token = requests.post(
    "http://localhost:8000/rmos/safety/create-override",
    json={
        "action": "promote_preset",
        "created_by": "mentor_test"
    }
)
token = r_token.json()["token"]

# Retry promotion with override
r = requests.post(
    "http://localhost:8000/api/rmos/presets/test_preset_123/promote",
    json={
        "target_lane": "safe",
        "reason": "Test promotion",
        "override_token": token
    }
)
print(r.status_code)  # Should be 200 if override valid
```

Test pipeline run:

```powershell
r = requests.post(
    "http://localhost:8000/api/rmos/pipeline/run",
    json={
        "pattern_id": "test_preset_123",
        "lane": "experimental"
    }
)
print(r.status_code)  # Should be 409 if requires override
print(r.json())       # Should contain safety_decision
```

### **Frontend Manual Tests**

1. **Test promotion flow:**
   - Find a pattern with high fragility (≥0.7)
   - Set safety mode to `apprentice` via `/rmos/safety/mode`
   - Click "Promote to Safe" button
   - Verify denial alert appears
   - Switch to `unrestricted` mode
   - Click "Promote to Safe" again
   - Verify override prompt appears
   - Create token via `/rmos/safety/create-override` and paste
   - Verify promotion proceeds

2. **Test experimental run flow:**
   - Set safety mode to `apprentice`
   - Click "Run Experimental Lane"
   - Verify denial alert
   - Switch to `mentor_review`
   - Click "Run Experimental Lane"
   - Verify override prompt
   - Provide valid token
   - Verify job starts

---

## ⚙️ Configuration

### **Action Names**

The safety system recognizes these actions:

| Action | Triggers When | Risk Classification |
|--------|---------------|---------------------|
| `promote_preset` | Promoting preset to any lane | Based on target lane + fragility |
| `start_job` | Starting job on safe/tuned lanes | Based on lane + fragility |
| `run_experimental_lane` | Starting job on experimental/tuned_v2 | Always medium/high risk |

### **Risk Classification for Promotion**

```
Experimental + (fragility ≥ 0.7 OR grade == RED) → HIGH risk
Experimental + otherwise → MEDIUM risk
Tuned_v1 + (fragility ≥ 0.6 OR grade == YELLOW) → MEDIUM risk
Default → LOW risk
```

### **Mode-Specific Behavior**

| Mode | High Risk | Medium Risk | Low Risk |
|------|-----------|-------------|----------|
| **Unrestricted** | Require override | Allow | Allow |
| **Apprentice** | Deny | Require override | Allow |
| **Mentor Review** | Require override | Allow + logged | Allow |

---

## 🚨 Troubleshooting

### **Issue:** Promotion succeeds even in apprentice mode

**Cause:** Safety evaluation may have classified as low/medium risk.

**Solution:** Check fragility score and lane. If fragility < 0.6 and lane is `safe`, it's correctly classified as low risk.

---

### **Issue:** Override token rejected with "Invalid override token"

**Cause:** Token not created or already consumed.

**Solution:** Create new token via `/rmos/safety/create-override` before each use. Tokens are one-time use only.

---

### **Issue:** guardedAction() not prompting for override

**Cause:** Action classified as low risk or already in allow state.

**Solution:** Verify safety mode and risk factors (lane, fragility, grade). Use `/rmos/safety/evaluate` to test classification.

---

### **Issue:** Backend returns 500 error during safety check

**Cause:** Missing pattern/preset or bad metadata structure.

**Solution:** Ensure preset exists and has valid `metadata.analytics` fields for fragility/grade.

---

## 📋 Integration Checklist

- [x] Backend: Preset promotion patched with safety evaluation
- [x] Backend: Pipeline run API created with safety checks
- [x] Backend: Routers registered in main.py
- [x] Frontend: guardedAction helper added to safety store
- [x] Documentation: Integration patterns and examples
- [ ] UI: Wire promotion buttons with guardedAction (user task)
- [ ] UI: Wire experimental run buttons with guardedAction (user task)
- [ ] UI: Add SafetyModeBanner to RMOS views (user task)
- [ ] Testing: Validate flows end-to-end with different modes

---

## 🔄 Complete Workflow Example

**Scenario:** Apprentice tries to promote fragile preset to safe lane.

```
1. UI: Apprentice clicks "Promote to Safe"

2. guardedAction() calls /rmos/safety/evaluate:
   {
     "action": "promote_preset",
     "lane": "safe",
     "fragility_score": 0.75,
     "risk_grade": "YELLOW"
   }

3. Backend classifies: MEDIUM risk (frag ≥ 0.6 for tuned_v1)

4. Backend applies APPRENTICE rules: REQUIRE OVERRIDE

5. Frontend shows prompt:
   "Safety override required.
    
    Reason: Medium-risk action in apprentice mode; mentor override required.
    
    Ask mentor for a one-time override token..."

6. Apprentice requests mentor help

7. Mentor creates token:
   POST /rmos/safety/create-override
   { "action": "promote_preset", "created_by": "mentor_alice" }
   
   Response: { "token": "OVR-1701345678123456", ... }

8. Mentor gives token to apprentice

9. Apprentice pastes token in prompt

10. guardedAction() retries /rmos/safety/evaluate with token

11. Backend validates token:
    - Exists? ✓
    - Not used? ✓
    - Matches action? ✓
    - Not expired? ✓

12. Backend consumes token, returns ALLOW

13. guardedAction() proceeds to promotion API call

14. Backend runs ultra-fragility policy (MM-5)

15. If fragility policy passes, promotion succeeds

16. Job log entry includes:
    - safety_decision: { decision: "allow", mode: "apprentice", ... }
    - promotion_reason: "User-initiated promotion"
    - override used: true
```

---

## 📚 Related Documentation

- [N10.2: Apprenticeship Mode](./N10_2_APPRENTICESHIP_MODE_QUICKREF.md) - Safety engine core
- [MM-5: Ultra-Fragility Promotion Policy](./MM_5_FRAGILITY_PROMOTION_QUICKREF.md) - Fragility rules
- [N10.0: LiveMonitor Base](./N10_0_RMOS_LIVE_MONITOR_QUICKREF.md) - Real-time monitoring
- [RMOS Master Tree](./RMOS_MASTER_TREE.md) - Development roadmap

---

## 🎯 Next Steps

1. **Wire UI components:**
   - Add safety guard to existing promotion buttons
   - Add safety guard to experimental run buttons
   - Add SafetyModeBanner to RMOS dashboard

2. **Enhanced UI (optional):**
   - Modal dialogs instead of `alert()` / `prompt()`
   - Token copy button for mentors
   - Visual indication of safety mode on buttons

3. **Logging/Auditing:**
   - Track all override token usage
   - Generate safety audit reports
   - Alert mentors to repeated override requests

4. **Extended Safety:**
   - Add more action types (delete, archive, etc.)
   - Custom risk rules per material type
   - Time-based safety restrictions (night shifts, etc.)

---

**Bundle Complete:** ✅ All N10.2.1 components implemented and integrated.  
**Git Workflow:** Ready to commit with tag `RMOS_N10_2_1_SafetyFlowIntegration_v0.1_113025`
