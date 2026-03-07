<template>
  <div class="guitar-dimensions-view">
    <GuitarDimensionsForm />
  </div>
</template>

<script setup lang="ts">
/**
 * GuitarDimensionsView - Wrapper view for parametric guitar body design
 *
 * Query params (loaded automatically by useGuitarDimensions composable):
 * - preset: "ai-extracted" triggers AI dimension loading
 * - bodyLength, bodyWidthLower, bodyWidthUpper, etc.
 */
import GuitarDimensionsForm from '@/components/toolbox/GuitarDimensionsForm.vue'
</script>

<style scoped>
.guitar-dimensions-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}
</style>
