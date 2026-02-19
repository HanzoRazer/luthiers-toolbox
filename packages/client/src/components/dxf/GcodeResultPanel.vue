<template>
  <div class="result-section">
    <!-- Results Header -->
    <div class="results-header">
      <div class="results-title">
        <h2>Result</h2>
        <RiskBadge
          v-if="riskLevel"
          :risk-level="riskLevel"
        />
      </div>

      <div class="result-meta">
        <span class="run-id">Run: {{ runId }}</span>
        <button
          class="copy-btn"
          title="Copy Run ID"
          @click="$emit('copyRunId')"
        >
          Copy
        </button>
        <button
          v-if="runId"
          class="btn-link"
          title="Open canonical RMOS run record"
          @click="$emit('viewRun')"
        >
          View Run <span class="ext" aria-hidden="true">↗</span>
        </button>
        <span v-if="!rmosPersisted" class="not-persisted">RMOS not persisted</span>
        <button
          v-if="hasExplainability"
          class="btn-link"
          :aria-expanded="showWhy"
          title="Show why this decision happened"
          @click="$emit('toggleWhy')"
        >
          Why?
        </button>
      </div>
    </div>

    <!-- Override Banner -->
    <OverrideBanner
      v-if="overrideReason"
      :reason="overrideReason"
    />

    <!-- Warnings -->
    <div v-if="warnings?.length" class="warnings">
      <strong>Warnings:</strong>
      <ul>
        <li v-for="(w, i) in warnings" :key="i">{{ w }}</li>
      </ul>
    </div>

    <!-- WhyPanel -->
    <WhyPanel
      v-if="hasExplainability && showWhy"
      :rules-triggered="rulesTriggered"
      :risk-level="riskLevel"
      :show-override-hint="riskLevel === 'YELLOW' && !hasOverride"
      :has-override="hasOverride"
      class="mt-3"
    />

    <!-- Compare Card -->
    <slot name="compare" />

    <!-- Action Row -->
    <div class="action-row">
      <span
        class="action-risk-badge"
        :class="riskLevel?.toLowerCase()"
        title="Decision from feasibility engine (RMOS)"
      >
        {{ riskLevel || 'N/A' }}
      </span>

      <button
        :disabled="!canDownloadGcode"
        class="btn-download"
        @click="$emit('downloadGcode')"
      >
        Download G-code (.nc)
      </button>

      <button
        :disabled="!canDownloadPack"
        class="btn-operator-pack"
        title="Downloads input.dxf + plan.json + manifest.json + output.nc"
        @click="$emit('downloadPack')"
      >
        Download Operator Pack (.zip)
      </button>

      <button
        :disabled="!canCompare"
        class="btn-compare"
        :title="compareTitle"
        @click="$emit('compare')"
      >
        {{ isComparing ? 'Comparing…' : 'Compare w/ Previous' }}
      </button>
    </div>

    <button
      v-if="runId"
      class="btn-view-run"
      title="Open canonical RMOS run record in a new tab"
      @click="$emit('viewRun')"
    >
      View Run <span class="ext" aria-hidden="true">↗</span>
    </button>

    <!-- Attachment Hint -->
    <div v-if="showAttachmentHint" class="attachment-hint">
      <p>G-code stored as RMOS attachment (too large for inline).</p>
      <p class="attachment-meta">
        Run ID: <code>{{ runId }}</code>
        <span v-if="gcodeAttachment">
          · SHA: <code>{{ gcodeAttachment.sha256?.slice(0, 12) }}…</code>
          · {{ ((gcodeAttachment.size_bytes ?? 0) / 1024).toFixed(1) }} KB
        </span>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import RiskBadge from '@/components/ui/RiskBadge.vue'
import OverrideBanner from '@/components/ui/OverrideBanner.vue'
import WhyPanel from '@/components/rmos/WhyPanel.vue'

defineProps<{
  runId: string
  riskLevel: string
  rmosPersisted: boolean
  warnings?: string[]
  rulesTriggered: string[]
  hasExplainability: boolean
  showWhy: boolean
  hasOverride: boolean
  overrideReason?: string
  canDownloadGcode: boolean
  canDownloadPack: boolean
  canCompare: boolean
  isComparing: boolean
  compareTitle: string
  showAttachmentHint: boolean
  gcodeAttachment?: { sha256?: string; size_bytes?: number } | null
}>()

defineEmits<{
  copyRunId: []
  viewRun: []
  toggleWhy: []
  downloadGcode: []
  downloadPack: []
  compare: []
}>()
</script>

<style scoped>
.result-section {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1.5rem;
  margin-bottom: 1rem;
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

.btn-view-run {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  background: #e5e7eb;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
  color: #374151;
  opacity: 0.9;
  margin-top: 0.75rem;
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
</style>
