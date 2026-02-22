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
import RunComparePanel from '@/components/rmos/RunComparePanel.vue'
import RiskBadge from '@/components/ui/RiskBadge.vue'
import OverrideBanner from '@/components/ui/OverrideBanner.vue'
import WhyPanel from '@/components/rmos/WhyPanel.vue'
import styles from './RmosRunViewerView.module.css'
import { buttons, badges, loaders } from '@/styles/shared'

import {
  useRmosRunViewerState,
  useRmosRunViewerStyles,
  useRmosRunViewerActions
} from './rmos_run_viewer/composables'

const route = useRoute()
const router = useRouter()

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
  },
  { immediate: true }
)

onMounted(loadRun)
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
        <div :class="styles.advisorySection">
          <div :class="styles.advisoryHead">
            <h3>Advisory Explanation</h3>
            <div :class="styles.advisoryActions">
              <button
                :class="buttons.btnSm"
                :disabled="isExplaining"
                @click="generateAdvisoryExplanation(false)"
              >
                {{ assistantExplanationAttachment ? 'Refresh Advisory' : 'Generate Advisory' }}
              </button>
              <button
                :class="buttons.btnSm"
                :disabled="isExplaining"
                title="Regenerate even if one exists"
                @click="generateAdvisoryExplanation(true)"
              >
                Regenerate (force)
              </button>
            </div>
          </div>
          <div
            v-if="explainError"
            :class="styles.advisoryError"
          >
            {{ explainError }}
          </div>
          <div
            v-else-if="isExplaining"
            :class="styles.advisoryLoading"
          >
            Generating advisory explanation…
          </div>

          <div
            v-if="assistantExplanation"
            :class="styles.advisoryBox"
          >
            <div :class="styles.advisorySummary">
              {{ assistantExplanation.summary }}
            </div>
            <div
              v-if="assistantExplanation.operator_notes?.length"
              :class="styles.advisorySubsection"
            >
              <h4>Operator Notes</h4>
              <ul>
                <li
                  v-for="(n, idx) in assistantExplanation.operator_notes"
                  :key="idx"
                >
                  {{ n }}
                </li>
              </ul>
            </div>
            <div
              v-if="assistantExplanation.suggested_actions?.length"
              :class="styles.advisorySubsection"
            >
              <h4>Suggested Actions</h4>
              <ul>
                <li
                  v-for="(a, idx) in assistantExplanation.suggested_actions"
                  :key="idx"
                >
                  {{ a }}
                </li>
              </ul>
            </div>
            <div :class="styles.advisoryDisclaimer">
              {{ assistantExplanation.disclaimer }}
            </div>
          </div>
          <div
            v-else-if="assistantExplanationAttachment"
            :class="styles.advisoryPlaceholder"
          >
            assistant_explanation.json attached (sha: <code>{{ assistantExplanationAttachment.sha256?.slice(0, 12) }}</code>…)
            — click "Refresh Advisory" to load it.
          </div>
          <div
            v-else
            :class="styles.advisoryEmpty"
          >
            No advisory explanation generated for this run.
          </div>
        </div>
      </section>

      <!-- Run Info -->
      <section :class="styles.infoSection">
        <h2>Run Info</h2>
        <div :class="styles.infoGrid">
          <div><strong>Created:</strong> {{ formatDate(run.created_at_utc) }}</div>
          <div><strong>Event Type:</strong> {{ run.event_type }}</div>
          <div><strong>Tool ID:</strong> {{ run.tool_id || "---" }}</div>
          <div><strong>Material ID:</strong> {{ run.material_id || "---" }}</div>
          <div><strong>Machine ID:</strong> {{ run.machine_id || "---" }}</div>
          <div><strong>Session:</strong> {{ run.workflow_session_id?.slice(0, 16) || "---" }}</div>
          <div><strong>Parent Run:</strong> {{ run.parent_run_id?.slice(0, 16) || "---" }}</div>
          <div><strong>Toolchain:</strong> {{ run.toolchain_id || "---" }}</div>
          <div><strong>Post Processor:</strong> {{ run.post_processor_id || "---" }}</div>
          <div><strong>Engine Version:</strong> {{ run.engine_version || "---" }}</div>
        </div>
      </section>

      <!-- Hashes -->
      <section :class="styles.infoSection">
        <h2>Hashes</h2>
        <div :class="styles.hashGrid">
          <div v-if="run.request_hash">
            <strong>Request:</strong>
            <code>{{ run.request_hash }}</code>
          </div>
          <div v-if="run.toolpaths_hash">
            <strong>Toolpaths:</strong>
            <code>{{ run.toolpaths_hash }}</code>
          </div>
          <div v-if="run.gcode_hash">
            <strong>G-code:</strong>
            <code>{{ run.gcode_hash }}</code>
          </div>
          <div v-if="run.geometry_hash">
            <strong>Geometry:</strong>
            <code>{{ run.geometry_hash }}</code>
          </div>
          <div v-if="run.config_fingerprint">
            <strong>Config:</strong>
            <code>{{ run.config_fingerprint }}</code>
          </div>
          <div
            v-if="!run.request_hash && !run.toolpaths_hash && !run.gcode_hash && !run.geometry_hash && !run.config_fingerprint"
            :class="styles.emptyState"
          >
            No hashes recorded
          </div>
        </div>
      </section>

      <!-- Drift Warning -->
      <section
        v-if="run.drift_detected"
        :class="styles.driftSection"
      >
        <h2>Drift Detected</h2>
        <p>{{ run.drift_summary || "Configuration drift detected from parent run." }}</p>
      </section>

      <!-- Attachments -->
      <section :class="styles.infoSection">
        <h2>Attachments ({{ run.attachments?.length || 0 }})</h2>
        <div
          v-if="run.attachments?.length"
          :class="styles.attachmentList"
        >
          <div
            v-for="att in run.attachments"
            :key="att.sha256"
            :class="styles.attachmentItem"
          >
            <span :class="styles.attKind">{{ att.kind }}</span>
            <span :class="styles.attName">{{ att.filename }}</span>
            <span :class="styles.attMime">{{ att.mime }}</span>
            <span :class="styles.attSize">{{ (att.size_bytes / 1024).toFixed(1) }} KB</span>
            <button
              :class="buttons.btnSm"
              :disabled="loading"
              @click="downloadAttachment(att)"
            >
              Download
            </button>
          </div>
        </div>
        <div
          v-else
          :class="styles.emptyState"
        >
          No attachments
        </div>
      </section>

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
