<template>
  <div class="dxf-to-gcode">
    <h1>DXF → G-code (GRBL)</h1>
    <p class="subtitle">
      Shop-floor quick path: upload DXF, set params, download G-code
    </p>

    <!-- Upload Zone (extracted component) -->
    <DxfUploadZone
      v-model:file="dxfFile"
      :disabled="isGenerating"
      class="mb-8"
      @error="uploadError = $event"
    />

    <!-- CAM Parameters (extracted component) -->
    <CamParametersForm
      v-model="params"
      :disabled="isGenerating"
    />

    <!-- Generate Button -->
    <div class="action-section">
      <button
        :disabled="!dxfFile || isGenerating"
        class="btn-generate"
        @click="generateGcode"
      >
        {{ isGenerating ? 'Generating...' : 'Generate G-code' }}
      </button>
      <p class="generate-hint">
        Uses GRBL profile � Units: mm � Output: .nc
      </p>
    </div>

    <!-- Result -->
    <div
      v-if="result"
      class="result-section"
    >
      <!-- Results Header: Title+Badge -> Run ID/Copy/View/Why? -> Override -> Warnings -> WhyPanel -->
      <div class="results-header">
        <div class="results-title">
          <h2>Result</h2>
          <RiskBadge
            v-if="result.decision?.risk_level"
            :risk-level="result.decision.risk_level"
          />
        </div>

        <div class="result-meta">
          <span class="run-id">Run: {{ result.run_id }}</span>
          <button
            class="copy-btn"
            title="Copy Run ID"
            @click="copyRunId"
          >
            Copy
          </button>
          <button
            v-if="canViewRun"
            class="btn-link"
            title="Open canonical RMOS run record"
            @click="viewRunNewTab"
          >
            View Run <span
              class="ext"
              aria-hidden="true"
            >↗</span>
          </button>
          <span
            v-if="!result.rmos_persisted"
            class="not-persisted"
          >RMOS not persisted</span>
          <button
            v-if="hasExplainability"
            class="btn-link"
            :aria-expanded="showWhy"
            title="Show why this decision happened"
            @click="showWhy = !showWhy"
          >
            Why?
          </button>
        </div>
      </div>

      <!-- Always-visible override banner (if any) -->
      <OverrideBanner
        v-if="overrideReason"
        :reason="overrideReason"
      />

      <div
        v-if="result.decision?.warnings?.length"
        class="warnings"
      >
        <strong>Warnings:</strong>
        <ul>
          <li
            v-for="(w, i) in result.decision.warnings"
            :key="i"
          >
            {{ w }}
          </li>
        </ul>
      </div>

      <!-- Explainability: auto-opens for YELLOW/RED; toggleable via header Why? button -->
      <WhyPanel
        v-if="hasExplainability && showWhy"
        :rules-triggered="triggeredRuleIds"
        :risk-level="riskLevel"
        :show-override-hint="riskLevel === 'YELLOW' && !hasOverrideAttachment"
        :has-override="hasOverrideAttachment"
        class="mt-3"
      />

      <!-- Run-to-run compare (extracted component) -->
      <RunCompareCard
        v-if="hasCompare || compareError"
        :compare-result="compareResult"
        :compare-error="compareError"
        :previous-run-id="previousRunId"
        :current-run-id="result?.run_id"
        @clear="clearCompare"
      />

      <!-- Action row with risk badge + downloads -->
      <div class="action-row">
        <span
          class="action-risk-badge"
          :class="riskLevel.toLowerCase()"
          title="Decision from feasibility engine (RMOS)"
        >
          {{ riskLevel || 'N/A' }}
        </span>

        <button
          :disabled="!canDownload"
          class="btn-download"
          @click="downloadGcode"
        >
          Download G-code (.nc)
        </button>

        <button
          :disabled="!canDownloadOperatorPack"
          class="btn-operator-pack"
          title="Downloads input.dxf + plan.json + manifest.json + output.nc"
          @click="downloadOperatorPack"
        >
          Download Operator Pack (.zip)
        </button>

        <button
          :disabled="!canCompare"
          class="btn-compare"
          :title="compareTitle"
          @click="compareWithPreviousRun"
        >
          {{ isComparing ? 'Comparing…' : 'Compare w/ Previous' }}
        </button>
      </div>

      <button
        v-if="canViewRun"
        class="btn-view-run"
        title="Open canonical RMOS run record in a new tab"
        @click="viewRunNewTab"
      >
        View Run <span
          class="ext"
          aria-hidden="true"
        >↗</span>
      </button>

      <div
        v-if="result && !result.gcode?.inline"
        class="attachment-hint"
      >
        <p>G-code stored as RMOS attachment (too large for inline).</p>
        <p class="attachment-meta">
          Run ID: <code>{{ result.run_id }}</code>
          <span v-if="gcodeAttachment">
            · SHA: <code>{{ gcodeAttachment.sha256?.slice(0, 12) }}…</code>
            · {{ (gcodeAttachment.size_bytes / 1024).toFixed(1) }} KB
          </span>
        </p>
      </div>
    </div>

    <!-- Error -->
    <div
      v-if="error"
      class="error"
    >
      <strong>Error:</strong> {{ error }}
      <button
        class="clear-btn"
        @click="error = null"
      >
        ×
      </button>
    </div>

    <!-- Override Modal (YELLOW gate) -->
    <OverrideModal
      :show="showOverrideModal"
      :is-submitting="isSubmittingOverride"
      :error="overrideError"
      @close="closeOverrideModal"
      @submit="submitOverride"
    />
  </div>
</template>

<script setup lang="ts">
import RiskBadge from '@/components/ui/RiskBadge.vue'
import OverrideBanner from '@/components/ui/OverrideBanner.vue'
import WhyPanel from '@/components/rmos/WhyPanel.vue'
import {
  DxfUploadZone,
  CamParametersForm,
  RunCompareCard,
  OverrideModal,
  useDxfToGcode
} from '@/components/dxf'

const {
  // File
  dxfFile,
  uploadError,
  // Params
  params,
  // Generation
  isGenerating,
  result,
  error,
  generateGcode,
  // Download
  canDownload,
  downloadGcode,
  canDownloadOperatorPack,
  downloadOperatorPack,
  // Run
  canViewRun,
  viewRunNewTab,
  copyRunId,
  gcodeAttachment,
  // Risk/Explainability
  riskLevel,
  triggeredRuleIds,
  hasExplainability,
  showWhy,
  hasOverrideAttachment,
  overrideReason,
  // Compare
  previousRunId,
  isComparing,
  compareError,
  compareResult,
  hasCompare,
  canCompare,
  compareTitle,
  compareWithPreviousRun,
  clearCompare,
  // Override modal
  showOverrideModal,
  isSubmittingOverride,
  overrideError,
  submitOverride,
  closeOverrideModal,
} = useDxfToGcode()
</script>

<style scoped>
.dxf-to-gcode {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}

h1 {
  margin: 0 0 0.5rem 0;
}

.subtitle {
  color: #6b7280;
  margin-bottom: 2rem;
}


.clear-btn {
  background: none;
  border: none;
  font-size: 1.25rem;
  color: #9ca3af;
  cursor: pointer;
  padding: 0 0.25rem;
}

.clear-btn:hover {
  color: #dc2626;
}


.action-section {
  margin-bottom: 2rem;
}

.generate-hint {
  margin: 0.5rem 0 0 0;
  font-size: 0.75rem;
  color: #9ca3af;
}

.btn-generate {
  width: 100%;
  padding: 1rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-size: 1.125rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-generate:hover:not(:disabled) {
  background: #2563eb;
}

.btn-generate:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.result-section {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1.5rem;
  margin-bottom: 1rem;
}

/* Risk Banner - prominent at top */
.risk-banner {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
}

.risk-banner.green {
  background: #d1fae5;
  border: 1px solid #10b981;
}

.risk-banner.yellow {
  background: #fef3c7;
  border: 1px solid #f59e0b;
}

.risk-banner.red {
  background: #fee2e2;
  border: 1px solid #ef4444;
}

.risk-label {
  font-weight: 700;
  font-size: 1rem;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.5);
}

.risk-banner.green .risk-label {
  color: #065f46;
}

.risk-banner.yellow .risk-label {
  color: #92400e;
}

.risk-banner.red .risk-label {
  color: #991b1b;
}

.risk-text {
  font-size: 0.875rem;
  color: #374151;
}

.results-header {
  margin-bottom: 1rem;
}

.results-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.results-title h2 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.result-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.mt-3 {
  margin-top: 0.75rem;
}

.run-id {
  font-family: monospace;
  font-size: 0.875rem;
  color: #6b7280;
}

.copy-btn {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  background: #e5e7eb;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  color: #374151;
}

.copy-btn:hover {
  background: #d1d5db;
}

.view-run-link {
  font-size: 0.75rem;
  color: #3b82f6;
  text-decoration: none;
}

.view-run-link:hover {
  text-decoration: underline;
}

.not-persisted {
  color: #f59e0b;
  font-size: 0.875rem;
}

.warnings {
  background: #fffbeb;
  border: 1px solid #fcd34d;
  border-radius: 0.375rem;
  padding: 0.75rem;
  margin-bottom: 1rem;
}

.warnings ul {
  margin: 0.5rem 0 0 1.25rem;
  padding: 0;
}

.warnings li {
  color: #92400e;
  font-size: 0.875rem;
}

.btn-download {
  padding: 0.75rem 1.5rem;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-download:hover:not(:disabled) {
  background: #059669;
}

.btn-download:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.btn-operator-pack {
  padding: 0.75rem 1.5rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
  margin-left: 0.5rem;
}

.btn-operator-pack:hover:not(:disabled) {
  background: #2563eb;
}

.btn-operator-pack:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.attachment-hint {
  background: #fef3c7;
  border: 1px solid #fcd34d;
  border-radius: 0.375rem;
  padding: 0.75rem;
  margin-top: 1rem;
}

.attachment-hint p {
  margin: 0;
  font-size: 0.875rem;
  color: #92400e;
}

.attachment-meta {
  margin-top: 0.5rem !important;
}

.attachment-meta code {
  background: #fde68a;
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
}

.error {
  background: #fee2e2;
  border: 1px solid #fca5a5;
  border-radius: 0.5rem;
  padding: 1rem;
  color: #991b1b;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}



.btn-view-run {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  background: #e5e7eb;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
  color: #374151;
  opacity: 0.9;
}

.btn-view-run:hover {
  background: #d1d5db;
}

.btn-link {
  padding: 0 4px;
  font-size: 13px;
  background: none;
  border: none;
  color: #3b82f6;
  text-decoration: underline;
  cursor: pointer;
  opacity: 0.85;
}

.btn-link:hover {
  opacity: 1;
}

.ext {
  display: inline-block;
  margin-left: 4px;
  font-size: 12px;
  opacity: 0.8;
  transform: translateY(-1px);
}

/* Action row with risk badge + download buttons */
.action-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.action-risk-badge {
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.25rem 0.625rem;
  border-radius: 9999px;
  cursor: help;
}

.action-risk-badge.green {
  background: #d1fae5;
  color: #065f46;
  border: 1px solid #10b981;
}

.action-risk-badge.yellow {
  background: #fef3c7;
  color: #92400e;
  border: 1px solid #f59e0b;
}

.action-risk-badge.red {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #ef4444;
}

.btn-compare {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 500;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-compare:hover:not(:disabled) {
  background: #e5e7eb;
  border-color: #9ca3af;
}

.btn-compare:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}


</style>
