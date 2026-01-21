<script setup lang="ts">
/**
 * AiImageGalleryRmos
 * Product surface: Attach → Review → Promote (RMOS spine)
 *
 * Canonical endpoints (via SDKs):
 * - Attach: POST /api/rmos/runs/{run_id}/advisory/attach  (visionApi.attachAdvisoryToRun)
 * - Review: POST /api/rmos/runs/{run_id}/advisory/{advisory_id}/review (runs.ts.reviewAdvisoryVariant)
 * - Promote: POST /api/rmos/runs/{run_id}/advisory/{advisory_id}/promote (runs.ts.promoteAdvisoryVariant)
 */
import { computed, ref } from "vue";
import type { VisionAsset } from "./api/visionApi";
import { attachAdvisoryToRun } from "./api/visionApi";
import { reviewAdvisoryVariant, promoteAdvisoryVariant, type RejectReasonCode, type VariantStatus } from "@/sdk/rmos/runs";

const props = defineProps<{
  assets: VisionAsset[];
  /**
   * The RMOS run id to bind advisories to.
   * (This gallery is intentionally "product-only": it does not create runs.)
   */
  runId: string;
}>();

const emit = defineEmits<{
  (e: "attached", payload: { runId: string; advisoryId: string }): void;
  (e: "reviewed", payload: { runId: string; advisoryId: string }): void;
  (e: "promoted", payload: { runId: string; advisoryId: string }): void;
  (e: "error", message: string): void;
}>();

// Per-asset UI state
const busy = ref<Record<string, { attach?: boolean; review?: boolean; promote?: boolean }>>({});
function _setBusy(sha: string, patch: Partial<{ attach: boolean; review: boolean; promote: boolean }>) {
  busy.value = { ...busy.value, [sha]: { ...(busy.value[sha] || {}), ...patch } };
}
function _isBusy(sha: string) {
  const b = busy.value[sha] || {};
  return !!(b.attach || b.review || b.promote);
}

const items = computed(() => props.assets ?? []);

function _guardRunId(): boolean {
  if (!props.runId || !props.runId.trim()) {
    emit("error", "No run selected. Provide runId to AiImageGalleryRmos.");
    return false;
  }
  return true;
}

// -----------------------------------------------------------------------------
// Attach → Review → Promote actions (high-signal, minimal UI)
// -----------------------------------------------------------------------------
async function attachAsset(a: VisionAsset) {
  if (!_guardRunId()) return;
  if (!a?.sha256) {
    emit("error", "Asset missing sha256; cannot attach.");
    return;
  }
  _setBusy(a.sha256, { attach: true });
  try {
    const res = await attachAdvisoryToRun(props.runId, {
      advisory_id: a.sha256,
      kind: "advisory",
    });
    const advisoryId = (res as any)?.advisory_id ?? a.sha256;
    emit("attached", { runId: props.runId, advisoryId });
  } catch (e: any) {
    emit("error", e?.message ?? "Attach failed");
  } finally {
    _setBusy(a.sha256, { attach: false });
  }
}

async function reviewAsset(a: VisionAsset) {
  if (!_guardRunId()) return;
  if (!a?.sha256) {
    emit("error", "Asset missing sha256; cannot review.");
    return;
  }
  _setBusy(a.sha256, { review: true });
  try {
    // Minimal operational review: allow quick rating + notes + optional reject
    const ratingRaw = window.prompt("Rating 1–5 (blank to skip):", "");
    const rating = ratingRaw && ratingRaw.trim() ? Math.max(1, Math.min(5, Number(ratingRaw))) : null;
    const notes = window.prompt("Operator notes (optional):", "") ?? null;

    const rejectedRaw = window.prompt("Reject? type YES to reject (blank = keep):", "");
    const rejected = (rejectedRaw ?? "").trim().toUpperCase() === "YES";

    let rejection_reason_code: RejectReasonCode | null = null;
    let rejection_reason_detail: string | null = null;
    let rejection_operator_note: string | null = null;
    let status: VariantStatus | null = "REVIEWED";

    if (rejected) {
      // Keep reason vocabulary tight; free-text goes to *_detail / *_note.
      const code = (window.prompt(
        "Reject reason code (GEOMETRY_UNSAFE | TEXT_REQUIRES_OUTLINE | AESTHETIC | DUPLICATE | OTHER):",
        "OTHER"
      ) ?? "OTHER") as RejectReasonCode;
      rejection_reason_code = code;
      rejection_reason_detail = window.prompt("Reject detail (optional):", "") ?? null;
      rejection_operator_note = window.prompt("Reject operator note (optional):", "") ?? null;
      status = "REJECTED";
    }

    await reviewAdvisoryVariant(props.runId, a.sha256, {
      rating,
      notes,
      rejected,
      rejection_reason_code,
      rejection_reason_detail,
      rejection_operator_note,
      status,
    } as any);

    emit("reviewed", { runId: props.runId, advisoryId: a.sha256 });
  } catch (e: any) {
    emit("error", e?.message ?? "Review failed");
  } finally {
    _setBusy(a.sha256, { review: false });
  }
}

async function promoteAsset(a: VisionAsset) {
  if (!_guardRunId()) return;
  if (!a?.sha256) {
    emit("error", "Asset missing sha256; cannot promote.");
    return;
  }
  _setBusy(a.sha256, { promote: true });
  try {
    await promoteAdvisoryVariant(props.runId, a.sha256);
    emit("promoted", { runId: props.runId, advisoryId: a.sha256 });
  } catch (e: any) {
    emit("error", e?.message ?? "Promote failed");
  } finally {
    _setBusy(a.sha256, { promote: false });
  }
}
</script>

<template>
  <div class="gallery">
    <div
      v-for="a in items"
      :key="a.sha256"
      class="card"
    >
      <img
        v-if="a.url"
        :src="a.url"
        class="thumb"
      >
      <div class="meta">
        <div class="mono">
          {{ a.sha256 }}
        </div>
        <div class="small muted">
          {{ a.revised_prompt || (a as any).prompt }}
        </div>
      </div>

      <div class="actions">
        <button
          class="btn small"
          type="button"
          :disabled="_isBusy(a.sha256)"
          @click="attachAsset(a)"
        >
          Attach
        </button>
        <button
          class="btn small"
          type="button"
          :disabled="_isBusy(a.sha256)"
          @click="reviewAsset(a)"
        >
          Review
        </button>
        <button
          class="btn small primary"
          type="button"
          :disabled="_isBusy(a.sha256)"
          @click="promoteAsset(a)"
        >
          Promote
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.gallery {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
}
.card {
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 16px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.thumb {
  width: 100%;
  border-radius: 12px;
  object-fit: cover;
  aspect-ratio: 1 / 1;
}
.meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.actions {
  display: flex;
  gap: 8px;
  margin-top: 6px;
}
.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 12px;
  word-break: break-all;
}
.small {
  font-size: 12px;
}
.muted {
  opacity: 0.72;
}
.btn {
  padding: 6px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-size: 12px;
}
.btn:hover:not(:disabled) {
  background: #f5f5f5;
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn.primary {
  background: #3b82f6;
  color: #fff;
  border-color: #3b82f6;
}
.btn.primary:hover:not(:disabled) {
  background: #2563eb;
}
.btn.small {
  padding: 4px 8px;
  font-size: 11px;
}
</style>
