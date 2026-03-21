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
import { onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAgenticEvents } from '@/composables/useAgenticEvents'
import RunComparePanel from '@/components/rmos/RunComparePanel.vue'
import WhyPanel from '@/components/rmos/WhyPanel.vue'
import AdvisoryExplanationPanel from './rmos_run_viewer/AdvisoryExplanationPanel.vue'
import AttachmentsSection from './rmos_run_viewer/AttachmentsSection.vue'
import HashesSection from './rmos_run_viewer/HashesSection.vue'
import RunInfoSection from './rmos_run_viewer/RunInfoSection.vue'
import styles from './RmosRunViewerView.module.css'
import { buttons, loaders } from '@/styles/shared'

import {
  useRmosRunViewerState,
  useRmosRunViewerStyles,
  useRmosRunViewerActions
} from './rmos_run_viewer/composables'

const route = useRoute()
const router = useRouter()

// E-1: Agentic Spine event emission
const { emitViewRendered, emitDecisionRequired } = useAgenticEvents()

// State
const {
  run,
  loading,
  error,
  showWhy,
  runId,
  triggeredRuleIds,
  triggeredRules,
  hasExplainability,
  riskLevel,
  overrideAttachment,
  parentRunId,
  explainError,
  isExplaining,
  assistantExplanation,
  assistantExplanationAttachment
} = useRmosRunViewerState(route)

// Styles
const {
  statusBadgeClass,
  gateBadgeClass,
  riskBadgeClass,
  rulePillClass
} = useRmosRunViewerStyles()

// Actions
const {
  loadRun,
  generateAdvisoryExplanation,
  formatDate,
  handleDownload,
  goToDiff,
  goToDiffWithParent,
  goBack,
  downloadOperatorPack,
  downloadAttachment
} = useRmosRunViewerActions(
  router,
  runId,
  parentRunId,
  run,
  loading,
  error,
  isExplaining,
  explainError,
  assistantExplanation
)

// Auto-open Why on YELLOW/RED when explainability exists
watch(
  [riskLevel, hasExplainability],
  ([rl, hasExp]) => {
    if (!run.value) return
    if (!hasExp) return
    showWhy.value = rl === 'YELLOW' || rl === 'RED'

    // E-1: Emit decision_required for YELLOW/RED risks
    if (rl === 'YELLOW' || rl === 'RED') {
      emitDecisionRequired('risk_assessment', ['accept', 'override', 'reject'])
    }
  },
  { immediate: true }
)

onMounted(() => {
  emitViewRendered('rmos_run_viewer')
  loadRun()
})
watch(runId, loadRun)
</script>

<template>
  <div :class="styles.runViewer">
    <!-- Header -->
    <header :class="styles.viewerHeader">
      <div :class="styles.headerLeft">
        <button
          :class="styles.btnBack"
          @click="goBack"
        >
          &larr; Back to Runs
        </button>
        <h1>Run Viewer</h1>
      </div>
      <div
        v-if="run"
        :class="styles.headerActions"
      >
        <button
          v-if="hasExplainability"
          :class="buttons.btn"
          :aria-expanded="showWhy"
          title="Show why this decision happened"
          @click="showWhy = !showWhy"
        >
          Why?
        </button>
        <button
          :class="buttons.btn"
          @click="handleDownload"
        >
          Download JSON
        </button>
        <button
          :class="buttons.btnSuccess"
          :disabled="loading"
          @click="downloadOperatorPack"
        >
          Operator Pack (.zip)
        </button>
        <button
          :class="buttons.btnPrimary"
          @click="goToDiff"
        >
          Compare (Diff)
        </button>
        <button
          :class="buttons.btn"
          :disabled="!parentRunId"
          :title="parentRunId ? 'Compare with parent run: ' + parentRunId.slice(0, 16) + '...' : 'No parent run'"
          @click="goToDiffWithParent"
        >
          Compare with Parent
        </button>
      </div>
    </header>

    <!-- Loading State -->
    <div
      v-if="loading"
      :class="styles.stateLoading"
    >
      <div :class="loaders.spinnerLg" />
      <p>Loading run artifact...</p>
    </div>

    <!-- Error State -->
    <div
      v-else-if="error"
      :class="styles.stateError"
    >
      <h2>Error</h2>
      <p>{{ error }}</p>
      <button
        :class="buttons.btn"
        @click="loadRun"
      >
        Retry
      </button>
    </div>

    <!-- Run Details -->
    <div
      v-else-if="run"
      :class="styles.runContent"
    >
      <!-- Run ID Banner -->
      <section :class="styles.idBanner">
        <code :class="styles.runId">{{ run.run_id }}</code>
        <div :class="styles.statusBadges">
          <span :class="statusBadgeClass(run.status)">{{ run.status }}</span>
          <span
            v-if="run.workflow_mode"
            :class="styles.badgeMode"
          >{{ run.workflow_mode }}</span>
        </div>
      </section>

      <!-- Gate Decision (Risk Level) -->
      <section
        v-if="run.gate_decision || run.feasibility"
        :class="styles.decisionSection"
      >
        <h2>Decision</h2>
        <div :class="styles.decisionGrid">
          <div
            v-if="run.gate_decision"
            :class="styles.decisionItem"
          >
            <span :class="styles.decisionItemLabel">Gate:</span>
            <span :class="gateBadgeClass(run.gate_decision)">
              {{ run.gate_decision }}
            </span>
          </div>
          <div
            v-if="run.feasibility?.risk_level"
            :class="styles.decisionItem"
          >
            <span :class="styles.decisionItemLabel">Risk Level:</span>
            <span :class="riskBadgeClass(run.feasibility.risk_level)">
              {{ run.feasibility.risk_level }}
            </span>
          </div>
          <div
            v-if="run.feasibility?.warnings?.length"
            :class="styles.decisionItemWarnings"
          >
            <span :class="styles.decisionItemLabel">Warnings:</span>
            <ul>
              <li
                v-for="(w, i) in run.feasibility.warnings"
                :key="i"
              >
                {{ w }}
              </li>
            </ul>
          </div>
          <div
            v-if="run.feasibility?.block_reason"
            :class="styles.decisionItem"
          >
            <span :class="styles.decisionItemLabel">Block Reason:</span>
            <span :class="styles.blockText">{{ run.feasibility.block_reason }}</span>
          </div>
        </div>

        <!-- WhyPanel: auto-opens for YELLOW/RED; toggleable via header Why? button -->
        <WhyPanel
          v-if="hasExplainability && showWhy"
          :rules-triggered="triggeredRuleIds"
          :risk-level="riskLevel"
          class="mt-3"
        />

        <!-- Phase 3.3: Explainability - Legacy Why section (shown when WhyPanel is closed) -->
        <div
          v-if="hasExplainability && !showWhy"
          :class="styles.explainSection"
        >
          <h3>Why</h3>
          <ul :class="styles.explainList">
            <li
              v-for="r in triggeredRules"
              :key="r.rule_id"
              :class="styles.explainItem"
            >
              <span
                :class="rulePillClass(r.level)"
                :data-level="r.level"
              >{{ r.level }}</span>
              <span :class="styles.ruleId">{{ r.rule_id }}</span>
              <span :class="styles.ruleSummary">{{ r.summary }}</span>
              <span
                v-if="r.operator_hint"
                :class="styles.ruleHint"
              >{{ r.operator_hint }}</span>
            </li>
          </ul>
        </div>

        <!-- Override info -->
        <div
          v-if="overrideAttachment"
          :class="styles.overrideInfo"
        >
          <span :class="styles.decisionItemLabel">Override:</span>
          <span :class="styles.overrideText">
            Recorded (sha: <code>{{ overrideAttachment.sha256?.slice(0, 12) }}…</code>)
          </span>
        </div>

        <!-- Phase 5: Advisory Explanation -->
        <AdvisoryExplanationPanel
          :is-explaining="isExplaining"
          :error="explainError"
          :explanation="assistantExplanation"
          :has-attachment="!!assistantExplanationAttachment"
          :attachment-sha="assistantExplanationAttachment?.sha256"
          @generate="generateAdvisoryExplanation"
        />
      </section>

      <!-- Run Info -->
      <RunInfoSection
        :created-at="run.created_at_utc"
        :event-type="run.event_type"
        :tool-id="run.tool_id"
        :material-id="run.material_id"
        :machine-id="run.machine_id"
        :session-id="run.workflow_session_id"
        :parent-run-id="run.parent_run_id"
        :toolchain-id="run.toolchain_id"
        :post-processor-id="run.post_processor_id"
        :engine-version="run.engine_version"
        :format-date="formatDate"
      />

      <!-- Hashes -->
      <HashesSection
        :request-hash="run.request_hash"
        :toolpaths-hash="run.toolpaths_hash"
        :gcode-hash="run.gcode_hash"
        :geometry-hash="run.geometry_hash"
        :config-fingerprint="run.config_fingerprint"
      />

      <!-- Drift Warning -->
      <section
        v-if="run.drift_detected"
        :class="styles.driftSection"
      >
        <h2>Drift Detected</h2>
        <p>{{ run.drift_summary || "Configuration drift detected from parent run." }}</p>
      </section>

      <!-- Attachments -->
      <AttachmentsSection
        :attachments="run.attachments"
        :loading="loading"
        @download="downloadAttachment"
      />

      <!-- Feasibility Details -->
      <section
        v-if="run.feasibility"
        :class="styles.infoSection"
      >
        <h2>Feasibility</h2>
        <pre :class="styles.codeBlock">{{ JSON.stringify(run.feasibility, null, 2) }}</pre>
      </section>

      <!-- Notes -->
      <section
        v-if="run.notes"
        :class="styles.infoSection"
      >
        <h2>Notes</h2>
        <p :class="styles.notesText">
          {{ run.notes }}
        </p>
      </section>

      <!-- Errors -->
      <section
        v-if="run.errors?.length"
        :class="styles.errorSection"
      >
        <h2>Errors</h2>
        <ul>
          <li
            v-for="(err, i) in run.errors"
            :key="i"
          >
            {{ err }}
          </li>
        </ul>
      </section>

      <!-- Inline Compare Panel -->
      <section :class="styles.infoSection">
        <RunComparePanel
          :current-run-id="runId"
          :default-other-run-id="parentRunId"
        />
      </section>
    </div>

    <!-- No Run State -->
    <div
      v-else
      :class="styles.stateEmpty"
    >
      <p>No run ID provided</p>
      <button
        :class="buttons.btn"
        @click="goBack"
      >
        Go to Runs List
      </button>
    </div>
  </div>
</template>
