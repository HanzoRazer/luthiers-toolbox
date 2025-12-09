<template>
  <div class="instrument-geometry-view">
    <InstrumentGeometryPanel />
  </div>
</template>

<script setup lang="ts">
import InstrumentGeometryPanel from "@/components/InstrumentGeometryPanel.vue";
</script>

<style scoped>
.instrument-geometry-view {
  width: 100%;
  min-height: 100vh;
  background: #0a0a0a;
}
</style>
