<script setup lang="ts">
/**
 * Test view for VisionAttachToRunWidget
 * Route: /dev/vision-attach
 */
import { ref } from 'vue';
import { VisionAttachToRunWidget } from '@/features/ai_images';

const showWidget = ref(true);

function handleAttached(payload: { runId: string; advisoryId: string }) {
  console.log('Attached:', payload);
  alert(`Attached advisory ${payload.advisoryId.slice(0, 12)}... to run ${payload.runId.slice(0, 12)}...`);
}

function handleError(message: string) {
  console.error('Error:', message);
}

function handleClose() {
  showWidget.value = false;
}
</script>

<template>
  <div class="test-container">
    <h1>Vision Attach Widget Test</h1>
    <p>This is a test page for the VisionAttachToRunWidget component.</p>

    <button
      v-if="!showWidget"
      class="show-btn"
      @click="showWidget = true"
    >
      Show Widget
    </button>

    <VisionAttachToRunWidget
      v-if="showWidget"
      @attached="handleAttached"
      @error="handleError"
      @close="handleClose"
    />
  </div>
</template>

<style scoped>
.test-container {
  max-width: 800px;
  margin: 40px auto;
  padding: 20px;
  font-family: system-ui, -apple-system, sans-serif;
}

h1 {
  margin-bottom: 8px;
  color: #333;
}

p {
  color: #666;
  margin-bottom: 24px;
}

.show-btn {
  padding: 12px 24px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}
.show-btn:hover {
  background: #2563eb;
}
</style>
