<template>
  <div :class="styles.cadLayout">
    <!-- Header -->
    <header :class="styles.cadHeader">
      <div :class="styles.cadHeaderLeft">
        <h1 :class="styles.cadTitle">DXF → G-code</h1>
        <span :class="styles.cadSubtitle">GRBL · Shop-floor quick path</span>
      </div>
      <div :class="styles.cadHeaderRight">
        <button
          v-if="canViewRun"
          :class="styles.headerBtn"
          title="Open canonical RMOS run record"
          @click="viewRunNewTab"
        >
          View Run <span :class="styles.ext">↗</span>
        </button>
      </div>
    </header>

    <!-- Main CAD Grid: Sidebar + Canvas -->
    <div :class="styles.cadGrid">
      <!-- Left Sidebar -->
      <aside :class="styles.cadSidebar">
        <!-- Upload Panel -->
        <div :class="styles.sidebarPanel">
          <h3 :class="styles.panelTitle">Upload DXF</h3>
          <DxfUploadZone
            v-model:file="dxfFile"
            :disabled="isGenerating"
            :class="styles.compactUpload"
            @error="uploadError = $event"
          />
        </div>

        <!-- Parameters Panel -->
        <div :class="styles.sidebarPanel">
          <h3 :class="styles.panelTitle">CAM Parameters</h3>
          <CamParametersForm
            v-model="params"
            :disabled="isGenerating"
            :class="styles.compactParams"
          />
        </div>

        <!-- Generate Button -->
        <button
          :disabled="!dxfFile || isGenerating"
          :class="styles.btnGenerateFull"
          @click="generateGcode"
        >
          {{ isGenerating ? 'Generating...' : 'Generate G-code' }}
        </button>

        <!-- Risk/Decision Panel (shown after result) -->
        <div
          v-if="result"
          :class="styles.sidebarPanel"
        >
          <h3 :class="styles.panelTitle">
            Decision
            <RiskBadge
              v-if="result.decision?.risk_level"
              :risk-level="result.decision.risk_level"
              :class="styles.inlineBadge"
            />
          </h3>

          <!-- Run ID -->
          <div :class="styles.runIdRow">
            <span :class="styles.runIdLabel">Run:</span>
            <code :class="styles.runIdCode">{{ result.run_id }}</code>
            <button
              :class="styles.copyBtnSmall"
              title="Copy Run ID"
              @click="copyRunId"
            >
              Copy
            </button>
          </div>

          <!-- Override Banner -->
          <OverrideBanner
            v-if="overrideReason"
            :reason="overrideReason"
            :class="styles.mt2"
          />

          <!-- Warnings -->
          <div
            v-if="result.decision?.warnings?.length"
            :class="styles.warningsCompact"
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

          <!-- Why Panel Toggle -->
          <button
            v-if="hasExplainability"
            :class="styles.whyBtn"
            :aria-expanded="showWhy"
            @click="showWhy = !showWhy"
          >
            {{ showWhy ? 'Hide' : 'Show' }} Why?
          </button>

          <WhyPanel
            v-if="hasExplainability && showWhy"
            :rules-triggered="triggeredRuleIds"
            :risk-level="riskLevel"
            :show-override-hint="riskLevel === 'YELLOW' && !hasOverrideAttachment"
            :has-override="hasOverrideAttachment"
            :class="styles.mt2"
          />
        </div>
      </aside>

      <!-- Main Canvas Area -->
      <main :class="styles.cadMain">
        <!-- Empty state (no result yet) -->
        <div
          v-if="!result && !isGenerating && !error"
          :class="styles.canvasEmpty"
        >
          <div :class="styles.emptyIcon">📐</div>
          <p :class="styles.emptyText">Upload a DXF file and click Generate to preview toolpath</p>
        </div>

        <!-- Generating state -->
        <div
          v-else-if="isGenerating"
          :class="styles.canvasLoading"
        >
          <span :class="styles.spinnerLarge" />
          <p>Generating G-code...</p>
        </div>

        <!-- Error state -->
        <div
          v-else-if="error"
          :class="styles.canvasError"
        >
          <strong>Error:</strong> {{ error }}
          <button
            :class="styles.clearBtn"
            @click="error = null"
          >
            Dismiss
          </button>
        </div>

        <!-- Result: Toolpath Preview + Actions -->
        <template v-else-if="result">
          <!-- Toolpath Preview (Hero) -->
          <div :class="styles.toolpathCanvas">
            <div :class="styles.toolpathHeader">
              <h3 :class="styles.toolpathTitle">
                Toolpath Preview
                <span
                  v-if="isGcodeAttachment"
                  :class="styles.toolpathBadge"
                >from attachment</span>
              </h3>

              <!-- Display toggles -->
              <div :class="styles.toolpathToggles">
                <label :class="styles.toggleLabel">
                  <input
                    v-model="showToolpath"
                    type="checkbox"
                    :class="styles.toggleInput"
                  >
                  Show
                </label>
                <label :class="styles.toggleLabel">
                  <input
                    v-model="toolpathShowHud"
                    type="checkbox"
                    :class="styles.toggleInput"
                    :disabled="!showToolpath"
                  >
                  HUD
                </label>
                <label :class="styles.toggleLabel">
                  <input
                    v-model="toolpathShowControls"
                    type="checkbox"
                    :class="styles.toggleInput"
                    :disabled="!showToolpath"
                  >
                  Controls
                </label>
                <label :class="styles.toggleLabel">
                  <input
                    v-model="toolpathAutoPlay"
                    type="checkbox"
                    :class="styles.toggleInput"
                    :disabled="!showToolpath"
                  >
                  Auto-play
                </label>
              </div>
            </div>

            <!-- Loading G-code -->
            <div
              v-if="isLoadingGcode"
              :class="styles.toolpathLoading"
            >
              <span :class="styles.spinner" />
              Loading toolpath from attachment...
            </div>

            <!-- G-code fetch error -->
            <div
              v-else-if="gcodeError"
              :class="styles.toolpathError"
            >
              <strong>Failed to load toolpath:</strong> {{ gcodeError }}
            </div>

            <!-- Player -->
            <ToolpathPlayer
              v-else-if="gcodeText && showToolpath"
              :gcode="gcodeText"
              :show-hud="toolpathShowHud"
              :show-controls="toolpathShowControls"
              :auto-play="toolpathAutoPlay"
              height="100%"
              :class="styles.playerFill"
            />

            <!-- Collapsed -->
            <div
              v-else-if="gcodeText && !showToolpath"
              :class="styles.toolpathCollapsed"
            >
              Toolpath preview hidden. Check "Show" to display.
            </div>

            <!-- No G-code available -->
            <div
              v-else
              :class="styles.toolpathEmpty"
            >
              <p>No toolpath data available</p>
            </div>
          </div>

          <!-- Action Bar (below canvas) -->
          <div :class="styles.actionBar">
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
              Operator Pack (.zip)
            </button>

            <button
              :disabled="!canCompare"
              :class="styles.btnCompare"
              :title="compareTitle"
              @click="compareWithPreviousRun"
            >
              {{ isComparing ? 'Comparing…' : 'Compare' }}
            </button>
          </div>

          <!-- Attachment hint (if large file) -->
          <div
            v-if="result && !result.gcode?.inline"
            :class="styles.attachmentHint"
          >
            <p>G-code stored as RMOS attachment (too large for inline).</p>
            <p :class="styles.attachmentMeta">
              SHA: <code>{{ gcodeAttachment?.sha256?.slice(0, 12) }}…</code>
              · {{ ((gcodeAttachment?.size_bytes || 0) / 1024).toFixed(1) }} KB
            </p>
          </div>

          <!-- Compare Card -->
          <RunCompareCard
            v-if="hasCompare || compareError"
            :compare-result="compareResult"
            :compare-error="compareError"
            :previous-run-id="previousRunId"
            :current-run-id="result?.run_id"
            :class="styles.compareCard"
            @clear="clearCompare"
          />
        </template>
      </main>
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
import { computed, ref } from 'vue'
import RiskBadge from '@/components/ui/RiskBadge.vue'
import OverrideBanner from '@/components/ui/OverrideBanner.vue'
import WhyPanel from '@/components/rmos/WhyPanel.vue'
import ToolpathPlayer from '@/components/cam/ToolpathPlayer.vue'
import { useGcodeFetcher } from '@/composables'
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

// G-code fetcher (Phase 2: handles both inline and attachment cases)
const {
  gcodeText,
  isLoading: isLoadingGcode,
  error: gcodeError,
  isAttachment: isGcodeAttachment,
} = useGcodeFetcher(result)

// Phase 3: Toolpath display toggles
const showToolpath = ref(true)
const toolpathShowHud = ref(true)
const toolpathShowControls = ref(true)
const toolpathAutoPlay = ref(false)
</script>
