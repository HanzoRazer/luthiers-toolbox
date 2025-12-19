<script setup lang="ts">
/**
 * RunDiffViewer.vue
 *
 * Side-by-side diff viewer for two run artifacts.
 * Reads run IDs from URL query params (?a=...&b=...).
 * Auto-reloads when query params change (no page refresh needed).
 */
import { ref, watch, computed } from "vue";
import { useRoute } from "vue-router";
import { fetchRun, fetchRunDiff, type RunArtifactDetail, type RunDiffResult, type DiffEntry } from "@/api/rmosRuns";

const route = useRoute();

const runAId = ref<string>("");
const runBId = ref<string>("");
const runA = ref<RunArtifactDetail | null>(null);
const runB = ref<RunArtifactDetail | null>(null);
const diffResult = ref<RunDiffResult | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);

// Watch for query param changes and auto-reload
watch(
  () => [route.query.a, route.query.b],
  () => {
    runAId.value = (route.query.a as string) || "";
    runBId.value = (route.query.b as string) || "";
    if (runAId.value && runBId.value) {
      load();
    }
  },
  { immediate: true }
);

async function load() {
  if (!runAId.value || !runBId.value) {
    error.value = "Both run A and run B are required.";
    return;
  }

  loading.value = true;
  error.value = null;
  runA.value = null;
  runB.value = null;
  diffResult.value = null;

  try {
    // Fetch both runs and diff in parallel
    const [a, b, diff] = await Promise.all([
      fetchRun(runAId.value),
      fetchRun(runBId.value),
      fetchRunDiff(runAId.value, runBId.value),
    ]);

    runA.value = a;
    runB.value = b;
    diffResult.value = diff;
  } catch (err: any) {
    error.value = err.message || "Failed to load diff";
    console.error("[RunDiffViewer] load error:", err);
  } finally {
    loading.value = false;
  }
}

const severityClass = computed(() => {
  if (!diffResult.value) return "";
  switch (diffResult.value.severity) {
    case "CRITICAL":
      return "severity-critical";
    case "WARNING":
      return "severity-warning";
    case "INFO":
      return "severity-info";
    default:
      return "severity-none";
  }
});

function diffEntryClass(entry: DiffEntry): string {
  switch (entry.severity) {
    case "CRITICAL":
      return "diff-critical";
    case "WARNING":
      return "diff-warning";
    default:
      return "diff-info";
  }
}

function formatValue(val: any): string {
  if (val === null || val === undefined) return "—";
  if (typeof val === "object") return JSON.stringify(val, null, 2);
  return String(val);
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
  <div class="run-diff-viewer">
    <!-- Loading State -->
    <div v-if="loading" class="state-message">
      Loading diff…
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="state-message error">
      {{ error }}
    </div>

    <!-- No IDs Provided -->
    <div v-else-if="!runAId || !runBId" class="state-message">
      <p>Select two runs to compare.</p>
      <p class="hint">Use the inputs above or navigate from the Run Artifacts list.</p>
    </div>

    <!-- Diff Results -->
    <template v-else-if="runA && runB && diffResult">
      <!-- Summary Banner -->
      <div class="diff-summary" :class="severityClass">
        <div class="summary-severity">{{ diffResult.severity }}</div>
        <div class="summary-text">{{ diffResult.summary }}</div>
        <div class="summary-count">{{ diffResult.diffs.length }} difference(s)</div>
      </div>

      <!-- Side-by-Side Headers -->
      <div class="comparison-header">
        <div class="side side-a">
          <h4>Run A</h4>
          <div class="run-id">{{ runA.run_id.slice(0, 16) }}…</div>
          <div class="run-meta">
            <span>{{ runA.status }}</span>
            <span>{{ formatDate(runA.created_at_utc) }}</span>
          </div>
        </div>
        <div class="side side-b">
          <h4>Run B</h4>
          <div class="run-id">{{ runB.run_id.slice(0, 16) }}…</div>
          <div class="run-meta">
            <span>{{ runB.status }}</span>
            <span>{{ formatDate(runB.created_at_utc) }}</span>
          </div>
        </div>
      </div>

      <!-- Diff Entries -->
      <div class="diff-entries">
        <div v-if="diffResult.diffs.length === 0" class="no-diffs">
          No differences found.
        </div>

        <div
          v-for="(entry, i) in diffResult.diffs"
          :key="i"
          class="diff-entry"
          :class="diffEntryClass(entry)"
        >
          <div class="diff-field">
            <span class="field-name">{{ entry.field }}</span>
            <span class="field-severity">{{ entry.severity }}</span>
          </div>
          <div class="diff-values">
            <div class="value value-a">
              <pre>{{ formatValue(entry.a_value) }}</pre>
            </div>
            <div class="value value-b">
              <pre>{{ formatValue(entry.b_value) }}</pre>
            </div>
          </div>
          <div v-if="entry.message" class="diff-message">
            {{ entry.message }}
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.run-diff-viewer {
  max-width: 1200px;
  margin: 0 auto;
}

.state-message {
  padding: 2rem;
  text-align: center;
  color: #6c757d;
  background: #f8f9fa;
  border-radius: 8px;
}

.state-message.error {
  color: #dc3545;
  background: #f8d7da;
}

.hint {
  font-size: 0.85rem;
  color: #868e96;
  margin-top: 0.5rem;
}

.diff-summary {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.severity-critical {
  background: #f8d7da;
  border: 1px solid #f5c6cb;
}

.severity-warning {
  background: #fff3cd;
  border: 1px solid #ffc107;
}

.severity-info {
  background: #d1ecf1;
  border: 1px solid #bee5eb;
}

.severity-none {
  background: #d4edda;
  border: 1px solid #c3e6cb;
}

.summary-severity {
  font-weight: 700;
  font-size: 0.9rem;
  padding: 0.3rem 0.6rem;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.1);
}

.summary-text {
  flex: 1;
}

.summary-count {
  font-size: 0.85rem;
  color: #6c757d;
}

.comparison-header {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
}

.side {
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #dee2e6;
}

.side h4 {
  margin: 0 0 0.5rem 0;
  font-size: 0.85rem;
  color: #6c757d;
  text-transform: uppercase;
}

.side-a {
  border-left: 3px solid #dc3545;
}

.side-b {
  border-left: 3px solid #28a745;
}

.run-id {
  font-family: monospace;
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.run-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.8rem;
  color: #6c757d;
}

.diff-entries {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.no-diffs {
  padding: 2rem;
  text-align: center;
  color: #28a745;
  background: #d4edda;
  border-radius: 8px;
}

.diff-entry {
  border: 1px solid #dee2e6;
  border-radius: 8px;
  overflow: hidden;
}

.diff-critical {
  border-color: #f5c6cb;
}

.diff-warning {
  border-color: #ffc107;
}

.diff-info {
  border-color: #bee5eb;
}

.diff-field {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0.75rem;
  background: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
}

.field-name {
  font-weight: 600;
  font-size: 0.9rem;
}

.field-severity {
  font-size: 0.75rem;
  padding: 0.15rem 0.4rem;
  border-radius: 3px;
  background: #e9ecef;
}

.diff-critical .field-severity {
  background: #f8d7da;
  color: #721c24;
}

.diff-warning .field-severity {
  background: #fff3cd;
  color: #856404;
}

.diff-info .field-severity {
  background: #d1ecf1;
  color: #0c5460;
}

.diff-values {
  display: grid;
  grid-template-columns: 1fr 1fr;
}

.value {
  padding: 0.75rem;
  overflow: auto;
  max-height: 150px;
}

.value-a {
  background: #fff5f5;
  border-right: 1px solid #dee2e6;
}

.value-b {
  background: #f0fff4;
}

.value pre {
  margin: 0;
  font-size: 0.8rem;
  white-space: pre-wrap;
  word-break: break-word;
}

.diff-message {
  padding: 0.5rem 0.75rem;
  background: #f8f9fa;
  border-top: 1px solid #dee2e6;
  font-size: 0.85rem;
  color: #6c757d;
}
</style>
