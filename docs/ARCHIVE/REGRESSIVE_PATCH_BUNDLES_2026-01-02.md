# Regressive Patch Bundles Archive

**Date:** 2026-01-02
**Archived by:** Claude Code (CBSP21 Protocol)
**Status:** REJECTED - Patches would downgrade existing functionality

---

## Overview

This document archives patch bundles that were provided but **not applied** because they would regress existing functionality. Per CBSP21.md guidelines, patches must be evaluated against the current codebase state before application.

In each case, the correct action was a **surgical migration** that updated import sources while preserving all existing features.

---

## Patch Bundle 1: ManufacturingCandidatesPanel.vue (Simplified Version)

### Provided Diff

```diff
diff --git a/packages/client/src/components/rmos/ManufacturingCandidatesPanel.vue b/packages/client/src/components/rmos/ManufacturingCandidatesPanel.vue
index 8a91f0c..b6f2d7e 100644
--- a/packages/client/src/components/rmos/ManufacturingCandidatesPanel.vue
+++ b/packages/client/src/components/rmos/ManufacturingCandidatesPanel.vue
@@ -1,15 +1,16 @@
 <script setup lang="ts">
 import { computed, onMounted, ref, watch } from "vue";
 import { useRoute } from "vue-router";
 
 import {
   listManufacturingCandidates,
   decideManufacturingCandidate,
   downloadManufacturingCandidateZip,
   type ManufacturingCandidate,
   type RiskLevel,
 } from "@/sdk/rmos/runs";
 
 // Small utility: download a Blob with a filename
 function downloadBlob(blob: Blob, filename: string) {
@@ -22,6 +23,47 @@ function downloadBlob(blob: Blob, filename: string) {
   URL.revokeObjectURL(url);
 }
 
+function fmtUtc(s?: string | null): string {
+  if (!s) return "";
+  const d = new Date(s);
+  if (Number.isNaN(d.getTime())) return s;
+  return d.toLocaleString();
+}
+
+function safeText(s: unknown): string {
+  return typeof s === "string" ? s : s == null ? "" : String(s);
+}
+
 const route = useRoute();
 const runId = computed(() => String(route.params.run_id ?? route.params.id ?? ""));
 
 const candidates = ref<ManufacturingCandidate[]>([]);
 const loading = ref(false);
 const error = ref<string | null>(null);
 
+// Hover audit drawer (product-only)
+const hoverId = ref<string | null>(null);
+const hoverCandidate = computed(() =>
+  candidates.value.find((c) => c.candidate_id === hoverId.value) ?? null
+);
+const hoverAuditText = computed(() => {
+  const c = hoverCandidate.value;
+  if (!c) return "";
+  const lines: string[] = [];
+  lines.push(`Candidate: ${c.candidate_id}`);
+  if (c.advisory_id) lines.push(`Advisory: ${c.advisory_id}`);
+  if (c.created_at_utc) lines.push(`Created: ${fmtUtc(c.created_at_utc)}`);
+  if (c.decided_at_utc || c.decided_by) {
+    lines.push(`Decided: ${fmtUtc(c.decided_at_utc)}${c.decided_by ? ` by ${c.decided_by}` : ""}`);
+  } else {
+    lines.push(`Decided: (none)`);
+  }
+  if (c.decision_note) lines.push(`Note: ${c.decision_note}`);
+  if (c.decision_history?.length) {
+    lines.push(`— History —`);
+    for (const h of c.decision_history) {
+      lines.push(
+        `${h.decision} • ${fmtUtc(h.decided_at_utc)}${h.decided_by ? ` • ${h.decided_by}` : ""}${h.note ? ` • ${h.note}` : ""}`
+      );
+    }
+  }
+  return lines.join("\n");
+});
+
 // Multi-select (product-only)
 const selectedIds = ref<Set<string>>(new Set());
 const selectedCount = computed(() => selectedIds.value.size);
 // ... truncated for brevity ...
```

### Why Rejected

| Aspect | Existing File (891 lines) | Patch (~300 lines) |
|--------|---------------------------|-------------------|
| Props | `runId` prop (reusable) | Route params only |
| Filters | Status/search/sort toolbar | None |
| Bulk Operations | Full BulkDecisionModal integration | None |
| Note Editor | Full inline editor with history | Simplified |
| Per-row States | `rowBusy`, `noteBusy`, `noteError` | None |
| Error Handling | Per-note error tracking | Global only |

**Verdict:** Patch would remove 600+ lines of production UX features.

### Correct Action Taken

The existing file was already migrated to SDK in a prior commit (`e669400`). No changes needed.

---

## Patch Bundle 2: BulkRejectModal.vue (Simplified Version)

### Provided Diff

```diff
diff --git a/packages/client/src/components/rmos/BulkRejectModal.vue b/packages/client/src/components/rmos/BulkRejectModal.vue
new file mode 100644
index 0000000..f1a4b21
--- /dev/null
+++ b/packages/client/src/components/rmos/BulkRejectModal.vue
@@ -0,0 +1,205 @@
+<script setup lang="ts">
+import { computed, ref, watch } from "vue";
+import type { RejectReasonCode } from "@/sdk/rmos/runs";
+
+const props = defineProps<{
+  open: boolean;
+  count: number;
+  defaultReasonCode?: RejectReasonCode | null;
+}>();
+
+const emit = defineEmits<{
+  (e: "close"): void;
+  (e: "confirm", payload: { reasonCode: RejectReasonCode; detail?: string | null; operatorNote?: string | null }): void;
+}>();
+
+const reasonCode = ref<RejectReasonCode>(props.defaultReasonCode ?? "OTHER");
+const detail = ref<string>("");
+const operatorNote = ref<string>("");
+
+watch(
+  () => props.open,
+  (v) => {
+    if (v) {
+      reasonCode.value = props.defaultReasonCode ?? "OTHER";
+      detail.value = "";
+      operatorNote.value = "";
+    }
+  }
+);
+
+const canConfirm = computed(() => props.count > 0);
+
+function close() {
+  emit("close");
+}
+
+function confirm() {
+  if (!canConfirm.value) return;
+  emit("confirm", {
+    reasonCode: reasonCode.value,
+    detail: detail.value.trim() ? detail.value.trim() : null,
+    operatorNote: operatorNote.value.trim() ? operatorNote.value.trim() : null,
+  });
+}
+</script>
+
+<template>
+  <div v-if="open" class="modal-backdrop" @click.self="close">
+    <div class="modal">
+      <div class="modal__head">
+        <div class="modal__title">Bulk reject variants</div>
+        <button class="btn btn--ghost" @click="close" aria-label="Close">✕</button>
+      </div>
+
+      <div class="modal__body">
+        <p class="muted">
+          You are about to reject <b>{{ count }}</b> selected variants with one shared reason code.
+        </p>
+
+        <label class="field">
+          <div class="field__label">Reason code</div>
+          <select v-model="reasonCode" class="field__control">
+            <option value="GEOMETRY_UNSAFE">GEOMETRY_UNSAFE</option>
+            <option value="TEXT_REQUIRES_OUTLINE">TEXT_REQUIRES_OUTLINE</option>
+            <option value="AESTHETIC">AESTHETIC</option>
+            <option value="DUPLICATE">DUPLICATE</option>
+            <option value="OTHER">OTHER</option>
+          </select>
+        </label>
+        <!-- ... truncated ... -->
+      </div>
+    </div>
+  </div>
+</template>
```

### Why Rejected

| Aspect | Existing File (144 lines) | Patch (205 lines) |
|--------|---------------------------|-------------------|
| Props | `runId`, `advisoryIds[]` | `count` only |
| API Calls | Handles rejection internally | Delegates to parent |
| Progress | Shows `done / total` | None |
| Error | Per-batch error handling | None |
| Emit | `@done` after completion | `@confirm` with payload |

**Verdict:** Patch changes the component architecture from "self-contained with progress" to "dumb form that delegates". This breaks existing parent integrations.

### Correct Action Taken

Surgical migration in commit `caff9b0`:
- Changed import from `@/api/rmosRuns.rejectAdvisoryVariant` to `@/sdk/rmos/runs.reviewAdvisoryVariant`
- Updated API call to use SDK's rejection fields
- Preserved all progress tracking, error handling, and emit patterns

---

## Patch Bundle 3: RunVariantsReviewPage.vue (Simplified Version)

### Provided Diff (Partial)

```diff
diff --git a/packages/client/src/views/Runs/RunVariantsReviewPage.vue b/packages/client/src/views/Runs/RunVariantsReviewPage.vue
index 3c1a9de..c7b8f50 100644
--- a/packages/client/src/views/Runs/RunVariantsReviewPage.vue
+++ b/packages/client/src/views/Runs/RunVariantsReviewPage.vue
@@ -1,33 +1,92 @@
 <script setup lang="ts">
-import { computed, onMounted, ref, watch } from "vue";
+import { computed, onMounted, ref, watch } from "vue";
 import { useRoute } from "vue-router";
 import VariantNotes from "@/components/rmos/VariantNotes.vue";
 import PromoteToManufacturingButton from "@/components/rmos/PromoteToManufacturingButton.vue";
 import ManufacturingCandidatesPanel from "@/components/rmos/ManufacturingCandidatesPanel.vue";
 import PromptLineageViewer from "@/components/rmos/PromptLineageViewer.vue";
 import SvgPathDiffViewer from "@/components/rmos/SvgPathDiffViewer.vue";
 import SvgPreview from "@/components/rmos/SvgPreview.vue";
+import BulkRejectModal from "@/components/rmos/BulkRejectModal.vue";
+
+import {
+  listAdvisoryVariants,
+  reviewAdvisoryVariant,
+  type AdvisoryVariantSummary,
+  type RejectReasonCode,
+} from "@/sdk/rmos/runs";
 
 const route = useRoute();
-const apiBase = "/api";
 // Run ID from route params
 const runId = computed(() => String(route.params.run_id ?? route.params.id ?? ""));
 
-// Variant list
-type VariantRow = {
-  advisory_id: string;
-  mime?: string | null;
-  filename?: string | null;
-  rating?: number | null;
-  notes?: string | null;
-  promoted?: boolean;
-};
-const variants = ref<VariantRow[]>([]);
+const variants = ref<AdvisoryVariantSummary[]>([]);
 const loading = ref(false);
 const error = ref<string | null>(null);
 // ... truncated ...
```

### Why Rejected

| Aspect | Existing File (473 lines) | Patch (~200 lines) |
|--------|---------------------------|-------------------|
| Status Filter | Full dropdown (ALL/NEW/REVIEWED/PROMOTED/REJECTED) | Checkbox only |
| Risk Filter | NEEDS_ATTENTION filter | None |
| Sort Options | 3 sort modes | None |
| Bulk Promote | Full BulkPromoteModal | None |
| Compare Mode | Full SVG diff viewer | None |
| Components | 8+ child components | 4 components |

**Verdict:** Patch removes 60% of the review workflow features.

### Correct Action Taken

Surgical migration in commit `caff9b0`:
- Changed import from `@/api/rmosRuns` to `@/sdk/rmos/runs`
- Updated `load()` to destructure `{ items }` from SDK response
- Preserved all 473 lines of existing functionality

---

## Summary

| Patch | Lines Existing | Lines in Patch | Features Lost | Action |
|-------|----------------|----------------|---------------|--------|
| ManufacturingCandidatesPanel | 891 | ~300 | Filters, bulk ops, inline editor | Already migrated |
| BulkRejectModal | 144 | 205 | Progress, self-contained API | Surgical migration |
| RunVariantsReviewPage | 473 | ~200 | Filters, sort, promote, compare | Surgical migration |

**Commits Applied Instead:**
- `e669400` - refactor(ui): migrate ManufacturingCandidatesPanel to H8.3 SDK
- `caff9b0` - refactor(ui): migrate BulkRejectModal and RunVariantsReviewPage to H8.3 SDK

---

## Lesson Learned

**CBSP21 Protocol Validation:**

When processing patch bundles, always:
1. Read the **existing file** to understand current state
2. Compare patch line count vs existing line count
3. Identify features that would be **removed** by the patch
4. If patch is a regression, perform **surgical migration** instead

This prevents well-intentioned "simplified" patches from destroying production features.

---

## Archive Metadata

| Field | Value |
|-------|-------|
| Archive Date | 2026-01-02 |
| Related Commits | `e669400`, `caff9b0`, `74b2ed5` |
| Protocol | CBSP21.md |
| Files Affected | 5 Vue components + 1 SDK file |
| Outcome | Surgical migrations applied, patches archived |

---

## Patch Bundle 4: RMOS Runs Typed SDK (runs.ts) — Replacement Version

### Provided Code

```typescript
// packages/client/src/sdk/rmos/runs.ts
// Proposed as "Typed SDK (H8.3 compliant)"

import { getRaw, postRaw } from "../core/apiFetchRaw";

/** Variant triage status */
export type VariantStatus =
  | "NEW"
  | "REVIEWED"
  | "PROMOTED"
  | "REJECTED";

/** Risk levels for operator decisions */
export type RiskLevel =
  | "GREEN"
  | "YELLOW"
  | "RED";

/** Rejection reason vocabulary */
export type RejectReasonCode =
  | "GEOMETRY_UNSAFE"
  | "TEXT_REQUIRES_OUTLINE"
  | "AESTHETIC"
  | "DUPLICATE"
  | "OTHER";

/** Advisory variant summary for review tables */
export type AdvisoryVariantSummary = {
  advisory_id: string;
  mime: string;
  filename: string;
  size_bytes: number;
  preview_blocked: boolean;
  preview_block_reason?: string | null;
  rating?: number | null;
  notes?: string | null;
  promoted: boolean;
  status: VariantStatus;
  risk_level: RiskLevel;
  created_at_utc?: string | null;
  updated_at_utc?: string | null;
  rejected: boolean;
  rejection_reason?: string | null;
  rejection_reason_code?: RejectReasonCode | null;
  rejection_reason_detail?: string | null;
  rejection_operator_note?: string | null;
  rejected_at_utc?: string | null;
};

/** Manufacturing candidate */
export type ManufacturingCandidate = {
  candidate_id: string;
  advisory_id: string;
  status: "PROPOSED" | "ACCEPTED" | "REJECTED";
  label?: string | null;
  note?: string | null;
  created_at_utc: string;
  created_by?: string | null;
  updated_at_utc: string;
  updated_by?: string | null;
};

export async function listAdvisoryVariants(runId: string): Promise<{
  items: AdvisoryVariantSummary[];
  count: number;
  requestId: string;
}> { /* ... */ }

export async function rejectAdvisoryVariant(
  runId: string,
  advisoryId: string,
  payload: { reason_code: RejectReasonCode; reason_detail?: string; operator_note?: string; }
): Promise<{ requestId: string }> { /* ... */ }

export async function bulkRejectAdvisoryVariants(
  runId: string,
  advisoryIds: string[],
  payload: { reason_code: RejectReasonCode; reason_detail?: string; operator_note?: string; }
): Promise<{ requestId: string }> { /* ... */ }

export async function listManufacturingCandidates(runId: string): Promise<{
  items: ManufacturingCandidate[];
  count: number;
  requestId: string;
}> { /* ... */ }
```

### Why Rejected

| Aspect | Existing File (556 lines) | Patch (~150 lines) |
|--------|---------------------------|-------------------|
| Types | 20+ detailed types | 4 simplified types |
| Functions | 15+ helpers | 4 helpers |
| `listAdvisoryVariants()` | ✅ Already exists | Duplicate |
| `reviewAdvisoryVariant()` | ✅ General purpose | `rejectAdvisoryVariant()` (less flexible) |
| `promoteAdvisoryVariant()` | ✅ Exists | ❌ Would be lost |
| `decideManufacturingCandidate()` | ✅ Exists | ❌ Would be lost |
| Blob download functions | ✅ 4 helpers | ❌ Would be lost |
| Attachment functions | ✅ Exists | ❌ Would be lost |
| Run CRUD | ✅ `listRuns`, `getRun`, etc. | ❌ Would be lost |

**Verdict:** Patch would replace 556-line comprehensive SDK with 150-line subset, losing 400+ lines of production functionality.

### Correct Action Taken

Surgical extraction in commit `74b2ed5`:
- Added **only** the net-new `bulkReviewAdvisoryVariants()` function (+30 lines)
- Added `BulkReviewAdvisoryVariantsRequest` and `BulkReviewAdvisoryVariantsResponse` types
- Preserved all 556 existing lines

---

## Patch Bundle 5: RunVariantsReviewPage.vue (Filter UI Version)

### Provided Diff (Partial)

```diff
diff --git a/packages/client/src/views/Runs/RunVariantsReviewPage.vue b/packages/client/src/views/Runs/RunVariantsReviewPage.vue
index 3c1a9de..5b7b2aa 100644
--- a/packages/client/src/views/Runs/RunVariantsReviewPage.vue
+++ b/packages/client/src/views/Runs/RunVariantsReviewPage.vue
@@ -1,32 +1,156 @@
 <script setup lang="ts">
 import { computed, onMounted, ref, watch } from "vue";
 import { useRoute } from "vue-router";
 import VariantNotes from "@/components/rmos/VariantNotes.vue";
 import PromoteToManufacturingButton from "@/components/rmos/PromoteToManufacturingButton.vue";
 import ManufacturingCandidatesPanel from "@/components/rmos/ManufacturingCandidatesPanel.vue";
 import PromptLineageViewer from "@/components/rmos/PromptLineageViewer.vue";
 import SvgPathDiffViewer from "@/components/rmos/SvgPathDiffViewer.vue";
 import SvgPreview from "@/components/rmos/SvgPreview.vue";

+// ✅ Canonical typed SDK (H8.3)
+import {
+  listAdvisoryVariants,
+  type AdvisoryVariantSummary,
+  type VariantStatus,
+  type RiskLevel,
+} from "@/sdk/rmos/runs";

// ... adds filter UI with q, showRejectedOnly, showPromotedOnly, statusFilter, riskFilter, sortMode ...
// ... removes 7 component imports: VariantStatusBadge, RejectVariantButton, UndoRejectButton, 
//     BulkRejectModal, BulkPromoteModal, ManufacturingCandidateList ...
```

### Why Rejected

| Aspect | Existing File (476 lines) | Patch (~250-300 lines) |
|--------|---------------------------|------------------------|
| Components | 11 imports | 7 imports (loses 4) |
| VariantStatusBadge | ✅ Dedicated component | ❌ Inline `<span>` badges |
| RejectVariantButton | ✅ Per-variant reject | ❌ Removed |
| UndoRejectButton | ✅ Undo rejection | ❌ Removed |
| BulkRejectModal | ✅ Full bulk reject flow | ❌ Removed |
| BulkPromoteModal | ✅ Full bulk promote flow | ❌ Removed |
| Bulk Selection | ✅ Checkboxes + Select All | ❌ Removed |
| Grid Layout | ✅ Responsive 2-column | Simple flexbox |
| Filter UI | ✅ Status + Risk + Sort | Similar but simpler |

**Verdict:** Patch removes bulk operations infrastructure, reject/undo buttons, and specialized components. Would regress ~200 lines of production UX.

### Correct Action Taken

No changes needed — the existing `RunVariantsReviewPage.vue` (476 lines) already:
- Uses `listAdvisoryVariants` from `@/sdk/rmos/runs`
- Has all the proposed filter UI PLUS more
- Has full bulk operations and reject/undo flows

---

## Updated Summary

| Patch | Lines Existing | Lines in Patch | Features Lost | Action |
|-------|----------------|----------------|---------------|--------|
| ManufacturingCandidatesPanel | 891 | ~300 | Filters, bulk ops, inline editor | Already migrated |
| BulkRejectModal | 144 | 205 | Progress, self-contained API | Surgical migration |
| RunVariantsReviewPage (v1) | 473 | ~200 | Filters, sort, promote, compare | Surgical migration |
| **runs.ts SDK** | **556** | **~150** | **11 helpers, 16 types, blob/attachment functions** | **Surgical extraction** |
| **RunVariantsReviewPage (v2)** | **476** | **~250** | **Bulk ops, reject/undo, badges** | **No changes needed** |

**Additional Commit Applied:**
- `74b2ed5` - feat(sdk): add bulkReviewAdvisoryVariants() to RMOS runs SDK
