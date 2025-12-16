# Run Artifact UI — NEW ADDITIONS ONLY

**From:** more_features.docx  
**Date:** December 15, 2025

These are the **specific additions** to integrate into existing files.

---

## 1. Store Addition: `lastSelectedRunId`

**File:** `packages/client/src/stores/rmosRunsStore.ts`

**ADD to state:**
```typescript
state: () => ({
  // ... existing state ...
  
  // NEW: deterministic "diff with last selected"
  lastSelectedRunId: null as string | null,
}),
```

**ADD to actions:**
```typescript
actions: {
  // ... existing actions ...

  async select(runId: string) {
    // NEW: shift current selected into lastSelected before replacing
    if (this.selected?.run_id && this.selected.run_id !== runId) {
      this.lastSelectedRunId = this.selected.run_id;
    }
    this.selected = await fetchRun(runId);
  },

  // NEW action
  setLastSelected(runId: string) {
    this.lastSelectedRunId = runId;
  },
}
```

---

## 2. Panel Change: Row Click Handler

**File:** `packages/client/src/components/rmos/RunArtifactPanel.vue`

**CHANGE row click binding from:**
```vue
<RunArtifactRow
  v-for="r in store.items"
  :key="r.run_id"
  :run="r"
  @select="store.select(r.run_id)"
/>
```

**TO:**
```vue
<RunArtifactRow
  v-for="r in store.items"
  :key="r.run_id"
  :run="r"
  @select="() => { store.setLastSelected(r.run_id); store.select(r.run_id); }"
/>
```

---

## 3. Detail Addition: Action Buttons

**File:** `packages/client/src/components/rmos/RunArtifactDetail.vue`

**ADD to script setup:**
```typescript
import { computed } from "vue";
import { useRouter } from "vue-router";
import { downloadRun } from "@/api/rmosRuns";
import { useRmosRunsStore } from "@/stores/rmosRunsStore";

const router = useRouter();
const store = useRmosRunsStore();

const canDiff = computed(
  () => !!store.lastSelectedRunId && 
       store.lastSelectedRunId !== props.artifact.run_id
);

function diffWithLastSelected() {
  if (!store.lastSelectedRunId) return;
  router.push({
    path: "/rmos/runs/diff",
    query: { a: store.lastSelectedRunId, b: props.artifact.run_id },
  });
}

function setAsA() {
  router.push({
    path: "/rmos/runs/diff",
    query: { a: props.artifact.run_id },
  });
}
```

**ADD to template (in header actions area):**
```vue
<div class="actions">
  <button @click="downloadRun(artifact.run_id)">Download JSON</button>
  <button @click="setAsA">Set as A</button>
  <button @click="diffWithLastSelected" :disabled="!canDiff">
    Diff with last selected
  </button>
</div>
```

---

## Summary

| Change | File | Type |
|--------|------|------|
| `lastSelectedRunId` state | rmosRunsStore.ts | ADD property |
| `setLastSelected()` action | rmosRunsStore.ts | ADD method |
| Modified `select()` | rmosRunsStore.ts | MODIFY method |
| Row click handler | RunArtifactPanel.vue | MODIFY binding |
| Action buttons | RunArtifactDetail.vue | ADD imports + methods + template |

These are **surgical additions** to existing files, not full replacements.
