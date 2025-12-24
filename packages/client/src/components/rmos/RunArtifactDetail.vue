<script setup lang="ts">
/**
 * RunArtifactDetail.vue
 *
 * Detail panel for a selected run artifact.
 * Includes:
 * - Download JSON button
 * - Diff with last selected button
 * - Set as A (pins A in URL for diff page)
 */
import { computed } from "vue";
import { useRouter } from "vue-router";
import { downloadRun, type RunArtifactDetail } from "@/api/rmosRuns";
import { useRmosRunsStore } from "@/stores/rmosRunsStore";
import AdvisoryBlobBrowser from "@/components/rmos/AdvisoryBlobBrowser.vue";

const props = defineProps<{
  artifact: RunArtifactDetail;
}>();

const router = useRouter();
const store = useRmosRunsStore();

const canDiff = computed(
  () => !!store.lastSelectedRunId && store.lastSelectedRunId !== props.artifact.run_id
);

function handleDownload() {
  downloadRun(props.artifact.run_id);
}

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

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}
</script>

<template>
  <aside class="run-detail">
    <!-- Header with Actions -->
    <div class="head">
      <div class="title-area">
        <h3>Run {{ artifact.run_id.slice(0, 16) }}…</h3>
        <div class="meta">
          <span><strong>Status:</strong> {{ artifact.status }}</span>
          <span><strong>Event:</strong> {{ artifact.event_type }}</span>
          <span><strong>Tool:</strong> {{ artifact.tool_id || "—" }}</span>
        </div>
      </div>

      <div class="actions">
        <button class="btn" @click="handleDownload" title="Download run as JSON">
          Download JSON
        </button>
        <button class="btn" @click="setAsA" title="Set as run A for comparison">
          Set as A
        </button>
        <button
          class="btn btn-primary"
          @click="diffWithLastSelected"
          :disabled="!canDiff"
          :title="canDiff ? 'Compare with last selected run' : 'Select another run first'"
        >
          Diff with last selected
        </button>
      </div>
    </div>

    <!-- Run Info -->
    <section class="info-section">
      <h4>Run Info</h4>
      <div class="info-grid">
        <div><strong>Created:</strong> {{ formatDate(artifact.created_at_utc) }}</div>
        <div><strong>Mode:</strong> {{ artifact.workflow_mode || "—" }}</div>
        <div><strong>Machine:</strong> {{ artifact.machine_id || "—" }}</div>
        <div><strong>Material:</strong> {{ artifact.material_id || "—" }}</div>
        <div><strong>Session:</strong> {{ artifact.workflow_session_id?.slice(0, 12) || "—" }}</div>
        <div><strong>Parent:</strong> {{ artifact.parent_run_id?.slice(0, 12) || "—" }}</div>
      </div>
    </section>

    <!-- Hashes -->
    <section class="info-section">
      <h4>Hashes</h4>
      <div class="hash-list">
        <div v-if="artifact.request_hash">
          <strong>Request:</strong>
          <code>{{ artifact.request_hash.slice(0, 16) }}…</code>
        </div>
        <div v-if="artifact.toolpaths_hash">
          <strong>Toolpaths:</strong>
          <code>{{ artifact.toolpaths_hash.slice(0, 16) }}…</code>
        </div>
        <div v-if="artifact.gcode_hash">
          <strong>G-code:</strong>
          <code>{{ artifact.gcode_hash.slice(0, 16) }}…</code>
        </div>
        <div v-if="artifact.geometry_hash">
          <strong>Geometry:</strong>
          <code>{{ artifact.geometry_hash.slice(0, 16) }}…</code>
        </div>
        <div v-if="artifact.config_fingerprint">
          <strong>Config:</strong>
          <code>{{ artifact.config_fingerprint.slice(0, 16) }}…</code>
        </div>
      </div>
    </section>

    <!-- Feasibility -->
    <section v-if="artifact.feasibility" class="info-section">
      <h4>Feasibility</h4>
      <pre class="code-block">{{ JSON.stringify(artifact.feasibility, null, 2) }}</pre>
    </section>

    <!-- Drift -->
    <section v-if="artifact.drift_detected" class="info-section drift-warning">
      <h4>⚠️ Drift Detected</h4>
      <p>{{ artifact.drift_summary || "Configuration drift detected from parent run." }}</p>
    </section>

    <!-- Gate Decision -->
    <section v-if="artifact.gate_decision" class="info-section">
      <h4>Gate Decision</h4>
      <div class="gate-badge" :class="artifact.gate_decision.toLowerCase()">
        {{ artifact.gate_decision }}
      </div>
    </section>

    <!-- Attachments -->
    <section v-if="artifact.attachments?.length" class="info-section">
      <h4>Attachments ({{ artifact.attachments.length }})</h4>
      <ul class="attachment-list">
        <li v-for="att in artifact.attachments" :key="att.sha256">
          <span class="att-kind">{{ att.kind }}</span>
          <span class="att-name">{{ att.filename }}</span>
          <span class="att-size">{{ (att.size_bytes / 1024).toFixed(1) }} KB</span>
        </li>
      </ul>
    </section>

    <!-- Advisory Blobs -->
    <section class="info-section">
      <AdvisoryBlobBrowser :runId="artifact.run_id" apiBase="/api" />
    </section>

    <!-- Notes / Errors -->
    <section v-if="artifact.notes" class="info-section">
      <h4>Notes</h4>
      <p>{{ artifact.notes }}</p>
    </section>

    <section v-if="artifact.errors?.length" class="info-section error-section">
      <h4>Errors</h4>
      <ul>
        <li v-for="(err, i) in artifact.errors" :key="i">{{ err }}</li>
      </ul>
    </section>
  </aside>
</template>

<style scoped>
.run-detail {
  padding: 1rem;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  background: #fff;
}

.head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #eee;
}

.title-area h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
  font-family: monospace;
}

.meta {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  color: #666;
  font-size: 0.85rem;
}

.actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.btn {
  padding: 0.45rem 0.8rem;
  font-size: 0.85rem;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
  white-space: nowrap;
}

.btn:hover:not(:disabled) {
  background: #e9ecef;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: #0066cc;
  border-color: #0066cc;
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background: #0052a3;
}

.info-section {
  margin-bottom: 1rem;
}

.info-section h4 {
  margin: 0 0 0.5rem 0;
  font-size: 0.9rem;
  color: #495057;
  border-bottom: 1px solid #eee;
  padding-bottom: 0.25rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 0.5rem;
  font-size: 0.85rem;
}

.hash-list {
  font-size: 0.85rem;
}

.hash-list div {
  margin-bottom: 0.25rem;
}

.hash-list code {
  background: #f4f4f4;
  padding: 0.15rem 0.4rem;
  border-radius: 3px;
  font-size: 0.8rem;
}

.code-block {
  background: #f8f9fa;
  padding: 0.75rem;
  border-radius: 6px;
  overflow: auto;
  font-size: 0.8rem;
  max-height: 200px;
}

.drift-warning {
  background: #fff3cd;
  padding: 0.75rem;
  border-radius: 6px;
  border: 1px solid #ffc107;
}

.drift-warning h4 {
  border-bottom: none;
  color: #856404;
}

.gate-badge {
  display: inline-block;
  padding: 0.3rem 0.75rem;
  border-radius: 4px;
  font-weight: 600;
  font-size: 0.85rem;
}

.gate-badge.approved {
  background: #d4edda;
  color: #155724;
}

.gate-badge.blocked {
  background: #f8d7da;
  color: #721c24;
}

.gate-badge.pending {
  background: #fff3cd;
  color: #856404;
}

.attachment-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.attachment-list li {
  display: flex;
  gap: 0.75rem;
  padding: 0.35rem 0;
  border-bottom: 1px solid #eee;
  font-size: 0.85rem;
}

.att-kind {
  background: #e9ecef;
  padding: 0.1rem 0.4rem;
  border-radius: 3px;
  font-size: 0.75rem;
  text-transform: uppercase;
}

.att-name {
  flex: 1;
  font-family: monospace;
}

.att-size {
  color: #6c757d;
}

.error-section {
  background: #f8d7da;
  padding: 0.75rem;
  border-radius: 6px;
}

.error-section h4 {
  color: #721c24;
  border-bottom-color: #f5c6cb;
}

.error-section ul {
  margin: 0;
  padding-left: 1.25rem;
  color: #721c24;
}
</style>
