<script setup lang="ts">
/**
 * VariantReviewPanel.vue
 *
 * Panel for reviewing, rating, and promoting advisory variants.
 * Integrates with the /api/runs/{run_id}/advisory/variants API.
 */
import { computed, onMounted, ref, watch } from "vue";
import { VariantCard, type Variant } from "./variant-review";

const props = defineProps<{
  runId: string;
  apiBase?: string;
}>();

const apiBase = computed(() => props.apiBase ?? "/api/rmos");

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
    const res = await fetch(`${apiBase.value}/runs/${encodeURIComponent(props.runId)}/advisory/variants`);
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
      `${apiBase.value}/runs/${encodeURIComponent(props.runId)}/advisory/${encodeURIComponent(v.advisory_id)}/review`,
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
      `${apiBase.value}/runs/${encodeURIComponent(props.runId)}/advisory/${encodeURIComponent(v.advisory_id)}/promote`,
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
      <VariantCard
        v-for="v in items"
        :key="v.advisory_id"
        :variant="v"
        :run-id="runId"
        :api-base="apiBase"
        :saving="!!saving[v.advisory_id]"
        :promoting="!!promoting[v.advisory_id]"
        @save="saveReview(v)"
        @promote="promote(v)"
        @update:rating="v.rating = $event"
        @update:notes="v.notes = $event"
      />
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
