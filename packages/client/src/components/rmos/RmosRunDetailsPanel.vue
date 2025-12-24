<script setup lang="ts">
/**
 * RMOS Run Details Panel - Bundle 31.0.27.2+
 *
 * Displays full details for a selected run artifact.
 * Includes copy buttons for run_id, JSON, and cURL.
 */

import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import {
  fetchRunDetails,
  copyToClipboard,
  buildCurlForRun,
  type RunDetails,
} from '../../services/rmosLogsClient';

const props = defineProps<{
  runId: string | null;
  baseUrl?: string;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
}>();

const details = ref<RunDetails | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);
const copyFeedback = ref<string | null>(null);

// Risk level colors
const riskColors: Record<string, string> = {
  GREEN: '#22c55e',
  YELLOW: '#eab308',
  RED: '#ef4444',
  ERROR: '#dc2626',
  UNKNOWN: '#6b7280',
};

const riskColor = computed(() => {
  const level = details.value?.decision?.risk_level || 'UNKNOWN';
  return riskColors[level] || riskColors.UNKNOWN;
});

const statusBadgeClass = computed(() => {
  const status = details.value?.status;
  if (status === 'OK') return 'badge-success';
  if (status === 'BLOCKED') return 'badge-warning';
  if (status === 'ERROR') return 'badge-error';
  return 'badge-neutral';
});

async function loadDetails() {
  if (!props.runId) {
    details.value = null;
    return;
  }

  loading.value = true;
  error.value = null;

  try {
    details.value = await fetchRunDetails(props.runId);
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to load run details';
    details.value = null;
  } finally {
    loading.value = false;
  }
}

async function copyRunId() {
  if (!details.value) return;
  const success = await copyToClipboard(details.value.run_id);
  showCopyFeedback(success ? 'Copied run_id!' : 'Copy failed');
}

async function copyJson() {
  if (!details.value) return;
  const json = JSON.stringify(details.value, null, 2);
  const success = await copyToClipboard(json);
  showCopyFeedback(success ? 'Copied JSON!' : 'Copy failed');
}

async function copyCurl() {
  if (!props.runId) return;
  const curl = buildCurlForRun(props.runId, props.baseUrl || window.location.origin);
  const success = await copyToClipboard(curl);
  showCopyFeedback(success ? 'Copied cURL!' : 'Copy failed');
}

function showCopyFeedback(message: string) {
  copyFeedback.value = message;
  setTimeout(() => {
    copyFeedback.value = null;
  }, 2000);
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    emit('close');
  }
  if (e.key === 'c' && !e.ctrlKey && !e.metaKey) {
    copyRunId();
  }
}

watch(() => props.runId, loadDetails, { immediate: true });

onMounted(() => {
  window.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown);
});
</script>

<template>
  <div class="run-details-panel" v-if="runId">
    <div class="panel-header">
      <h3>Run Details</h3>
      <button class="close-btn" @click="$emit('close')" title="Close (Esc)">
        &times;
      </button>
    </div>

    <div v-if="loading" class="loading">Loading...</div>

    <div v-else-if="error" class="error">{{ error }}</div>

    <div v-else-if="details" class="panel-content">
      <!-- Copy feedback toast -->
      <div v-if="copyFeedback" class="copy-feedback">{{ copyFeedback }}</div>

      <!-- Header with status -->
      <div class="detail-header">
        <span class="run-id">{{ details.run_id }}</span>
        <span :class="['status-badge', statusBadgeClass]">{{ details.status }}</span>
      </div>

      <!-- Copy buttons -->
      <div class="copy-buttons">
        <button @click="copyRunId" title="Copy run_id (c)">Copy run_id</button>
        <button @click="copyJson" title="Copy full JSON">Copy JSON</button>
        <button @click="copyCurl" title="Copy cURL command">Copy cURL</button>
      </div>

      <!-- Risk level -->
      <div class="detail-row">
        <span class="label">Risk Level:</span>
        <span class="risk-badge" :style="{ backgroundColor: riskColor }">
          {{ details.decision?.risk_level || 'UNKNOWN' }}
        </span>
        <span v-if="details.decision?.score !== null" class="score">
          Score: {{ details.decision.score?.toFixed(1) }}
        </span>
      </div>

      <!-- Metadata -->
      <div class="detail-row">
        <span class="label">Mode:</span>
        <span>{{ details.mode }}</span>
      </div>
      <div class="detail-row">
        <span class="label">Tool:</span>
        <span>{{ details.tool_id }}</span>
      </div>
      <div class="detail-row">
        <span class="label">Created:</span>
        <span>{{ new Date(details.created_at_utc).toLocaleString() }}</span>
      </div>

      <!-- Warnings -->
      <div v-if="details.decision?.warnings?.length" class="warnings-section">
        <h4>Warnings</h4>
        <ul>
          <li v-for="(warning, idx) in details.decision.warnings" :key="idx">
            {{ warning }}
          </li>
        </ul>
      </div>

      <!-- Block reason -->
      <div v-if="details.decision?.block_reason" class="block-reason">
        <h4>Block Reason</h4>
        <p>{{ details.decision.block_reason }}</p>
      </div>

      <!-- Request summary -->
      <div class="json-section">
        <h4>Request Summary</h4>
        <pre>{{ JSON.stringify(details.request_summary, null, 2) }}</pre>
      </div>

      <!-- Feasibility -->
      <div class="json-section">
        <h4>Feasibility</h4>
        <pre>{{ JSON.stringify(details.feasibility, null, 2) }}</pre>
      </div>

      <!-- Hashes -->
      <div class="json-section">
        <h4>Hashes</h4>
        <pre>{{ JSON.stringify(details.hashes, null, 2) }}</pre>
      </div>

      <!-- Meta -->
      <div v-if="Object.keys(details.meta || {}).length" class="json-section">
        <h4>Metadata</h4>
        <pre>{{ JSON.stringify(details.meta, null, 2) }}</pre>
      </div>
    </div>
  </div>
</template>

<style scoped>
.run-details-panel {
  background: #1a1a2e;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 16px;
  max-height: 80vh;
  overflow-y: auto;
  font-family: monospace;
  font-size: 13px;
  color: #e0e0e0;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  border-bottom: 1px solid #333;
  padding-bottom: 8px;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
}

.close-btn {
  background: none;
  border: none;
  color: #888;
  font-size: 24px;
  cursor: pointer;
  padding: 0 8px;
}

.close-btn:hover {
  color: #fff;
}

.loading,
.error {
  padding: 20px;
  text-align: center;
}

.error {
  color: #ef4444;
}

.copy-feedback {
  position: fixed;
  top: 20px;
  right: 20px;
  background: #22c55e;
  color: #fff;
  padding: 8px 16px;
  border-radius: 4px;
  z-index: 1000;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.run-id {
  font-weight: bold;
  color: #60a5fa;
}

.status-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: bold;
}

.badge-success {
  background: #22c55e;
  color: #fff;
}

.badge-warning {
  background: #eab308;
  color: #000;
}

.badge-error {
  background: #ef4444;
  color: #fff;
}

.badge-neutral {
  background: #6b7280;
  color: #fff;
}

.copy-buttons {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.copy-buttons button {
  background: #333;
  border: 1px solid #555;
  color: #e0e0e0;
  padding: 4px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.copy-buttons button:hover {
  background: #444;
}

.detail-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.label {
  color: #888;
  min-width: 80px;
}

.risk-badge {
  padding: 2px 8px;
  border-radius: 4px;
  color: #fff;
  font-weight: bold;
  font-size: 11px;
}

.score {
  color: #888;
  font-size: 12px;
}

.warnings-section,
.block-reason {
  margin-top: 16px;
  padding: 12px;
  background: rgba(234, 179, 8, 0.1);
  border-radius: 4px;
  border-left: 3px solid #eab308;
}

.block-reason {
  background: rgba(239, 68, 68, 0.1);
  border-left-color: #ef4444;
}

.warnings-section h4,
.block-reason h4 {
  margin: 0 0 8px 0;
  font-size: 13px;
  color: #eab308;
}

.block-reason h4 {
  color: #ef4444;
}

.warnings-section ul {
  margin: 0;
  padding-left: 20px;
}

.warnings-section li {
  margin-bottom: 4px;
}

.json-section {
  margin-top: 16px;
}

.json-section h4 {
  margin: 0 0 8px 0;
  font-size: 13px;
  color: #888;
}

.json-section pre {
  background: #111;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 11px;
  margin: 0;
}
</style>
