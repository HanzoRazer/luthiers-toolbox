<script setup lang="ts">
/**
 * RmosRunViewerView.vue
 *
 * Read-only viewer for a single Run Artifact.
 * Route: /rmos/runs/:id
 *
 * Displays:
 * - run_id, status, mode, tool_id, created_at
 * - decision (risk_level, warnings, block_reason)
 * - hashes (request, toolpaths, gcode, geometry, config)
 * - attachments list
 * - outputs summary
 */
import { ref, computed, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { fetchRun, downloadRun, type RunArtifactDetail } from "@/api/rmosRuns";

const route = useRoute();
const router = useRouter();

const run = ref<RunArtifactDetail | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);

const runId = computed(() => route.params.id as string);

async function loadRun() {
  if (!runId.value) return;
  loading.value = true;
  error.value = null;
  try {
    run.value = await fetchRun(runId.value);
  } catch (e: any) {
    error.value = e.message || "Failed to load run";
    run.value = null;
  } finally {
    loading.value = false;
  }
}

onMounted(loadRun);
watch(runId, loadRun);

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function handleDownload() {
  if (runId.value) {
    downloadRun(runId.value);
  }
}

function goToDiff() {
  router.push({ path: "/rmos/runs/diff", query: { a: runId.value } });
}

function goBack() {
  router.push("/rmos/runs");
}

async function downloadOperatorPack() {
  if (!runId.value) return;
  error.value = null;
  let url: string | null = null;
  try {
    const res = await fetch(`/api/rmos/runs_v2/${encodeURIComponent(runId.value)}/operator-pack`);
    if (!res.ok) {
      let msg = `HTTP ${res.status}`;
      try { const t = await res.text(); if (t) msg = t; } catch {}
      throw new Error(msg);
    }
    const blob = await res.blob();
    url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `operator_pack_${runId.value}.zip`;
    a.click();
  } catch (e: any) {
    error.value = String(e?.message || e);
  } finally {
    if (url) URL.revokeObjectURL(url);
  }
}

async function downloadAttachment(att: any) {
  if (!att?.sha256) return;
  error.value = null;
  let url: string | null = null;
  try {
    const res = await fetch(`/api/rmos/runs_v2/attachments/${encodeURIComponent(att.sha256)}`);
    if (!res.ok) {
      let msg = `HTTP ${res.status}`;
      try { const t = await res.text(); if (t) msg = t; } catch {}
      throw new Error(msg);
    }
    const blob = await res.blob();
    url = URL.createObjectURL(blob);
    const dl = document.createElement("a");
    dl.href = url;
    // Prefer original filename if present, else sha-based
    const safeName = (att.filename || `${att.sha256}`).replace(/[^\w.\-]+/g, "_");
    dl.download = safeName;
    dl.click();
  } catch (e: any) {
    error.value = String(e?.message || e);
  } finally {
    if (url) URL.revokeObjectURL(url);
  }
}
</script>

<template>
  <div class="run-viewer">
    <!-- Header -->
    <header class="viewer-header">
      <div class="header-left">
        <button class="btn btn-back" @click="goBack">
          &larr; Back to Runs
        </button>
        <h1>Run Viewer</h1>
      </div>
      <div class="header-actions" v-if="run">
        <button class="btn" @click="handleDownload">Download JSON</button>
        <button class="btn btn-success" @click="downloadOperatorPack" :disabled="loading">
          Operator Pack (.zip)
        </button>
        <button class="btn btn-primary" @click="goToDiff">Compare (Diff)</button>
      </div>
    </header>

    <!-- Loading State -->
    <div v-if="loading" class="state-loading">
      <div class="spinner"></div>
      <p>Loading run artifact...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="state-error">
      <h2>Error</h2>
      <p>{{ error }}</p>
      <button class="btn" @click="loadRun">Retry</button>
    </div>

    <!-- Run Details -->
    <div v-else-if="run" class="run-content">
      <!-- Run ID Banner -->
      <section class="id-banner">
        <code class="run-id">{{ run.run_id }}</code>
        <div class="status-badges">
          <span class="badge" :class="run.status?.toLowerCase()">{{ run.status }}</span>
          <span class="badge mode" v-if="run.workflow_mode">{{ run.workflow_mode }}</span>
        </div>
      </section>

      <!-- Gate Decision (Risk Level) -->
      <section v-if="run.gate_decision || run.feasibility" class="decision-section">
        <h2>Decision</h2>
        <div class="decision-grid">
          <div v-if="run.gate_decision" class="decision-item">
            <span class="label">Gate:</span>
            <span class="gate-badge" :class="run.gate_decision.toLowerCase()">
              {{ run.gate_decision }}
            </span>
          </div>
          <div v-if="run.feasibility?.risk_level" class="decision-item">
            <span class="label">Risk Level:</span>
            <span class="risk-badge" :class="run.feasibility.risk_level.toLowerCase()">
              {{ run.feasibility.risk_level }}
            </span>
          </div>
          <div v-if="run.feasibility?.warnings?.length" class="decision-item warnings">
            <span class="label">Warnings:</span>
            <ul>
              <li v-for="(w, i) in run.feasibility.warnings" :key="i">{{ w }}</li>
            </ul>
          </div>
          <div v-if="run.feasibility?.block_reason" class="decision-item block-reason">
            <span class="label">Block Reason:</span>
            <span class="block-text">{{ run.feasibility.block_reason }}</span>
          </div>
        </div>
      </section>

      <!-- Run Info -->
      <section class="info-section">
        <h2>Run Info</h2>
        <div class="info-grid">
          <div><strong>Created:</strong> {{ formatDate(run.created_at_utc) }}</div>
          <div><strong>Event Type:</strong> {{ run.event_type }}</div>
          <div><strong>Tool ID:</strong> {{ run.tool_id || "---" }}</div>
          <div><strong>Material ID:</strong> {{ run.material_id || "---" }}</div>
          <div><strong>Machine ID:</strong> {{ run.machine_id || "---" }}</div>
          <div><strong>Session:</strong> {{ run.workflow_session_id?.slice(0, 16) || "---" }}</div>
          <div><strong>Parent Run:</strong> {{ run.parent_run_id?.slice(0, 16) || "---" }}</div>
          <div><strong>Toolchain:</strong> {{ run.toolchain_id || "---" }}</div>
          <div><strong>Post Processor:</strong> {{ run.post_processor_id || "---" }}</div>
          <div><strong>Engine Version:</strong> {{ run.engine_version || "---" }}</div>
        </div>
      </section>

      <!-- Hashes -->
      <section class="info-section">
        <h2>Hashes</h2>
        <div class="hash-grid">
          <div v-if="run.request_hash">
            <strong>Request:</strong>
            <code>{{ run.request_hash }}</code>
          </div>
          <div v-if="run.toolpaths_hash">
            <strong>Toolpaths:</strong>
            <code>{{ run.toolpaths_hash }}</code>
          </div>
          <div v-if="run.gcode_hash">
            <strong>G-code:</strong>
            <code>{{ run.gcode_hash }}</code>
          </div>
          <div v-if="run.geometry_hash">
            <strong>Geometry:</strong>
            <code>{{ run.geometry_hash }}</code>
          </div>
          <div v-if="run.config_fingerprint">
            <strong>Config:</strong>
            <code>{{ run.config_fingerprint }}</code>
          </div>
          <div v-if="!run.request_hash && !run.toolpaths_hash && !run.gcode_hash && !run.geometry_hash && !run.config_fingerprint" class="empty-state">
            No hashes recorded
          </div>
        </div>
      </section>

      <!-- Drift Warning -->
      <section v-if="run.drift_detected" class="drift-section">
        <h2>Drift Detected</h2>
        <p>{{ run.drift_summary || "Configuration drift detected from parent run." }}</p>
      </section>

      <!-- Attachments -->
      <section class="info-section">
        <h2>Attachments ({{ run.attachments?.length || 0 }})</h2>
        <div v-if="run.attachments?.length" class="attachment-list">
          <div v-for="att in run.attachments" :key="att.sha256" class="attachment-item">
            <span class="att-kind">{{ att.kind }}</span>
            <span class="att-name">{{ att.filename }}</span>
            <span class="att-mime">{{ att.mime }}</span>
            <span class="att-size">{{ (att.size_bytes / 1024).toFixed(1) }} KB</span>
            <button class="btn btn-sm" @click="downloadAttachment(att)" :disabled="loading">
              Download
            </button>
          </div>
        </div>
        <div v-else class="empty-state">No attachments</div>
      </section>

      <!-- Feasibility Details -->
      <section v-if="run.feasibility" class="info-section">
        <h2>Feasibility</h2>
        <pre class="code-block">{{ JSON.stringify(run.feasibility, null, 2) }}</pre>
      </section>

      <!-- Notes -->
      <section v-if="run.notes" class="info-section">
        <h2>Notes</h2>
        <p class="notes-text">{{ run.notes }}</p>
      </section>

      <!-- Errors -->
      <section v-if="run.errors?.length" class="error-section">
        <h2>Errors</h2>
        <ul>
          <li v-for="(err, i) in run.errors" :key="i">{{ err }}</li>
        </ul>
      </section>
    </div>

    <!-- No Run State -->
    <div v-else class="state-empty">
      <p>No run ID provided</p>
      <button class="btn" @click="goBack">Go to Runs List</button>
    </div>
  </div>
</template>

<style scoped>
.run-viewer {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1.5rem 2rem;
}

.viewer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #dee2e6;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-left h1 {
  margin: 0;
  font-size: 1.5rem;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.btn {
  padding: 0.5rem 1rem;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
  font-size: 0.9rem;
}

.btn:hover {
  background: #f8f9fa;
}

.btn-back {
  color: #6c757d;
}

.btn-primary {
  background: #0066cc;
  border-color: #0066cc;
  color: #fff;
}

.btn-primary:hover {
  background: #0052a3;
}

.btn-success {
  background: #28a745;
  border-color: #28a745;
  color: #fff;
}

.btn-success:hover {
  background: #218838;
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
}

/* States */
.state-loading,
.state-error,
.state-empty {
  text-align: center;
  padding: 3rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #dee2e6;
  border-top-color: #0066cc;
  border-radius: 50%;
  margin: 0 auto 1rem;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.state-error {
  background: #f8d7da;
  border-radius: 8px;
  color: #721c24;
}

/* ID Banner */
.id-banner {
  background: #f8f9fa;
  padding: 1rem 1.5rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.run-id {
  font-size: 0.95rem;
  background: #e9ecef;
  padding: 0.4rem 0.8rem;
  border-radius: 4px;
  word-break: break-all;
}

.status-badges {
  display: flex;
  gap: 0.5rem;
}

.badge {
  padding: 0.3rem 0.75rem;
  border-radius: 4px;
  font-weight: 600;
  font-size: 0.85rem;
  text-transform: uppercase;
}

.badge.completed,
.badge.success {
  background: #d4edda;
  color: #155724;
}

.badge.pending,
.badge.in_progress {
  background: #fff3cd;
  color: #856404;
}

.badge.failed,
.badge.error {
  background: #f8d7da;
  color: #721c24;
}

.badge.mode {
  background: #e7f1ff;
  color: #004085;
}

/* Decision Section */
.decision-section {
  background: #fff;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 1rem 1.5rem;
  margin-bottom: 1.5rem;
}

.decision-section h2 {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
  color: #495057;
}

.decision-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  align-items: flex-start;
}

.decision-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.decision-item .label {
  font-weight: 600;
  color: #6c757d;
}

.gate-badge,
.risk-badge {
  padding: 0.3rem 0.75rem;
  border-radius: 4px;
  font-weight: 600;
  font-size: 0.85rem;
}

.gate-badge.approved,
.risk-badge.green {
  background: #d4edda;
  color: #155724;
}

.gate-badge.blocked,
.risk-badge.red {
  background: #f8d7da;
  color: #721c24;
}

.gate-badge.pending,
.risk-badge.yellow {
  background: #fff3cd;
  color: #856404;
}

.decision-item.warnings {
  flex-direction: column;
  align-items: flex-start;
}

.decision-item.warnings ul {
  margin: 0.25rem 0 0 1rem;
  padding: 0;
  color: #856404;
}

.decision-item.block-reason .block-text {
  color: #721c24;
  font-weight: 500;
}

/* Info Sections */
.info-section {
  background: #fff;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 1rem 1.5rem;
  margin-bottom: 1.5rem;
}

.info-section h2 {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
  color: #495057;
  border-bottom: 1px solid #eee;
  padding-bottom: 0.5rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 0.75rem;
  font-size: 0.9rem;
}

.hash-grid {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.hash-grid code {
  background: #f4f4f4;
  padding: 0.2rem 0.5rem;
  border-radius: 3px;
  font-size: 0.8rem;
  word-break: break-all;
}

.empty-state {
  color: #6c757d;
  font-style: italic;
}

/* Drift Section */
.drift-section {
  background: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 8px;
  padding: 1rem 1.5rem;
  margin-bottom: 1.5rem;
}

.drift-section h2 {
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
  color: #856404;
}

.drift-section p {
  margin: 0;
  color: #856404;
}

/* Attachments */
.attachment-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.attachment-item {
  display: flex;
  gap: 1rem;
  padding: 0.5rem;
  background: #f8f9fa;
  border-radius: 4px;
  font-size: 0.85rem;
  align-items: center;
}

.att-kind {
  background: #e9ecef;
  padding: 0.15rem 0.5rem;
  border-radius: 3px;
  font-size: 0.75rem;
  text-transform: uppercase;
  font-weight: 600;
}

.att-name {
  flex: 1;
  font-family: monospace;
}

.att-mime {
  color: #6c757d;
}

.att-size {
  color: #6c757d;
  white-space: nowrap;
}

/* Code Block */
.code-block {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 6px;
  overflow: auto;
  font-size: 0.8rem;
  max-height: 300px;
  margin: 0;
}

/* Notes */
.notes-text {
  margin: 0;
  line-height: 1.6;
}

/* Error Section */
.error-section {
  background: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 8px;
  padding: 1rem 1.5rem;
  margin-bottom: 1.5rem;
}

.error-section h2 {
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
  color: #721c24;
}

.error-section ul {
  margin: 0;
  padding-left: 1.25rem;
  color: #721c24;
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
  .viewer-header {
    border-bottom-color: #495057;
  }

  .header-left h1 {
    color: #f8f9fa;
  }

  .btn {
    background: #343a40;
    border-color: #495057;
    color: #f8f9fa;
  }

  .btn:hover {
    background: #495057;
  }

  .btn-primary {
    background: #0066cc;
    border-color: #0066cc;
  }

  .id-banner {
    background: #343a40;
  }

  .run-id {
    background: #495057;
    color: #f8f9fa;
  }

  .decision-section,
  .info-section {
    background: #343a40;
    border-color: #495057;
  }

  .decision-section h2,
  .info-section h2 {
    color: #adb5bd;
    border-bottom-color: #495057;
  }

  .info-grid {
    color: #f8f9fa;
  }

  .hash-grid code {
    background: #495057;
    color: #f8f9fa;
  }

  .code-block {
    background: #2d3748;
    color: #f8f9fa;
  }

  .attachment-item {
    background: #495057;
  }

  .att-kind {
    background: #6c757d;
  }
}
</style>
