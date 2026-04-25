<script setup lang="ts">
/**
 * WoodworkingCalculator - Standalone woodworking calculator for Calculator Hub
 * Wraps WoodworkPanel with state management
 * Seeds the Woodworking Suite per Phase 2 triage decisions
 */
import { ref } from 'vue'
import WoodworkPanel from './calculator/WoodworkPanel.vue'

const woodworkCategories = ['Board Feet', 'Volume', 'Angles']
const activeCategory = ref('Board Feet')
</script>

<template>
  <div class="woodworking-calculator-wrapper">
    <WoodworkPanel
      v-model:active-category="activeCategory"
      :categories="woodworkCategories"
    />
  </div>
</template>

<style scoped>
.woodworking-calculator-wrapper {
  padding: 1.5rem;
  background: #1e1e1e;
  min-height: 100%;
}
</style>
