<script setup lang="ts">
/**
 * ManufacturingCandidatesSimple.vue
 * 
 * Ultra-minimal candidate list. Just: ID + decision buttons.
 */
import { ref, computed, onMounted, watch } from "vue";
import {
  listManufacturingCandidates,
  decideManufacturingCandidate,
  type ManufacturingCandidate,
  type RiskLevel,
} from "@/sdk/rmos/runs";

const props = defineProps<{
  runId: string;
}>();

const loading = ref(false);
const error = ref<string | null>(null);
const candidates = ref<ManufacturingCandidate[]>([]);
const deciding = ref<string | null>(null);

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem("LTB_JWT") || "";
  const role = localStorage.getItem("LTB_USER_ROLE") || "";
  const uid = localStorage.getItem("LTB_USER_ID") || "";
  const h: Record<string, string> = {};
  if (token) {
    h["Authorization"] = \;
  } else {
    h["x-user-role"] = role || "operator";
    h["x-user-id"] = uid || "dev-user";
  }
  return h;
}

const summary = computed(() => {
  const g = candidates.value.filter(c => c.decision === 'GREEN').length;
  const y = candidates.value.filter(c => c.decision === 'YELLOW').length;
  const r = candidates.value.filter(c => c.decision === 'RED').length;
  const u = candidates.value.filter(c => !c.decision).length;
  return { total: candidates.value.length, green: g, yellow: y, red: r, undecided: u };
});

const allDecided = computed(() => summary.value.undecided === 0);

async function load() {
  if (!props.runId) return;
  loading.value = true;
  error.value = null;
  try {
    const res = await listManufacturingCandidates(props.runId, { headers: authHeaders() });
    candidates.value = res.items ?? [];
  } catch (e: any) {
    error.value = e?.message ?? String(e);
  } finally {
    loading.value = false;
  }
}

async function decide(c: ManufacturingCandidate, decision: RiskLevel) {
  deciding.value = c.candidate_id;
  error.value = null;
  try {
    const res = await decideManufacturingCandidate(props.runId, c.candidate_id, {
      decision,
      note: null,
      decided_by: "operator",
    }, { headers: authHeaders() });
    // Update local state
    const idx = candidates.value.findIndex(x => x.candidate_id === c.candidate_id);
    if (idx !== -1) {
      candidates.value[idx] = { ...candidates.value[idx], decision: res.decision as any };
    }
  } catch (e: any) {
    error.value = e?.message ?? String(e);
  } finally {
    deciding.value = null;
  }
}

onMounted(load);
watch(() => props.runId, load);
</script>

<template>
  <div class="simple-candidates">
    <div class="header">
      <h3>Manufacturing Candidates</h3>
      <button class="btn-refresh" :disabled="loading" @click="load">
        {{ loading ? '...' : '↻' }}
      </button>
    </div>

    <div v-if="error" class="error">{{ error }}</div>

    <div v-if="!loading && candidates.length > 0" class="summary">
      <span class="badge total">{{ summary.total }}</span>
      <span class="badge green">{{ summary.green }} ✓</span>
      <span class="badge yellow">{{ summary.yellow }} ⚠</span>
      <span class="badge red">{{ summary.red }} ✗</span>
      <span v-if="summary.undecided > 0" class="badge undecided">{{ summary.undecided }} pending</span>
      <span v-if="allDecided" class="ready">✓ Ready to export</span>
    </div>

    <div v-if="loading" class="muted">Loading...</div>
    <div v-else-if="candidates.length === 0" class="muted">No candidates yet.</div>

    <div v-else class="list">
      <div 
        v-for="c in candidates" 
        :key="c.candidate_id"
        :class="['row', c.decision?.toLowerCase()]"
      >
        <span class="id">{{ c.candidate_id.slice(0, 12) }}</span>
        
        <span class="status">
          {{ c.decision || 'PENDING' }}
        </span>

        <div class="actions">
          <button 
            class="btn green" 
            :disabled="deciding === c.candidate_id || c.decision === 'GREEN'"
            @click="decide(c, 'GREEN')"
          >✓</button>
          <button 
            class="btn yellow"
            :disabled="deciding === c.candidate_id || c.decision === 'YELLOW'"
            @click="decide(c, 'YELLOW')"
          >⚠</button>
          <button 
            class="btn red"
            :disabled="deciding === c.candidate_id || c.decision === 'RED'"
            @click="decide(c, 'RED')"
          >✗</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.simple-candidates {
  border: 1px solid #ddd;
  border-radius: 12px;
  padding: 16px;
  background: #fff;
}

.header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.header h3 {
  margin: 0;
  font-size: 1rem;
  flex: 1;
}

.btn-refresh {
  width: 32px;
  height: 32px;
  border: 1px solid #ccc;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-size: 1.1rem;
}

.error {
  background: #f8d7da;
  color: #721c24;
  padding: 8px 12px;
  border-radius: 6px;
  margin-bottom: 12px;
  font-size: 0.85rem;
}

.summary {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
}

.badge.total { background: #e9ecef; color: #495057; }
.badge.green { background: #d4edda; color: #155724; }
.badge.yellow { background: #fff3cd; color: #856404; }
.badge.red { background: #f8d7da; color: #721c24; }
.badge.undecided { background: #e2e3e5; color: #383d41; }

.ready {
  color: #28a745;
  font-weight: 600;
  font-size: 0.85rem;
}

.muted {
  color: #888;
  font-size: 0.9rem;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border: 1px solid #eee;
  border-radius: 8px;
  background: #fafafa;
}

.row.green { border-left: 4px solid #28a745; background: #f8fff8; }
.row.yellow { border-left: 4px solid #ffc107; background: #fffef8; }
.row.red { border-left: 4px solid #dc3545; background: #fff8f8; }

.id {
  font-family: monospace;
  font-size: 0.85rem;
  color: #666;
  min-width: 100px;
}

.status {
  font-size: 0.8rem;
  font-weight: 600;
  min-width: 80px;
}

.actions {
  margin-left: auto;
  display: flex;
  gap: 6px;
}

.btn {
  width: 36px;
  height: 36px;
  border: 2px solid;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: bold;
  transition: all 0.15s;
}

.btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn.green {
  border-color: #28a745;
  background: #fff;
  color: #28a745;
}
.btn.green:hover:not(:disabled) {
  background: #28a745;
  color: #fff;
}

.btn.yellow {
  border-color: #ffc107;
  background: #fff;
  color: #856404;
}
.btn.yellow:hover:not(:disabled) {
  background: #ffc107;
  color: #000;
}

.btn.red {
  border-color: #dc3545;
  background: #fff;
  color: #dc3545;
}
.btn.red:hover:not(:disabled) {
  background: #dc3545;
  color: #fff;
}
</style>
