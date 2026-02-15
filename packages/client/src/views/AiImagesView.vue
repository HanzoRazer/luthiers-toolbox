<script setup lang="ts">
import { api } from '@/services/apiBase';
/**
 * AI Images View — Production Visual Analyzer Interface
 *
 * Main entry point for the AI Image Generation feature.
 * Provides the full workflow: generate → review → attach to run.
 *
 * Route: /ai-images
 */
import { ref, computed, onMounted } from "vue";
import {
  AiImagePanel,
  AiImageProperties,
  AiImageGallery,
  useAiImageStore,
  VisionAttachToRunWidget,
} from "@/features/ai_images";

const store = useAiImageStore();
const projectId = ref("default-project");
const activeTab = ref<"generate" | "attach" | "context">("generate");

// AI Context state
const aiContextLoading = ref(false);
const aiContextError = ref<string | null>(null);
const aiContextResult = ref<any>(null);
const aiContextRunId = ref("");

// Initialize on mount
onMounted(async () => {
  try {
    await store.initialize(projectId.value);
  } catch (e) {
    console.warn("Failed to initialize AI image store:", e);
  }
});

// Selected image from store
const selectedImage = computed(() => store.selectedImage);

// Event handlers
function handleImageSelect(imageId: string) {
  store.selectImage(imageId);
}

function handleAttach(imageId: string, targetId: string) {
  console.log("Attach request:", imageId, "->", targetId);
  // The VisionAttachToRunWidget handles this flow
}

function handleRegenerate() {
  if (store.selectedImage) {
    store.generate({
      prompt: store.selectedImage.userPrompt,
      projectId: projectId.value,
    });
  }
}

async function handleDelete() {
  if (store.selectedId) {
    await store.deleteImage(store.selectedId);
  }
}

async function handleRate(rating: number) {
  if (store.selectedId) {
    await store.rateImage(store.selectedId, rating);
  }
}

function handleAttached(payload: { runId: string; advisoryId: string }) {
  console.log("Image attached to run:", payload);
  // Could show toast or navigate
}

// AI Context functions
async function buildAiContext() {
  aiContextLoading.value = true;
  aiContextError.value = null;
  aiContextResult.value = null;

  try {
    const res = await api("/api/ai/context/build", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        run_id: aiContextRunId.value.trim() || null,
        include: ["run_summary", "design_intent", "governance_notes"],
      }),
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || `HTTP ${res.status}`);
    }

    aiContextResult.value = await res.json();
  } catch (e: any) {
    aiContextError.value = e.message || "Failed to build AI context";
  } finally {
    aiContextLoading.value = false;
  }
}

function copyAiContext() {
  if (!aiContextResult.value) return;
  const text = JSON.stringify(aiContextResult.value, null, 2);
  navigator.clipboard.writeText(text).catch(() => {
    // Fallback
    const ta = document.createElement("textarea");
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    document.body.removeChild(ta);
  });
}
</script>

<template>
  <div class="ai-images-view">
    <header class="view-header">
      <h1>Visual Analyzer</h1>
      <p class="subtitle">
        AI-powered guitar design visualization
      </p>

      <div class="tab-bar">
        <button
          :class="['tab', { active: activeTab === 'generate' }]"
          @click="activeTab = 'generate'"
        >
          Generate Images
        </button>
        <button
          :class="['tab', { active: activeTab === 'attach' }]"
          @click="activeTab = 'attach'"
        >
          Attach to Run
        </button>
        <button
          :class="['tab', { active: activeTab === 'context' }]"
          @click="activeTab = 'context'"
        >
          AI Context
        </button>
      </div>
    </header>

    <!-- Tab: Generate Images -->
    <div
      v-if="activeTab === 'generate'"
      class="tab-content generate-tab"
    >
      <div class="layout-three-col">
        <!-- Left: Generation Panel -->
        <div class="panel left-panel">
          <AiImagePanel
            :project-id="projectId"
            @image:select="handleImageSelect"
            @image:attach="handleAttach"
          />
        </div>

        <!-- Center: Gallery -->
        <div class="panel center-panel">
          <h2>Generated Images</h2>
          <AiImageGallery
            :images="store.images"
            :selected-id="store.selectedId"
            @select="handleImageSelect"
          />
        </div>

        <!-- Right: Properties -->
        <div class="panel right-panel">
          <AiImageProperties
            v-if="selectedImage"
            :image="selectedImage"
            @regenerate="handleRegenerate"
            @delete="handleDelete"
            @rate="handleRate"
          />
          <div
            v-else
            class="empty-state"
          >
            <p>Select an image to view properties</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab: Attach to Run -->
    <div
      v-if="activeTab === 'attach'"
      class="tab-content attach-tab"
    >
      <VisionAttachToRunWidget
        @attached="handleAttached"
        @error="(msg) => console.error('Attach error:', msg)"
      />
    </div>

    <!-- Tab: AI Context -->
    <div
      v-if="activeTab === 'context'"
      class="tab-content context-tab"
    >
      <div class="context-panel">
        <h2>Generate AI Context</h2>
        <p class="context-description">
          Build a bounded context envelope for AI consumption.
          Manufacturing secrets (toolpaths, G-code) are excluded by design.
        </p>

        <div class="context-form">
          <label>
            Run ID (optional)
            <input
              v-model="aiContextRunId"
              type="text"
              placeholder="run_abc123..."
              class="context-input"
            >
          </label>

          <button
            class="btn-build-context"
            :disabled="aiContextLoading"
            @click="buildAiContext"
          >
            {{ aiContextLoading ? 'Building...' : 'Build AI Context' }}
          </button>
        </div>

        <div
          v-if="aiContextError"
          class="context-error"
        >
          <strong>Error:</strong> {{ aiContextError }}
        </div>

        <div
          v-if="aiContextResult"
          class="context-result"
        >
          <div class="context-result-header">
            <span class="context-id">{{ aiContextResult.context_id }}</span>
            <button
              class="btn-copy"
              @click="copyAiContext"
            >
              Copy JSON
            </button>
          </div>

          <div
            v-if="aiContextResult.warnings?.length"
            class="context-warnings"
          >
            <strong>Warnings:</strong>
            <ul>
              <li
                v-for="(w, i) in aiContextResult.warnings"
                :key="i"
              >
                {{ w }}
              </li>
            </ul>
          </div>

          <pre class="context-json">{{ JSON.stringify(aiContextResult, null, 2) }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ai-images-view {
  min-height: 100vh;
  background: var(--bg-page, #0d1421);
  color: var(--text, #e0e0e0);
}

.view-header {
  padding: 24px 32px;
  border-bottom: 1px solid var(--border, #2a3f5f);
}

.view-header h1 {
  margin: 0 0 4px;
  font-size: 24px;
  font-weight: 700;
  color: var(--text, #fff);
}

.subtitle {
  margin: 0 0 16px;
  font-size: 14px;
  color: var(--text-dim, #8892a0);
}

.tab-bar {
  display: flex;
  gap: 8px;
}

.tab {
  padding: 10px 20px;
  background: var(--bg-input, #0f1629);
  border: 1px solid var(--border, #2a3f5f);
  border-radius: 8px;
  color: var(--text-dim, #8892a0);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.tab:hover {
  background: var(--bg-panel, #16213e);
  color: var(--text, #e0e0e0);
}

.tab.active {
  background: var(--accent, #4fc3f7);
  border-color: var(--accent, #4fc3f7);
  color: #000;
}

.tab-content {
  padding: 24px 32px;
}

.layout-three-col {
  display: grid;
  grid-template-columns: 320px 1fr 300px;
  gap: 24px;
  min-height: calc(100vh - 200px);
}

.panel {
  background: var(--bg-panel, #16213e);
  border: 1px solid var(--border, #2a3f5f);
  border-radius: 12px;
  padding: 16px;
  overflow: hidden;
}

.panel h2 {
  margin: 0 0 16px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text, #fff);
}

.center-panel {
  overflow-y: auto;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--text-dim, #8892a0);
  font-size: 14px;
}

.attach-tab {
  max-width: 900px;
  margin: 0 auto;
}

/* AI Context Tab */
.context-tab {
  max-width: 900px;
  margin: 0 auto;
}

.context-panel {
  background: var(--bg-panel, #16213e);
  border: 1px solid var(--border, #2a3f5f);
  border-radius: 12px;
  padding: 24px;
}

.context-panel h2 {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 600;
  color: var(--text, #fff);
}

.context-description {
  margin: 0 0 20px;
  font-size: 14px;
  color: var(--text-dim, #8892a0);
}

.context-form {
  display: flex;
  gap: 16px;
  align-items: flex-end;
  margin-bottom: 20px;
}

.context-form label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 14px;
  color: var(--text-dim, #8892a0);
}

.context-input {
  padding: 10px 14px;
  background: var(--bg-input, #0f1629);
  border: 1px solid var(--border, #2a3f5f);
  border-radius: 8px;
  color: var(--text, #e0e0e0);
  font-size: 14px;
  width: 280px;
}

.context-input:focus {
  outline: none;
  border-color: var(--accent, #4fc3f7);
}

.btn-build-context {
  padding: 10px 20px;
  background: var(--accent, #4fc3f7);
  border: none;
  border-radius: 8px;
  color: #000;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-build-context:hover:not(:disabled) {
  background: #29b6f6;
}

.btn-build-context:disabled {
  background: var(--bg-input, #0f1629);
  color: var(--text-dim, #8892a0);
  cursor: not-allowed;
}

.context-error {
  background: rgba(244, 67, 54, 0.15);
  border: 1px solid #f44336;
  border-radius: 8px;
  padding: 12px 16px;
  color: #f44336;
  margin-bottom: 16px;
  font-size: 14px;
}

.context-result {
  background: var(--bg-input, #0f1629);
  border: 1px solid var(--border, #2a3f5f);
  border-radius: 8px;
  overflow: hidden;
}

.context-result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border, #2a3f5f);
}

.context-id {
  font-family: monospace;
  font-size: 13px;
  color: var(--accent, #4fc3f7);
}

.btn-copy {
  padding: 6px 12px;
  background: var(--bg-panel, #16213e);
  border: 1px solid var(--border, #2a3f5f);
  border-radius: 6px;
  color: var(--text, #e0e0e0);
  font-size: 12px;
  cursor: pointer;
}

.btn-copy:hover {
  background: var(--accent, #4fc3f7);
  color: #000;
}

.context-warnings {
  padding: 12px 16px;
  background: rgba(255, 193, 7, 0.1);
  border-bottom: 1px solid var(--border, #2a3f5f);
  font-size: 13px;
  color: #ffc107;
}

.context-warnings ul {
  margin: 8px 0 0 20px;
  padding: 0;
}

.context-warnings li {
  margin-bottom: 4px;
}

.context-json {
  margin: 0;
  padding: 16px;
  font-family: monospace;
  font-size: 12px;
  color: var(--text, #e0e0e0);
  overflow-x: auto;
  max-height: 500px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

/* Responsive */
@media (max-width: 1200px) {
  .layout-three-col {
    grid-template-columns: 1fr;
  }

  .left-panel,
  .right-panel {
    max-width: 100%;
  }
}
</style>
