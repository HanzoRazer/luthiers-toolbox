<template>
  <div :class="styles.dxfToGcode">
    <h1>DXF → G-code (GRBL)</h1>
    <p :class="styles.subtitle">
      Shop-floor quick path: upload DXF, set params, download G-code
    </p>

    <!-- Upload Zone (extracted component) -->
    <DxfUploadZone
      v-model:file="dxfFile"
      :disabled="isGenerating"
      :class="styles.mb8"
      @error="uploadError = $event"
    />

    <!-- CAM Parameters (extracted component) -->
    <CamParametersForm
      v-model="params"
      :disabled="isGenerating"
    />

    <!-- Generate Button -->
    <div :class="styles.actionSection">
      <button
        :disabled="!dxfFile || isGenerating"
        :class="styles.btnGenerate"
        @click="generateGcode"
      >
        {{ isGenerating ? 'Generating...' : 'Generate G-code' }}
      </button>
      <p :class="styles.generateHint">
        Uses GRBL profile · Units: mm · Output: .nc
      </p>
    </div>

    <!-- Result -->
    <div
      v-if="result"
      :class="styles.resultSection"
    >
      <!-- Results Header: Title+Badge -> Run ID/Copy/View/Why? -> Override -> Warnings -> WhyPanel -->
      <div :class="styles.resultsHeader">
        <div :class="styles.resultsTitle">
          <h2>Result</h2>
          <RiskBadge
            v-if="result.decision?.risk_level"
            :risk-level="result.decision.risk_level"
          />
        </div>

        <div :class="styles.resultMeta">
          <span :class="styles.runId">Run: {{ result.run_id }}</span>
          <button
            :class="styles.copyBtn"
            title="Copy Run ID"
            @click="copyRunId"
          >
            Copy
          </button>
          <button
            v-if="canViewRun"
            :class="styles.btnLink"
            title="Open canonical RMOS run record"
            @click="viewRunNewTab"
          >
            View Run <span
              :class="styles.ext"
              aria-hidden="true"
            >↗</span>
          </button>
          <span
            v-if="!result.rmos_persisted"
            :class="styles.notPersisted"
          >RMOS not persisted</span>
          <button
            v-if="hasExplainability"
            :class="styles.btnLink"
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
        :class="styles.warnings"
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
        :class="styles.mt3"
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
      <div :class="styles.actionRow">
        <span
          :class="riskBadgeClass"
          title="Decision from feasibility engine (RMOS)"
        >
          {{ riskLevel || 'N/A' }}
        </span>

        <button
          :disabled="!canDownload"
          :class="styles.btnDownload"
          @click="downloadGcode"
        >
          Download G-code (.nc)
        </button>

        <button
          :disabled="!canDownloadOperatorPack"
          :class="styles.btnOperatorPack"
          title="Downloads input.dxf + plan.json + manifest.json + output.nc"
          @click="downloadOperatorPack"
        >
          Download Operator Pack (.zip)
        </button>

        <button
          :disabled="!canCompare"
          :class="styles.btnCompare"
          :title="compareTitle"
          @click="compareWithPreviousRun"
        >
          {{ isComparing ? 'Comparing…' : 'Compare w/ Previous' }}
        </button>
      </div>

      <button
        v-if="canViewRun"
        :class="styles.btnViewRun"
        title="Open canonical RMOS run record in a new tab"
        @click="viewRunNewTab"
      >
        View Run <span
          :class="styles.ext"
          aria-hidden="true"
        >↗</span>
      </button>

      <div
        v-if="result && !result.gcode?.inline"
        :class="styles.attachmentHint"
      >
        <p>G-code stored as RMOS attachment (too large for inline).</p>
        <p :class="styles.attachmentMeta">
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
      :class="styles.error"
    >
      <strong>Error:</strong> {{ error }}
      <button
        :class="styles.clearBtn"
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
import { computed } from 'vue'
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
import styles from './DxfToGcodeView.module.css'

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

// Computed class for risk badge
const riskBadgeClass = computed(() => {
  const level = riskLevel.value?.toLowerCase() || ''
  return {
    [styles.actionRiskBadgeGreen]: level === 'green',
    [styles.actionRiskBadgeYellow]: level === 'yellow',
    [styles.actionRiskBadgeRed]: level === 'red',
    [styles.actionRiskBadge]: !['green', 'yellow', 'red'].includes(level),
  }
})
</script>
