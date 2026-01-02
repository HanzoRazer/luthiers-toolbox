<template>
  <div class="panel">
    <h2>RMOS Operation E2E Panel</h2>
    <p class="subtitle">Bundle 06: Minimal UI for testing Operation Lane endpoints</p>

    <div class="grid">
      <div class="left">
        <!-- Configuration -->
        <div class="card">
          <div class="row">
            <label>Operation</label>
            <select v-model="operation">
              <option value="saw_v1">Saw - v1</option>
              <option value="cam_roughing_v1">CAM Roughing - v1</option>
            </select>
          </div>

          <div class="row">
            <label>X-Request-Id (optional)</label>
            <input v-model="requestId" placeholder="leave blank to auto-generate" />
          </div>

          <div class="row">
            <label>cam_intent_v1 (JSON)</label>
            <textarea v-model="camIntentText" rows="10" spellcheck="false"></textarea>
          </div>

          <div class="row">
            <label>feasibility (JSON)</label>
            <textarea v-model="feasibilityText" rows="6" spellcheck="false"></textarea>
          </div>

          <div class="actions">
            <button :disabled="busy" @click="onPlan">Plan</button>
            <button :disabled="busy || !planRunId" @click="onExecute">Execute</button>
            <button :disabled="busy || !lastRunId" @click="onExport">Export ZIP</button>
          </div>

          <div class="status">
            <div v-if="busy">Working...</div>
            <div v-if="lastRequestId"><strong>X-Request-Id:</strong> <code>{{ lastRequestId }}</code></div>
            <div v-if="planRunId"><strong>Plan run_id:</strong> <code>{{ planRunId }}</code></div>
            <div v-if="executeRunId"><strong>Execute run_id:</strong> <code>{{ executeRunId }}</code></div>
            <div v-if="error" class="error"><strong>Error:</strong> {{ error }}</div>
          </div>
        </div>
      </div>

      <div class="right">
        <!-- Response -->
        <div class="card">
          <div class="title">Last Response</div>
          <pre class="pre" v-if="lastResponse">{{ lastResponse }}</pre>
          <div v-else class="empty">No response yet. Click Plan or Execute to test.</div>
        </div>
      </div>
    </div>

    <div class="card" v-if="history.length > 0">
      <div class="title">History</div>
      <div class="history-list">
        <div v-for="(h, i) in history" :key="i" class="history-item">
          <div class="history-header">
            <strong>{{ h.action }}</strong>
            <span class="timestamp">{{ h.timestamp }}</span>
          </div>
          <div class="history-meta">
            <code>{{ h.runId }}</code>
            <span v-if="h.status" class="badge" :class="statusClass(h.status)">{{ h.status }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { rmosOperations } from "@/sdk/rmos/operations";

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

type OperationType = "saw_v1" | "cam_roughing_v1";

const operation = ref<OperationType>("saw_v1");
const requestId = ref<string>("");

const camIntentText = ref<string>(
  JSON.stringify(
    {
      mode: "saw",
      tool: { tool_id: "blade_123" },
      params: { units: "inch", feed_ipm: 12, depth_in: 0.03 },
      job: { name: "e2e_test" },
    },
    null,
    2
  )
);

const feasibilityText = ref<string>(
  JSON.stringify({ risk_level: "GREEN", score: 85 }, null, 2)
);

const busy = ref(false);
const error = ref("");
const lastRequestId = ref("");
const planRunId = ref<string | null>(null);
const executeRunId = ref<string | null>(null);
const lastResponse = ref("");

const lastRunId = computed(() => executeRunId.value || planRunId.value);

type HistoryEntry = {
  action: string;
  runId: string;
  status?: string;
  timestamp: string;
};

const history = ref<HistoryEntry[]>([]);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function parseJsonOrThrow(label: string, text: string): unknown {
  try {
    return JSON.parse(text);
  } catch (e) {
    throw new Error(`${label} is not valid JSON`);
  }
}

function statusClass(status: string): string {
  if (status === "EXECUTED" || status === "OK") return "status-green";
  if (status === "PLANNED") return "status-blue";
  if (status === "BLOCKED") return "status-red";
  return "status-yellow";
}

function addHistory(action: string, runId: string, status?: string) {
  history.value.unshift({
    action,
    runId,
    status,
    timestamp: new Date().toISOString().split("T")[1].split(".")[0],
  });
  if (history.value.length > 10) {
    history.value = history.value.slice(0, 10);
  }
}

// ---------------------------------------------------------------------------
// Actions
// ---------------------------------------------------------------------------

async function onPlan() {
  busy.value = true;
  error.value = "";
  lastResponse.value = "";
  planRunId.value = null;
  executeRunId.value = null;

  try {
    const camIntent = parseJsonOrThrow("cam_intent_v1", camIntentText.value);
    const feasibility = parseJsonOrThrow("feasibility", feasibilityText.value);
    const rid = requestId.value.trim() || undefined;

    let result;
    if (operation.value === "saw_v1") {
      result = await rmosOperations.planSawV1(
        { cam_intent_v1: camIntent as Record<string, unknown>, feasibility: feasibility as any },
        { requestId: rid }
      );
    } else {
      result = await rmosOperations.planCamRoughingV1(
        { cam_intent_v1: camIntent as Record<string, unknown>, feasibility: feasibility as any },
        { requestId: rid }
      );
    }

    lastRequestId.value = rid || "auto-generated";
    planRunId.value = result.run_id;
    lastResponse.value = JSON.stringify(result, null, 2);
    addHistory(`Plan (${operation.value})`, result.run_id, result.status);
  } catch (e: any) {
    error.value = e.message ?? String(e);
    lastResponse.value = JSON.stringify({ error: e.message }, null, 2);
  } finally {
    busy.value = false;
  }
}

async function onExecute() {
  if (!planRunId.value) return;

  busy.value = true;
  error.value = "";
  lastResponse.value = "";
  executeRunId.value = null;

  try {
    const camIntent = parseJsonOrThrow("cam_intent_v1", camIntentText.value);
    const feasibility = parseJsonOrThrow("feasibility", feasibilityText.value);
    const rid = requestId.value.trim() || undefined;

    const request = {
      cam_intent_v1: camIntent as Record<string, unknown>,
      feasibility: feasibility as any,
      parent_plan_run_id: planRunId.value,
    };

    let result;
    if (operation.value === "saw_v1") {
      result = await rmosOperations.executeSawV1(request, { requestId: rid });
    } else {
      result = await rmosOperations.executeCamRoughingV1(request, { requestId: rid });
    }

    lastRequestId.value = rid || "auto-generated";
    executeRunId.value = result.run_id;
    lastResponse.value = JSON.stringify(result, null, 2);
    addHistory(`Execute (${operation.value})`, result.run_id, result.status);
  } catch (e: any) {
    error.value = e.message ?? String(e);
    lastResponse.value = JSON.stringify({ error: e.message }, null, 2);

    // Try to extract run_id from 409 response
    if (e.details?.run_id) {
      executeRunId.value = e.details.run_id;
      addHistory(`Execute BLOCKED (${operation.value})`, e.details.run_id, "BLOCKED");
    }
  } finally {
    busy.value = false;
  }
}

async function onExport() {
  const runId = lastRunId.value;
  if (!runId) return;

  busy.value = true;
  error.value = "";

  try {
    const rid = requestId.value.trim() || undefined;
    const { requestId: echoedRid } = await rmosOperations.downloadZip(runId, { requestId: rid });
    lastRequestId.value = echoedRid;
    addHistory("Export ZIP", runId);
  } catch (e: any) {
    error.value = e.message ?? String(e);
  } finally {
    busy.value = false;
  }
}
</script>

<style scoped>
.panel {
  display: grid;
  gap: 12px;
  max-width: 1200px;
}

.subtitle {
  opacity: 0.8;
  font-size: 12px;
  margin-top: -8px;
}

.grid {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 12px;
  align-items: start;
}

@media (max-width: 1000px) {
  .grid {
    grid-template-columns: 1fr;
  }
}

.card {
  border: 1px solid #ddd;
  border-radius: 12px;
  padding: 12px;
  display: grid;
  gap: 10px;
}

.row {
  display: grid;
  gap: 6px;
}

label {
  font-weight: 700;
}

textarea,
input,
select {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 8px;
  width: 100%;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono",
    "Courier New", monospace;
  font-size: 12px;
  box-sizing: border-box;
}

.actions {
  display: flex;
  gap: 10px;
}

button {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 8px 10px;
  cursor: pointer;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.status {
  display: grid;
  gap: 6px;
  font-size: 12px;
  opacity: 0.95;
}

.error {
  border: 1px solid #f1b3b3;
  border-radius: 10px;
  padding: 8px 10px;
  color: #c00;
}

.title {
  font-weight: 800;
}

.pre {
  margin: 0;
  padding: 10px;
  border: 1px solid #eee;
  border-radius: 10px;
  overflow: auto;
  font-size: 12px;
  max-height: 400px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono",
    "Courier New", monospace;
}

.empty {
  opacity: 0.8;
  font-size: 12px;
}

code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono",
    "Courier New", monospace;
  font-size: 12px;
}

.history-list {
  display: grid;
  gap: 8px;
  max-height: 200px;
  overflow: auto;
}

.history-item {
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 8px 10px;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.timestamp {
  opacity: 0.7;
  font-size: 11px;
}

.history-meta {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-top: 4px;
}

.badge {
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 10px;
  font-weight: 700;
}

.status-green {
  background: #d4edda;
  color: #155724;
}

.status-yellow {
  background: #fff3cd;
  color: #856404;
}

.status-red {
  background: #f8d7da;
  color: #721c24;
}

.status-blue {
  background: #cce5ff;
  color: #004085;
}
</style>
