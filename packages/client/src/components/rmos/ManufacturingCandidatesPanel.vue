<script setup lang="ts">
/**
 * ManufacturingCandidatesPanel.vue
 *
 * Panel for managing manufacturing candidates.
 * Allows operators to approve/reject promoted variants and export ZIPs.
 */
import { computed, onMounted, ref, watch } from "vue";
import SvgPreview from "@/components/rmos/SvgPreview.vue";

type Candidate = {
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

const props = defineProps<{
  runId: string;
  apiBase?: string;
}>();

const apiBase = computed(() => props.apiBase ?? "/api");
const loading = ref(false);
const error = ref<string | null>(null);
const items = ref<Candidate[]>([]);
const acting = ref<Record<string, boolean>>({});

function authHeaders(): Record<string, string> {
  // Support JWT Bearer from localStorage, or rely on cookies/session
  const token = localStorage.getItem("LTB_JWT") || "";
  // Legacy header support for dev mode
  const role = localStorage.getItem("LTB_USER_ROLE") || "";
  const uid = localStorage.getItem("LTB_USER_ID") || "";

  const h: Record<string, string> = { "Content-Type": "application/json" };
  if (token) {
    h["Authorization"] = `Bearer ${token}`;
  } else {
    // Fallback to header-based auth for dev
    if (role) h["x-user-role"] = role;
    if (uid) h["x-user-id"] = uid;
  }
  return h;
}

async function refresh() {
  if (!props.runId) return;
  loading.value = true;
  error.value = null;
  try {
    const res = await fetch(
      `${apiBase.value}/rmos/runs/${encodeURIComponent(props.runId)}/manufacturing/candidates`,
      {
        headers: authHeaders(),
        credentials: "include",
      }
    );
    if (!res.ok) throw new Error(`Load candidates failed (${res.status})`);
    const data = await res.json();
    items.value = Array.isArray(data?.items) ? data.items : [];
  } catch (e: any) {
    error.value = e?.message ?? String(e);
    items.value = [];
  } finally {
    loading.value = false;
  }
}

async function decide(c: Candidate, decision: "ACCEPT" | "REJECT") {
  acting.value[c.candidate_id] = true;
  error.value = null;
  try {
    const res = await fetch(
      `${apiBase.value}/rmos/runs/${encodeURIComponent(props.runId)}/manufacturing/candidates/${encodeURIComponent(
        c.candidate_id
      )}/decision`,
      {
        method: "POST",
        headers: authHeaders(),
        credentials: "include",
        body: JSON.stringify({ decision, note: c.note ?? null }),
      }
    );
    if (res.status === 401) throw new Error("Not authenticated");
    if (res.status === 403) throw new Error("Forbidden: requires role admin/operator");
    if (!res.ok) throw new Error(`Decision failed (${res.status})`);
    await refresh();
  } catch (e: any) {
    error.value = e?.message ?? String(e);
  } finally {
    acting.value[c.candidate_id] = false;
  }
}

function downloadUrl(c: Candidate): string {
  return `${apiBase.value}/rmos/runs/${encodeURIComponent(props.runId)}/manufacturing/candidates/${encodeURIComponent(
    c.candidate_id
  )}/download-zip`;
}

function statusClass(status: string): string {
  return status.toLowerCase();
}

onMounted(refresh);
watch(() => props.runId, () => refresh());
</script>

<template>
  <div class="manufacturing-panel">
    <div class="panel-header">
      <div>
        <h3 class="title">Manufacturing Candidates</h3>
        <p class="subtitle">Approve or reject promoted variants. Export ZIP for manufacturing.</p>
      </div>
      <button class="btn btn-secondary" @click="refresh" :disabled="loading">
        {{ loading ? "Loading..." : "Refresh" }}
      </button>
    </div>

    <div v-if="error" class="error-banner">
      {{ error }}
      <button @click="error = null">&times;</button>
    </div>

    <div v-if="loading && !items.length" class="loading">Loading candidates...</div>
    <div v-else-if="!items.length" class="empty">No manufacturing candidates yet.</div>

    <div v-else class="candidate-grid">
      <div v-for="c in items" :key="c.candidate_id" class="candidate-card">
        <div class="card-header">
          <code class="candidate-id">{{ c.candidate_id }}</code>
          <span class="status-pill" :class="statusClass(c.status)">{{ c.status }}</span>
        </div>

        <!-- SVG Preview -->
        <SvgPreview
          v-if="c.advisory_id"
          :runId="runId"
          :advisoryId="c.advisory_id"
          :apiBase="apiBase"
        />

        <div class="form-group">
          <input
            class="label-input"
            v-model="c.label"
            placeholder="Label (optional)"
            :disabled="c.status !== 'PROPOSED'"
          />
        </div>

        <div class="form-group">
          <textarea
            class="note-input"
            v-model="c.note"
            placeholder="Decision note (optional)"
            rows="2"
          ></textarea>
        </div>

        <div class="action-row">
          <button
            class="btn btn-accept"
            :disabled="acting[c.candidate_id] || c.status !== 'PROPOSED'"
            @click="decide(c, 'ACCEPT')"
          >
            {{ acting[c.candidate_id] ? "Working..." : "Accept" }}
          </button>
          <button
            class="btn btn-reject"
            :disabled="acting[c.candidate_id] || c.status !== 'PROPOSED'"
            @click="decide(c, 'REJECT')"
          >
            {{ acting[c.candidate_id] ? "Working..." : "Reject" }}
          </button>
          <a
            class="btn btn-link"
            :href="downloadUrl(c)"
            target="_blank"
            rel="noreferrer"
          >Download ZIP</a>
        </div>

        <div class="meta">
          <span class="subtle">advisory: </span>
          <code>{{ c.advisory_id.slice(0, 12) }}...</code>
          <br />
          <span class="subtle">updated: {{ c.updated_at_utc }}</span>
          <span v-if="c.updated_by" class="subtle"> by {{ c.updated_by }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.manufacturing-panel {
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

.candidate-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 1rem;
  padding: 1rem;
}

.candidate-card {
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
  justify-content: space-between;
  align-items: center;
}

.candidate-id {
  font-size: 0.8rem;
  background: #e9ecef;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
}

.status-pill {
  font-size: 0.75rem;
  padding: 0.2rem 0.5rem;
  border-radius: 999px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  text-transform: uppercase;
  font-weight: 500;
}

.status-pill.proposed {
  background: #fff3cd;
  color: #856404;
}

.status-pill.accepted {
  background: #d4edda;
  color: #155724;
  font-weight: 700;
}

.status-pill.rejected {
  background: #f8d7da;
  color: #721c24;
}

.form-group {
  width: 100%;
}

.label-input,
.note-input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 6px;
  font-size: 0.9rem;
}

.label-input:focus,
.note-input:focus {
  outline: none;
  border-color: #0066cc;
  box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.15);
}

.label-input:disabled,
.note-input:disabled {
  background: #f8f9fa;
  opacity: 0.7;
}

.action-row {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.btn {
  padding: 0.4rem 0.75rem;
  font-size: 0.85rem;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
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

.btn-accept {
  background: #28a745;
  border-color: #28a745;
  color: #fff;
  font-weight: 600;
}

.btn-accept:hover:not(:disabled) {
  background: #218838;
}

.btn-reject {
  background: #dc3545;
  border-color: #dc3545;
  color: #fff;
}

.btn-reject:hover:not(:disabled) {
  background: #c82333;
}

.btn-link {
  color: #0066cc;
}

.meta {
  font-size: 0.75rem;
  color: #6c757d;
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
