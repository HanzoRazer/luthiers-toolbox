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
import { useRouter } from "vue-router";
import {
  generateImages,
  attachAdvisoryToRun,
  listRecentRuns,
  createRun,
  getProviders,
  type VisionAsset,
  type VisionGenerateRequest,
  type RunSummary,
  type VisionProvider,
  type ProviderName,
} from "./api/visionApi";

const router = useRouter();

const DEFAULT_EVENT_TYPE = "vision_image_review";

// =============================================================================
// PROPS & EMITS
// =============================================================================

const props = defineProps<{
  /** Pre-select a run ID (optional) */
  runId?: string;
  /** Initial prompt (optional) */
  initialPrompt?: string;
}>();

const emit = defineEmits<{
  (e: "attached", payload: { runId: string; advisoryId: string }): void;
  (e: "close"): void;
  (e: "error", message: string): void;
}>();

// =============================================================================
// STATE
// =============================================================================

// Generation
const prompt = ref(props.initialPrompt || "");
const provider = ref<ProviderName>("openai");
const numImages = ref(1);
const size = ref("1024x1024");
const quality = ref("standard");

// Generated assets
const generatedAssets = ref<VisionAsset[]>([]);
const selectedAssetSha = ref<string | null>(null);

// Runs
const runs = ref<RunSummary[]>([]);
const selectedRunId = ref<string | null>(props.runId || null);

// Providers
const providers = ref<VisionProvider[]>([]);

// UI state
const isGenerating = ref(false);
const isAttaching = ref(false);
const isLoadingRuns = ref(false);
const error = ref<string | null>(null);
const successMessage = ref<string | null>(null);

// =============================================================================
// COMPUTED
// =============================================================================

const canGenerate = computed(() => {
  return prompt.value.trim().length > 0 && !isGenerating.value;
});

const canAttach = computed(() => {
  return (
    selectedAssetSha.value !== null &&
    selectedRunId.value !== null &&
    !isAttaching.value
  );
});

const selectedAsset = computed(() => {
  if (!selectedAssetSha.value) return null;
  return generatedAssets.value.find((a) => a.sha256 === selectedAssetSha.value);
});

const configuredProviders = computed(() => {
  return providers.value.filter((p) => p.configured);
});

// =============================================================================
// LIFECYCLE
// =============================================================================

onMounted(async () => {
  await Promise.all([loadProviders(), loadRuns()]);
});

// =============================================================================
// METHODS
// =============================================================================

async function loadProviders() {
  try {
    const res = await getProviders();
    providers.value = res.providers;

    // Default to first configured provider
    const configured = res.providers.find((p) => p.configured);
    if (configured) {
      provider.value = configured.name as ProviderName;
    }
  } catch (e: any) {
    console.warn("Failed to load providers:", e);
  }
}

async function loadRuns() {
  isLoadingRuns.value = true;
  try {
    const res = await listRecentRuns(20);
    runs.value = res.runs || [];
  } catch (e: any) {
    console.warn("Failed to load runs:", e);
    runs.value = [];
  } finally {
    isLoadingRuns.value = false;
  }
}

async function createAndSelectRun() {
  error.value = null;
  successMessage.value = null;
  isLoadingRuns.value = true;
  try {
    const res = await createRun({ event_type: DEFAULT_EVENT_TYPE });
    selectedRunId.value = res.run_id;
    await loadRuns();
    successMessage.value = `Created run ${res.run_id.slice(0, 12)}...`;
  } catch (e: any) {
    const msg = e?.message ?? "Failed to create run";
    error.value = msg;
    emit("error", msg);
  } finally {
    isLoadingRuns.value = false;
  }
}

async function generate() {
  if (!canGenerate.value) return;

  error.value = null;
  successMessage.value = null;
  isGenerating.value = true;

  try {
    const request: VisionGenerateRequest = {
      prompt: prompt.value.trim(),
      provider: provider.value,
      num_images: numImages.value,
      size: size.value,
      quality: quality.value,
    };

    const res = await generateImages(request);
    generatedAssets.value = [...res.assets, ...generatedAssets.value];

    // Auto-select first generated asset
    if (res.assets.length > 0) {
      selectedAssetSha.value = res.assets[0].sha256;
    }

    successMessage.value = `Generated ${res.assets.length} image(s)`;
  } catch (e: any) {
    error.value = e.message || "Failed to generate images";
    emit("error", error.value);
  } finally {
    isGenerating.value = false;
  }
}

async function attachToRun() {
  if (!canAttach.value || !selectedAssetSha.value || !selectedRunId.value) return;

  error.value = null;
  successMessage.value = null;
  isAttaching.value = true;

  try {
    const asset = selectedAsset.value;
    const res = await attachAdvisoryToRun(selectedRunId.value, {
      advisory_id: selectedAssetSha.value,
      kind: "advisory",
      mime: asset?.mime,
      filename: asset?.filename,
      size_bytes: asset?.size_bytes,
    });

    if (res.attached) {
      successMessage.value = `Attached to run ${res.run_id.slice(0, 8)}...`;
      emit("attached", { runId: res.run_id, advisoryId: res.advisory_id });
      // Deep-link to canonical review surface
      router.push({ name: "RunVariantsReview", params: { run_id: res.run_id } });
    } else {
      successMessage.value = res.message || "Already attached";
    }
  } catch (e: any) {
    error.value = e.message || "Failed to attach to run";
    emit("error", error.value);
  } finally {
    isAttaching.value = false;
  }
}

function selectAsset(sha: string) {
  selectedAssetSha.value = sha;
}

function selectRun(runId: string) {
  selectedRunId.value = runId;
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function truncate(s: string, len: number): string {
  return s.length > len ? s.slice(0, len) + "..." : s;
}
</script>

<template>
  <div class="vision-attach-widget">
    <!-- Header -->
    <div class="widget-header">
      <h3>Vision &rarr; Attach to Run</h3>
      <button class="close-btn" @click="emit('close')" title="Close">&times;</button>
    </div>

    <!-- Messages -->
    <div v-if="error" class="message error">{{ error }}</div>
    <div v-if="successMessage" class="message success">{{ successMessage }}</div>

    <!-- Generation Section -->
    <section class="section">
      <h4>1. Generate Image</h4>
      <div class="form-row">
        <label>Prompt</label>
        <textarea
          v-model="prompt"
          placeholder="Describe the image you want to generate..."
          rows="3"
        ></textarea>
      </div>

      <div class="form-row-inline">
        <div class="form-field">
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

        <div class="form-field">
          <label>Count</label>
          <select v-model="numImages">
            <option :value="1">1</option>
            <option :value="2">2</option>
            <option :value="4">4</option>
          </select>
        </div>

        <div class="form-field">
          <label>Quality</label>
          <select v-model="quality">
            <option value="standard">Standard</option>
            <option value="hd">HD</option>
          </select>
        </div>
      </div>

      <button
        class="btn primary"
        :disabled="!canGenerate"
        @click="generate"
      >
        <span v-if="isGenerating">Generating...</span>
        <span v-else>Generate</span>
      </button>
    </section>

    <!-- Assets Section -->
    <section class="section" v-if="generatedAssets.length > 0">
      <h4>2. Select Asset</h4>
      <div class="assets-grid">
        <div
          v-for="asset in generatedAssets"
          :key="asset.sha256"
          class="asset-card"
          :class="{ selected: selectedAssetSha === asset.sha256 }"
          @click="selectAsset(asset.sha256)"
        >
          <div class="asset-preview">
            <img
              :src="asset.url"
              :alt="asset.filename"
              loading="lazy"
              @error="($event.target as HTMLImageElement).src = '/placeholder.svg'"
            />
          </div>
          <div class="asset-info">
            <div class="asset-filename" :title="asset.filename">
              {{ truncate(asset.filename, 20) }}
            </div>
            <div class="asset-meta">
              <span class="sha" :title="asset.sha256">
                {{ asset.sha256.slice(0, 8) }}...
              </span>
              <span class="provider">{{ asset.provider }}</span>
            </div>
          </div>
          <div v-if="selectedAssetSha === asset.sha256" class="check-badge">&#10003;</div>
        </div>
      </div>
    </section>

    <!-- Run Selection Section -->
    <section class="section" v-if="selectedAssetSha">
      <h4>3. Select Run</h4>
      <div v-if="isLoadingRuns" class="loading">Loading runs...</div>
      <div v-else-if="runs.length === 0" class="empty">
        No runs available.
        <div style="margin-top: 10px;">
          <button
            class="btn primary"
            type="button"
            :disabled="isLoadingRuns"
            @click="createAndSelectRun"
          >
            + Create Run (vision_image_review)
          </button>
        </div>
      </div>
      <div v-else class="runs-list">
        <div
          v-for="run in runs"
          :key="run.run_id"
          class="run-item"
          :class="{ selected: selectedRunId === run.run_id }"
          @click="selectRun(run.run_id)"
        >
          <div class="run-id">{{ run.run_id.slice(0, 12) }}...</div>
          <div class="run-meta">
            <span class="run-status" :class="run.status.toLowerCase()">
              {{ run.status }}
            </span>
            <span class="run-type">{{ run.event_type || run.mode || "run" }}</span>
            <span class="run-date">{{ formatDate(run.created_at_utc) }}</span>
          </div>
          <div v-if="selectedRunId === run.run_id" class="check-badge">&#10003;</div>
        </div>
      </div>
    </section>

    <!-- Attach Action -->
    <section class="section action-section" v-if="selectedAssetSha && selectedRunId">
      <h4>4. Attach</h4>
      <div class="attach-summary">
        <div class="summary-item">
          <span class="label">Asset:</span>
          <span class="value">{{ selectedAsset?.sha256.slice(0, 12) }}...</span>
        </div>
        <div class="summary-item">
          <span class="label">Run:</span>
          <span class="value">{{ selectedRunId?.slice(0, 12) }}...</span>
        </div>
      </div>
      <button
        class="btn primary attach-btn"
        :disabled="!canAttach"
        @click="attachToRun"
      >
        <span v-if="isAttaching">Attaching...</span>
        <span v-else>Attach to Run</span>
      </button>
    </section>
  </div>
</template>

<style scoped>
.vision-attach-widget {
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 16px;
  max-width: 600px;
  font-family: system-ui, -apple-system, sans-serif;
}

.widget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #eee;
}

.widget-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  color: #999;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
}
.close-btn:hover {
  background: #f5f5f5;
  color: #333;
}

.message {
  padding: 10px 12px;
  border-radius: 8px;
  margin-bottom: 12px;
  font-size: 13px;
  font-weight: 500;
}
.message.error {
  background: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecaca;
}
.message.success {
  background: #f0fdf4;
  color: #166534;
  border: 1px solid #bbf7d0;
}

.section {
  margin-bottom: 20px;
}
.section h4 {
  margin: 0 0 12px 0;
  font-size: 13px;
  font-weight: 700;
  color: #555;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.form-row {
  margin-bottom: 12px;
}
.form-row label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: #666;
  margin-bottom: 4px;
}
.form-row textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  resize: vertical;
  font-family: inherit;
}
.form-row textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-row-inline {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}
.form-field {
  flex: 1;
}
.form-field label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  color: #666;
  margin-bottom: 4px;
}
.form-field select {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 13px;
  background: #fff;
}

.btn {
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}
.btn.primary {
  background: #3b82f6;
  color: #fff;
}
.btn.primary:hover:not(:disabled) {
  background: #2563eb;
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.assets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
}

.asset-card {
  position: relative;
  border: 2px solid #e5e5e5;
  border-radius: 10px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.15s;
}
.asset-card:hover {
  border-color: #bbb;
}
.asset-card.selected {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

.asset-preview {
  aspect-ratio: 1;
  background: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
}
.asset-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.asset-info {
  padding: 8px;
  background: #fafafa;
}
.asset-filename {
  font-size: 11px;
  font-weight: 600;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.asset-meta {
  display: flex;
  gap: 8px;
  margin-top: 4px;
  font-size: 10px;
  color: #888;
}
.asset-meta .sha {
  font-family: monospace;
}

.check-badge {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 20px;
  height: 20px;
  background: #3b82f6;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
}

.runs-list {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #e5e5e5;
  border-radius: 8px;
}

.run-item {
  position: relative;
  padding: 10px 12px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  transition: background 0.1s;
}
.run-item:last-child {
  border-bottom: none;
}
.run-item:hover {
  background: #fafafa;
}
.run-item.selected {
  background: #eff6ff;
}

.run-id {
  font-family: monospace;
  font-size: 12px;
  font-weight: 600;
  color: #333;
}
.run-meta {
  display: flex;
  gap: 10px;
  margin-top: 4px;
  font-size: 11px;
  color: #666;
}
.run-status {
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 600;
  text-transform: uppercase;
  font-size: 10px;
}
.run-status.ok {
  background: #dcfce7;
  color: #166534;
}
.run-status.blocked {
  background: #fef3c7;
  color: #92400e;
}
.run-status.error {
  background: #fee2e2;
  color: #b91c1c;
}

.loading,
.empty {
  padding: 20px;
  text-align: center;
  color: #888;
  font-size: 13px;
}

.action-section {
  background: #f8fafc;
  margin: 0 -16px -16px -16px;
  padding: 16px;
  border-radius: 0 0 12px 12px;
  border-top: 1px solid #e5e5e5;
}

.attach-summary {
  display: flex;
  gap: 20px;
  margin-bottom: 12px;
}
.summary-item {
  font-size: 12px;
}
.summary-item .label {
  color: #666;
}
.summary-item .value {
  font-family: monospace;
  font-weight: 600;
  color: #333;
}

.attach-btn {
  width: 100%;
}
</style>
