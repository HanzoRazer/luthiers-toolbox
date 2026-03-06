<template>
  <div class="layout-three-col">
    <!-- Left: Generation Panel -->
    <div class="panel left-panel">
      <AiImagePanel
        :project-id="projectId"
        @image:select="$emit('select', $event)"
        @image:attach="(imageId, targetId) => $emit('attach', imageId, targetId)"
      />
    </div>

    <!-- Center: Gallery -->
    <div class="panel center-panel">
      <h2>Generated Images</h2>
      <AiImageGallery
        :images="images"
        :selected-id="selectedId"
        @select="$emit('select', $event)"
      />
    </div>

    <!-- Right: Properties -->
    <div class="panel right-panel">
      <AiImageProperties
        v-if="selectedImage"
        :image="selectedImage"
        @regenerate="$emit('regenerate')"
        @delete="$emit('delete')"
        @rate="$emit('rate', $event)"
        @vectorize="$emit('vectorize')"
      />
      <div
        v-else
        class="empty-state"
      >
        <p>Select an image to view properties</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  AiImagePanel,
  AiImageProperties,
  AiImageGallery,
} from "@/features/ai_images"
import type { ImageAsset } from "@/features/ai_images/types"

defineProps<{
  projectId: string
  images: ImageAsset[]
  selectedId: string | null
  selectedImage: ImageAsset | null
}>()

defineEmits<{
  select: [imageId: string]
  attach: [imageId: string, targetId: string]
  regenerate: []
  delete: []
  rate: [rating: number]
  vectorize: []
}>()
</script>

<style scoped>
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
