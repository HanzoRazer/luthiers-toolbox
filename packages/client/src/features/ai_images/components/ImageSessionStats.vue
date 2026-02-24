<script setup lang="ts">
/**
 * ImageSessionStats - Session statistics display
 * Extracted from AiImageProperties.vue
 */
import { useAiImageStore } from '../useAiImageStore'

defineProps<{
  provider: string
  providerName: string
}>()

const store = useAiImageStore()
</script>

<template>
  <div class="stats-section">
    <h4>Session Stats</h4>

    <div class="property-row">
      <span class="label">Images today</span>
      <span class="value">{{ store.sessionCount }}</span>
    </div>

    <div class="property-row">
      <span class="label">Total cost</span>
      <span class="value">${{ store.totalCost.toFixed(2) }}</span>
    </div>

    <div
      v-if="store.providerStats[provider]"
      class="property-row"
    >
      <span class="label">{{ providerName }} count</span>
      <span class="value">{{ store.providerStats[provider]?.count ?? 0 }}</span>
    </div>
  </div>
</template>

<style scoped>
.stats-section {
  padding: 16px;
  border-bottom: 1px solid var(--border, #2a3f5f);
}

.stats-section h4 {
  font-size: 12px;
  color: var(--text-dim, #8892a0);
  text-transform: uppercase;
  margin: 0 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border, #2a3f5f);
}

.property-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 13px;
}

.property-row .label {
  color: var(--text-dim, #8892a0);
}

.property-row .value {
  color: var(--text, #e0e0e0);
}
</style>
