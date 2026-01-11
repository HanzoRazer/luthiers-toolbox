<script setup lang="ts">
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
const activeTab = ref<"generate" | "attach">("generate");

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
</script>

<template>
  <div class="ai-images-view">
    <header class="view-header">
      <h1>Visual Analyzer</h1>
      <p class="subtitle">AI-powered guitar design visualization</p>

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
      </div>
    </header>

    <!-- Tab: Generate Images -->
    <div v-if="activeTab === 'generate'" class="tab-content generate-tab">
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
          <div v-else class="empty-state">
            <p>Select an image to view properties</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab: Attach to Run -->
    <div v-if="activeTab === 'attach'" class="tab-content attach-tab">
      <VisionAttachToRunWidget
        @attached="handleAttached"
        @error="(msg) => console.error('Attach error:', msg)"
      />
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
