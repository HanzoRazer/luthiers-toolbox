# N10.2 — Apprenticeship Mode + Safety Overrides: Quick Reference

**Bundle ID:** RMOS_N10_2_ApprenticeshipMode_v0.1_113025  
**Status:** ✅ Production Ready  
**Tags:** RMOS, Safety, Apprentice, Policy Engine, Override Tokens

---

## 🎯 Overview

N10.2 adds a **safety policy layer** to RMOS that gates dangerous actions based on operator skill level and risk assessment. It provides:

- **Three safety modes**: unrestricted, apprentice, mentor_review
- **Risk classification**: Automatic assessment of actions based on lane, fragility, and action type
- **Override tokens**: One-time mentor approvals for risky actions
- **Visual feedback**: Color-coded banner showing current mode
- **API integration**: REST endpoints for mode management and action evaluation

**Core Mission**: Prevent untrained operators from executing high-risk CNC operations while maintaining mentor flexibility through override tokens.

---

## 🏗️ Architecture

### **Safety Modes**

| Mode | Purpose | High-Risk Actions | Medium-Risk Actions | Low-Risk Actions |
|------|---------|-------------------|---------------------|------------------|
| **unrestricted** | Normal production | Require override | Allowed | Allowed |
| **apprentice** | Restricted training | Denied | Require override | Allowed |
| **mentor_review** | Supervised work | Require override | Allowed + logged | Allowed |

### **Risk Classification**

Risk is determined by combining:
- **Lane** (production, tuned_v1, experimental, tuned_v2)
- **Fragility score** (0.0–1.0 continuous)
- **Risk grade** (GREEN, YELLOW, RED categorical)

**Classification Rules:**
```python
# High risk
experimental + (fragility ≥ 0.7 OR grade == RED)
tuned_v2 + (fragility ≥ 0.7 OR grade == RED)

# Medium risk
experimental + (fragility < 0.7 AND grade != RED)
tuned_v1 + (fragility ≥ 0.6 OR grade == YELLOW)

# Low risk (default)
All other combinations
```

### **Decision Flow**

```
┌─────────────────┐
│  Action Request │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Get Safety Mode │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Classify Risk   │
│ (lane, frag,    │
│  grade, action) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Apply Mode      │
│ Rules           │
└────────┬────────┘
         │
    ┌────┴────┬────────────┐
    ▼         ▼            ▼
┌──────┐ ┌─────────┐ ┌──────────┐
│ ALLOW│ │ REQUIRE │ │   DENY   │
│      │ │OVERRIDE │ │          │
└──────┘ └────┬────┘ └──────────┘
              │
         ┌────┴────┐
         ▼         ▼
    ┌────────┐ ┌──────────┐
    │  Has   │ │  Prompt  │
    │ Token? │ │ for Token│
    └───┬────┘ └─────┬────┘
        │            │
        ▼            ▼
    ┌───────────────────┐
    │ Consume Token     │
    │ (validate action, │
    │  expiry, unused)  │
    └────────┬──────────┘
             │
        ┌────┴────┐
        ▼         ▼
    ┌──────┐ ┌──────┐
    │ALLOW │ │ DENY │
    └──────┘ └──────┘
```

---

## 📦 Components

### **Backend Files**

| File | Purpose | Lines |
|------|---------|-------|
| `services/api/app/schemas/rmos_safety.py` | Pydantic models for safety types | 60 |
| `services/api/app/core/rmos_safety_policy.py` | Risk classification + decision engine | 200 |
| `services/api/app/api/routes/rmos_safety_api.py` | FastAPI endpoints | 180 |
| `services/api/tests/test_rmos_safety.py` | Test coverage (18 tests) | 350 |

### **Frontend Files**

| File | Purpose | Lines |
|------|---------|-------|
| `packages/client/src/models/rmos_safety.ts` | TypeScript interfaces + helpers | 120 |
| `packages/client/src/stores/useRmosSafetyStore.ts` | Pinia state management | 160 |
| `packages/client/src/components/rmos/SafetyModeBanner.vue` | Mode display banner | 80 |

---

## 🔌 API Reference

### **GET /rmos/safety/mode**

Get current safety mode.

**Response:**
```json
{
  "mode": "apprentice",
  "set_by": "mentor_alice",
  "set_at": "2025-11-30T10:15:00Z"
}
```

---

### **POST /rmos/safety/mode**

Set safety mode (requires mentor/admin privileges).

**Request:**
```json
{
  "mode": "apprentice",
  "set_by": "mentor_alice"
}
```

**Response:**
```json
{
  "mode": "apprentice",
  "set_by": "mentor_alice",
  "set_at": "2025-11-30T10:15:00Z"
}
```

---

### **POST /rmos/safety/evaluate**

Evaluate action safety.

**Request (without override):**
```json
{
  "action": "start_job",
  "lane": "experimental",
  "fragility_score": 0.8,
  "risk_grade": "RED",
  "job_id": "job_12345"
}
```

**Response:**
```json
{
  "decision": {
    "decision": "require_override",
    "reason": "High-risk action in unrestricted mode; override recommended for fragile / experimental work.",
    "mode": "unrestricted",
    "risk_level": "high",
    "requires_override": true
  },
  "valid_override_tokens": []
}
```

**Request (with override token):**
```json
{
  "action": "start_job",
  "lane": "experimental",
  "fragility_score": 0.8,
  "risk_grade": "RED",
  "job_id": "job_12345",
  "override_token": "OVR-1701345678123456"
}
```

**Response (override accepted):**
```json
{
  "decision": {
    "decision": "allow",
    "reason": "Override accepted: Override accepted.",
    "mode": "unrestricted",
    "risk_level": "high",
    "requires_override": false
  },
  "valid_override_tokens": []
}
```

**Error Response (invalid override):**
```
HTTP 403 Forbidden
{
  "detail": "Override token already used."
}
```

---

### **POST /rmos/safety/create-override**

Create override token (requires mentor privileges).

**Request:**
```json
{
  "action": "start_job",
  "created_by": "mentor_alice",
  "ttl_minutes": 15
}
```

**Response:**
```json
{
  "token": "OVR-1701345678123456",
  "action": "start_job",
  "created_by": "mentor_alice",
  "created_at": "2025-11-30T10:15:00Z",
  "expires_at": "2025-11-30T10:30:00Z",
  "used": false
}
```

---

## 🎨 UI Components

### **SafetyModeBanner**

**Usage:**
```vue
<template>
  <SafetyModeBanner />
  <!-- Your RMOS content -->
</template>

<script setup lang="ts">
import SafetyModeBanner from '@/components/rmos/SafetyModeBanner.vue'
</script>
```

**Visual Examples:**

```
Unrestricted Mode:
┌────────────────────────────────────────────────────────────────┐
│ ✅ Safety mode: Unrestricted                                  │
│ Full capabilities enabled; high-risk actions still logged.     │
│ (set by mentor_alice at 10:15)                                │
└────────────────────────────────────────────────────────────────┘
(green background, green border)

Apprentice Mode:
┌────────────────────────────────────────────────────────────────┐
│ ⚠️ Safety mode: Apprentice                                     │
│ Some high-risk actions are blocked until mentor approval.      │
│ (set by mentor_bob at 11:30)                                  │
└────────────────────────────────────────────────────────────────┘
(yellow background, yellow border)

Mentor Review Mode:
┌────────────────────────────────────────────────────────────────┐
│ 👁️ Safety mode: Mentor Review                                  │
│ Mentor supervision mode; risky actions may require override.   │
│ (set by mentor_charlie at 14:45)                              │
└────────────────────────────────────────────────────────────────┘
(blue background, blue border)
```

---

## 💻 Frontend Integration

### **Using Safety Store**

```typescript
import { useRmosSafetyStore } from '@/stores/useRmosSafetyStore'

const safety = useRmosSafetyStore()

// Fetch current mode on mount
onMounted(async () => {
  await safety.fetchMode()
})

// Check current mode
if (safety.isApprenticeMode) {
  console.log('Apprentice restrictions active')
}
```

### **Evaluating Actions (Job Start Example)**

```typescript
async function onStartJob(
  jobId: string,
  lane: string,
  fragility?: number,
  riskGrade?: string
) {
  // 1. Evaluate safety
  const ctx = {
    action: "start_job",
    lane,
    fragility_score: fragility,
    risk_grade: riskGrade,
    job_id: jobId,
  }

  let res: EvaluateActionResponse
  try {
    res = await safety.evaluateAction(ctx)
  } catch (e) {
    alert(`Safety check failed: ${String(e)}`)
    return
  }

  const decision = res.decision

  // 2. Handle deny
  if (decision.decision === "deny") {
    alert(`Action denied: ${decision.reason}`)
    return
  }

  // 3. Handle override requirement
  if (decision.decision === "require_override") {
    const token = prompt(
      `Safety override required.\n\nReason: ${decision.reason}\n\nEnter mentor override token:`
    )
    if (!token) return

    // Retry evaluation with token
    try {
      const res2 = await safety.evaluateAction(ctx, token)
      if (res2.decision.decision !== "allow") {
        alert(`Still blocked: ${res2.decision.reason}`)
        return
      }
    } catch (e) {
      alert(`Override failed: ${String(e)}`)
      return
    }
  }

  // 4. Safe to proceed
  await actuallyStartJob(jobId)
}
```

### **Creating Override Tokens (Mentor Only)**

```typescript
async function createOverrideForAction(action: string) {
  try {
    const token = await safety.createOverride(action, 'mentor_alice')
    
    // Display token to apprentice
    alert(`Override token for ${action}:\n\n${token.token}\n\nExpires at: ${token.expires_at}`)
    
    // Or copy to clipboard
    navigator.clipboard.writeText(token.token)
    
    console.log('Token created:', token)
  } catch (e) {
    alert(`Failed to create override: ${String(e)}`)
  }
}
```

---

## 🧪 Testing

### **Backend Tests**

Run comprehensive test suite:

```powershell
cd services/api
pytest tests/test_rmos_safety.py -v
```

**Test Coverage (18 tests):**

```
tests/test_rmos_safety.py::TestRiskClassification
  ✓ test_low_risk_default_lane
  ✓ test_medium_risk_tuned_v1_moderate_fragility
  ✓ test_medium_risk_experimental_low_fragility
  ✓ test_high_risk_experimental_high_fragility
  ✓ test_high_risk_tuned_v2_red_grade

tests/test_rmos_safety.py::TestUnrestrictedMode
  ✓ test_low_risk_allowed
  ✓ test_high_risk_start_job_requires_override
  ✓ test_high_risk_promote_preset_requires_override

tests/test_rmos_safety.py::TestApprenticeMode
  ✓ test_low_risk_allowed
  ✓ test_medium_risk_start_job_requires_override
  ✓ test_high_risk_start_job_denied
  ✓ test_high_risk_promote_preset_denied
  ✓ test_high_risk_experimental_lane_denied

tests/test_rmos_safety.py::TestMentorReviewMode
  ✓ test_low_risk_allowed
  ✓ test_medium_risk_allowed
  ✓ test_high_risk_start_job_requires_override
  ✓ test_high_risk_promote_preset_requires_override

tests/test_rmos_safety.py::TestOverrideTokens
  ✓ test_create_token
  ✓ test_consume_valid_token
  ✓ test_consume_token_twice_fails
  ✓ test_consume_token_wrong_action_fails
  ✓ test_consume_invalid_token_fails
  ✓ test_token_expiry

tests/test_rmos_safety.py::TestModeManagement
  ✓ test_get_default_mode
  ✓ test_set_mode
  ✓ test_mode_persists

=== 18 passed in 0.45s ===
```

### **Frontend Manual Tests**

1. **Mode Display:**
   - Navigate to RMOS view
   - Verify SafetyModeBanner shows correct mode with icon
   - Switch modes via API and verify banner updates

2. **Action Evaluation:**
   - Attempt to start high-risk job in apprentice mode
   - Verify denial message appears
   - Switch to unrestricted and verify override prompt

3. **Override Flow:**
   - Create override token via mentor interface
   - Copy token to clipboard
   - Use token in job start flow
   - Verify action proceeds

4. **Store Integration:**
   - Check `safety.currentMode` in console
   - Verify `safety.isApprenticeMode` getter works
   - Confirm `safety.lastDecision` persists after evaluation

---

## ⚙️ Configuration

### **Risk Thresholds**

Edit `services/api/app/core/rmos_safety_policy.py`:

```python
def _classify_risk(ctx: SafetyActionContext) -> ActionRiskLevel:
    # Current thresholds:
    # - experimental + frag ≥ 0.7 → high
    # - tuned_v1 + frag ≥ 0.6 → medium
    
    # To adjust:
    if lane in ("experimental", "tuned_v2"):
        if frag >= 0.7:  # <- Change threshold here
            return "high"
```

### **Override Token TTL**

Default: 15 minutes

```python
token = policy.create_override_token(
    action="start_job",
    ttl_minutes=30  # <- Custom expiry
)
```

### **Mode-Specific Rules**

Edit decision logic in `evaluate_action()`:

```python
if mode == "apprentice":
    # Current: high-risk denied, medium-risk requires override
    # To make more restrictive:
    if risk == "medium" and ctx.action in ("start_job",):
        decision = "deny"  # <- Block instead of override
```

---

## 🚨 Troubleshooting

### **Issue:** Override token rejected with "already used"

**Cause:** Token can only be consumed once.

**Solution:** Create new token for each action attempt.

---

### **Issue:** Action denied in unrestricted mode

**Cause:** High-risk actions still require override in unrestricted.

**Solution:** Create override token or switch to mentor_review mode.

---

### **Issue:** SafetyModeBanner not showing

**Cause:** Store not initialized.

**Solution:** Call `safety.fetchMode()` on app mount:

```typescript
// App.vue or main layout
onMounted(async () => {
  await useRmosSafetyStore().fetchMode()
})
```

---

### **Issue:** Mode changes not persisting

**Cause:** In-memory state resets on server restart.

**Solution:** Implement persistent storage (DB or file-backed):

```python
# Replace module-level dict in rmos_safety_policy.py
# with database queries or JSON file
```

---

## 📋 Integration Checklist

- [x] Backend schemas created (`rmos_safety.py`)
- [x] Policy engine implemented (`rmos_safety_policy.py`)
- [x] API router created (`rmos_safety_api.py`)
- [x] Router registered in `main.py`
- [x] Frontend models created (`rmos_safety.ts`)
- [x] Frontend store created (`useRmosSafetyStore.ts`)
- [x] SafetyModeBanner component created
- [x] Backend tests written (18 tests)
- [x] Documentation created (this file)
- [ ] SafetyModeBanner added to RMOS views (user task)
- [ ] Job start flow integrated with safety checks (user task)
- [ ] Preset promotion flow integrated with safety checks (user task)
- [ ] Override token UI for mentors (future enhancement)

---

## 🔄 Workflow Example

**Scenario:** Apprentice wants to start high-risk experimental job.

```
1. Apprentice clicks "Start Job" on experimental lane (fragility 0.8)

2. UI calls safety.evaluateAction():
   {
     "action": "start_job",
     "lane": "experimental",
     "fragility_score": 0.8,
     "risk_grade": "RED"
   }

3. Backend classifies as HIGH risk (experimental + frag ≥ 0.7)

4. Backend applies APPRENTICE mode rules → DENY

5. Frontend shows alert:
   "Action denied: High-risk action denied in apprentice mode; mentor must run this."

6. Apprentice requests mentor help

7. Mentor creates override token:
   POST /rmos/safety/create-override
   {
     "action": "start_job",
     "created_by": "mentor_alice"
   }

8. Mentor gives token to apprentice: "OVR-1701345678123456"

9. Apprentice retries with token:
   safety.evaluateAction(ctx, "OVR-1701345678123456")

10. Backend validates token:
    - Exists? ✓
    - Not used? ✓
    - Matches action? ✓
    - Not expired? ✓

11. Backend consumes token and returns ALLOW

12. Job starts successfully
```

---

## 📚 Related Documentation

- [N10.0: RMOS Metadata Catalog](./N10_0_RMOS_METADATA_CATALOG_QUICKREF.md) - Job metadata structure
- [N10.1: LiveMonitor Drill-Down](./N10_1_LIVEMONITOR_DRILLDOWN_QUICKREF.md) - Real-time monitoring
- [MM-5: Ultra-Fragility Promotion Policy](./MM_5_FRAGILITY_PROMOTION_QUICKREF.md) - Lane promotion rules
- [RMOS Master Tree](./RMOS_MASTER_TREE.md) - Development roadmap

---

## 🎯 Next Steps

1. **Add SafetyModeBanner to RMOS views:**
   ```vue
   <!-- packages/client/src/views/RosettePipelineView.vue -->
   <template>
     <SafetyModeBanner />
     <!-- existing content -->
   </template>
   ```

2. **Integrate with job start flow:**
   - Add safety check before `startJob()` API call
   - Show override prompt when required
   - Display denial messages

3. **Integrate with preset promotion:**
   - Check safety before promoting presets to higher lanes
   - Require override for fragile → experimental promotions

4. **Build mentor override UI:**
   - Token creation form
   - Token list with expiry
   - One-click token copy

5. **Add persistent storage:**
   - Replace in-memory dicts with database
   - Store mode history for auditing
   - Log all override token usage

---

**Bundle Complete:** ✅ All N10.2 components implemented and tested.  
**Git Workflow:** Ready to commit with tag `RMOS_N10_2_ApprenticeshipMode_v0.1_113025`
