# Issue: Blank Page on Root Route (/)

**Date:** 2026-01-05
**Status:** Resolved
**Priority:** Medium (other routes work)

---

## Symptom

- http://localhost:5174/ shows blank white page
- No visible errors in browser (needs console check)
- Other routes work fine (e.g., http://localhost:5174/saw)

---

## Affected Route

```typescript
// packages/client/src/router/index.ts
{
  path: "/",
  name: "Home",
  component: RosettePipelineView,  // <-- This component or its children
}
```

---

## Component Tree (RosettePipelineView.vue)

```
RosettePipelineView.vue
├── RosettePatternLibrary.vue
├── JobLogMiniList.vue
├── RosetteTemplateLab.vue (conditional: v-if="selectedPattern")
├── RosetteMultiRingOpPanel.vue (conditional: v-if="batchOp")
├── RosetteManufacturingPlanPanel.vue
└── LiveMonitor.vue
```

---

## What's Been Verified

| Check | Result |
|-------|--------|
| TypeScript errors in RosettePipelineView.vue | ✅ None |
| TypeScript errors in child components | ✅ None |
| TypeScript errors in useRosettePatternStore.ts | ✅ None |
| /saw route works | ✅ Yes |
| /rmos route (same component) | ✅ Fixed (same root cause) |
| Browser console errors | ✅ Fixed - 404s on RMOS API endpoints |
| Missing server endpoints | ✅ Fixed - Created rmos_router.py |

---

## Likely Causes

1. **Runtime error in child component** - A component throws during render but error isn't surfacing
2. **Pinia store initialization** - `useRosettePatternStore` may fail on first load
3. **API call on mount** - One of the child components may be calling an API that fails silently
4. **CSS issue** - Content renders but is invisible (unlikely since /saw works)

---

## Debugging Steps

### 1. Check Browser Console (F12 → Console)

Load http://localhost:5174/ and look for:
- Red error messages
- Failed network requests
- Vue warnings

### 2. Test /rmos Route

```
http://localhost:5174/rmos
```

This uses the same `RosettePipelineView` component. If it also fails, the issue is in the component, not routing.

### 3. Isolate Components

Temporarily simplify `RosettePipelineView.vue`:

```vue
<template>
  <div class="p-4">
    <h1>Test - RosettePipelineView</h1>
    <!-- Comment out child components one by one -->
  </div>
</template>
```

### 4. Check Pinia Store

In browser console:
```javascript
// Check if store loads
import('@/stores/useRosettePatternStore').then(m => console.log(m.useRosettePatternStore()))
```

---

## Files to Investigate

| File | Path |
|------|------|
| Main View | `packages/client/src/views/RosettePipelineView.vue` |
| Pattern Store | `packages/client/src/stores/useRosettePatternStore.ts` |
| Pattern Library | `packages/client/src/components/rmos/RosettePatternLibrary.vue` |
| Job Log List | `packages/client/src/components/rmos/JobLogMiniList.vue` |
| Live Monitor | `packages/client/src/components/rmos/LiveMonitor.vue` |

---

## Recent Changes (Context)

The following commits were made to `ManufacturingCandidateList.vue` before this issue was noticed:

- `8d9f8eb`: style(rmos): refine Audit column CSS
- `5edc32f`: feat(rmos): clickable Audit header cycles sort
- `b0d7eb9`: feat(rmos): add currentOperator prop with localStorage fallback

**Note:** `ManufacturingCandidateList.vue` is NOT used by `RosettePipelineView`, so these changes are unlikely to be the cause.

---

## Fix Applied (Unrelated but same session)

Two syntax issues were fixed before this issue was noticed:

1. **geometry.ts** - Removed corrupted `*** End of File` marker at EOF
2. **ManufacturingCandidateList.vue** - Fixed `runId.value` → `props.runId` at line 426

These fixes were committed separately by the user.

---

## Next Steps

1. Get browser console output when loading `/`
2. Test if `/rmos` also fails
3. Binary search by commenting out child components
4. Check network tab for failed API calls

---

## Resolution

**Resolved:** 2026-01-05

### Root Cause

The client components (`RosettePipelineView` and children) were calling API endpoints that didn't exist on the server:

- `GET /api/rosette-patterns` - Pattern library
- `GET /api/joblog` - Job log entries
- `POST /api/rosette/manufacturing-plan` - Manufacturing plans
- `GET /api/rmos/live-monitor/{jobId}/drilldown` - Live monitoring

The server returned 404 for all these endpoints, causing:
1. Stores to set `error` state
2. Components to render minimal/empty UI
3. Result: Blank-looking page

### Fix Applied

Created `server/rmos_router.py` with the missing RMOS endpoints:

1. **Pattern CRUD** - Full CRUD for `/api/rosette-patterns`
2. **Job Log** - GET/POST for `/api/joblog`
3. **Manufacturing Plan** - POST `/api/rosette/manufacturing-plan`
4. **Live Monitor** - GET `/api/rmos/live-monitor/{job_id}/drilldown`

Updated `server/app.py` to include the new router.

### Files Changed

| File | Change |
|------|--------|
| `server/rmos_router.py` | NEW - RMOS API endpoints |
| `server/app.py` | Added import and router inclusion |

### Testing

Restart the server and navigate to `http://localhost:5174/` - the page should now load with the pattern library and other components visible.
