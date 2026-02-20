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

// CSS Module class helper for asset card selection
function assetCardClass(sha: string, selectedSha: string | null): string {
  return selectedSha === sha ? styles.assetCardSelected : styles.assetCard;
}

/** Base URL for cross-origin API deployments */
const API_BASE = (import.meta as any).env?.VITE_API_BASE || '';

/**
 * Resolve asset URL to full URL (handles cross-origin deployments).
 * If url is relative (starts with /), prepend API_BASE.
 */
function resolveAssetUrl(url: string): string {
  if (!url) return '/placeholder.svg';
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:')) {
    return url;
  }
  // Relative URL - prepend API_BASE
  return `${API_BASE}${url}`;
}

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

// =============================================================================
// UTILITIES
// =============================================================================

function truncate(s: string, len: number): string {
  return s.length > len ? s.slice(0, len) + "..." : s;
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
    <section
      v-if="generatedAssets.length > 0"
      :class="styles.section"
    >
      <h4>2. Select Asset</h4>
      <div :class="styles.assetsGrid">
        <div
          v-for="asset in generatedAssets"
          :key="asset.sha256"
          :class="assetCardClass(asset.sha256, selectedAssetSha)"
          @click="selectAsset(asset.sha256)"
        >
          <div :class="styles.assetPreview">
            <img
              :src="resolveAssetUrl(asset.url)"
              :alt="asset.filename"
              loading="lazy"
              @error="($event.target as HTMLImageElement).src = '/placeholder.svg'"
            >
          </div>
          <div :class="styles.assetInfo">
            <div
              :class="styles.assetFilename"
              :title="asset.filename"
            >
              {{ truncate(asset.filename, 20) }}
            </div>
            <div :class="styles.assetMeta">
              <span
                :class="styles.assetSha"
                :title="asset.sha256"
              >
                {{ asset.sha256.slice(0, 8) }}...
              </span>
              <span :class="styles.assetProvider">{{ asset.provider }}</span>
            </div>
          </div>
          <div
            v-if="selectedAssetSha === asset.sha256"
            :class="styles.checkBadge"
          >
            &#10003;
          </div>
        </div>
      </div>
    </section>

    <!-- Run Selection Section -->
    <section
      v-if="selectedAssetSha"
      :class="styles.section"
    >
      <div :class="styles.stepHeader">
        <h4>3. Select Run</h4>
        <button
          :class="styles.btn"
          type="button"
          :disabled="isLoadingRuns"
          @click="loadRuns"
        >
          Refresh
        </button>
      </div>

      <!-- Search + Create row -->
      <div :class="styles.runTools">
        <input
          v-model="runSearch"
          :class="styles.runSearchInput"
          placeholder="Search runs (id / event_type)…"
          :disabled="isLoadingRuns"
          @keydown.enter.prevent="loadRuns"
        >
        <button
          :class="styles.btn"
          type="button"
          :disabled="isLoadingRuns"
          @click="loadRuns"
        >
          Search
        </button>
        <button
          :class="styles.btnPrimary"
          type="button"
          :disabled="isLoadingRuns"
          @click="createAndSelectRun"
        >
          + Create Run
        </button>
      </div>

      <!-- Empty state message -->
      <div
        v-if="runs.length === 0 && !isLoadingRuns"
        :class="styles.emptyHint"
      >
        No runs available.
        <div :class="styles.hintTip">
          Tip: click <strong>+ Create Run</strong> to start a <code>vision_image_review</code> run.
        </div>
      </div>

      <!-- Run dropdown selector -->
      <div
        v-else-if="runs.length > 0"
        :class="styles.runSelector"
      >
        <label :class="styles.formLabel">Recent runs</label>
        <select
          v-model="selectedRunId"
          :class="styles.runSelect"
        >
          <option
            :value="null"
            disabled
          >
            Select a run...
          </option>
          <option
            v-for="run in runs"
            :key="run.run_id"
            :value="run.run_id"
          >
            {{ run.run_id.slice(0, 16) }}... {{ run.event_type ? `• ${run.event_type}` : "" }}
          </option>
        </select>

        <div :class="styles.runPickerFooter">
          <button
            v-if="runsHasMore"
            :class="styles.btn"
            type="button"
            :disabled="isLoadingRuns"
            @click="loadMoreRuns"
          >
            Load more
          </button>
          <div
            v-else
            :class="styles.runsCount"
          >
            Showing {{ runs.length }} run(s)
          </div>
        </div>
      </div>
    </section>

    <!-- Attach Action -->
    <section
      v-if="selectedAssetSha && selectedRunId"
      :class="styles.actionSection"
    >
      <h4>4. Attach</h4>
      <div :class="styles.attachSummary">
        <div :class="styles.summaryItem">
          <span :class="styles.summaryItemLabel">Asset:</span>
          <span :class="styles.summaryItemValue">{{ selectedAsset?.sha256.slice(0, 12) }}...</span>
        </div>
        <div :class="styles.summaryItem">
          <span :class="styles.summaryItemLabel">Run:</span>
          <span :class="styles.summaryItemValue">{{ selectedRunId?.slice(0, 12) }}...</span>
        </div>
      </div>
      <button
        :class="styles.attachBtn"
        :disabled="!canAttach"
        @click="attachToRun"
      >
        <span v-if="isAttaching">Attaching...</span>
        <span v-else>Attach &amp; Review</span>
      </button>
      <div
        v-if="successMessage && !autoNavigate && lastAttached"
        :class="styles.successActions"
      >
        <button
          :class="styles.btn"
          type="button"
          @click="goToReview(lastAttached.runId)"
        >
          Go to Review
        </button>
      </div>
    </section>
  </div>
</template>
