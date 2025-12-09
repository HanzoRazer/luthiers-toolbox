<template>
  <div class="export-toolbar">
    <button @click="$emit('export-dxf')" aria-label="Export DXF (Diff)">Export DXF (Diff)</button>
    <button @click="$emit('export-svg')" aria-label="Export SVG (Diff)">Export SVG (Diff)</button>
    <button @click="$emit('export-gcode')" aria-label="Export G-code (Candidate)">Export G-code (Candidate)</button>
  </div>
</template>
<script setup lang="ts">
defineEmits(['export-dxf', 'export-svg', 'export-gcode'])
</script>
<style scoped>
.export-toolbar { margin: 1.5rem 0; display: flex; gap: 1rem; }
</style>
