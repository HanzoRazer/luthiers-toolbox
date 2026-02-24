<script setup lang="ts">
/**
 * CamResultsCard.vue - RMOS result display with stats, warnings, and download
 * Extracted from Phase3CamPanel.vue
 */
import type { RmosResult } from "@/composables/useBlueprintWorkflow";

defineProps<{
  rmosResult: RmosResult;
  gcodeReady: boolean;
}>();

const emit = defineEmits<{
  "download-gcode": [];
}>();
</script>

<template>
  <div class="results-card">
    <div class="stats-grid">
      <div class="stat-card">
        <span class="stat-value">{{ rmosResult.decision?.risk_level || 'N/A' }}</span>
        <span class="stat-label">Risk Level</span>
      </div>
      <div class="stat-card">
        <span class="stat-value run-id">{{ rmosResult.run_id || 'N/A' }}</span>
        <span class="stat-label">RMOS Run ID</span>
      </div>
      <div class="stat-card">
        <span class="stat-value">{{ rmosResult.rmos_persisted ? 'Y' : 'N' }}</span>
        <span class="stat-label">RMOS Persisted</span>
      </div>
    </div>

    <!-- Warnings -->
    <div
      v-if="rmosResult.decision?.warnings?.length"
      class="warning-list"
    >
      <strong>Warnings:</strong>
      <ul>
        <li
          v-for="(w, i) in rmosResult.decision.warnings"
          :key="i"
        >
          {{ w }}
        </li>
      </ul>
    </div>

    <!-- RMOS Error -->
    <div
      v-if="!rmosResult.rmos_persisted && rmosResult.rmos_error"
      class="rmos-error"
    >
      <strong>RMOS Error:</strong> {{ rmosResult.rmos_error }}
    </div>

    <!-- Download Button -->
    <div class="export-row">
      <button
        :disabled="!gcodeReady"
        class="btn-primary"
        @click="emit('download-gcode')"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
          />
        </svg>
        Download G-code (.nc)
      </button>
      <span
        v-if="rmosResult && !rmosResult.gcode?.inline"
        class="hint-small"
      >
        G-code too large for inline delivery. Use RMOS attachments.
      </span>
    </div>
  </div>
</template>

<style scoped>
.results-card {
  background: #f9fafb;
  border-radius: 0.75rem;
  padding: 1.5rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: white;
  padding: 1rem;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  color: #f59e0b;
}

.stat-value.run-id {
  font-size: 0.75rem;
  word-break: break-all;
}

.stat-label {
  display: block;
  color: #6b7280;
  font-size: 0.875rem;
  margin-top: 0.25rem;
}

.warning-list {
  background: #fef3c7;
  border: 1px solid #fcd34d;
  border-radius: 0.5rem;
  padding: 1rem;
  margin-bottom: 1rem;
}

.warning-list ul {
  margin: 0.5rem 0 0 1.25rem;
  padding: 0;
}

.warning-list li {
  color: #92400e;
  font-size: 0.875rem;
}

.rmos-error {
  background: #fee2e2;
  border: 1px solid #fca5a5;
  border-radius: 0.5rem;
  padding: 1rem;
  margin-bottom: 1rem;
  color: #991b1b;
}

.export-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: center;
}

.hint-small {
  color: #9ca3af;
  font-size: 0.875rem;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.5rem;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  background: #f59e0b;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #d97706;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary svg {
  width: 20px;
  height: 20px;
}
</style>
