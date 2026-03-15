<script setup lang="ts">
/**
 * ResolutionSlider — Resolution adjustment bar for ToolpathPlayer
 *
 * Extracted from ToolpathPlayer.vue to reduce component size.
 * Shows resolution slider when memory warning is active.
 */

import { ref } from 'vue';

interface Props {
  visible: boolean;
}

defineProps<Props>();

const emit = defineEmits<{
  apply: [resolution: number];
}>();

const resSlider = ref(100);

function applyResolution(): void {
  emit('apply', resSlider.value);
}
</script>

<template>
  <div
    v-if="visible"
    class="res-bar"
  >
    <span class="res-label">Resolution:</span>
    <input
      v-model.number="resSlider"
      type="range"
      class="res-slider"
      min="10"
      max="100"
    >
    <span class="res-val">{{ resSlider }}%</span>
    <button
      class="res-apply"
      @click="applyResolution"
    >
      Apply
    </button>
  </div>
</template>

<style scoped>
.res-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 10px;
  background: #1a1a2e;
  border-top: 1px solid #2a2a4a;
  font-size: 11px;
  color: #aaa;
}

.res-label {
  color: #666;
}

.res-slider {
  flex: 1;
  accent-color: #4a90d9;
  height: 4px;
}

.res-val {
  min-width: 36px;
  color: #4a90d9;
}

.res-apply {
  padding: 2px 8px;
  background: #252538;
  border: 1px solid #3a3a5c;
  color: #ccc;
  border-radius: 4px;
  cursor: pointer;
}

.res-apply:hover {
  background: #33334a;
  color: #fff;
}
</style>
