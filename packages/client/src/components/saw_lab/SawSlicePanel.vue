<template>
  <div :class="styles.sawSlicePanel">
    <div :class="styles.panelHeader">
      <h2>Saw Slice Operation</h2>
      <p :class="styles.subtitle">
        Kerf-aware straight cuts with multi-pass depth control
      </p>
    </div>

    <div :class="styles.panelContent">
      <!-- Left Column: Parameters -->
      <SawSliceParametersForm
        :form-state="formState"
        :blades="blades"
        :selected-blade="selectedBlade"
        :can-validate="canValidate"
        :can-merge="canMerge"
        :is-valid="isValid"
        :has-gcode="hasGcode"
        @update:form-state="formState = $event"
        @blade-change="handleBladeChange"
        @validate="validateOperation"
        @merge-learned-params="mergeLearnedParams"
        @generate-gcode="generateGcode"
        @send-to-job-log="sendToJobLog"
      />

      <!-- Right Column: Preview & Validation -->
      <div :class="styles.previewSection">
        <!-- Validation, Learned Params, G-code Preview, Run Link -->
        <SawSliceResultsSection
          :validation-result="validationResult"
          :merged-params="mergedParams"
          :gcode="gcode"
          :gcode-stats="gcodeStats"
          :run-id="runId"
          :base-rpm="formState.rpm"
          :base-feed-ipm="formState.feedIpm"
          :base-depth-per-pass="formState.depthPerPass"
          @download-gcode="downloadGcode"
        />

        <!-- SVG Preview -->
        <SawSlicePathPreview
          :geometry="pathGeometry"
          :kerf-mm="selectedBlade?.kerf_mm ?? null"
          :svg-view-box="svgViewBox"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * SawSlicePanel.vue - Kerf-aware straight cuts with multi-pass depth control
 *
 * REFACTORED: Uses composables for cleaner separation:
 * - useSawBladeRegistry: Blade loading and selection
 * - useSawSliceGcode: G-code generation, preview, statistics
 * - useSawSliceApi: Validation, learned params, job log
 *
 * DECOMPOSED: Template sections extracted to child components:
 * - SawSliceParametersForm: Form inputs and action buttons
 * - SawSliceResultsSection: Validation, learned params, gcode preview, run link
 * - SawSlicePathPreview: SVG path visualization
 */
import { reactive, computed, onMounted, watch } from "vue";
import {
  useSawBladeRegistry,
  useSawSliceGcode,
  useSawSliceApi,
} from "./composables";
import styles from "./SawSlicePanel.module.css";
import {
  SawSliceParametersForm,
  SawSlicePathPreview,
  SawSliceResultsSection,
  type SawSliceFormState,
  type GcodeStats,
} from "./saw_slice_panel";

// ============================================================================
// Form State (reactive object for child component binding)
// ============================================================================

const formState = reactive<SawSliceFormState>({
  selectedBladeId: "",
  machineProfile: "bcam_router_2030",
  materialFamily: "hardwood",
  startX: 0,
  startY: 0,
  endX: 100,
  endY: 0,
  totalDepth: 12,
  depthPerPass: 3,
  rpm: 3600,
  feedIpm: 120,
  safeZ: 5,
});

// ============================================================================
// Composables
// ============================================================================

// Blade registry
const bladeRegistry = useSawBladeRegistry(() => {
  // Clear validation when blade changes
  sliceApi.clearValidation();
});

// Convenience aliases
const { blades, selectedBladeId, selectedBlade, loadBlades, onBladeChange } =
  bladeRegistry;

// Sync blade selection between formState and composable
watch(
  () => formState.selectedBladeId,
  (newId) => {
    if (selectedBladeId.value !== newId) {
      selectedBladeId.value = newId;
    }
  }
);

function handleBladeChange() {
  selectedBladeId.value = formState.selectedBladeId;
  onBladeChange();
}

// G-code generation
const gcodeGen = useSawSliceGcode(
  () => ({
    startX: formState.startX,
    startY: formState.startY,
    endX: formState.endX,
    endY: formState.endY,
  }),
  () => ({
    totalDepth: formState.totalDepth,
    depthPerPass: formState.depthPerPass,
    rpm: formState.rpm,
    feedIpm: formState.feedIpm,
    safeZ: formState.safeZ,
  }),
  () => selectedBlade.value,
  () => formState.materialFamily
);

// Convenience aliases
const {
  gcode,
  hasGcode,
  depthPasses,
  totalLengthMm,
  estimatedTimeSec,
  gcodePreview,
  svgViewBox,
  generateGcode,
  downloadGcode,
} = gcodeGen;

// API operations
const sliceApi = useSawSliceApi(
  {
    getBlade: () => selectedBlade.value,
    getBladeId: () => formState.selectedBladeId,
    getMaterial: () => formState.materialFamily,
    getMachine: () => formState.machineProfile,
    getRpm: () => formState.rpm,
    getFeedIpm: () => formState.feedIpm,
    getDepthPerPass: () => formState.depthPerPass,
    getSafeZ: () => formState.safeZ,
    getDepthPasses: () => depthPasses.value,
    getTotalLengthMm: () => totalLengthMm.value,
    getStartX: () => formState.startX,
    getStartY: () => formState.startY,
    getEndX: () => formState.endX,
    getEndY: () => formState.endY,
  },
  (merged) => {
    // Apply merged params to form
    formState.rpm = merged.rpm;
    formState.feedIpm = merged.feed_ipm;
    formState.depthPerPass = merged.doc_mm;
  }
);

// Convenience aliases
const {
  validationResult,
  mergedParams,
  runId,
  isValid,
  validateOperation,
  mergeLearnedParams,
  sendToJobLog,
} = sliceApi;

// ============================================================================
// Computed (for child components)
// ============================================================================

const canValidate = computed((): boolean => {
  return Boolean(
    formState.selectedBladeId &&
    formState.startX !== null &&
    formState.endX !== null
  );
});

const canMerge = computed((): boolean => {
  return Boolean(
    formState.selectedBladeId &&
    formState.machineProfile &&
    formState.materialFamily
  );
});

const pathGeometry = computed(() => ({
  startX: formState.startX,
  startY: formState.startY,
  endX: formState.endX,
  endY: formState.endY,
}));

const gcodeStats = computed<GcodeStats | null>(() => {
  if (!gcode.value) return null;
  return {
    totalLengthMm: totalLengthMm.value,
    depthPasses: depthPasses.value,
    estimatedTimeSec: estimatedTimeSec.value,
    gcodePreview: gcodePreview.value,
  };
});

// ============================================================================
// Lifecycle
// ============================================================================

onMounted(() => {
  loadBlades();
});
</script>
