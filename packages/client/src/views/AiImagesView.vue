<script setup lang="ts">
import { api } from '@/services/apiBase';
/**
 * AI Design Studio — AI-Powered Instrument Visualization
 *
 * Design tool for generating guitar concept images with DALL-E.
 * Provides the full workflow: generate → review → attach to run.
 *
 * Route: /ai-images
 */
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAiImageStore, VisionAttachToRunWidget } from "@/features/ai_images";
import GenerateTabPanel from "./ai_images/GenerateTabPanel.vue";
import AiContextPanel from "./ai_images/AiContextPanel.vue";

const store = useAiImageStore();
const router = useRouter();
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
// Send selected image to Blueprint Lab for vectorization
function handleVectorize() {
  if (!store.selectedImage) return;
  // Store the image URL in sessionStorage for Blueprint Lab to pick up
  const imageUrl = store.selectedImage.url;
  sessionStorage.setItem("blueprintLab.pendingImage", JSON.stringify({
    url: imageUrl,
    source: "ai-images",
    filename: `ai-generated-${store.selectedId}.png`,
    prompt: store.selectedImage.userPrompt,
  }));
  // Navigate to Blueprint Lab
  router.push("/blueprint");
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
      <h1>AI Design Studio</h1>
      <p class="subtitle">
        Generate stunning instrument concept images with AI
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
      <GenerateTabPanel
        :project-id="projectId"
        :images="store.images"
        :selected-id="store.selectedId"
        :selected-image="selectedImage"
        @select="handleImageSelect"
        @attach="handleAttach"
        @regenerate="handleRegenerate"
        @delete="handleDelete"
        @rate="handleRate"
        @vectorize="handleVectorize"
      />
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
      <AiContextPanel
        :run-id="aiContextRunId"
        :loading="aiContextLoading"
        :error="aiContextError"
        :result="aiContextResult"
        @update:run-id="aiContextRunId = $event"
        @build="buildAiContext"
        @copy="copyAiContext"
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

.attach-tab,
.context-tab {
  max-width: 900px;
  margin: 0 auto;
}
</style>
