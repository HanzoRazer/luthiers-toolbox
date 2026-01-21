<template>
  <div class="export-toolbar">
    <button
      aria-label="Export DXF (Diff)"
      @click="$emit('export-dxf')"
    >
      Export DXF (Diff)
    </button>
    <button
      aria-label="Export SVG (Diff)"
      @click="$emit('export-svg')"
    >
      Export SVG (Diff)
    </button>
    <button
      aria-label="Export G-code (Candidate)"
      @click="$emit('export-gcode')"
    >
      Export G-code (Candidate)
    </button>
  </div>
</template>
<script setup lang="ts">
defineEmits(['export-dxf', 'export-svg', 'export-gcode'])
</script>
<style scoped>
.export-toolbar { margin: 1.5rem 0; display: flex; gap: 1rem; }
</style>
