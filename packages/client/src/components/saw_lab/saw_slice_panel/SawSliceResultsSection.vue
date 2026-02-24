<script setup lang="ts">
/**
 * SawSliceResultsSection.vue - Validation results, learned params, G-code preview, run link
 * Extracted from SawSlicePanel.vue
 */
import styles from "../SawSlicePanel.module.css";

export interface ValidationCheck {
  result: "OK" | "WARN" | "ERROR";
  message: string;
}

export interface ValidationResult {
  overall_result: string;
  checks: Record<string, ValidationCheck>;
}

export interface MergedParams {
  rpm?: number;
  feed_ipm?: number;
  doc_mm?: number;
  lane_scale?: number;
}

export interface GcodeStats {
  totalLengthMm: number;
  depthPasses: number;
  estimatedTimeSec: number;
  gcodePreview: string;
}

const props = defineProps<{
  validationResult: ValidationResult | null;
  mergedParams: MergedParams | null;
  gcode: string | null;
  gcodeStats: GcodeStats | null;
  runId: string | null;
  baseRpm: number;
  baseFeedIpm: number;
  baseDepthPerPass: number;
}>();

const emit = defineEmits<{
  downloadGcode: [];
}>();

function formatCheckName(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function getOverallBadgeClass(result: string): string {
  const r = result.toLowerCase();
  if (r === "ok") return styles.validationBadgeOk;
  if (r === "warn") return styles.validationBadgeWarn;
  return styles.validationBadgeError;
}

function getCheckItemClass(result: string): string {
  const r = result.toLowerCase();
  if (r === "ok") return styles.checkItemOk;
  if (r === "warn") return styles.checkItemWarn;
  return styles.checkItemError;
}
</script>

<template>
  <!-- Validation Results -->
  <div
    v-if="validationResult"
    :class="styles.validationResults"
  >
    <h3>Validation Results</h3>
    <div :class="getOverallBadgeClass(validationResult.overall_result)">
      {{ validationResult.overall_result }}
    </div>
    <div :class="styles.validationChecks">
      <div
        v-for="(check, key) in validationResult.checks"
        :key="key"
        :class="getCheckItemClass(check.result)"
      >
        <span :class="styles.checkIcon">{{
          check.result === "OK"
            ? "✓"
            : check.result === "WARN"
              ? "⚠"
              : "✗"
        }}</span>
        <span :class="styles.checkName">{{ formatCheckName(String(key)) }}</span>
        <span :class="styles.checkMessage">{{ check.message }}</span>
      </div>
    </div>
  </div>

  <!-- Learned Parameters -->
  <div
    v-if="mergedParams"
    :class="styles.learnedParams"
  >
    <h3>Learned Parameters Applied</h3>
    <div :class="styles.paramComparison">
      <div :class="styles.paramRow">
        <span :class="styles.paramLabel">RPM:</span>
        <span :class="styles.paramBaseline">{{ baseRpm }}</span>
        <span :class="styles.paramArrow">→</span>
        <span :class="styles.paramMerged">{{
          mergedParams.rpm?.toFixed(0) || baseRpm
        }}</span>
      </div>
      <div :class="styles.paramRow">
        <span :class="styles.paramLabel">Feed:</span>
        <span :class="styles.paramBaseline">{{ baseFeedIpm }}</span>
        <span :class="styles.paramArrow">→</span>
        <span :class="styles.paramMerged">{{
          mergedParams.feed_ipm?.toFixed(1) || baseFeedIpm
        }}</span>
      </div>
      <div :class="styles.paramRow">
        <span :class="styles.paramLabel">DOC:</span>
        <span :class="styles.paramBaseline">{{ baseDepthPerPass }}</span>
        <span :class="styles.paramArrow">→</span>
        <span :class="styles.paramMerged">{{
          mergedParams.doc_mm?.toFixed(1) || baseDepthPerPass
        }}</span>
      </div>
    </div>
    <div :class="styles.laneInfo">
      Lane scale: {{ mergedParams.lane_scale?.toFixed(2) || "1.00" }}
    </div>
  </div>

  <!-- G-code Preview -->
  <div
    v-if="gcode && gcodeStats"
    :class="styles.gcodePreview"
  >
    <h3>G-code Preview</h3>
    <div :class="styles.previewStats">
      <div :class="styles.stat">
        <span :class="styles.statLabel">Total Length:</span>
        <span :class="styles.statValue">{{ gcodeStats.totalLengthMm.toFixed(1) }} mm</span>
      </div>
      <div :class="styles.stat">
        <span :class="styles.statLabel">Depth Passes:</span>
        <span :class="styles.statValue">{{ gcodeStats.depthPasses }}</span>
      </div>
      <div :class="styles.stat">
        <span :class="styles.statLabel">Est. Time:</span>
        <span :class="styles.statValue">{{ gcodeStats.estimatedTimeSec.toFixed(0) }}s</span>
      </div>
    </div>
    <pre :class="styles.gcodeText">{{ gcodeStats.gcodePreview }}</pre>
    <button
      :class="styles.btnSecondary"
      @click="emit('downloadGcode')"
    >
      Download G-code
    </button>
  </div>

  <!-- Run Artifact Link -->
  <div
    v-if="runId"
    :class="styles.runArtifactLink"
  >
    <h3>Run Artifact</h3>
    <p>
      Job logged with Run ID: <code>{{ runId }}</code>
    </p>
    <router-link
      :to="`/rmos/runs?run_id=${runId}`"
      :class="styles.btnPrimary"
    >
      View Run Artifact
    </router-link>
  </div>
</template>
