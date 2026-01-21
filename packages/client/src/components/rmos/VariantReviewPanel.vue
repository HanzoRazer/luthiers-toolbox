<script setup lang="ts">
/**
 * VariantReviewPanel.vue
 *
 * Panel for reviewing, rating, and promoting advisory variants.
 * Integrates with the /api/rmos/runs/{run_id}/advisory/variants API.
 */
import { computed, onMounted, ref, watch } from "vue";
import StarRating from "@/components/rmos/StarRating.vue";
import SvgPreview from "@/components/rmos/SvgPreview.vue";

type Variant = {
  advisory_id: string;
  mime: string;
  filename: string;
  size_bytes: number;
  preview_blocked: boolean;
  preview_block_reason?: string | null;
  rating?: number | null;
  notes?: string | null;
  promoted: boolean;
};

const props = defineProps<{
  runId: string;
  apiBase?: string;
}>();

const apiBase = computed(() => props.apiBase ?? "/api");

const loading = ref(false);
const error = ref<string | null>(null);
const items = ref<Variant[]>([]);
const saving = ref<Record<string, boolean>>({});
const promoting = ref<Record<string, boolean>>({});

function roleHeaders(): Record<string, string> {
  // Minimal RBAC wiring: send role if stored in localStorage
  const role = localStorage.getItem("LTB_USER_ROLE") || "";
  const uid = localStorage.getItem("LTB_USER_ID") || "";
  const h: Record<string, string> = { "Content-Type": "application/json" };
  if (role) h["x-user-role"] = role;
  if (uid) h["x-user-id"] = uid;
  return h;
}

async function refresh() {
  if (!props.runId) return;
  loading.value = true;
  error.value = null;
  try {
    const res = await fetch(`${apiBase.value}/rmos/runs/${encodeURIComponent(props.runId)}/advisory/variants`);
    if (!res.ok) throw new Error(`Load variants failed (${res.status})`);
    const data = await res.json();
    items.value = Array.isArray(data?.items) ? data.items : [];
  } catch (e: any) {
    error.value = e?.message ?? String(e);
    items.value = [];
  } finally {
    loading.value = false;
  }
}

async function saveReview(v: Variant) {
  saving.value[v.advisory_id] = true;
  error.value = null;
  try {
    const res = await fetch(
      `${apiBase.value}/rmos/runs/${encodeURIComponent(props.runId)}/advisory/${encodeURIComponent(v.advisory_id)}/review`,
      {
        method: "POST",
        headers: roleHeaders(),
        body: JSON.stringify({ rating: v.rating ?? null, notes: v.notes ?? null }),
      }
    );
    if (!res.ok) throw new Error(`Save failed (${res.status})`);
  } catch (e: any) {
    error.value = e?.message ?? String(e);
  } finally {
    saving.value[v.advisory_id] = false;
  }
}

async function promote(v: Variant) {
  promoting.value[v.advisory_id] = true;
  error.value = null;
  try {
    const res = await fetch(
      `${apiBase.value}/rmos/runs/${encodeURIComponent(props.runId)}/advisory/${encodeURIComponent(v.advisory_id)}/promote`,
      {
        method: "POST",
        headers: roleHeaders(),
        body: JSON.stringify({ label: null, note: v.notes ?? null }),
      }
    );
    if (res.status === 403) throw new Error("Promotion forbidden (role required: admin/operator/engineer)");
    if (res.status === 409) throw new Error("Already promoted");
    if (!res.ok) throw new Error(`Promote failed (${res.status})`);
    const out = await res.json();
    if (out?.decision === "BLOCK") {
      throw new Error(`Promotion blocked: ${out?.reason ?? "policy"}`);
    }
    await refresh();
  } catch (e: any) {
    error.value = e?.message ?? String(e);
  } finally {
    promoting.value[v.advisory_id] = false;
  }
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  return `${Math.round(bytes / 1024)} KB`;
}

onMounted(refresh);
watch(() => props.runId, () => refresh());
</script>

<template>
  <div class="variant-review-panel">
    <div class="panel-header">
      <div>
        <h3 class="title">
          Variant Review
        </h3>
        <p class="subtitle">
          Rate, note, and promote advisory variants for this run.
        </p>
      </div>
      <button
        class="btn btn-secondary"
        :disabled="loading"
        @click="refresh"
      >
        {{ loading ? "Loading..." : "Refresh" }}
      </button>
    </div>

    <div
      v-if="error"
      class="error-banner"
    >
      {{ error }}
      <button @click="error = null">
        &times;
      </button>
    </div>

    <div
      v-if="loading && !items.length"
      class="loading"
    >
      Loading variants...
    </div>
    <div
      v-else-if="!items.length"
      class="empty"
    >
      No advisory variants found for this run.
    </div>

    <div
      v-else
      class="variant-grid"
    >
      <div
        v-for="v in items"
        :key="v.advisory_id"
        class="variant-card"
      >
        <div class="card-header">
          <code class="advisory-id">{{ v.advisory_id.slice(0, 12) }}...</code>
          <span class="file-info">{{ v.filename }} - {{ formatSize(v.size_bytes) }}</span>
        </div>

        <!-- SVG Preview -->
        <SvgPreview
          v-if="v.mime === 'image/svg+xml'"
          :run-id="runId"
          :advisory-id="v.advisory_id"
          :api-base="apiBase"
        />
        <div
          v-else
          class="non-svg-blob"
        >
          <span class="subtle">Non-SVG blob: {{ v.mime }}</span>
        </div>

        <!-- Review Controls -->
        <div class="review-controls">
          <div class="rating-row">
            <label>Rating:</label>
            <StarRating v-model="v.rating" />
          </div>

          <textarea
            v-model="v.notes"
            class="notes-input"
            placeholder="Review notes..."
            rows="3"
          />

          <div class="action-row">
            <button
              class="btn"
              :disabled="!!saving[v.advisory_id]"
              @click="saveReview(v)"
            >
              {{ saving[v.advisory_id] ? "Saving..." : "Save Review" }}
            </button>

            <button
              class="btn btn-primary"
              :disabled="v.promoted || !!promoting[v.advisory_id]"
              @click="promote(v)"
            >
              {{ v.promoted ? "Promoted" : (promoting[v.advisory_id] ? "Promoting..." : "Promote") }}
            </button>
          </div>

          <div
            v-if="v.preview_blocked"
            class="preview-warning"
          >
            Preview blocked: {{ v.preview_block_reason }}
          </div>

          <div class="download-link">
            <a
              :href="`${apiBase}/rmos/runs/${encodeURIComponent(runId)}/advisory/blobs/${encodeURIComponent(v.advisory_id)}/download`"
              target="_blank"
              rel="noreferrer"
            >Download</a>
          </div>
        </div>
      </div>
    </div>

    <div class="panel-footer">
      <small class="subtle">
        Promotion requires role header: <code>x-user-role</code> = admin/operator/engineer.
        Set <code>LTB_USER_ROLE</code> in localStorage for testing.
      </small>
    </div>
  </div>
</template>

<style scoped>
.variant-review-panel {
  border: 1px solid #dee2e6;
  border-radius: 12px;
  background: #fff;
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 1rem;
  background: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
}

.title {
  margin: 0 0 0.25rem 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.subtitle {
  margin: 0;
  font-size: 0.85rem;
  color: #6c757d;
}

.error-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: #f8d7da;
  color: #721c24;
  border-bottom: 1px solid #f5c6cb;
}

.error-banner button {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  color: inherit;
}

.loading,
.empty {
  padding: 2rem;
  text-align: center;
  color: #6c757d;
}

.variant-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1rem;
  padding: 1rem;
}

.variant-card {
  border: 1px solid #dee2e6;
  border-radius: 10px;
  padding: 1rem;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.card-header {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.advisory-id {
  font-size: 0.8rem;
  background: #e9ecef;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
  display: inline-block;
}

.file-info {
  font-size: 0.8rem;
  color: #6c757d;
}

.non-svg-blob {
  border: 1px dashed #dee2e6;
  border-radius: 8px;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.02);
  text-align: center;
}

.review-controls {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.rating-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.rating-row label {
  font-size: 0.85rem;
  font-weight: 500;
}

.notes-input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 6px;
  font-size: 0.9rem;
  resize: vertical;
}

.notes-input:focus {
  outline: none;
  border-color: #0066cc;
  box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.15);
}

.action-row {
  display: flex;
  gap: 0.5rem;
}

.btn {
  padding: 0.4rem 0.75rem;
  font-size: 0.85rem;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
}

.btn:hover:not(:disabled) {
  background: #e9ecef;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  opacity: 0.85;
}

.btn-primary {
  background: #0066cc;
  border-color: #0066cc;
  color: #fff;
  font-weight: 500;
}

.btn-primary:hover:not(:disabled) {
  background: #0052a3;
}

.btn-primary:disabled {
  background: #28a745;
  border-color: #28a745;
}

.preview-warning {
  font-size: 0.8rem;
  color: #8a5a00;
  padding: 0.25rem 0.5rem;
  background: #fff3cd;
  border-radius: 4px;
}

.download-link {
  text-align: right;
}

.download-link a {
  font-size: 0.8rem;
  color: #0066cc;
}

.panel-footer {
  padding: 0.75rem 1rem;
  background: #f8f9fa;
  border-top: 1px solid #dee2e6;
}

.subtle {
  opacity: 0.7;
}

code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.85em;
  background: #f4f4f4;
  padding: 0.1rem 0.3rem;
  border-radius: 3px;
}
</style>
