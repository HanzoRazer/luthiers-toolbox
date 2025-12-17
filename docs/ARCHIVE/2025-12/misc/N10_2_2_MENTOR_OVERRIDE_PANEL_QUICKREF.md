# N10.2.2 — Mentor Override Panel: Quick Reference

**Bundle ID:** RMOS_N10_2_2_MentorOverridePanel_v0.1_113025  
**Status:** ✅ Production Ready  
**Tags:** RMOS, Safety, UI, Mentor Tools

---

## 🎯 Overview

N10.2.2 delivers a **dedicated UI panel for mentors** to generate and manage override tokens without leaving the RMOS interface.

**What it adds:**
- Visual panel for token generation with action/mentor/TTL controls
- In-session token history (shows recent tokens with expiration times)
- One-click toggle from Safety Mode Banner
- Clean, minimal UX for quick mentor workflows

**Key benefit:** Mentors no longer need to call backend APIs directly - they have a self-service UI that integrates naturally into the RMOS experience.

---

## 🏗️ Architecture

### **Component Structure**

```
SafetyModeBanner.vue
├── "Mentor overrides" button → toggles panel
└── MentorOverridePanel.vue (absolute positioned)
    ├── Action selector (start_job, run_experimental_lane, promote_preset)
    ├── Mentor name input (optional)
    ├── TTL minutes input (1-120, default 15)
    ├── Generate button
    └── Recent tokens table (in-memory, session-only)
```

### **Token Generation Flow**

```
1. Mentor clicks "Mentor overrides" in Safety banner
2. Panel opens with form:
   - Select action type
   - Enter name (optional)
   - Set TTL (default 15 min)
3. Click "Generate override token"
4. API call: POST /rmos/safety/create-override
5. Token appears in Recent tokens table
6. Mentor copies token
7. Mentor shares token verbally/on paper with apprentice
8. Apprentice pastes token when guardedAction prompts
```

---

## 📦 Components Changed

### **New Component (1 file)**

| File | Purpose |
|------|---------|
| `packages/client/src/components/rmos/MentorOverridePanel.vue` | Token generation UI with history |

### **Patched Components (2 files)**

| File | Changes | Purpose |
|------|---------|---------|
| `packages/client/src/stores/useRmosSafetyStore.ts` | Added `ttlMinutes` parameter to `createOverride()` | Configure token expiration |
| `packages/client/src/components/rmos/SafetyModeBanner.vue` | Added toggle button + panel display | Easy mentor access |

---

## 🎨 UI Component Details

### **MentorOverridePanel.vue**

**Location:** Absolute positioned (`right-2 top-10 z-30 w-80`)  
**Appearance:** White card with shadow, rounded borders, 11px text  
**State:** In-memory only (no persistence, cleared on page refresh)

**Form Fields:**

1. **Action selector** (dropdown):
   - `start_job` - Start job (normal lane)
   - `run_experimental_lane` - Run experimental lane
   - `promote_preset` - Promote preset

2. **Mentor name** (text input, optional):
   - Placeholder: "e.g. Ross, Mentor1"
   - Stored in token for audit trail

3. **TTL minutes** (number input):
   - Range: 1-120 minutes
   - Default: 15 minutes
   - Controls token expiration time

4. **Generate button**:
   - Disabled while creating
   - Shows "Generating…" during API call
   - Adds token to Recent tokens table on success

**Recent Tokens Table:**

Shows last 10 tokens generated in current session:

| Column | Content |
|--------|---------|
| Token | Full token string (e.g., `OVR-1701345678123456`) |
| Action | Action type authorized |
| Created by | Mentor name or "—" |
| Expires | Expiration timestamp |

**Features:**
- Auto-scrolls new tokens to top
- Limits to 10 entries (oldest dropped)
- Footer reminder about single-use tokens

---

### **SafetyModeBanner.vue Patch**

**New Elements:**

1. **"Mentor overrides" button** (right side of banner):
   - Appearance: Small border button, white background
   - Behavior: Toggles `showMentorPanel` ref
   - Position: Next to existing hint text

2. **Conditional panel display**:
   - Shows when `showMentorPanel === true`
   - Positioned absolutely relative to banner
   - Closes on panel's `@close` event

**Updated Script:**
- Imports `MentorOverridePanel` component
- Adds `showMentorPanel` ref (default `false`)

---

## 🔌 API Integration

### **Updated Store Method**

**`useRmosSafetyStore.createOverride()`**

**Signature:**
```typescript
async createOverride(
  action: string,
  createdBy?: string,
  ttlMinutes = 15
): Promise<OverrideToken>
```

**Parameters:**
- `action` - Action type (start_job, run_experimental_lane, promote_preset)
- `createdBy` - Optional mentor identifier (for audit trail)
- `ttlMinutes` - Token expiration time in minutes (default 15)

**Request Body:**
```json
{
  "action": "promote_preset",
  "created_by": "Ross",
  "ttl_minutes": 30
}
```

**Response:**
```json
{
  "token": "OVR-1701345678123456",
  "action": "promote_preset",
  "created_by": "Ross",
  "created_at": "2025-11-30T10:30:45",
  "expires_at": "2025-11-30T11:00:45",
  "used": false
}
```

---

## 📖 Usage Workflows

### **Workflow 1: Generate Token for Experimental Run**

1. **Mentor opens RMOS dashboard**
2. **Safety banner shows current mode** (e.g., "Safety mode: apprentice")
3. **Mentor clicks "Mentor overrides"** button
4. **Panel opens** with form
5. **Mentor configures:**
   - Action: "Run experimental lane"
   - Mentor: "Ross"
   - TTL: 30 minutes
6. **Clicks "Generate override token"**
7. **Token appears in table:**
   ```
   Token: OVR-1701345678123456
   Action: run_experimental_lane
   Created by: Ross
   Expires: 2025-11-30 11:00:45
   ```
8. **Mentor tells apprentice:** "Your override token is `OVR-1701345678123456`"
9. **Apprentice tries experimental run** → guardedAction prompts for token
10. **Apprentice pastes token** → run proceeds

---

### **Workflow 2: Batch Token Generation**

**Scenario:** Mentor wants to authorize multiple promotions ahead of time.

1. **Open Mentor Override Panel**
2. **Generate 3 tokens:**
   - Token 1: promote_preset, TTL 60 min
   - Token 2: promote_preset, TTL 60 min
   - Token 3: promote_preset, TTL 60 min
3. **Recent tokens table shows all 3**
4. **Mentor writes tokens on paper** or sends via secure channel
5. **Apprentices use tokens** as needed throughout the hour
6. **Each token consumed on first use**

---

## 🧪 Testing

### **Manual UI Tests**

**Test 1: Panel Toggle**
```
1. Open RMOS dashboard
2. Verify SafetyModeBanner visible at top
3. Click "Mentor overrides" button
4. ✓ Panel appears below banner
5. Click "✕" close button
6. ✓ Panel disappears
7. Click "Mentor overrides" again
8. ✓ Panel reopens
```

**Test 2: Token Generation**
```
1. Open panel
2. Select action: "Promote preset"
3. Enter mentor name: "Test Mentor"
4. Set TTL: 5 minutes
5. Click "Generate override token"
6. ✓ Button shows "Generating…"
7. ✓ Token appears in Recent tokens table
8. ✓ Token string starts with "OVR-"
9. ✓ Action shows "promote_preset"
10. ✓ Created by shows "Test Mentor"
11. ✓ Expires shows future timestamp (5 min ahead)
```

**Test 3: Token History**
```
1. Generate token #1 (action: start_job)
2. Generate token #2 (action: run_experimental_lane)
3. Generate token #3 (action: promote_preset)
4. ✓ All 3 tokens visible in table
5. ✓ Newest token at top
6. ✓ Each has unique token string
7. ✓ Each shows correct action
```

**Test 4: Token Usage**
```
1. Generate token for "run_experimental_lane"
2. Copy token string from table
3. Navigate to experimental run button
4. Click run → safety prompt appears
5. Paste token in prompt
6. ✓ Run proceeds successfully
7. Try using same token again
8. ✓ Backend rejects: "Invalid override token"
```

---

### **API Integration Tests**

Test store method with TTL parameter:

```typescript
// In browser console:
import { useRmosSafetyStore } from '@/stores/useRmosSafetyStore'

const safety = useRmosSafetyStore()

// Test with custom TTL
const token = await safety.createOverride('start_job', 'TestMentor', 30)
console.log(token)
// Should show expires_at 30 minutes in future

// Test with default TTL (15 min)
const token2 = await safety.createOverride('promote_preset', 'Ross')
console.log(token2)
// Should show expires_at 15 minutes in future
```

---

## 🎨 UI Customization

### **Panel Positioning**

Default: `absolute right-2 top-10 z-30 w-80`

**Alternative placements:**

1. **Sidebar integration:**
```vue
<!-- In RosettePipelineView.vue sidebar -->
<MentorOverridePanel class="mb-4" />
```

2. **Modal overlay:**
```vue
<Teleport to="body">
  <div v-if="showMentorPanel" class="fixed inset-0 bg-black/20 z-50 flex items-center justify-center">
    <MentorOverridePanel @close="showMentorPanel = false" />
  </div>
</Teleport>
```

3. **Bottom drawer:**
```vue
<Transition name="slide-up">
  <div v-if="showMentorPanel" class="fixed bottom-0 left-0 right-0 z-30">
    <MentorOverridePanel @close="showMentorPanel = false" />
  </div>
</Transition>
```

---

### **Styling Adjustments**

**Change panel width:**
```vue
<div class="w-96">  <!-- Instead of w-80 -->
```

**Add shadow/border effects:**
```vue
<div class="border-2 border-blue-500 shadow-2xl">
```

**Dark mode support:**
```vue
<div class="bg-white dark:bg-gray-800 dark:text-gray-100">
```

---

## ⚙️ Configuration

### **Token TTL Range**

Default limits: 1-120 minutes

**Adjust in MentorOverridePanel.vue:**
```vue
<input
  v-model.number="ttl"
  type="number"
  min="5"      <!-- Minimum 5 minutes -->
  max="240"    <!-- Maximum 4 hours -->
  class="..."
/>
```

---

### **Token History Limit**

Default: 10 tokens

**Adjust in `onGenerate()` method:**
```typescript
tokens.value.unshift(token);
// Change limit:
if (tokens.value.length > 20) tokens.value.pop();  // Keep 20 instead of 10
```

---

### **Action Options**

Default actions:
- `start_job` - Start job (normal lane)
- `run_experimental_lane` - Run experimental lane
- `promote_preset` - Promote preset

**Add custom actions:**
```vue
<select v-model="action" class="...">
  <option value="start_job">Start job (normal lane)</option>
  <option value="run_experimental_lane">Run experimental lane</option>
  <option value="promote_preset">Promote preset</option>
  <option value="delete_pattern">Delete pattern</option>  <!-- NEW -->
  <option value="archive_preset">Archive preset</option>  <!-- NEW -->
</select>
```

---

## 🚨 Troubleshooting

### **Issue:** Panel doesn't appear when button clicked

**Cause:** `showMentorPanel` ref not initialized.

**Solution:** Verify SafetyModeBanner script setup:
```typescript
const showMentorPanel = ref(false);  // Must be defined
```

---

### **Issue:** Token generation fails with 500 error

**Cause:** Backend `/rmos/safety/create-override` endpoint not available.

**Solution:** 
1. Verify API server running: `http://localhost:8000`
2. Check backend logs for errors
3. Verify N10.2 bundle installed (safety API must exist)

---

### **Issue:** Token appears but apprentice can't use it

**Cause:** Token might be expired or already consumed.

**Solution:**
1. Check `expires_at` timestamp in Recent tokens table
2. Generate new token if expired
3. Remember: tokens are single-use only

---

### **Issue:** Panel overlaps other UI elements

**Cause:** Absolute positioning conflicts with layout.

**Solution:** Adjust z-index or use alternative placement:
```vue
<!-- Higher z-index -->
<div class="absolute right-2 top-10 z-50 w-80">

<!-- Or use relative positioning in container -->
<div class="relative">
  <div class="absolute ...">
```

---

## 📋 Integration Checklist

- [x] Create MentorOverridePanel.vue component
- [x] Add TTL parameter to createOverride() store method
- [x] Patch SafetyModeBanner with toggle button
- [x] Add panel display conditional
- [x] Test token generation flow
- [x] Test token usage with guardedAction
- [x] Document UI integration patterns
- [ ] Add to RMOS views beyond dashboard (optional)
- [ ] Implement persistent token history (optional)
- [ ] Add mode switcher to panel (optional future)

---

## 🎯 Future Enhancements

### **1. Persistent Token History**

Store tokens in localStorage or backend:
```typescript
// Save to localStorage
localStorage.setItem('mentor_tokens', JSON.stringify(tokens.value))

// Load on mount
onMounted(() => {
  const saved = localStorage.getItem('mentor_tokens')
  if (saved) tokens.value = JSON.parse(saved)
})
```

---

### **2. Mode Switcher in Panel**

Add mode controls to panel:
```vue
<div class="border-t pt-2 mt-2">
  <span class="text-xs font-semibold">Quick Mode Switch:</span>
  <div class="flex gap-1 mt-1">
    <button @click="safety.setMode('unrestricted')" class="...">
      Unrestricted
    </button>
    <button @click="safety.setMode('apprentice')" class="...">
      Apprentice
    </button>
    <button @click="safety.setMode('mentor_review')" class="...">
      Mentor Review
    </button>
  </div>
</div>
```

---

### **3. Token Revocation**

Add "Revoke" button for unused tokens:
```vue
<td class="p-1">
  <button
    v-if="!t.used"
    @click="onRevoke(t.token)"
    class="text-[10px] text-red-600 hover:underline"
  >
    Revoke
  </button>
</td>
```

---

### **4. Batch Token Export**

Export all tokens to clipboard or file:
```vue
<button @click="exportTokens">
  Export all tokens
</button>

<script>
function exportTokens() {
  const csv = tokens.value.map(t => `${t.token},${t.action},${t.created_by}`).join('\n')
  navigator.clipboard.writeText(csv)
  alert('Tokens copied to clipboard')
}
</script>
```

---

## 📚 Related Documentation

- [N10.2: Apprenticeship Mode](./N10_2_APPRENTICESHIP_MODE_QUICKREF.md) - Safety engine core
- [N10.2.1: Safety Flow Integration](./N10_2_1_SAFETY_FLOW_INTEGRATION_QUICKREF.md) - Backend integration
- [RMOS Master Tree](./RMOS_MASTER_TREE.md) - Development roadmap

---

## 🎯 Complete Workflow Example

**Scenario:** Mentor authorizes apprentice to promote fragile preset.

```
=== Mentor Side ===
1. Open RMOS dashboard
2. See "Safety mode: apprentice" banner
3. Click "Mentor overrides" button
4. Panel opens with form
5. Configure:
   - Action: "Promote preset"
   - Mentor: "Ross"
   - TTL: 20 minutes
6. Click "Generate override token"
7. Token appears: OVR-1701345678123456
8. Mentor tells apprentice: "Your token is OVR-1701345678123456"

=== Apprentice Side ===
9. Apprentice navigates to Patterns view
10. Finds preset with fragility 0.85 (high-risk)
11. Clicks "Promote to Safe" button
12. Safety system evaluates:
    - Mode: apprentice
    - Fragility: 0.85 (high)
    - Risk level: HIGH
    - Decision: REQUIRE OVERRIDE
13. guardedAction() shows prompt:
    "Safety override required.
    
    Reason: High-risk action denied in apprentice mode; mentor must run this.
    
    Ask mentor for override token:"
14. Apprentice pastes: OVR-1701345678123456
15. guardedAction() retries with token
16. Backend validates:
    ✓ Token exists
    ✓ Not expired (within 20 min)
    ✓ Not used
    ✓ Action matches (promote_preset)
17. Backend consumes token, returns ALLOW
18. Promotion proceeds (fragility policy also passes)
19. Success! Preset promoted to safe lane
20. Job log includes:
    - safety_decision: "allow (override used)"
    - override_created_by: "Ross"
```

---

**Bundle Complete:** ✅ All N10.2.2 components implemented and integrated.  
**Git Workflow:** Ready to commit with tag `RMOS_N10_2_2_MentorOverridePanel_v0.1_113025`
