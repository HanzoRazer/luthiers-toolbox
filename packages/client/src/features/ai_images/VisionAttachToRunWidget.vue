<script setup lang="ts">
/**
 * Vision Attach-to-Run Widget
 *
 * Allows users to:
 * 1. Generate images via the Vision API
 * 2. View generated assets (with sha256 identity)
 * 3. Select a run to attach to
 * 4. Attach the asset to the run's advisory_inputs
 *
 * Implements the canonical Phase B hybrid architecture.
 *
 * @package features/ai_images
 */

import { ref, computed, onMounted } from "vue";
import {
  useVisionProviders,
  useVisionGeneration,
  useRunSelection,
  useVisionAttach,
} from "./composables";
import styles from "./VisionAttachToRunWidget.module.css";
import GeneratedAssetsSection from "./vision_attach/GeneratedAssetsSection.vue";
import RunSelectionSection from "./vision_attach/RunSelectionSection.vue";
import AttachActionSection from "./vision_attach/AttachActionSection.vue";


// =============================================================================
// PROPS & EMITS
// =============================================================================

const props = defineProps<{
  /** Pre-select a run ID (optional) */
  runId?: string;
  /** Initial prompt (optional) */
  initialPrompt?: string;
  /**
   * When true (default), after a successful attach the widget deep-links to the
   * run variants review surface.
   */
  autoNavigateToReview?: boolean;
}>();

const emit = defineEmits<{
  (e: "attached", payload: { runId: string; advisoryId: string }): void;
  (e: "close"): void;
  (e: "error", message: string): void;
}>();

// =============================================================================
// COMPOSABLES
// =============================================================================

// Providers
const {
  providers,
  provider,
  configuredProviders,
  loadProviders,
} = useVisionProviders();

// Generation
const {
  prompt,
  numImages,
  size,
  quality,
  generatedAssets,
  selectedAssetSha,
  isGenerating,
  canGenerate,
  selectedAsset,
  generate: doGenerate,
  selectAsset,
} = useVisionGeneration(() => provider.value, props.initialPrompt);

// Runs
const {
  runs,
  selectedRunId,
  runSearch,
  runsHasMore,
  isLoadingRuns,
  loadRuns,
  loadMoreRuns,
  createAndSelectRun: doCreateAndSelectRun,
  selectRun,
} = useRunSelection(props.runId, (msg) => {
  error.value = msg;
  emit("error", msg);
});

// Computed for auto-navigate
const autoNavigate = computed(() => props.autoNavigateToReview !== false);

// Attach
const {
  isAttaching,
  lastAttached,
  canAttach,
  attachToRun: doAttachToRun,
  goToReview,
} = useVisionAttach(
  () => selectedAssetSha.value,
  () => selectedRunId.value,
  () => selectedAsset.value,
  () => autoNavigate.value
);

// =============================================================================
// LOCAL STATE (UI messages)
// =============================================================================

const error = ref<string | null>(null);
const successMessage = ref<string | null>(null);

// =============================================================================
// LIFECYCLE
// =============================================================================

onMounted(async () => {
  await Promise.all([loadProviders(), loadRuns()]);
});

// =============================================================================
// METHODS (wrapped for error/success handling)
// =============================================================================

async function generate() {
  error.value = null;
  successMessage.value = null;

  const result = await doGenerate();
  if (result.success) {
    successMessage.value = `Generated ${result.count} image(s)`;
  } else {
    error.value = result.error || "Failed to generate images";
    emit("error", error.value);
  }
}

async function createAndSelectRun() {
  error.value = null;
  successMessage.value = null;

  const result = await doCreateAndSelectRun();
  if (result.runId) {
    successMessage.value = `Created run ${result.runId}`;
  } else if (result.error) {
    error.value = result.error;
    emit("error", result.error);
  }
}

async function attachToRun() {
  error.value = null;
  successMessage.value = null;

  const result = await doAttachToRun();
  if (result.success) {
    successMessage.value = result.message || "Attached";
    if (lastAttached.value) {
      emit("attached", { runId: lastAttached.value.runId, advisoryId: lastAttached.value.advisoryId });
    }
  } else {
    error.value = result.error || "Failed to attach to run";
    emit("error", error.value);
  }
}

</script>

<template>
  <div :class="styles.visionAttachWidget">
    <!-- Header -->
    <div :class="styles.widgetHeader">
      <h3>Vision &rarr; Attach to Run</h3>
      <button
        :class="styles.closeBtn"
        title="Close"
        @click="emit('close')"
      >
        &times;
      </button>
    </div>

    <!-- Messages -->
    <div
      v-if="error"
      :class="styles.messageError"
    >
      {{ error }}
    </div>
    <div
      v-if="successMessage"
      :class="styles.messageSuccess"
    >
      {{ successMessage }}
    </div>

    <!-- Generation Section -->
    <section :class="styles.section">
      <h4>1. Generate Image</h4>
      <div :class="styles.formRow">
        <label>Prompt</label>
        <textarea
          v-model="prompt"
          placeholder="Describe the image you want to generate..."
          rows="3"
        />
      </div>

      <div :class="styles.formRowInline">
        <div :class="styles.formField">
          <label>Provider</label>
          <select v-model="provider">
            <option
              v-for="p in configuredProviders"
              :key="p.name"
              :value="p.name"
            >
              {{ p.name }}
            </option>
          </select>
        </div>

        <div :class="styles.formField">
          <label>Count</label>
          <select v-model="numImages">
            <option :value="1">
              1
            </option>
            <option :value="2">
              2
            </option>
            <option :value="4">
              4
            </option>
          </select>
        </div>

        <div :class="styles.formField">
          <label>Quality</label>
          <select v-model="quality">
            <option value="standard">
              Standard
            </option>
            <option value="hd">
              HD
            </option>
          </select>
        </div>
      </div>

      <button
        :class="styles.btnPrimary"
        :disabled="!canGenerate"
        @click="generate"
      >
        <span v-if="isGenerating">Generating...</span>
        <span v-else>Generate</span>
      </button>
    </section>

    <!-- Assets Section -->
    <GeneratedAssetsSection
      v-if="generatedAssets.length > 0"
      :assets="generatedAssets"
      :selected-asset-sha="selectedAssetSha"
      :styles="styles"
      @select-asset="selectAsset"
    />

    <!-- Run Selection Section -->
    <RunSelectionSection
      v-if="selectedAssetSha"
      :runs="runs"
      :selected-run-id="selectedRunId"
      :run-search="runSearch"
      :runs-has-more="runsHasMore"
      :is-loading-runs="isLoadingRuns"
      :styles="styles"
      @update:selected-run-id="$event && selectRun($event)"
      @update:run-search="runSearch = $event"
      @load-runs="loadRuns"
      @load-more-runs="loadMoreRuns"
      @create-run="createAndSelectRun"
    />

    <!-- Attach Action -->
    <AttachActionSection
      v-if="selectedAssetSha && selectedRunId"
      :selected-asset-sha="selectedAssetSha"
      :selected-run-id="selectedRunId"
      :can-attach="canAttach"
      :is-attaching="isAttaching"
      :show-go-to-review="!!successMessage && !autoNavigate && !!lastAttached"
      :last-attached-run-id="lastAttached?.runId ?? null"
      :styles="styles"
      @attach="attachToRun"
      @go-to-review="goToReview"
    />
  </div>
</template>
