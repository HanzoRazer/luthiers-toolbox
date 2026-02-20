<template>
  <section class="workflow-section">
    <div class="section-header">
      <h2>
        <span class="step-number">1</span>
        AI Analysis (Claude Sonnet 4)
      </h2>
      <button
        v-if="analysis && !isAnalyzing"
        class="btn-secondary"
        @click="emit('reset')"
      >
        Upload New Blueprint
      </button>
    </div>

    <!-- Pre-Analysis Action Card -->
    <div
      v-if="!analysis"
      class="action-card"
    >
      <p class="hint">
        Analyze blueprint to detect scale, dimensions, and blueprint type
      </p>
      <button
        :disabled="isAnalyzing"
        class="btn-primary"
        @click="emit('analyze')"
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
            d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
          />
        </svg>
        {{ isAnalyzing ? 'Analyzing...' : 'Start Analysis' }}
      </button>
      <div
        v-if="isAnalyzing"
        class="progress-timer"
      >
        {{ analysisProgress }}s elapsed
      </div>
    </div>

    <!-- Analysis Results -->
    <div
      v-if="analysis"
      class="results-card"
    >
      <!-- Scale Info -->
      <div class="scale-grid">
        <div class="info-card">
          <span class="label">Detected Scale:</span>
          <span class="value">{{ analysis.scale || 'Unknown' }}</span>
          <span :class="['confidence', `confidence-${analysis.scale_confidence}`]">
            {{ analysis.scale_confidence || 'unknown' }}
          </span>
        </div>
        <div
          v-if="analysis.blueprint_type"
          class="info-card"
        >
          <span class="label">Type:</span>
          <span class="value">{{ analysis.blueprint_type }}</span>
        </div>
        <div
          v-if="analysis.detected_model"
          class="info-card"
        >
          <span class="label">Model:</span>
          <span class="value">{{ analysis.detected_model }}</span>
        </div>
      </div>

      <!-- Dimensions Table (Collapsible) -->
      <details
        class="dimensions-details"
        :open="(analysis.dimensions?.length || 0) <= 10"
      >
        <summary>
          <strong>Detected Dimensions ({{ analysis.dimensions?.length || 0 }})</strong>
        </summary>
        <div class="dimensions-table">
          <div class="table-header">
            <span>Label</span>
            <span>Value</span>
            <span>Type</span>
            <span>Confidence</span>
          </div>
          <div
            v-for="(dim, idx) in analysis.dimensions?.slice(0, 50)"
            :key="idx"
            class="table-row"
            :class="dim.type"
          >
            <span class="dim-label">{{ dim.label }}</span>
            <span class="dim-value">{{ dim.value }}</span>
            <span :class="['dim-type', dim.type]">{{ dim.type }}</span>
            <span :class="['dim-confidence', `confidence-${dim.confidence}`]">
              {{ dim.confidence }}
            </span>
          </div>
        </div>
      </details>

      <!-- Phase 1 Export -->
      <div class="export-row">
        <button
          :disabled="isExporting"
          class="btn-secondary"
          @click="emit('export-svg')"
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
          Export SVG (Dimensions Only)
        </button>
        <button
          class="btn-primary"
          style="margin-left: 12px;"
          @click="emit('edit-dimensions')"
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
              d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
            />
          </svg>
          Edit Dimensions in Parametric Designer
        </button>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { AnalysisResult } from '@/composables/useBlueprintWorkflow'

// Props
interface Props {
  analysis: AnalysisResult | null
  isAnalyzing: boolean
  isExporting: boolean
  analysisProgress: number
}

defineProps<Props>()

// Emits
const emit = defineEmits<{
  'analyze': []
  'reset': []
  'export-svg': []
  'edit-dimensions': []
}>()
</script>

<style scoped>
.workflow-section {
  border: 2px solid #e5e7eb;
  border-radius: 1rem;
  padding: 1.5rem;
  background: white;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.section-header h2 {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin: 0;
  font-size: 1.25rem;
}

.step-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #3b82f6;
  color: white;
  font-weight: bold;
  font-size: 1rem;
}

.action-card {
  background: #f9fafb;
  border-radius: 0.75rem;
  padding: 1.5rem;
  text-align: center;
}

.hint {
  color: #6b7280;
  margin-bottom: 1rem;
}

.progress-timer {
  margin-top: 0.75rem;
  color: #6b7280;
  font-size: 0.875rem;
}

.results-card {
  background: #f9fafb;
  border-radius: 0.75rem;
  padding: 1.5rem;
}

.scale-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.info-card {
  background: white;
  padding: 1rem;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
}

.info-card .label {
  display: block;
  color: #6b7280;
  font-size: 0.875rem;
  margin-bottom: 0.25rem;
}

.info-card .value {
  display: block;
  font-weight: 600;
  font-size: 1.125rem;
}

.confidence {
  display: inline-block;
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 500;
  margin-top: 0.25rem;
}

.confidence-high { background: #d1fae5; color: #065f46; }
.confidence-medium { background: #fef3c7; color: #92400e; }
.confidence-low { background: #fee2e2; color: #991b1b; }

.dimensions-details {
  margin-bottom: 1.5rem;
}

.dimensions-details summary {
  cursor: pointer;
  padding: 0.5rem;
  background: white;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
}

.dimensions-table {
  margin-top: 0.75rem;
  background: white;
  border-radius: 0.5rem;
  overflow: hidden;
  border: 1px solid #e5e7eb;
}

.table-header {
  display: grid;
  grid-template-columns: 2fr 1.5fr 1fr 1fr;
  padding: 0.75rem 1rem;
  background: #f3f4f6;
  font-weight: 600;
  font-size: 0.875rem;
}

.table-row {
  display: grid;
  grid-template-columns: 2fr 1.5fr 1fr 1fr;
  padding: 0.5rem 1rem;
  border-top: 1px solid #e5e7eb;
  font-size: 0.875rem;
}

.table-row:hover {
  background: #f9fafb;
}

.dim-label { font-weight: 500; }
.dim-value { color: #374151; }

.dim-type {
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  text-align: center;
}

.dim-type.linear { background: #dbeafe; color: #1d4ed8; }
.dim-type.angular { background: #fce7f3; color: #be185d; }
.dim-type.radius { background: #d1fae5; color: #065f46; }

.dim-confidence {
  font-size: 0.75rem;
}

.export-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

/* Buttons */
.btn-primary,
.btn-secondary {
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
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-secondary {
  background: #e5e7eb;
  color: #374151;
}

.btn-secondary:hover:not(:disabled) {
  background: #d1d5db;
}

.btn-primary:disabled,
.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary svg,
.btn-secondary svg {
  width: 20px;
  height: 20px;
}
</style>
