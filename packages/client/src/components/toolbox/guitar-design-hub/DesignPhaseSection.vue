<script setup lang="ts">
/**
 * DesignPhaseSection - Phase category wrapper for Guitar Design Hub
 * Extracted from GuitarDesignHub.vue
 */
defineProps<{
  icon: string
  phase: string
  title: string
  description: string
}>()
</script>

<template>
  <div class="design-category">
    <h3>{{ icon }} {{ phase }}: {{ title }}</h3>
    <p class="phase-desc">
      {{ description }}
    </p>
    <div class="tool-cards">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.design-category {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  border-left: 4px solid #3b82f6;
}

.design-category h3 {
  font-size: 1.6rem;
  margin-bottom: 0.5rem;
  color: #2c3e50;
}

.phase-desc {
  color: #666;
  font-style: italic;
  margin-bottom: 1.5rem;
  font-size: 0.95rem;
}

.tool-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1.25rem;
}
</style>
